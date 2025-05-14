from collections import deque
import logging
from threading import Event, Thread
import time
import uuid

logger = logging.getLogger(__name__)

EVENTS = {}
TICK_JOB_RUNNING = False
TICK_THREAD = None
TICK_THREAD_STOP = Event()


# lazy eval (i hope this works)
def _wrap_action(func, args):
    def wrapped():
        logger.debug(">> Evaluating: %s%s", func.__name__, args)
        return func(*args)

    return wrapped


def add_task(timestamps, default, conditional_funcs=None):
    """
    Queue a sequence of timestamped actions to be executed over time.
    An action (function with argumets) will be lazy-evaled on each timestamp.
    Tasks can be canceled prematurelly with cancel_task

    Args:
        timestamps (Iterable[int]): A list of countdowns
        default (dict): A dictionary with keys:
            - "func" (callable): The default function to execute at each timestamp.
            - "args" (tuple): Arguments to pass to the function.
        conditional_funcs (dict, optional): Overrides the default function:
            - "on_start":   {"func": callable, "args": tuple}
                -> executes INSTEAD of the FIRST ts
            - "on_success": {"func": callable, "args": tuple}
                -> executes INSTEAD of the LAST ts
            - "on_cancel":  {"func": callable, "args": tuple}
                -> executes on the task cancel
            -  Or custom timestamp-based overrides: {timestamp: {"func": ..., "args": ...}}

    Returns:
        str: A UUID key identifying the registered task.

    EXAMPLE:
        task_id = add_task(
            timestamps=list(range(freq, total + 1, freq)),
            default={"func": update_captcha_message, "args": (user_id,)},
            conditional_funcs={
                "on_success": {"func": fail_user, "args": (user_id, "❌ Time expired")},
                "on_cancel": {"func": fail_user, "args": (user_id, "❌ CAPTCHA cancelled")},
            },
        )
    """
    key = str(uuid.uuid4())
    if not conditional_funcs:
        conditional_funcs = {}

    sorted_ts = sorted(timestamps)
    sub_events = deque()

    for i, ts in enumerate(sorted_ts):
        if i == 0 and "on_start" in conditional_funcs:
            func = conditional_funcs["on_start"]["func"]
            args = conditional_funcs["on_start"].get("args", ())
            action = _wrap_action(func, args)
        elif i == len(sorted_ts) - 1 and "on_success" in conditional_funcs:
            func = conditional_funcs["on_success"]["func"]
            args = conditional_funcs["on_success"].get("args", ())
            action = _wrap_action(func, args)
        elif ts in conditional_funcs:
            func = conditional_funcs[ts]["func"]
            args = conditional_funcs[ts].get("args", ())
            action = _wrap_action(func, args)
        else:
            func = default["func"]
            args = default.get("args", ())
            action = _wrap_action(func, args)

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
        logger.debug("⛔ Canceling task: %s", key)
        if silently:
            return

        if "on_cancel" in cond:
            func = cond["on_cancel"]["func"]
            args = cond["on_cancel"].get("args", ())
            logger.debug(
                "🔁 Executing on_cancel: %s%s",
                getattr(func, "__name__", repr(func)),
                args,
            )

            try:
                func(*args)
            except Exception:
                logger.exception("❌ on_cancel hook failed for task %s", key)


def tick():
    remove_keys = []

    for key, event in list(EVENTS.items()):
        if event["cancelled"]:
            remove_keys.append(key)
            continue

        if not event["sub_events"]:
            remove_keys.append(key)
            continue

        event["offset"] += 1
        offset = event["offset"]

        while event["sub_events"] and event["sub_events"][0]["timestamp"] <= offset:
            next_event = event["sub_events"].popleft()
            try:
                next_event["action"]()
            except Exception as e:
                logger.exception("Event key=%s failed: %s", key, e)

        if not event["sub_events"]:
            remove_keys.append(key)

    for k in remove_keys:
        EVENTS.pop(k, None)
        logger.debug("Removed entire event key=%s", k)

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
