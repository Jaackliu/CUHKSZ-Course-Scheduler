import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QDialog, QHBoxLayout, QLineEdit, QTextEdit, QMenuBar, QAction, QFileDialog,
    QMessageBox, QComboBox, QPushButton
)
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, pyqtProperty, QRect, QEasingCurve
)

REPEAT_PATTERNS = {
    "None": [],
    "MoWe": [0, 2],      
    "TuTh": [1, 3],     
    "MoWeFr": [0, 2, 4]
}


class CourseDialog(QDialog):
    def __init__(self, parent=None, existing_data=None, is_lecture=True):
        super().__init__(parent)
        self.setWindowTitle("Edit Course")
        self.setModal(True)
        self.setMinimumWidth(250)

        self.course_line = QLineEdit(self)
        self.instructor_line = QLineEdit(self)
        self.remarks_text = QTextEdit(self)
        self.duration_combo = QComboBox(self)
        self.duration_combo.addItems(["50", "80", "110"])

        # Repeat pattern combo
        self.repeat_combo = QComboBox(self)
        self.repeat_combo.addItems(["None", "MoWe", "TuTh", "MoWeFr"])

        default_duration = "80" if is_lecture else "50"
        self.is_new = (not existing_data or len(existing_data) == 0)

        # Fill dialog fields if editing an existing course
        if not self.is_new:
            self.course_line.setText(existing_data.get("course_name", ""))
            self.instructor_line.setText(existing_data.get("instructor_name", ""))
            self.remarks_text.setPlainText(existing_data.get("remarks", ""))
            current_duration = existing_data.get("duration", default_duration)
            current_pattern = existing_data.get("repeat_pattern", "None")
        else:
            current_duration = default_duration
            current_pattern = "None"

        self.duration_combo.setCurrentText(current_duration)
        self.repeat_combo.setCurrentText(current_pattern)

        form_layout = QVBoxLayout()
        lbl_course = QLabel("Course Name (required):")
        lbl_course.setFont(QFont("Arial", 10))
        form_layout.addWidget(lbl_course)
        form_layout.addWidget(self.course_line)

        lbl_instructor = QLabel("Instructor Name (optional):")
        lbl_instructor.setFont(QFont("Arial", 10))
        form_layout.addWidget(lbl_instructor)
        form_layout.addWidget(self.instructor_line)

        lbl_remarks = QLabel("Remarks (optional):")
        lbl_remarks.setFont(QFont("Arial", 10))
        form_layout.addWidget(lbl_remarks)
        form_layout.addWidget(self.remarks_text)

        lbl_duration = QLabel("Class Duration (mins):")
        lbl_duration.setFont(QFont("Arial", 10))
        form_layout.addWidget(lbl_duration)
        form_layout.addWidget(self.duration_combo)

        # "Repeat" selection
        lbl_repeat = QLabel("Repeat:")
        lbl_repeat.setFont(QFont("Arial", 10))
        form_layout.addWidget(lbl_repeat)
        form_layout.addWidget(self.repeat_combo)

        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFont(QFont("Arial", 10))
        btn_layout.addWidget(self.cancel_btn)

        # If it's a new slot, don't show Delete
        if not self.is_new:
            self.delete_btn = QPushButton("Delete")
            self.delete_btn.setFont(QFont("Arial", 10))
            btn_layout.addWidget(self.delete_btn)
        else:
            self.delete_btn = None

        self.save_btn = QPushButton("Save")
        self.save_btn.setFont(QFont("Arial", 10))
        self.save_btn.setDefault(True)
        btn_layout.addWidget(self.save_btn)

        form_layout.addLayout(btn_layout)
        self.setLayout(form_layout)

        self.save_btn.clicked.connect(self.save_course)
        if self.delete_btn:
            self.delete_btn.clicked.connect(self.delete_course)
        self.cancel_btn.clicked.connect(self.reject)

        self.saved_data = None
        self.deleted = False

    def save_course(self):
        course_name = self.course_line.text().strip()
        if not course_name:
            QMessageBox.warning(self, "Error", "Course Name is required.")
            return
        instructor = self.instructor_line.text().strip()
        remarks = self.remarks_text.toPlainText().strip()
        duration = self.duration_combo.currentText().strip()
        pattern = self.repeat_combo.currentText().strip()

        self.saved_data = {
            "course_name": course_name,
            "instructor_name": instructor,
            "remarks": remarks,
            "duration": duration,
            "repeat_pattern": pattern
        }
        self.accept()

    def delete_course(self):
        self.deleted = True
        self.accept()


class TimeSlotWidget(QWidget):
    def __init__(self, parent, day_idx, slot_idx, start_min_offset, column_x, y_offset_top, pixel_per_minute, is_lecture=True):
        super().__init__(parent)
        self.day_idx = day_idx
        self.slot_idx = slot_idx
        self.start_min_offset = start_min_offset
        self.pixel_per_minute = pixel_per_minute
        self.column_x = column_x
        self.y_offset_top = y_offset_top
        self.is_lecture = is_lecture

        self.setFont(QFont("Arial", 12))

        # Possible states: "empty", "filled", "conflict", "selected"
        self.state = "empty"
        self.course_name = ""
        self.instructor = ""
        self.remarks = ""
        self.duration = 80 if is_lecture else 50

        self.setToolTip("Click to add course")
        self.setMouseTracking(True)  # For hover
        self.resize_slot()

        # Animated properties
        self._borderWidth = 1
        self._borderColor = QColor("#AAAAAA")
        self._borderStyle = "dashed"
        self._fillColor = QColor(0,0,0,0)

        # Faster 80ms animations
        self.enter_animation = QPropertyAnimation(self, b"borderWidth")
        self.enter_animation.setDuration(80)
        self.enter_animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.leave_animation = QPropertyAnimation(self, b"borderWidth")
        self.leave_animation.setDuration(80)
        self.leave_animation.setEasingCurve(QEasingCurve.InOutCubic)

    def resize_slot(self):
        top = self.start_min_offset * self.pixel_per_minute
        height = self.duration * self.pixel_per_minute
        # narrower box
        self.setGeometry(self.column_x, self.y_offset_top + top, 90, height)

    @pyqtProperty(int)
    def borderWidth(self):
        return self._borderWidth

    @borderWidth.setter
    def borderWidth(self, w):
        self._borderWidth = w
        self.update()

    @pyqtProperty(QColor)
    def borderColor(self):
        return self._borderColor

    @borderColor.setter
    def borderColor(self, c):
        self._borderColor = c
        self.update()

    def setState(self, state):
        self.state = state
        if state == "empty":
            self._borderStyle = "dashed"
            self._borderColor = QColor("#AAAAAA")
            self._borderWidth = 1
            self._fillColor = QColor(0,0,0,0)
            self.setToolTip("Click to add course")
        elif state == "filled":
            self._borderStyle = "solid"
            self._borderColor = QColor("#000000")
            self._borderWidth = 2
            self._fillColor = QColor("#FFFFCC") if self.is_lecture else QColor("#CCFFCC")
            self.setToolTip("Filled slot")
        elif state == "conflict":
            self._borderStyle = "dashed"
            self._borderColor = QColor("#AAAAAA")
            self._borderWidth = 1
            self._fillColor = QColor(0,0,0,0)
            self.setToolTip("Unavailable due to conflict")
        elif state == "selected":
            self._borderStyle = "solid"
            self._borderColor = QColor("#000000")
            self._borderWidth = 3
            if self.course_name.strip():
                self._fillColor = QColor("#FFFFCC") if self.is_lecture else QColor("#CCFFCC")
            else:
                self._fillColor = QColor(0,0,0,0)
            self.setToolTip("Editing...")
        self.update()

    def setCourseInfo(self, course_name, instructor, remarks, duration):
        self.course_name = course_name
        self.instructor = instructor
        self.remarks = remarks
        self.duration = int(duration)
        self.resize_slot()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill
        painter.setBrush(QBrush(self._fillColor))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())

        # Border
        pen = QPen(self._borderColor, self._borderWidth)
        if self._borderStyle == "solid":
            pen.setStyle(Qt.SolidLine)
        else:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect())

        # Show text if filled or selected
        if self.state in ["filled", "selected"]:
            if self.course_name.strip():
                painter.setPen(Qt.black)
                painter.setFont(QFont("Arial", 10))
                text = self.course_name
                if self.instructor.strip():
                    text += "\n" + self.instructor
                painter.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, text)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.state == "selected":
            return
        if self.state == "empty":
            self.enter_animation.stop()
            self.enter_animation.setStartValue(self.borderWidth)
            self.enter_animation.setEndValue(3)
            self.enter_animation.start()
            self._borderColor = QColor("#000000")
            self._borderStyle = "solid"
            self.update()
        elif self.state == "conflict":
            self.enter_animation.stop()
            self.enter_animation.setStartValue(self.borderWidth)
            self.enter_animation.setEndValue(3)
            self.enter_animation.start()
            self._borderColor = QColor("#FF0000")
            self._borderStyle = "solid"
            self.update()
        elif self.state == "filled":
            self.enter_animation.stop()
            self.enter_animation.setStartValue(self.borderWidth)
            self.enter_animation.setEndValue(3)
            self.enter_animation.start()
            self._borderColor = QColor("#000000")
            self._borderStyle = "solid"
            self.update()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self.state == "selected":
            return
        if self.state == "empty":
            self.leave_animation.stop()
            self.leave_animation.setStartValue(self.borderWidth)
            self.leave_animation.setEndValue(1)
            self.leave_animation.start()
            self._borderColor = QColor("#AAAAAA")
            self._borderStyle = "dashed"
            self.update()
        elif self.state == "conflict":
            self.leave_animation.stop()
            self.leave_animation.setStartValue(self.borderWidth)
            self.leave_animation.setEndValue(1)
            self.leave_animation.start()
            self._borderColor = QColor("#AAAAAA")
            self._borderStyle = "dashed"
            self.update()
        elif self.state == "filled":
            self.leave_animation.stop()
            self.leave_animation.setStartValue(self.borderWidth)
            self.leave_animation.setEndValue(2)
            self.leave_animation.start()
            self._borderColor = QColor("#000000")
            self._borderStyle = "solid"
            self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.state == "conflict":
            return
        self.setState("selected")
        self.window().edit_slot(self.day_idx, self.slot_idx)


class ScheduleWidget(QWidget):
    def __init__(self, timetable_data, parent=None):
        super().__init__(parent)
        self.timetable_data = timetable_data
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        self.slots_info = [
            ("8:30am", 0, True),
            ("10:30am", 120, True),
            ("1:30pm", 300, True),
            ("3:30pm", 420, True),
            ("6:00pm", 570, False),
            ("7:00pm", 630, False),
            ("8:00pm", 690, False)
        ]

        self.pixel_per_minute = 1
        self.y_offset_top = 40
        self.x_offset_initial = 100
        self.base_width = 90

        total_height = self.y_offset_top + 750*self.pixel_per_minute + 50
        total_width = self.x_offset_initial + (self.base_width * len(self.days)) + 100
        self.setFixedSize(total_width, total_height)

        self.slot_widgets = {}
        self.initUI()

    def initUI(self):
        font_day = QFont("Arial", 12, QFont.Bold)
        for i, day in enumerate(self.days):
            lbl = QLabel(day, self)
            lbl.setFont(font_day)
            lbl.setAlignment(Qt.AlignCenter)
            day_x = self.x_offset_initial + i * self.base_width
            lbl.setGeometry(day_x, 0, self.base_width, self.y_offset_top - 20)

        # Create slot widgets
        for day_idx in range(len(self.days)):
            for slot_idx, (time_str, offset_min, is_lecture) in enumerate(self.slots_info):
                column_x = self.x_offset_initial + day_idx * self.base_width
                w = TimeSlotWidget(self, day_idx, slot_idx, offset_min, column_x,
                                   self.y_offset_top, self.pixel_per_minute, is_lecture=is_lecture)
                self.slot_widgets[(day_idx, slot_idx)] = w
                w.setState("empty")

        self.update_conflicts()

    def refresh_slot(self, day_idx, slot_idx, data):
        """Populate the slot with new data, re-check conflicts."""
        w = self.slot_widgets[(day_idx, slot_idx)]
        _, _, is_lecture = self.slots_info[slot_idx]

        if not data:
            # empty
            w.setCourseInfo("", "", "", "80" if is_lecture else "50")
            w.setState("empty")
        else:
            duration = data.get("duration", "80" if is_lecture else "50")
            w.setCourseInfo(
                data.get("course_name", ""),
                data.get("instructor_name", ""),
                data.get("remarks", ""),
                duration
            )
            w.setState("filled")

        self.update_conflicts()

    def update_conflicts(self):
        # First, reset states to "empty" or "filled" unless "selected"
        for (d, s), w in self.slot_widgets.items():
            if w.state == "selected":
                # keep it
                continue
            data = self.window().timetable_data.get((d, s), {})
            _, _, is_lecture = self.slots_info[s]
            if data:
                w.setState("filled")
            else:
                w.setState("empty")

        # Then mark conflicts
        for day_idx in range(len(self.days)):
            ends = []
            for slot_idx, (tstr, start_min, is_lecture) in enumerate(self.slots_info):
                data = self.window().timetable_data.get((day_idx, slot_idx), {})
                dur = int(data.get("duration", 80 if is_lecture else 50)) if data else (80 if is_lecture else 50)
                end_min = start_min + dur
                ends.append((slot_idx, start_min, end_min))

            # Overlap check
            for i in range(len(ends)):
                for j in range(i+1, len(ends)):
                    if ends[i][2] > ends[j][1]:
                        w_conflict = self.slot_widgets[(day_idx, ends[j][0])]
                        if w_conflict.state != "selected":
                            w_conflict.setState("conflict")
                            w_conflict.setToolTip("Unavailable due to conflict")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background lines every 30 minutes
        painter.setPen(QPen(QColor("#DDDDDD"), 1, Qt.DotLine))
        minute = 0
        while minute <= 750:
            y_pos = self.y_offset_top + minute
            painter.drawLine(self.x_offset_initial - 30, y_pos, self.width()-20, y_pos)
            minute += 30

        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Arial", 9))

        def minutes_to_hhmm(m):
            base_hour = 8
            base_minute = 30
            total_min = base_hour*60 + base_minute + m
            h = total_min // 60
            mm = total_min % 60
            am_pm = "am" if h<12 else "pm"
            disp_h = h if h<=12 else (h-12)
            return f"{disp_h}:{mm:02d}{am_pm}"

        minute = 0
        while minute <= 750:
            y_pos = self.y_offset_top + minute
            time_str = minutes_to_hhmm(minute)
            painter.drawText(self.x_offset_initial - 90, y_pos+4, time_str)
            minute += 30


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CUHK(SZ) Course Scheduler (v1.0)")
        self.resize(800, 600)
        self.timetable_data = {}
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.schedule_widget = ScheduleWidget(self.timetable_data)
        layout.addWidget(self.schedule_widget)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save Timetable", self)
        save_action.triggered.connect(self.save_timetable)
        file_menu.addAction(save_action)

        load_action = QAction("Load Timetable", self)
        load_action.triggered.connect(self.load_timetable)
        file_menu.addAction(load_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self.apply_stylesheet()

    def apply_stylesheet(self):
        qss = """
        QMainWindow {
            background-color: #F8F8F8;
        }
        QLabel {
            font-family: Arial;
            font-size: 12pt;
        }
        QMenuBar {
            background-color: #ffffff;
        }
        QMenuBar::item {
            background-color: #ffffff;
            padding: 5px 5px;
        }
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        """
        self.setStyleSheet(qss)

    def edit_slot(self, day_idx, slot_idx):
        """Handle user clicking a slot, opening the edit dialog."""
        w = self.schedule_widget.slot_widgets[(day_idx, slot_idx)]
        if w.state == "conflict":
            return

        _, _, is_lecture = self.schedule_widget.slots_info[slot_idx]
        existing = self.timetable_data.get((day_idx, slot_idx), {})

        dialog = CourseDialog(self, existing_data=existing if existing else None, is_lecture=is_lecture)
        if dialog.exec_():
            if dialog.deleted:
                # If user deletes a repeated course, remove from all repeated days
                if (day_idx, slot_idx) in self.timetable_data:
                    # Retrieve its pattern
                    old_pattern = existing.get("repeat_pattern", "None")
                    # Remove this course from all days in that pattern
                    self.delete_course_in_pattern(day_idx, slot_idx, old_pattern)
                self.schedule_widget.refresh_slot(day_idx, slot_idx, {})
            elif dialog.saved_data:
                new_data = dialog.saved_data
                # If user sets a pattern, we replicate the data to all days in that pattern
                self.apply_course_in_pattern(day_idx, slot_idx, new_data)
        else:
            # The user canceled. Revert from "selected" to prior state
            if (day_idx, slot_idx) not in self.timetable_data:
                w.setState("empty")
            else:
                w.setState("filled")

    def apply_course_in_pattern(self, day_idx, slot_idx, course_data):
        """
        Place the course data into (day_idx, slot_idx) and all other days
        indicated by repeat_pattern, if day_idx is in that pattern.
        """
        # Example: If user chooses "MonWed" and day_idx=0 (Monday),
        # then we also update day_idx=2 (Wednesday). If day_idx=2 was chosen,
        # we also confirm that 2 is in [0,2]. Then apply to day_idx=0.
        pattern_name = course_data.get("repeat_pattern", "None")
        pattern_days = REPEAT_PATTERNS.get(pattern_name, [])

        # If the current day_idx is not in the chosen pattern, we do nothing special
        # (User might have chosen "MonWed" while editing the Tuesday slot, which is ambiguous.)
        # But let's assume we only replicate if day_idx is indeed in pattern_days.
        if day_idx in pattern_days:
            # For each day in pattern_days, store the same course data
            for d in pattern_days:
                self.timetable_data[(d, slot_idx)] = course_data
            # Also store for the original day, in case it's not repeated
            self.timetable_data[(day_idx, slot_idx)] = course_data
        else:
            # If "None" or day_idx not in pattern, just store it in the single slot
            self.timetable_data[(day_idx, slot_idx)] = course_data

        # Update UI
        for d in pattern_days:
            self.schedule_widget.refresh_slot(d, slot_idx, self.timetable_data.get((d, slot_idx), {}))
        self.schedule_widget.refresh_slot(day_idx, slot_idx, course_data)

    def delete_course_in_pattern(self, day_idx, slot_idx, pattern_name):
        """Remove the course from the chosen day_idx and all repeated days in the pattern."""
        pattern_days = REPEAT_PATTERNS.get(pattern_name, [])
        if day_idx in pattern_days:
            # Delete from all days in that pattern
            for d in pattern_days:
                if (d, slot_idx) in self.timetable_data:
                    del self.timetable_data[(d, slot_idx)]
                self.schedule_widget.refresh_slot(d, slot_idx, {})
        else:
            # Just delete from the single slot
            if (day_idx, slot_idx) in self.timetable_data:
                del self.timetable_data[(day_idx, slot_idx)]
            self.schedule_widget.refresh_slot(day_idx, slot_idx, {})

    def save_timetable(self):
        # Convert keys to strings
        str_data = {}
        for (d, s), val in self.timetable_data.items():
            key = f"{d},{s}"
            str_data[key] = val

        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Timetable", "", "JSON Files (*.json)", options=options)
        if fileName:
            with open(fileName, "w") as f:
                json.dump(str_data, f, indent=4)
            QMessageBox.information(self, "Saved", "Timetable saved successfully.")

    def load_timetable(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Timetable", "", "JSON Files (*.json)", options=options)
        if fileName:
            try:
                with open(fileName, "r") as f:
                    str_data = json.load(f)
                self.timetable_data = {}
                for key, val in str_data.items():
                    d_str, s_str = key.split(",")
                    d, s = int(d_str), int(s_str)
                    self.timetable_data[(d, s)] = val

                # Update UI
                for d in range(len(self.schedule_widget.days)):
                    for s in range(len(self.schedule_widget.slots_info)):
                        if (d, s) in self.timetable_data:
                            self.schedule_widget.refresh_slot(d, s, self.timetable_data[(d,s)])
                        else:
                            self.schedule_widget.refresh_slot(d, s, {})
                QMessageBox.information(self, "Loaded", "Timetable loaded successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load file:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
