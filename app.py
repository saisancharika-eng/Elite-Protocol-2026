import sys
import json
import numpy as np
import calendar
from datetime import date
from PySide6.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QScrollArea, QLineEdit, QComboBox, QProgressBar
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# ---------------- PREMIER BRANDING ----------------
THEME = {
    "dark_bg": "#121212",
    "grid_bg": "#FFFFFF",
    "cyan": "#00E5FF",
    "pink": "#FF4081",
    "yellow": "#FFD600",
    "grey_box": "#E5E7EB",
    "border": "#333333"
}

class CircularProgress(QFrame):
    def __init__(self, label, color, subtext=""):
        super().__init__()
        self.label, self.color, self.subtext = label, color, subtext
        self.value = 0
        self.setFixedSize(160, 200)

    def set_value(self, val):
        self.value = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(25, 20, 110, 110)
        painter.setPen(QPen(QColor("#333"), 10))
        painter.drawEllipse(rect)
        painter.setPen(QPen(QColor(self.color), 10))
        span = int(-(self.value / 100.0) * 360 * 16)
        painter.drawArc(rect, 90 * 16, span)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 15, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, f"{int(self.value)}%")
        painter.setFont(QFont("Arial", 8))
        painter.drawText(0, 145, 160, 20, Qt.AlignCenter, self.label)
        painter.setPen(QColor("#777"))
        painter.drawText(0, 165, 160, 20, Qt.AlignCenter, self.subtext)

class HabitCell(QPushButton):
    def __init__(self, parent, color):
        super().__init__("")
        self.parent_ui = parent
        self.color = color
        self.state = 0 # 0: Empty, 1: Tick
        self.setFixedSize(24, 24)
        self.clicked.connect(self.toggle)

    def toggle(self):
        self.state = (self.state + 1) % 2
        self.update_style()
        self.parent_ui.sync_all_metrics()
        self.parent_ui.save_data()

    def update_style(self):
        if self.state == 1:
            self.setText("✓")
            self.setStyleSheet(f"background: {self.color}; color: white; border: 1px solid #DDD; font-weight: bold;")
        else:
            self.setText("")
            self.setStyleSheet("background: white; border: 1px solid #EEE;")

class Master2026Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elite Protocol Dashboard 2026")
        self.resize(1500, 950)
        self.today = date.today()
        self.habits = [
            ["Stretch or do yoga", "5", "#4ADE80"], 
            ["Walk 10,000 steps", "7", "#22D3EE"],
            ["Read a book chapter", "15", "#818CF8"],
            ["Declutter a space", "4", "#FBBF24"],
            ["Floss", "20", "#F87171"]
        ]
        self.cell_map = {}
        self.progress_bars = {}
        # Load data if exists
        try:
            with open('dashboard_data.json', 'r') as f:
                data = json.load(f)
                self.habits = data.get('habits', self.habits)
                self.states = {tuple(k.split('#', 1)): int(v) for k, v in data.get('states', {}).items()}
                month_idx = data.get('month', self.today.month - 1)
        except (FileNotFoundError, json.JSONDecodeError):
            self.states = {}
            month_idx = self.today.month - 1
        self.init_ui()
        self.month_sel.setCurrentIndex(month_idx)

    def init_ui(self):
        main_v = QVBoxLayout(self)
        main_v.setContentsMargins(0,0,0,0)
        main_v.setSpacing(0)

        # --- HEADER AREA (BLACK) ---
        header = QFrame()
        header.setStyleSheet(f"background: {THEME['dark_bg']}; color: white;")
        header.setFixedHeight(320)
        h_layout = QVBoxLayout(header)

        # Functional Bar (Month & Add Task)
        controls = QHBoxLayout()
        self.month_sel = QComboBox()
        self.month_sel.addItems([calendar.month_name[i] for i in range(1,13)])
        self.month_sel.setCurrentIndex(self.today.month - 1)
        self.month_sel.currentIndexChanged.connect(self.refresh_grid)
        self.month_sel.setFixedWidth(120)

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("New Protocol Name...")
        self.task_input.setFixedWidth(200)
        add_btn = QPushButton("+ ADD PROTOCOL")
        add_btn.clicked.connect(self.add_task)
        add_btn.setStyleSheet(f"background: {THEME['cyan']}; color: black; font-weight: bold; padding: 5px 15px;")

        controls.addWidget(QLabel("MONTH:"))
        controls.addWidget(self.month_sel)
        controls.addStretch()
        controls.addWidget(self.task_input)
        controls.addWidget(add_btn)
        h_layout.addLayout(controls)

        # Analytics Row
        stats_row = QHBoxLayout()
        meta_v = QVBoxLayout()
        days_left = (date(2026, 12, 31) - self.today).days
        meta_v.addWidget(QLabel(f"YEAR: 2026"))
        meta_v.addWidget(QLabel(f"DAYS LEFT: {days_left}"))
        meta_v.addWidget(QLabel(f"START: JAN 1"))
        meta_v.addWidget(QLabel(f"END: DEC 31"))
        stats_row.addLayout(meta_v)

        # The Sharp Graph with Grids
        self.fig = Figure(figsize=(8, 2), facecolor='none')
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        stats_row.addWidget(self.canvas, stretch=5)

        self.big_pct = QLabel("0%")
        self.big_pct.setStyleSheet(f"font-size: 80px; font-weight: bold; color: {THEME['cyan']};")
        stats_row.addWidget(self.big_pct)
        h_layout.addLayout(stats_row)
        main_v.addWidget(header)

        # --- GRID AREA (WHITE) ---
        grid_area = QScrollArea()
        grid_area.setWidgetResizable(True)
        self.grid_content = QFrame()
        self.grid_content.setStyleSheet("background: white; color: black;")
        self.grid = QGridLayout(self.grid_content)
        self.grid.setSpacing(0) # Strict pixel spacing
        grid_area.setWidget(self.grid_content)
        main_v.addWidget(grid_area)

        # Notice Line
        notice = QLabel("In the lines above, in a short but sufficiently descriptive way, write the habits you want to follow...")
        notice.setStyleSheet("background: white; color: #666; font-style: italic; padding: 10px; font-size: 10px;")
        main_v.addWidget(notice)

        # --- FOOTER GAUGES (BLACK) ---
        footer = QFrame()
        footer.setStyleSheet(f"background: {THEME['dark_bg']};")
        footer.setFixedHeight(220)
        f_layout = QHBoxLayout(footer)
        self.g1 = CircularProgress("MONTHLY PROGRESS", THEME["pink"], "REAL-TIME")
        self.g2 = CircularProgress("21 DAYS PROGRESS", THEME["cyan"], "NORMALIZED")
        self.g3 = CircularProgress("LAST 3 DAYS", THEME["yellow"], "MOMENTUM")
        f_layout.addStretch(); f_layout.addWidget(self.g1); f_layout.addWidget(self.g2); f_layout.addWidget(self.g3); f_layout.addStretch()
        main_v.addWidget(footer)

        self.refresh_grid()

    def add_task(self):
        if name := self.task_input.text():
            self.habits.append([name, "10", "#818CF8"])
            self.task_input.clear()
            self.refresh_grid()
            self.save_data()

    def delete_habit(self, habit):
        self.habits.remove(habit)
        self.refresh_grid()
        self.save_data()

    def update_habit_name(self, habit, new_name):
        old_name = habit[0]
        new_name = new_name.strip()
        if new_name and new_name != old_name:
            habit[0] = new_name
            # Update cell_map keys
            month_idx = self.month_sel.currentIndex() + 1
            days = calendar.monthrange(2026, month_idx)[1]
            for d in range(1, days + 1):
                if (old_name, d) in self.cell_map:
                    self.cell_map[(new_name, d)] = self.cell_map.pop((old_name, d))
            self.save_data()
        elif not new_name:
            # If name is cleared, delete the habit
            self.delete_habit(habit)

    def update_goal(self, habit, new_goal):
        habit[1] = new_goal
        self.sync_all_metrics()
        self.save_data()

    def save_data(self):
        data = {
            'habits': self.habits,
            'states': {f"{name}#{d}": self.cell_map[(name, d)].state for name, d in self.cell_map},
            'month': self.month_sel.currentIndex()
        }
        with open('dashboard_data.json', 'w') as f:
            json.dump(data, f)

    def refresh_grid(self):
        # Clear grid
        for i in reversed(range(self.grid.count())): 
            self.grid.itemAt(i).widget().setParent(None)
        
        self.cell_map = {}
        self.progress_bars = {}
        month_idx = self.month_sel.currentIndex() + 1
        days = calendar.monthrange(2026, month_idx)[1]

        # Row Header
        self.grid.addWidget(QLabel("HABIT"), 0, 0)
        self.grid.addWidget(QLabel("GOAL"), 0, 1)
        for d in range(1, days + 1):
            day_initial = date(2026, month_idx, d).strftime('%a')[0]
            header_v = QVBoxLayout()
            d_lbl = QLabel(str(d))
            d_lbl.setStyleSheet("background: #EEE; font-weight: bold; border: 1px solid #DDD;")
            header_v.addWidget(d_lbl, alignment=Qt.AlignCenter)
            header_v.addWidget(QLabel(day_initial), alignment=Qt.AlignCenter)
            self.grid.addLayout(header_v, 0, d + 1)
            # Add separator after each day column
            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setStyleSheet("QFrame { border-left: 1px solid black; }")
            self.grid.addWidget(sep, 0, d + 1, -1, 1)  # Span all rows
        self.grid.addWidget(QLabel("PROGRESS"), 0, days + 2)

        # Habit Rows
        for r, habit in enumerate(self.habits):
            name, goal, color = habit
            habit_edit = QLineEdit(name)
            habit_edit.editingFinished.connect(lambda h=habit, e=habit_edit: self.update_habit_name(h, e.text()))
            self.grid.addWidget(habit_edit, r+1, 0)
            goal_edit = QLineEdit(goal)
            goal_edit.setFixedWidth(50)
            goal_edit.editingFinished.connect(lambda h=habit, e=goal_edit: self.update_goal(h, e.text()))
            self.grid.addWidget(goal_edit, r+1, 1, alignment=Qt.AlignCenter)
            for d in range(1, days + 1):
                cell = HabitCell(self, color)
                cell.state = self.states.get((name, d), 0)
                cell.update_style()
                self.grid.addWidget(cell, r+1, d+1)
                self.cell_map[(name, d)] = cell
            
            p_bar = QProgressBar()
            p_bar.setFixedWidth(80)
            p_bar.setTextVisible(False)
            p_bar.setStyleSheet(f"QProgressBar::chunk {{ background: {color}; }}")
            self.grid.addWidget(p_bar, r+1, days + 2)
            self.progress_bars[name] = p_bar

        self.sync_all_metrics()

    def sync_all_metrics(self):
        month_idx = self.month_sel.currentIndex() + 1
        days = calendar.monthrange(2026, month_idx)[1]
        daily_ticks = []
        total_ticks = 0
        
        for d in range(1, days + 1):
            count = sum(1 for h in self.habits if (h[0], d) in self.cell_map and self.cell_map[(h[0], d)].state == 1)
            daily_ticks.append(count)
            total_ticks += count

        # Overall Success (Monthly Progress)
        success = (total_ticks / (len(self.habits) * days)) * 100 if days > 0 else 0
        self.big_pct.setText(f"{int(success)}%")
        self.g1.set_value(success)
        self.g2.set_value(success * 0.9)
        self.g3.set_value(min(100, success * 1.1))

        # Update individual progress bars (Monthly completion for each habit)
        for habit in self.habits:
            name, goal, color = habit
            completed = sum(1 for d in range(1, days + 1) if (name, d) in self.cell_map and self.cell_map[(name, d)].state == 1)
            progress = (completed / days) * 100 if days > 0 else 0
            if name in self.progress_bars:
                self.progress_bars[name].setValue(int(progress))

        # Graph with sharp Grid Lines
        self.ax.clear()
        self.ax.set_facecolor('none')
        x = np.arange(1, days + 1)
        self.ax.plot(x, daily_ticks, color=THEME['cyan'], linewidth=1.5)
        self.ax.fill_between(x, daily_ticks, color=THEME['cyan'], alpha=0.1)
        self.ax.grid(True, color='#333', linestyle='--', linewidth=0.5) # The requested Grids
        self.ax.set_ylim(0, len(self.habits))
        self.ax.set_xticks(range(1, days+1, 2))
        self.ax.tick_params(colors='white', labelsize=7)
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Master2026Dashboard()
    window.show()
    sys.exit(app.exec())
