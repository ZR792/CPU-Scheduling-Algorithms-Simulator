from copy import deepcopy
from typing import List

class Process:
    def __init__(self, pid, arrival, burst, priority=1):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
        self.remaining = burst

        # Output values
        self.start_time = None
        self.completion_time = None
        self.response_time = None

    def reset(self):
        self.remaining = self.burst
        self.start_time = None
        self.completion_time = None
        self.response_time = None


# -------------------------------------------------------------
# ---------------------- FCFS ---------------------------------
# -------------------------------------------------------------
def fcfs(process_list: List[Process]):
    procs = deepcopy(process_list)
    procs.sort(key=lambda p: p.arrival)

    time = 0
    gantt = []

    for p in procs:
        if time < p.arrival:
            time = p.arrival

        p.start_time = time
        p.response_time = p.start_time - p.arrival
        gantt.append((p.pid, time, p.burst))
        time += p.burst
        p.completion_time = time

    _sync(process_list, procs)
    return gantt


# -------------------------------------------------------------
# ------------------- SJF NON-PREEMPTIVE ----------------------
# -------------------------------------------------------------
def sjf_non_preemptive(process_list: List[Process]):
    procs = deepcopy(process_list)
    time = 0
    completed = 0
    gantt = []
    n = len(procs)

    while completed < n:
        ready = [p for p in procs if p.arrival <= time and p.completion_time is None]

        if not ready:
            time = min(p.arrival for p in procs if p.completion_time is None)
            continue

        current = min(ready, key=lambda p: (p.burst, p.arrival))

        if current.start_time is None:
            current.start_time = time
            current.response_time = current.start_time - current.arrival

        gantt.append((current.pid, time, current.burst))
        time += current.burst
        current.completion_time = time
        current.remaining = 0
        completed += 1

    _sync(process_list, procs)
    return gantt


# -------------------------------------------------------------
# ------------------- SJF PREEMPTIVE --------------------------
# -------------------------------------------------------------
def sjf_preemptive(process_list: List[Process]):
    procs = deepcopy(process_list)
    time = 0
    completed = 0
    gantt = []
    n = len(procs)
    last_pid = None

    while completed < n:
        ready = [p for p in procs if p.arrival <= time and p.remaining > 0]

        if not ready:
            time = min(p.arrival for p in procs if p.remaining > 0)
            last_pid = None
            continue

        current = min(ready, key=lambda p: (p.remaining, p.arrival))

        if current.start_time is None:
            current.start_time = time
            current.response_time = current.start_time - current.arrival

        # Gantt block begins
        if last_pid != current.pid:
            gantt.append((current.pid, time, 1))
        else:
            pid, start, dur = gantt.pop()
            gantt.append((pid, start, dur + 1))

        current.remaining -= 1
        time += 1
        last_pid = current.pid

        if current.remaining == 0:
            current.completion_time = time
            completed += 1

    _sync(process_list, procs)
    return gantt


# -------------------------------------------------------------
# -------------- PRIORITY NON-PREEMPTIVE ----------------------
# -------------------------------------------------------------
def priority_non_preemptive(process_list: List[Process]):
    procs = deepcopy(process_list)
    time = 0
    completed = 0
    gantt = []
    n = len(procs)

    while completed < n:
        ready = [p for p in procs if p.arrival <= time and p.completion_time is None]

        if not ready:
            time = min(p.arrival for p in procs if p.completion_time is None)
            continue

        current = min(ready, key=lambda p: (p.priority, p.arrival))

        if current.start_time is None:
            current.start_time = time
            current.response_time = current.start_time - current.arrival

        gantt.append((current.pid, time, current.burst))
        time += current.burst
        current.completion_time = time
        current.remaining = 0
        completed += 1

    _sync(process_list, procs)
    return gantt


# -------------------------------------------------------------
# -------------- PRIORITY PREEMPTIVE --------------------------
# -------------------------------------------------------------
def priority_preemptive(process_list: List[Process]):
    procs = deepcopy(process_list)
    time = 0
    completed = 0
    gantt = []
    n = len(procs)
    last_pid = None

    while completed < n:
        ready = [p for p in procs if p.arrival <= time and p.remaining > 0]

        if not ready:
            time = min(p.arrival for p in procs if p.remaining > 0)
            last_pid = None
            continue

        current = min(ready, key=lambda p: (p.priority, p.arrival))

        if current.start_time is None:
            current.start_time = time
            current.response_time = current.start_time - current.arrival

        if last_pid != current.pid:
            gantt.append((current.pid, time, 1))
        else:
            pid, start, dur = gantt.pop()
            gantt.append((pid, start, dur + 1))

        current.remaining -= 1
        time += 1
        last_pid = current.pid

        if current.remaining == 0:
            current.completion_time = time
            completed += 1

    _sync(process_list, procs)
    return gantt


# -------------------------------------------------------------
# --------------------- ROUND ROBIN ---------------------------
# -------------------------------------------------------------
def round_robin(process_list: List[Process], quantum: int):
    procs = deepcopy(process_list)

    time = 0
    i = 0
    gantt = []
    queue = []

    procs_by_arrival = sorted(procs, key=lambda p: p.arrival)
    n = len(procs)

    # Load initial arrivals
    while i < n and procs_by_arrival[i].arrival <= time:
        queue.append(procs_by_arrival[i])
        i += 1

    if not queue and i < n:
        time = procs_by_arrival[i].arrival
        queue.append(procs_by_arrival[i])
        i += 1

    while queue:
        cur = queue.pop(0)

        if cur.start_time is None:
            cur.start_time = time
            cur.response_time = cur.start_time - cur.arrival

        run = min(quantum, cur.remaining)
        gantt.append((cur.pid, time, run))
        time += run
        cur.remaining -= run

        # Add arrivals during execution
        while i < n and procs_by_arrival[i].arrival <= time:
            queue.append(procs_by_arrival[i])
            i += 1

        if cur.remaining > 0:
            queue.append(cur)
        else:
            cur.completion_time = time

        if not queue and i < n:
            time = procs_by_arrival[i].arrival
            queue.append(procs_by_arrival[i])
            i += 1

    _sync(process_list, procs)
    return gantt


# -------------------------------------------------------------
# ----------- UTILITY TO SYNC RESULTS BACK TO ORIGINAL --------
# -------------------------------------------------------------
def _sync(orig_list, new_list):
    for orig in orig_list:
        for p in new_list:
            if p.pid == orig.pid:
                orig.start_time = p.start_time
                orig.completion_time = p.completion_time
                orig.response_time = p.response_time
                orig.remaining = p.remaining
