# animation_widget.py
from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont
from PyQt5.QtCore import QTimer, QRectF, Qt
import random
from typing import List, Tuple


class AnimationWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Scroll area setup
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.inner = _AnimationCanvas()
        self.scroll_area.setWidget(self.inner)

        layout = QVBoxLayout()
        layout.addWidget(self.scroll_area)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    # EXPOSE the play() function for external use
    def play(self, gantt, processes, time_unit_ms=350):
        self.inner.play(gantt, processes, time_unit_ms)

    def stop(self):
        self.inner.stop()


class _AnimationCanvas(QWidget):
    """Internal canvas that actually draws the animation"""
    def __init__(self):
        super().__init__()

        self.setMinimumHeight(600)

        self.gantt = []
        self.proc_map = {}
        self.colors = {}

        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)

        self.time_unit_ms = 350
        self.fps = 40

        # animation state
        self.running = False
        self.current_index = 0
        self.block_elapsed_ms = 0

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
        self.current_index = 0
        self.block_elapsed_ms = 0
        self.update()

    def play(self, gantt_list: List[Tuple[str, int, int]], processes, time_unit_ms=350):
        if not gantt_list:
            return

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

        # adjust canvas height depending on processes
        self.setMinimumHeight(120 + len(gantt_list) * 70)

    def _tick(self):
        if not self.running:
            return

        if self.current_index >= len(self.gantt):
            self.stop()
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

            # draw background bar
            painter.setPen(QColor(60, 60, 60))
            painter.setBrush(QColor(225, 225, 225))
            painter.drawRoundedRect(QRectF(x0, bar_y, full_w, bar_h), 6, 6)

            # fill progress
            painter.setBrush(QBrush(self.colors.get(pid)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x0, bar_y, fill_w, bar_h), 6, 6)

            # highlight running
            if idx == self.current_index:
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
        painter.drawText(self.width() - 200, 25, f"Time ≈ {sim_time:.1f}")
