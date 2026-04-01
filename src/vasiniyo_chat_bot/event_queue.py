from collections import deque
import logging
from threading import Event, Thread
import time
from typing import Callable
import uuid

logger = logging.getLogger(__name__)

EVENTS = {}
TICK_JOB_RUNNING = False
TICK_THREAD = None
TICK_THREAD_STOP = Event()


def add_task(
    timestamps,
    default: Callable[[], None],
    conditional_funcs=dict[
        "on_start" : Callable[[], None],
        "on_success" : Callable[[], None],
        "on_cancel" : Callable[[], None],
        str : Callable[[], None],
    ],
):
    """
    Queue a sequence of timestamped actions to be executed over time.
    An action (function with argumets) will be lazy-evaled on each timestamp.
    Tasks can be canceled prematurelly with cancel_task

    Args:
        timestamps (Iterable[int]): A list of countdowns
        default (callable): The default function to execute at each timestamp.
        conditional_funcs (dict, optional): Overrides the default function:
            - "on_start": callable
                -> executes INSTEAD of the FIRST ts
            - "on_success": callable
                -> executes INSTEAD of the LAST ts
            - "on_cancel": callable
                -> executes on the task cancel
            -  Or custom timestamp-based overrides: {timestamp: callable}

    Returns:
        str: A UUID key identifying the registered task.

    EXAMPLE:
        task_id = add_task(
            timestamps=list(range(freq, total + 1, freq)),
            default=lambda: update_captcha_message(user_id),
            conditional_funcs={
                "on_success": lambda: fail_user(user_id, "❌ Time expired"),
                "on_cancel": lambda: fail_user(user_id, "❌ CAPTCHA cancelled")
            }
        )
    """
    key = str(uuid.uuid4())
    if not conditional_funcs:
        conditional_funcs = {}

    sorted_ts = sorted(timestamps)
    sub_events = deque()

    for i, ts in enumerate(sorted_ts):
        if i == 0 and "on_start" in conditional_funcs:
            action = conditional_funcs["on_start"]
        elif i == len(sorted_ts) - 1 and "on_success" in conditional_funcs:
            action = conditional_funcs["on_success"]
        elif ts in conditional_funcs:
            action = conditional_funcs[ts]
        else:
            action = default
        sub_events.append({"timestamp": ts, "action": action})

    EVENTS[key] = {
        "offset": 0,
        "cancelled": False,
        "sub_events": sub_events,
        "conditional_funcs": conditional_funcs,
    }
    start_ticking_if_needed()
    return key


def cancel_task(key, silently=False):
    if key in EVENTS:
        EVENTS[key]["cancelled"] = True
        cond = EVENTS[key].get("conditional_funcs", {})
        logger.debug("⛔ Canceling task", extra={"task": key})
        if silently:
            return

        if "on_cancel" in cond:
            func = cond["on_cancel"]
            logger.debug(
                "Executing on_cancel",
                extra={"func": getattr(func, "__name__", repr(func))},
            )
            try:
                func()
            except Exception:
                logger.exception("on_cancel hook failed", extra={"task": key})


def tick():
    remove_keys = []

    for key, event in list(EVENTS.items()):
        if event["cancelled"]:
            remove_keys.append(key)
            continue

        if not event["sub_events"]:
            remove_keys.append(key)
            continue

        offset = event["offset"]

        while event["sub_events"] and event["sub_events"][0]["timestamp"] <= offset:
            next_event = event["sub_events"].popleft()
            try:
                next_event["action"]()
            except:
                logger.exception("Event failed", extra={"task": key})

        event["offset"] += 1

        if not event["sub_events"]:
            remove_keys.append(key)

    for key in remove_keys:
        EVENTS.pop(key, None)
        logger.debug("Removed entire event", extra={"task": key})

    if not EVENTS:
        stop_ticking()


def start_ticking_if_needed():
    global TICK_JOB_RUNNING, TICK_THREAD
    if TICK_JOB_RUNNING:
        return
    if not EVENTS:
        return

    logger.debug("Started ticking thread for event_queue")
    TICK_JOB_RUNNING = True
    TICK_THREAD_STOP.clear()

    def loop():
        while not TICK_THREAD_STOP.is_set():
            tick()
            time.sleep(1)

    TICK_THREAD = Thread(target=loop, daemon=True)
    TICK_THREAD.start()


def stop_ticking():
    global TICK_JOB_RUNNING
    TICK_THREAD_STOP.set()
    TICK_JOB_RUNNING = False
    logger.debug("Stopped ticking thread since no events remain")


def is_thread_running():
    return TICK_JOB_RUNNING
