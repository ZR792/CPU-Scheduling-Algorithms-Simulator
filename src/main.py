# main.py
import sys
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Tuple, Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt

from animation_widget import AnimationWidget


# ---------------------------
# Data class
# ---------------------------
@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int
    remaining: int = None
    start_time: int = None
    completion_time: int = None
    response_time: int = None

    def __post_init__(self):
        if self.remaining is None:
            self.remaining = self.burst

    def reset_runtime(self):
        self.remaining = self.burst
        self.start_time = None
        self.completion_time = None
        self.response_time = None


# ---------------------------
# Schedulers (return gantt list and update processes)
# gantt: List[ (pid, start, duration) ]
# ---------------------------
def fcfs_scheduler(process_list: List[Process]) -> List[Tuple[str,int,int]]:
    procs = deepcopy(process_list)
    procs.sort(key=lambda p: (p.arrival, p.pid))
    time_cursor = 0
    gantt = []
    for p in procs:
        if time_cursor < p.arrival:
            time_cursor = p.arrival
        if p.start_time is None:
            p.start_time = time_cursor
            p.response_time = p.start_time - p.arrival
        gantt.append((p.pid, time_cursor, p.burst))
        time_cursor += p.burst
        p.completion_time = time_cursor
        p.remaining = 0
    _sync(process_list, procs)
    return gantt

def sjf_nonpreemptive(process_list: List[Process]) -> List[Tuple[str,int,int]]:
    procs = deepcopy(process_list)
    n = len(procs)
    completed = 0
    time_cursor = 0
    gantt = []
    while completed < n:
        available = [p for p in procs if p.arrival <= time_cursor and p.completion_time is None]
        if not available:
            time_cursor = min(p.arrival for p in procs if p.completion_time is None)
            continue
        cur = min(available, key=lambda p: (p.burst, p.arrival))
        if cur.start_time is None:
            cur.start_time = time_cursor
            cur.response_time = cur.start_time - cur.arrival
        gantt.append((cur.pid, time_cursor, cur.burst))
        time_cursor += cur.burst
        cur.completion_time = time_cursor
        cur.remaining = 0
        completed += 1
    _sync(process_list, procs)
    return gantt

def sjf_preemptive(process_list: List[Process]) -> List[Tuple[str,int,int]]:
    procs = deepcopy(process_list)
    time_cursor = 0
    gantt = []
    n = len(procs)
    finished = 0
    last_pid = None
    while finished < n:
        available = [p for p in procs if p.arrival <= time_cursor and p.remaining > 0]
        if not available:
            time_cursor = min(p.arrival for p in procs if p.remaining > 0)
            last_pid = None
            continue
        cur = min(available, key=lambda p: (p.remaining, p.arrival))
        if cur.start_time is None:
            cur.start_time = time_cursor
            cur.response_time = cur.start_time - cur.arrival
        # run 1 unit
        if gantt and gantt[-1][0] == cur.pid:
            pid, s, d = gantt.pop()
            gantt.append((pid, s, d + 1))
        else:
            gantt.append((cur.pid, time_cursor, 1))
        cur.remaining -= 1
        time_cursor += 1
        if cur.remaining == 0:
            cur.completion_time = time_cursor
            finished += 1
        last_pid = cur.pid
    _sync(process_list, procs)
    return gantt

def priority_nonpreemptive(process_list: List[Process]) -> List[Tuple[str,int,int]]:
    procs = deepcopy(process_list)
    n = len(procs)
    completed = 0
    time_cursor = 0
    gantt = []
    while completed < n:
        available = [p for p in procs if p.arrival <= time_cursor and p.completion_time is None]
        if not available:
            time_cursor = min(p.arrival for p in procs if p.completion_time is None)
            continue
        cur = min(available, key=lambda p: (p.priority, p.arrival))
        if cur.start_time is None:
            cur.start_time = time_cursor
            cur.response_time = cur.start_time - cur.arrival
        gantt.append((cur.pid, time_cursor, cur.burst))
        time_cursor += cur.burst
        cur.completion_time = time_cursor
        cur.remaining = 0
        completed += 1
    _sync(process_list, procs)
    return gantt

def priority_preemptive(process_list: List[Process]) -> List[Tuple[str,int,int]]:
    procs = deepcopy(process_list)
    time_cursor = 0
    gantt = []
    n = len(procs)
    finished = 0
    last_pid = None
    while finished < n:
        available = [p for p in procs if p.arrival <= time_cursor and p.remaining > 0]
        if not available:
            time_cursor = min(p.arrival for p in procs if p.remaining > 0)
            last_pid = None
            continue
        cur = min(available, key=lambda p: (p.priority, p.arrival))
        if cur.start_time is None:
            cur.start_time = time_cursor
            cur.response_time = cur.start_time - cur.arrival
        if gantt and gantt[-1][0] == cur.pid:
            pid, s, d = gantt.pop()
            gantt.append((pid, s, d + 1))
        else:
            gantt.append((cur.pid, time_cursor, 1))
        cur.remaining -= 1
        time_cursor += 1
        if cur.remaining == 0:
            cur.completion_time = time_cursor
            finished += 1
        last_pid = cur.pid
    _sync(process_list, procs)
    return gantt

def round_robin(process_list: List[Process], quantum: int) -> List[Tuple[str,int,int]]:
    procs = deepcopy(process_list)
    gantt = []
    time_cursor = 0
    procs_by_arrival = sorted(procs, key=lambda p: p.arrival)
    i = 0
    n = len(procs)
    queue = []
    # enqueue initial arrivals
    while i < n and procs_by_arrival[i].arrival <= time_cursor:
        queue.append(procs_by_arrival[i]); i += 1
    if not queue and i < n:
        time_cursor = procs_by_arrival[i].arrival
        queue.append(procs_by_arrival[i]); i += 1
    while queue:
        cur = queue.pop(0)
        if cur.start_time is None:
            cur.start_time = time_cursor
            cur.response_time = cur.start_time - cur.arrival
        run = min(quantum, cur.remaining)
        gantt.append((cur.pid, time_cursor, run))
        time_cursor += run
        cur.remaining -= run
        while i < n and procs_by_arrival[i].arrival <= time_cursor:
            queue.append(procs_by_arrival[i]); i += 1
        if cur.remaining > 0:
            queue.append(cur)
        else:
            cur.completion_time = time_cursor
        if not queue and i < n:
            time_cursor = procs_by_arrival[i].arrival
            queue.append(procs_by_arrival[i]); i += 1
    _sync(process_list, procs)
    return gantt

def _sync(orig_list: List[Process], new_list: List[Process]):
    for orig in orig_list:
        for p in new_list:
            if p.pid == orig.pid:
                orig.start_time = p.start_time
                orig.completion_time = p.completion_time
                orig.response_time = p.response_time
                orig.remaining = p.remaining

def compute_metrics(processes: List[Process]) -> Dict[str,float]:
    n = len(processes)
    total_tat = 0
    total_wt = 0
    total_rt = 0
    for p in processes:
        tat = p.completion_time - p.arrival
        wt = tat - p.burst
        rt = p.response_time if p.response_time is not None else 0
        total_tat += tat
        total_wt += wt
        total_rt += rt
    return {
        'avg_tat': total_tat / n if n else 0,
        'avg_wt': total_wt / n if n else 0,
        'avg_rt': total_rt / n if n else 0
    }

# ---------------------------
# GUI
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Scheduler Simulator")
        self.setGeometry(200, 100, 1000, 720)

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        # control row
        ctrl_row = QHBoxLayout()
        layout.addLayout(ctrl_row)

        self.algo_box = QComboBox()
        self.algo_box.addItems([
            'FCFS', 'SJF (Non-Preemptive)', 'SJF (Preemptive)',
            'Priority (Non-Preemptive)', 'Priority (Preemptive)', 'Round Robin'
        ])
        ctrl_row.addWidget(QLabel('Algorithm:'))
        ctrl_row.addWidget(self.algo_box)

        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 10)
        self.quantum_spin.setValue(2)
        ctrl_row.addWidget(QLabel('Quantum:'))
        ctrl_row.addWidget(self.quantum_spin)

        self.btn_generate = QPushButton('Generate Random Processes')
        self.btn_run = QPushButton('Run Simulation')
        self.btn_reset = QPushButton('Reset')
        ctrl_row.addWidget(self.btn_generate)
        ctrl_row.addWidget(self.btn_run)
        ctrl_row.addWidget(self.btn_reset)

        # process input table
        self.proc_table = QTableWidget(0, 4)
        self.proc_table.setHorizontalHeaderLabels(['PID', 'Arrival', 'Burst', 'Priority'])
        layout.addWidget(QLabel('Processes (you can edit values before running):'))
        layout.addWidget(self.proc_table)

        # animation widget
        self.animation = AnimationWidget()
        layout.addWidget(self.animation)

        # result table
        self.result_table = QTableWidget(0, 8)
        self.result_table.setHorizontalHeaderLabels(['PID','Arrival','Burst','Priority','Start','Completion','TAT','WT','Response'][:9])
        layout.addWidget(QLabel('Results:'))
        layout.addWidget(self.result_table)

        # connect
        self.btn_generate.clicked.connect(self.generate_random_processes)
        self.btn_run.clicked.connect(self.run_simulation)
        self.btn_reset.clicked.connect(self.reset_all)

        # initial
        self.generate_random_processes()

    def generate_random_processes(self, n=5):
        self.proc_table.setRowCount(0)
        for i in range(n):
            pid = f'P{i+1}'
            arrival = random.randint(0, 5)
            burst = random.randint(1, 8)
            priority = random.randint(1, 5)
            row = self.proc_table.rowCount()
            self.proc_table.insertRow(row)
            self.proc_table.setItem(row, 0, QTableWidgetItem(pid))
            self.proc_table.setItem(row, 1, QTableWidgetItem(str(arrival)))
            self.proc_table.setItem(row, 2, QTableWidgetItem(str(burst)))
            self.proc_table.setItem(row, 3, QTableWidgetItem(str(priority)))

    def read_processes_from_table(self) -> List[Process]:
        procs = []
        for r in range(self.proc_table.rowCount()):
            pid = self.proc_table.item(r,0).text()
            arrival = int(self.proc_table.item(r,1).text())
            burst = int(self.proc_table.item(r,2).text())
            priority = int(self.proc_table.item(r,3).text())
            procs.append(Process(pid, arrival, burst, priority))
        return procs

    def run_simulation(self):
        try:
            processes = self.read_processes_from_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid process table values: {e}")
            return

        # reset runtime fields
        for p in processes:
            p.reset_runtime()

        algo = self.algo_box.currentText()
        if algo == 'FCFS':
            gantt = fcfs_scheduler(processes)
        elif algo == 'SJF (Non-Preemptive)':
            gantt = sjf_nonpreemptive(processes)
        elif algo == 'SJF (Preemptive)':
            gantt = sjf_preemptive(processes)
        elif algo == 'Priority (Non-Preemptive)':
            gantt = priority_nonpreemptive(processes)
        elif algo == 'Priority (Preemptive)':
            gantt = priority_preemptive(processes)
        elif algo == 'Round Robin':
            q = int(self.quantum_spin.value())
            gantt = round_robin(processes, q)
        else:
            QMessageBox.critical(self, "Error", "Unknown algorithm selected")
            return

        # prepare display gantt and animate
        # compress consecutive entries with same pid & contiguous time (done by schedulers for preemptive already)
        compressed = []
        for pid, s, d in gantt:
            if compressed and compressed[-1][0] == pid and compressed[-1][1] + compressed[-1][2] == s:
                compressed[-1] = (compressed[-1][0], compressed[-1][1], compressed[-1][2] + d)
            else:
                compressed.append((pid, s, d))

        # animate: we will use time unit ms multiplier
        # create a mapping of processes to colors and pass metrics for result table
        self.animation.play(compressed, processes, time_unit_ms=350)

        # fill result table
        for i in range(self.result_table.rowCount()):
            self.result_table.removeRow(i)
        self.result_table.setRowCount(0)

        # compute TAT, WT, RT
        for p in sorted(processes, key=lambda x: x.pid):
            tat = p.completion_time - p.arrival
            wt = tat - p.burst
            rt = p.response_time if p.response_time is not None else 0
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(p.pid))
            self.result_table.setItem(row, 1, QTableWidgetItem(str(p.arrival)))
            self.result_table.setItem(row, 2, QTableWidgetItem(str(p.burst)))
            self.result_table.setItem(row, 3, QTableWidgetItem(str(p.priority)))
            self.result_table.setItem(row, 4, QTableWidgetItem(str(p.start_time if p.start_time is not None else '-')))
            self.result_table.setItem(row, 5, QTableWidgetItem(str(p.completion_time if p.completion_time is not None else '-')))
            self.result_table.setItem(row, 6, QTableWidgetItem(str(tat)))
            self.result_table.setItem(row, 7, QTableWidgetItem(str(wt)))
            self.result_table.setItem(row, 8, QTableWidgetItem(str(rt)))

        # show averages as a small message
        metrics = compute_metrics(processes)
        QMessageBox.information(self, "Metrics",
                                f"Avg TAT: {metrics['avg_tat']:.2f}\nAvg WT: {metrics['avg_wt']:.2f}\nAvg RT: {metrics['avg_rt']:.2f}")

    def reset_all(self):
        self.proc_table.setRowCount(0)
        self.result_table.setRowCount(0)
        self.animation.stop()
        self.generate_random_processes()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
