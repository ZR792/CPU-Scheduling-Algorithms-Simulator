# -------------------------------------------------
# Imports
# -------------------------------------------------
import sys
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Dict

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QFrame, QScrollArea, QSizePolicy, QHeaderView
)
from PyQt5.QtCore import Qt

from animation_widget import AnimationWidget
from datetime import datetime, timedelta

BASE_TIME = datetime.now().replace(microsecond=0)


# -------------------------------------------------
# Data Model
# -------------------------------------------------
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
        self.reset_runtime()

    def reset_runtime(self):
        self.remaining = self.burst
        self.start_time = None
        self.completion_time = None
        self.response_time = None


# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def seconds_to_time(sec):
    if sec is None:
        return "--"
    return (BASE_TIME + timedelta(seconds=int(sec))).strftime("%H:%M:%S")


def sync_processes(original: List[Process], updated: List[Process]):
    for o in original:
        for u in updated:
            if o.pid == u.pid:
                o.start_time = u.start_time
                o.completion_time = u.completion_time
                o.response_time = u.response_time
                o.remaining = u.remaining


def compute_metrics(processes: List[Process]) -> Dict[str, float]:
    n = len(processes)
    tat = sum(p.completion_time - p.arrival for p in processes)
    wt = sum((p.completion_time - p.arrival - p.burst) for p in processes)
    rt = sum(p.response_time or 0 for p in processes)

    return {
        "avg_tat": tat / n if n else 0,
        "avg_wt": wt / n if n else 0,
        "avg_rt": rt / n if n else 0
    }


# -------------------------------------------------
# Scheduling Algorithms
# -------------------------------------------------
def fcfs_scheduler(processes: List[Process]):
    procs = sorted(deepcopy(processes), key=lambda p: (p.arrival, p.pid))
    time, gantt = 0, []

    for p in procs:
        time = max(time, p.arrival)
        p.start_time = time
        p.response_time = time - p.arrival
        gantt.append((p.pid, time, p.burst))
        time += p.burst
        p.completion_time = time
        p.remaining = 0

    sync_processes(processes, procs)
    return gantt


def sjf_nonpreemptive(processes: List[Process]):
    procs = deepcopy(processes)
    time, gantt = 0, []

    while any(p.remaining > 0 for p in procs):
        ready = [p for p in procs if p.arrival <= time and p.remaining > 0]
        if not ready:
            time += 1
            continue

        p = min(ready, key=lambda x: x.burst)
        p.start_time = time
        p.response_time = time - p.arrival
        gantt.append((p.pid, time, p.burst))
        time += p.burst
        p.remaining = 0
        p.completion_time = time

    sync_processes(processes, procs)
    return gantt


def sjf_preemptive(processes: List[Process]):
    procs = deepcopy(processes)
    time, gantt = 0, []

    while any(p.remaining > 0 for p in procs):
        ready = [p for p in procs if p.arrival <= time and p.remaining > 0]
        if not ready:
            time += 1
            continue

        p = min(ready, key=lambda x: x.remaining)
        if p.start_time is None:
            p.start_time = time
            p.response_time = time - p.arrival

        if gantt and gantt[-1][0] == p.pid:
            pid, s, d = gantt.pop()
            gantt.append((pid, s, d + 1))
        else:
            gantt.append((p.pid, time, 1))

        p.remaining -= 1
        time += 1
        if p.remaining == 0:
            p.completion_time = time

    sync_processes(processes, procs)
    return gantt


def priority_nonpreemptive(processes: List[Process]):
    procs = deepcopy(processes)
    time, gantt = 0, []

    while any(p.remaining > 0 for p in procs):
        ready = [p for p in procs if p.arrival <= time and p.remaining > 0]
        if not ready:
            time += 1
            continue

        p = min(ready, key=lambda x: x.priority)
        p.start_time = time
        p.response_time = time - p.arrival
        gantt.append((p.pid, time, p.burst))
        time += p.burst
        p.remaining = 0
        p.completion_time = time

    sync_processes(processes, procs)
    return gantt


def priority_preemptive(processes: List[Process]):
    procs = deepcopy(processes)
    time, gantt = 0, []

    while any(p.remaining > 0 for p in procs):
        ready = [p for p in procs if p.arrival <= time and p.remaining > 0]
        if not ready:
            time += 1
            continue

        p = min(ready, key=lambda x: x.priority)
        if p.start_time is None:
            p.start_time = time
            p.response_time = time - p.arrival

        if gantt and gantt[-1][0] == p.pid:
            pid, s, d = gantt.pop()
            gantt.append((pid, s, d + 1))
        else:
            gantt.append((p.pid, time, 1))

        p.remaining -= 1
        time += 1
        if p.remaining == 0:
            p.completion_time = time

    sync_processes(processes, procs)
    return gantt


def round_robin(processes: List[Process], quantum: int):
    procs = deepcopy(processes)
    procs.sort(key=lambda p: p.arrival)
    time, gantt, queue = 0, [], []
    i = 0

    while queue or i < len(procs):
        while i < len(procs) and procs[i].arrival <= time:
            queue.append(procs[i])
            i += 1

        if not queue:
            time = procs[i].arrival
            continue

        p = queue.pop(0)
        if p.start_time is None:
            p.start_time = time
            p.response_time = time - p.arrival

        run = min(quantum, p.remaining)
        gantt.append((p.pid, time, run))
        time += run
        p.remaining -= run

        while i < len(procs) and procs[i].arrival <= time:
            queue.append(procs[i])
            i += 1

        if p.remaining > 0:
            queue.append(p)
        else:
            p.completion_time = time

    sync_processes(processes, procs)
    return gantt

# -------------------------------------------------
# Simulation Window
# -------------------------------------------------

class SimulationWindow(QMainWindow):
    def __init__(self, processes, gantt, algo_name, preserve_state=True):
        super().__init__()
        self.setWindowTitle("CPU Scheduler Simulator - Animation & Results")
        self.showMaximized() 
        self.processes = processes
        self.algo_name = algo_name
        self.preserve_state = preserve_state

        # Scrollable root widget
        root = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)
        # self.scroll = scroll  # store reference for scrolling

        layout = QVBoxLayout(root)

        # Animation widget
        self.animation = AnimationWidget()
        layout.addWidget(self.animation)

        # Result table (initially hidden)
        
        self.result_table = QTableWidget()
        self.result_table.setVisible(False)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.result_table)

        # 🔹 Connect animation finished signal BEFORE starting animation
        self.animation.finished.connect(self.show_results)

        # Start animation
        self.animation.play(gantt, processes, time_unit_ms=350, preserve_state=self.preserve_state)

    def show_results(self):
        processes = self.processes

        show_priority = "Priority" in self.algo_name
        
        # 🔹 Headers
        if show_priority:
            headers = [
                "PID", "Arrival", "Burst", "Priority",
                "Start", "Completion", "TAT", "WT", "Response"
            ]
        else:
            headers = [
                "PID", "Arrival", "Burst",
                "Start", "Completion", "TAT", "WT", "Response"
            ]

        self.result_table.clear()
        self.result_table.setColumnCount(len(headers))
        self.result_table.setHorizontalHeaderLabels(headers)
        self.result_table.setRowCount(0)

        # Fill table
        for p in processes:
            tat = p.completion_time - p.arrival
            wt = tat - p.burst
            row = [
                p.pid,
                seconds_to_time(p.arrival),
                p.burst
            ]

            # Priority column handling
            if show_priority:
                row.append(p.priority)   

            row += [
                seconds_to_time(p.start_time),
                seconds_to_time(p.completion_time),
                tat,
                wt,
                seconds_to_time(p.response_time)
            ]

            r = self.result_table.rowCount()
            self.result_table.insertRow(r)

            for c, v in enumerate(row):
                self.result_table.setItem(
                    r, c, QTableWidgetItem(str(v))
                )

        # 🔹 IMPORTANT PART STARTS HERE 🔹

        row_h = self.result_table.verticalHeader().defaultSectionSize()
        header_h = self.result_table.horizontalHeader().height()

        total_h = header_h + row_h * len(processes) + 10

        self.result_table.setMinimumHeight(total_h)
        self.result_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.result_table.setVisible(True)

# -------------------------------------------------
# Main App Window
# -------------------------------------------------
class SchedulerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Scheduler Simulator")
        self.showMaximized() 
        self.setStyleSheet("background-color:#f5f5f5;")
        self.processes: List[Process] = []

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        root = QWidget()
        scroll.setWidget(root)
        self.setCentralWidget(scroll)

        self.main_layout = QVBoxLayout(root)
        self.main_layout.setContentsMargins(15,15,15,15)
        self.main_layout.setSpacing(12)

        header = QLabel("CPU Scheduler Simulator")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size:22px; font-weight:bold; color:#0D3B66;")
        self.main_layout.addWidget(header)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        algo_card = QFrame()
        algo_card.setStyleSheet("QFrame {background:white; border-radius:8px; padding:8px; font-size:15px;}")
        algo_layout = QVBoxLayout(algo_card)
        algo_layout.addWidget(QLabel("Select Algorithm"))
        self.algo_box = QComboBox()
        self.algo_box.addItems([
            'FCFS','SJF (Non-Preemptive)','SJF (Preemptive)',
            'Priority (Non-Preemptive)','Priority (Preemptive)','Round Robin'
        ])
        self.algo_box.setStyleSheet("font-size:13px;")
        algo_layout.addWidget(self.algo_box)
        algo_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_row.addWidget(algo_card, 1)

        num_card = QFrame()
        num_card.setStyleSheet("QFrame {background:white; border-radius:8px; padding:8px; font-size:15px;}")
        num_layout = QVBoxLayout(num_card)
        num_layout.addWidget(QLabel("Select Number of Processes"))
        self.num_spin = QSpinBox()
        self.num_spin.setRange(1, 200)
        self.num_spin.setValue(5)
        self.num_spin.setStyleSheet("font-size:13px;")
        num_layout.addWidget(self.num_spin)
        num_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_row.addWidget(num_card, 1)

        self.main_layout.addLayout(top_row)

        self.quantum_card = QFrame()
        self.quantum_card.setStyleSheet("QFrame {background:white; border-radius:8px; padding:8px; font-size:15px;}")
        ql = QHBoxLayout(self.quantum_card)
        ql.setSpacing(10)
        ql.addWidget(QLabel("Quantum (Round Robin)"))
        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 20)
        self.quantum_spin.setValue(2)
        self.quantum_spin.setStyleSheet("font-size:13px;")
        self.quantum_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ql.addWidget(self.quantum_spin)
        self.quantum_card.setVisible(False)
        self.main_layout.addWidget(self.quantum_card)

        self.algo_box.currentIndexChanged.connect(
            lambda: self.quantum_card.setVisible('Round Robin' in self.algo_box.currentText())
        )

        btn_row = QHBoxLayout()
        gen = QPushButton("Generate Table")
        gen.setStyleSheet("background-color:#0D3B66;color:white;padding:8px 12px;border-radius:5px;")
        gen.clicked.connect(self.generate_table)
        run = QPushButton("Run Simulation")
        run.setStyleSheet("background-color:#119DA4;color:white;padding:8px 12px;border-radius:5px;")
        run.clicked.connect(self.run_simulation)
        btn_row.addWidget(gen)
        btn_row.addWidget(run)
        self.main_layout.addLayout(btn_row)


                # 🔹 Placeholder to reserve table space
        self.table_placeholder = QWidget()
        self.table_placeholder.setMinimumHeight(300)
        self.table_placeholder.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.main_layout.addWidget(self.table_placeholder)

        self.proc_table = QTableWidget()
        self.proc_table.setVisible(False)

       

        # self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proc_table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        # self.main_layout.replaceWidget(self.table_placeholder, self.proc_table)
        # self.table_placeholder.hide()
        # self.main_layout.addWidget(self.proc_table)
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.main_layout.addWidget(self.proc_table)


    def generate_table(self):
        algo = self.algo_box.currentText()

        # decide columns based on algorithm
        if 'Priority' in algo:
            headers = ['PID','Arrival','Burst','Priority']
        else:
            headers = ['PID','Arrival','Burst']

        self.proc_table.clear()
        self.proc_table.setColumnCount(len(headers))
        self.proc_table.setHorizontalHeaderLabels(headers)
        self.proc_table.setRowCount(self.num_spin.value())

        self.processes.clear()
        for i in range(self.num_spin.value()):
            p = Process(f"P{i+1}", random.randint(0,30), random.randint(1,10), random.randint(1,10))
            self.processes.append(p)
            values = [p.pid, seconds_to_time(p.arrival), p.burst]
            if 'Priority' in headers:
                values.append(p.priority)
            for c, v in enumerate(values):
                self.proc_table.setItem(i, c, QTableWidgetItem(str(v)))

            self.proc_table.resizeRowsToContents()
        self.proc_table.setVisible(True)        # show table
        self.table_placeholder.setVisible(False)     
    def run_simulation(self):
        for p in self.processes:
            p.reset_runtime()

        algo = self.algo_box.currentText()
        if algo == 'FCFS':
            gantt = fcfs_scheduler(self.processes)
        elif algo == 'SJF (Non-Preemptive)':
            gantt = sjf_nonpreemptive(self.processes)
        elif algo == 'SJF (Preemptive)':
            gantt = sjf_preemptive(self.processes)
        elif algo == 'Priority (Non-Preemptive)':
            gantt = priority_nonpreemptive(self.processes)
        elif algo == 'Priority (Preemptive)':
            gantt = priority_preemptive(self.processes)
        else:
            gantt = round_robin(self.processes, self.quantum_spin.value())

        self.sim = SimulationWindow(self.processes, gantt, self.algo_box.currentText())
        self.sim.show()

# -------------------------------------------------
# Run Application
# -------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SchedulerApp()
    window.show()
    sys.exit(app.exec_())
