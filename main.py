import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QDialog, QHBoxLayout, QLineEdit, QTextEdit, QMenuBar, QAction, QFileDialog,
    QMessageBox, QComboBox
)
from PyQt5.QtGui import QFont, QPainter, QPen, QColor
from PyQt5.QtCore import Qt

class CourseDialog(QDialog):
    def __init__(self, parent=None, existing_data=None, is_lecture=True):
        super().__init__(parent)
        self.setWindowTitle("Edit Course")
        self.setModal(True)
        self.setMinimumWidth(300)

        self.course_line = QLineEdit(self)
        self.instructor_line = QLineEdit(self)
        self.remarks_text = QTextEdit(self)
        self.duration_combo = QComboBox(self)
        self.duration_combo.addItems(["50", "80", "110"])

        default_duration = "80" if is_lecture else "50"
        self.duration_combo.setCurrentText(default_duration)

        if existing_data:
            self.course_line.setText(existing_data.get("course_name", ""))
            self.instructor_line.setText(existing_data.get("instructor_name", ""))
            self.remarks_text.setPlainText(existing_data.get("remarks", ""))
            current_duration = existing_data.get("duration", default_duration)
            self.duration_combo.setCurrentText(current_duration)

        form_layout = QVBoxLayout()

        lbl_course = QLabel("Course Name (required):")
        lbl_course.setFont(QFont("Arial", 11))
        form_layout.addWidget(lbl_course)
        form_layout.addWidget(self.course_line)

        lbl_instructor = QLabel("Instructor Name (optional):")
        lbl_instructor.setFont(QFont("Arial", 11))
        form_layout.addWidget(lbl_instructor)
        form_layout.addWidget(self.instructor_line)

        lbl_remarks = QLabel("Remarks (optional):")
        lbl_remarks.setFont(QFont("Arial", 11))
        form_layout.addWidget(lbl_remarks)
        form_layout.addWidget(self.remarks_text)

        lbl_duration = QLabel("Class Duration (mins):")
        lbl_duration.setFont(QFont("Arial", 11))
        form_layout.addWidget(lbl_duration)
        form_layout.addWidget(self.duration_combo)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.delete_btn = QPushButton("Delete")
        self.cancel_btn = QPushButton("Cancel")

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.cancel_btn)

        form_layout.addLayout(btn_layout)
        self.setLayout(form_layout)

        self.save_btn.clicked.connect(self.save_course)
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

        self.saved_data = {
            "course_name": course_name,
            "instructor_name": instructor,
            "remarks": remarks,
            "duration": duration
        }
        self.accept()

    def delete_course(self):
        self.deleted = True
        self.accept()


class TimeSlotWidget(QPushButton):
    def __init__(self, parent, day_idx, slot_idx, start_min_offset, column_x, y_offset_top, pixel_per_minute, width=140, is_lecture=True):
        super().__init__("", parent)
        self.day_idx = day_idx
        self.slot_idx = slot_idx
        self.start_min_offset = start_min_offset
        self.pixel_per_minute = pixel_per_minute
        self.column_x = column_x
        self.y_offset_top = y_offset_top
        self.width = width
        self.is_lecture = is_lecture

        # Default duration
        self.current_duration = 80 if is_lecture else 50

        self.set_font()
        self.setToolTip("Click to edit")

        if self.is_lecture:
            # Lecture
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FFF8DC; 
                    border: 1px solid #AAAAAA; 
                    border-radius: 4px; 
                    font-size: 11pt;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #FFEFD5;
                }
            """)
        else:
            # Tutorial
            self.setStyleSheet("""
                QPushButton {
                    background-color: #E0FFE0; 
                    border: 1px solid #AAAAAA; 
                    border-radius: 4px; 
                    font-size: 11pt;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #D0FFD0;
                }
            """)

        self.update_geometry()

    def set_font(self):
        f = QFont("Arial", 11)
        self.setFont(f)

    def update_duration(self, duration):
        self.current_duration = int(duration)
        self.update_geometry()

    def update_info(self, course_name, instructor, remarks):
        # Display course name and instructor
        if instructor:
            display_text = f"{course_name}\n{instructor}"
        else:
            display_text = course_name
        tooltip = f"Course: {course_name}" if course_name else "Click to edit"
        if instructor:
            tooltip += f"\nInstructor: {instructor}"
        if remarks:
            tooltip += f"\nRemarks: {remarks}"
        self.setText(display_text)
        self.setToolTip(tooltip)

    def update_geometry(self):
        top = self.start_min_offset * self.pixel_per_minute
        height = self.current_duration * self.pixel_per_minute
        self.setGeometry(self.column_x, self.y_offset_top + top, self.width, height)


class ScheduleWidget(QWidget):
    def __init__(self, timetable_data, parent=None):
        super().__init__(parent)
        self.timetable_data = timetable_data
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        # slot times: (label, offset_min, is_lecture)
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
        self.y_offset_top = 50
        self.x_offset_initial = 100
        self.base_width = 140

        total_height = self.y_offset_top + 750*self.pixel_per_minute + 50
        total_width = self.x_offset_initial + (self.base_width * len(self.days)) + 100
        self.setFixedSize(total_width, total_height)

        self.slot_widgets = {}
        self.initUI()

    def initUI(self):
        # Day labels
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
                w = TimeSlotWidget(self, day_idx, slot_idx, offset_min, column_x, self.y_offset_top, self.pixel_per_minute, is_lecture=is_lecture)
                data = self.timetable_data.get((day_idx, slot_idx), {})
                if data:
                    w.update_info(data.get("course_name",""), data.get("instructor_name",""), data.get("remarks",""))
                    w.update_duration(data.get("duration","80" if is_lecture else "50"))
                else:
                    default_dur = "80" if is_lecture else "50"
                    w.update_info("", "", "")
                    w.update_duration(default_dur)

                w.clicked.connect(lambda _, d=day_idx, s=slot_idx: self.window().edit_slot(d, s))
                self.slot_widgets[(day_idx, slot_idx)] = w

    def refresh_slot(self, day_idx, slot_idx, data):
        w = self.slot_widgets[(day_idx, slot_idx)]
        _, _, is_lecture = self.slots_info[slot_idx]
        if not data:
            default_dur = "80" if is_lecture else "50"
            w.update_info("", "", "")
            w.update_duration(default_dur)
        else:
            w.update_info(data.get("course_name",""), data.get("instructor_name",""), data.get("remarks",""))
            w.update_duration(data.get("duration", "80" if is_lecture else "50"))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background lines every 30 minutes
        start_offset = 0
        end_offset = 750  # 8:30am to 9:00pm
        painter.setPen(QPen(QColor("#DDDDDD"), 1, Qt.DotLine))
        minute = 0
        while minute <= end_offset:
            y_pos = self.y_offset_top + minute * self.pixel_per_minute
            painter.drawLine(self.x_offset_initial - 30, y_pos, self.width()-20, y_pos)
            minute += 30

        # Label every 30 min
        painter.setPen(QPen(Qt.black, 1))
        painter.setFont(QFont("Arial", 11))

        def minutes_to_hhmm(m):
            base_hour = 8
            base_minute = 30
            total_min = base_hour*60 + base_minute + m
            h = total_min // 60
            mm = total_min % 60
            am_pm = "am" if h<12 else "pm"
            disp_h = h if h<=12 else h-12
            return f"{disp_h}:{mm:02d}{am_pm}"

        minute = 0
        while minute <= end_offset:
            y_pos = self.y_offset_top + minute * self.pixel_per_minute
            time_str = minutes_to_hhmm(minute)
            painter.drawText(self.x_offset_initial - 90, y_pos+4, time_str)
            minute += 30

        # Add ending times of classes (in black, no extra line)
        # We only add ending times that don't coincide with existing lines (to show difference)
        # Actually, we can show them anyway, just as text on the left.
        # We'll show all class end times next to the line if it's not already shown.
        # If it's exactly on a 30-min line, it will be duplicated - acceptable for simplicity.
        for (d, s), data in self.timetable_data.items():
            _, start_offset_min, _ = self.slots_info[s]
            duration = int(data.get("duration", "80"))
            end_offset_min = start_offset_min + duration
            if 0 <= end_offset_min <= 750:
                y_pos = self.y_offset_top + end_offset_min * self.pixel_per_minute
                end_time_str = minutes_to_hhmm(end_offset_min)
                painter.drawText(self.x_offset_initial - 90, y_pos+4, end_time_str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Undergrad Course Scheduler")
        self.resize(1100, 900)
        self.timetable_data = {}
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.schedule_widget = ScheduleWidget(self.timetable_data)
        layout.addWidget(self.schedule_widget)

        # Menus
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
            font-size: 11pt;
        }
        QMenuBar {
            background-color: #ffffff;
        }
        QMenuBar::item {
            background-color: #ffffff;
            padding: 5px 10px;
        }
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        """
        self.setStyleSheet(qss)

    def edit_slot(self, day_idx, slot_idx):
        _, _, is_lecture = self.schedule_widget.slots_info[slot_idx]
        existing = self.timetable_data.get((day_idx, slot_idx), {})
        dialog = CourseDialog(self, existing_data=existing if existing else None, is_lecture=is_lecture)
        if dialog.exec_():
            if dialog.deleted:
                if (day_idx, slot_idx) in self.timetable_data:
                    del self.timetable_data[(day_idx, slot_idx)]
                self.schedule_widget.refresh_slot(day_idx, slot_idx, {})
            elif dialog.saved_data:
                self.timetable_data[(day_idx, slot_idx)] = dialog.saved_data
                self.schedule_widget.refresh_slot(day_idx, slot_idx, dialog.saved_data)

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
