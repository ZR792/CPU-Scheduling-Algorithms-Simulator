# animation_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont
from PyQt5.QtCore import QTimer, QRectF, Qt, pyqtSignal
import random
from typing import List, Tuple


class AnimationWidget(QWidget):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.inner = _AnimationCanvas()
        layout = QVBoxLayout()
        layout.addWidget(self.inner)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # forward signal
        self.inner.finished.connect(self.finished)
    # EXPOSE the play() function for external use
    def play(self, gantt, processes, time_unit_ms=350, preserve_state=False):
        self.inner.play(gantt, processes, time_unit_ms, preserve_state)

    def stop(self):
        self.inner.stop()


class _AnimationCanvas(QWidget):
    finished = pyqtSignal()
    """Internal canvas that actually draws the animation"""
    def __init__(self):
        super().__init__()

        self.setMinimumHeight(600)

        self.setMouseTracking(True)    # mouse hover track kare
        self.bar_rects = []             # bars ka rectangle store karne ke liye


        self.gantt = []
        self.proc_map = {}
        self.colors = {}

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

        self.time_unit_ms = 350
        self.fps = 10

        # animation state
        self.running = False
        self.current_index = 0
        self.block_elapsed_ms = 0
        self.setMinimumHeight(max(600, 120 + len(self.gantt) * 70))
        self.update()
        # drawing settings
        self.timeline_origin = 40
        self.font = QFont("Arial", 10, QFont.Bold)

        self.timer.setInterval(self.fps)

    def assign_color(self, pid):
        if pid not in self.colors:
            self.colors[pid] = QColor(
                random.randint(40, 220),
                random.randint(40, 220),
                random.randint(40, 220)
            )

    def stop(self):
        self.running = False
        self.timer.stop()
        if not self.preserve_state:
            self.current_index = 0
            self.block_elapsed_ms = 0
        

    def play(self, gantt_list: List[Tuple[str, int, int]], processes, time_unit_ms=350, preserve_state=False):
        if not gantt_list:
            return

        self.preserve_state = preserve_state
        self.gantt = gantt_list
        self.proc_map = {p.pid: p for p in processes}
        for pid, _, _ in gantt_list:
            self.assign_color(pid)

        self.time_unit_ms = time_unit_ms

        self.current_index = 0
        self.block_elapsed_ms = 0
        self.running = True

        if self.timer.isActive():
            self.timer.stop()

        self.timer.start()
        self.update()

        self.setMinimumHeight(max(600, 120 + len(gantt_list) * 70))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _tick(self):
        if not self.running:
            return

        if self.current_index >= len(self.gantt):
            if not self.preserve_state:
                self.stop()
            else:
                self.running = False  # animation complete but preserve bars
             # Emit finished signal once
            self.finished.emit()
            return

        pid, start, dur = self.gantt[self.current_index]
        block_ms = dur * self.time_unit_ms

        self.block_elapsed_ms += self.fps

        if self.block_elapsed_ms >= block_ms:
            self.current_index += 1
            self.block_elapsed_ms = 0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(245, 245, 245))

        # timeline
        y0 = 40
        painter.setPen(QColor(70, 70, 70))
        painter.drawLine(self.timeline_origin, y0 + 20, self.width() - 40, y0 + 20)

        # ===== HEIGHT FIX START =====
        total_bars = len(self.gantt)          # ✅ DEFINE HERE
        bar_h = 36
        canvas_height = 120 + total_bars * (bar_h + 30)
        self.setMinimumHeight(max(600, canvas_height))
        # ===== HEIGHT FIX END =====

        # find total time
        end_time = 0
        for _, s, d in self.gantt:
            end_time = max(end_time, s + d)

        usable_width = max(300, self.width() - self.timeline_origin - 40)
        scale = usable_width / max(1, end_time)

        # draw time ticks
        for t in range(0, end_time + 1):
            x = self.timeline_origin + t * scale
            painter.drawLine(int(x), y0 + 15, int(x), y0 + 25)
            painter.drawText(int(x) - 5, y0 + 40, str(t))

        self.bar_rects.clear()  # har paintEvent ke start me reset kare

        # draw bars
        bar_y = y0 + 80
        bar_h = 36

        for idx, (pid, start, dur) in enumerate(self.gantt):
            x0 = self.timeline_origin + start * scale
            full_w = dur * scale

            if idx < self.current_index:
                fill_w = full_w
            elif idx == self.current_index:
                block_ms = dur * self.time_unit_ms
                frac = min(1.0, self.block_elapsed_ms / block_ms)
                fill_w = full_w * frac
            else:
                fill_w = 0


            rect = QRectF(x0, bar_y, full_w, bar_h)
            self.bar_rects.append((rect, pid))  # store rectangle + PID

   
            # draw background bar
            painter.setPen(QColor(60, 60, 60))
            painter.setBrush(QColor(225, 225, 225))
            painter.drawRoundedRect(QRectF(x0, bar_y, full_w, bar_h), 6, 6)

            # fill progress
            painter.setBrush(QBrush(self.colors.get(pid)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x0, bar_y, fill_w, bar_h), 6, 6)

            # highlight running
            if idx == self.current_index and self.running:
                painter.setPen(QColor(255, 140, 0))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(QRectF(x0 - 2, bar_y - 2, full_w + 4, bar_h + 4), 8, 8)

            # PID text
            painter.setPen(QColor(255, 255, 255) if fill_w > 40 else QColor(0, 0, 0))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(QRectF(x0 + 5, bar_y, full_w - 10, bar_h),
                             Qt.AlignVCenter | Qt.AlignLeft, pid)

            bar_y += bar_h + 30

        # simulated time
        sim_time = 0
        for i in range(self.current_index):
            sim_time += self.gantt[i][2]
        if self.current_index < len(self.gantt):
            sim_time += (self.block_elapsed_ms / self.time_unit_ms)

        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.setPen(QColor(50, 50, 50))
        from hmain import seconds_to_time   # top pe import
        painter.drawText(
            self.width() - 200,
            25,
            f"Time ≈ {seconds_to_time(sim_time)}"
        )


    def mouseMoveEvent(self, event):
        cursor = event.pos()
        tooltip_text = ""  # default

        for rect, pid in self.bar_rects:
            if rect.contains(cursor):
                p = self.proc_map.get(pid)
                if p:
                    total_burst = p.burst
                    remaining_burst = p.remaining
                    executed_burst = total_burst - remaining_burst
                    visits_details = [d for x, _, d in self.gantt if x == pid]
                    num_visits = len(visits_details)

                    # build tooltip text
                    tooltip_text = (
                        f"PID: {p.pid}\n"
                        f"Total Burst: {total_burst}\n"
                        f"Remaining Burst: {remaining_burst}\n"
                        f"Total Executed Burst: {executed_burst}\n"
                        f"CPU Visits: {num_visits}"
                    )

                    # add per-visit details only if more than 1 visit
                    if num_visits > 1:
                        tooltip_text += f"\nExecuted per Visit: {visits_details}"

                break  # exit loop if we found the bar

        self.setToolTip(tooltip_text)  # always safe to call