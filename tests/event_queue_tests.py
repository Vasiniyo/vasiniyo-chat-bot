import threading
import time
import unittest
from unittest.mock import patch

from src.event_queue import EVENTS, add_task, cancel_task, tick


def log_tick_results(result, current_tick):
    def record(val):
        result.append((val, current_tick["i"]))

    return record


class TestEventQueueSync(unittest.TestCase):

    # ---------- helpers --------------------------------------------------
    def _drive_ticks(self, total, current_tick):
        for _ in range(total + 1):
            tick()
            current_tick["i"] += 1

    # ---------- tests ----------------------------------------------------
    @patch("src.event_queue.start_ticking_if_needed", lambda: None)
    def test_start_middle_success(self):
        EVENTS.clear()
        result, current_tick = [], {"i": 0}
        record = log_tick_results(result, current_tick)

        total, freq = 10, 2
        timestamps = list(range(0, total + 1, freq))  # [0,2,4,6,8,10]
        middle = timestamps[len(timestamps) // 2]  # 6

        add_task(
            timestamps=timestamps,
            default={"func": record, "args": ("default",)},
            conditional_funcs={
                "on_start": {"func": record, "args": ("start",)},
                "on_success": {"func": record, "args": ("success",)},
                middle: {"func": record, "args": ("middle",)},
            },
        )

        self._drive_ticks(total, current_tick)

        expected = [
            ("start", 0),
            ("default", 2),
            ("default", 4),
            ("middle", 6),
            ("default", 8),
            ("success", 10),
        ]
        self.assertEqual(result, expected)

    # ---------- silent-success ------------------------------------------
    @patch("src.event_queue.start_ticking_if_needed", lambda: None)
    def test_silent_success(self):
        EVENTS.clear()
        result, current_tick = [], {"i": 0}
        record = log_tick_results(result, current_tick)

        total = 10
        timestamps = [0, 10]

        task_id = add_task(
            timestamps=timestamps,
            default={"func": record, "args": ("default",)},
            conditional_funcs={
                "on_start": {"func": record, "args": ("start",)},
                "on_success": {"func": record, "args": ("success",)},
                "on_cancel": {"func": record, "args": ("cancel",)},
            },
        )

        def cancel_after_one_tick():
            time.sleep(0.75)
            cancel_task(task_id, silently=True)

        threading.Thread(target=cancel_after_one_tick).start()

        while task_id in EVENTS:
            tick()
            current_tick["i"] += 1
            time.sleep(0.25)

        self.assertEqual(result, [("start", 0)])

    # ---------- final-tick ----------------------------------------------
    @patch("src.event_queue.start_ticking_if_needed", lambda: None)
    def test_success_runs_on_final_tick(self):
        EVENTS.clear()
        result, current_tick = [], {"i": 0}
        record = log_tick_results(result, current_tick)

        total = 4
        timestamps = [0, 2, 4]

        add_task(
            timestamps=timestamps,
            default={"func": record, "args": ("default",)},
            conditional_funcs={
                "on_start": {"func": record, "args": ("start",)},
                "on_success": {"func": record, "args": ("success",)},
            },
        )

        self._drive_ticks(total, current_tick)

        expected = [("start", 0), ("default", 2), ("success", 4)]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
