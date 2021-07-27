from typing import Optional

from Project.schedule import Schedule

_schedule_queue: list[Schedule] = list[Schedule]()
_current_schedule: Optional[Schedule] = None


def enqueue_schedule(schedule: Schedule) -> None:
    print("Enqueue Schedule!")
    _schedule_queue.append(schedule)
    rotate()


def rotate() -> None:
    global _current_schedule
    global _schedule_queue
    if _current_schedule is None:
        if _schedule_queue:
            _current_schedule = _schedule_queue.pop(0)
            print(f"Queue: {_schedule_queue}, Current Schedule = {_current_schedule}")
            _current_schedule.measure()
        else:
            print("No schedules on queue!")
    else:
        print("Couldn't execute current schedule since a measure is already running")


def measurement_finish() -> None:
    global _current_schedule
    global _schedule_queue
    print("Measure Finished!")
    _current_schedule = None
    rotate()