import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QPushButton, QDialog, QVBoxLayout, 
    QHBoxLayout, QLineEdit, QTextEdit, QMenuBar, QAction, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt

class CourseDialog(QDialog):
    def __init__(self, parent=None, existing_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Course")
        
        self.course_line = QLineEdit(self)
        self.instructor_line = QLineEdit(self)
        self.remarks_text = QTextEdit(self)
        
        if existing_data:
            self.course_line.setText(existing_data.get("course_name", ""))
            self.instructor_line.setText(existing_data.get("instructor_name", ""))
            self.remarks_text.setPlainText(existing_data.get("remarks", ""))
        
        form_layout = QVBoxLayout()
        
        # Course Name (Mandatory)
        form_layout.addWidget(QLabel("Course Name (required):"))
        form_layout.addWidget(self.course_line)
        
        # Instructor Name (Optional)
        form_layout.addWidget(QLabel("Instructor Name (optional):"))
        form_layout.addWidget(self.instructor_line)
        
        # Remarks (Optional)
        form_layout.addWidget(QLabel("Remarks (optional):"))
        form_layout.addWidget(self.remarks_text)
        
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
        # Course name mandatory
        course_name = self.course_line.text().strip()
        if not course_name:
            QMessageBox.warning(self, "Error", "Course Name is required.")
            return
        
        instructor = self.instructor_line.text().strip()
        remarks = self.remarks_text.toPlainText().strip()
        
        self.saved_data = {
            "course_name": course_name,
            "instructor_name": instructor,
            "remarks": remarks
        }
        self.accept()
    
    def delete_course(self):
        # Indicate that user wants to clear/delete the slot
        self.deleted = True
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Undergrad Course Scheduler")
        self.resize(1200, 600)
        
        # Define timetable structure
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.lecture_slots = ["8:00am-9:50am", "10:30am-11:50am", "1:30pm-2:50pm", "3:30pm-4:50pm"]
        self.tutorial_slots = ["6:00pm-6:50pm", "7:00pm-7:50pm", "8:00pm-8:50pm"]
        
        self.all_timeslots = self.lecture_slots + self.tutorial_slots
        
        # Data structure to hold course info
        self.timetable_data = {}
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QGridLayout()
        central_widget.setLayout(layout)
        
        # Create headers
        layout.addWidget(QLabel("Time / Day"), 0, 0)
        for i, day in enumerate(self.days):
            lbl = QLabel(day)
            lbl.setFont(QFont("Arial", 14, QFont.Bold))
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl, 0, i+1)
        
        # Create time row labels and slot widgets
        self.slot_buttons = {}  # key: (day_idx, slot_idx) -> button
        
        for slot_idx, timestr in enumerate(self.all_timeslots):
            time_lbl = QLabel(timestr)
            time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(time_lbl, slot_idx+1, 0)
            
            for day_idx in range(len(self.days)):
                btn = QPushButton("")
                btn.setStyleSheet(self.get_slot_style(slot_idx))
                btn.clicked.connect(lambda _, d=day_idx, s=slot_idx: self.edit_slot(d, s))
                
                self.slot_buttons[(day_idx, slot_idx)] = btn
                layout.addWidget(btn, slot_idx+1, day_idx+1)
        
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
    
    def get_slot_style(self, slot_idx):
        # Different colors for lecture vs tutorial
        # Lectures: 0-3, Tutorials: 4-6
        if slot_idx < 4:
            # Lecture slot
            return "background-color: #FFF8DC;" # Cornsilk
        else:
            # Tutorial slot
            return "background-color: #E0FFE0;" # Light greenish
         
    def edit_slot(self, day_idx, slot_idx):
        # Fetch existing data if any
        existing = self.timetable_data.get((day_idx, slot_idx), {})
        dialog = CourseDialog(self, existing_data=existing if existing else None)
        if dialog.exec_():
            if dialog.deleted:
                # Delete course
                if (day_idx, slot_idx) in self.timetable_data:
                    del self.timetable_data[(day_idx, slot_idx)]
                self.slot_buttons[(day_idx, slot_idx)].setText("")
                self.slot_buttons[(day_idx, slot_idx)].setToolTip("")
            elif dialog.saved_data:
                self.timetable_data[(day_idx, slot_idx)] = dialog.saved_data
                self.update_slot_button(day_idx, slot_idx)
    
    def update_slot_button(self, day_idx, slot_idx):
        data = self.timetable_data.get((day_idx, slot_idx), {})
        course_name = data.get("course_name", "")
        instructor = data.get("instructor_name", "")
        remarks = data.get("remarks", "")
        
        display_text = course_name
        tooltip = f"Course: {course_name}"
        if instructor:
            tooltip += f"\nInstructor: {instructor}"
        if remarks:
            tooltip += f"\nRemarks: {remarks}"
        
        self.slot_buttons[(day_idx, slot_idx)].setText(display_text)
        self.slot_buttons[(day_idx, slot_idx)].setToolTip(tooltip)
    
    def save_timetable(self):
        # Show file dialog
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save Timetable", "", "JSON Files (*.json)", options=options)
        if fileName:
            # Serialize self.timetable_data
            with open(fileName, "w") as f:
                json.dump(self.timetable_data, f, indent=4)
            QMessageBox.information(self, "Saved", "Timetable saved successfully.")
    
    def load_timetable(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Load Timetable", "", "JSON Files (*.json)", options=options)
        if fileName:
            try:
                with open(fileName, "r") as f:
                    data = json.load(f)
                self.timetable_data = data
                # Update UI
                for (day_idx, slot_idx), course_data in self.timetable_data.items():
                    self.update_slot_button(day_idx, slot_idx)
                # Clear any slots not mentioned in the file
                for key, btn in self.slot_buttons.items():
                    if key not in self.timetable_data:
                        btn.setText("")
                        btn.setToolTip("")
                QMessageBox.information(self, "Loaded", "Timetable loaded successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load file:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Optionally set a modern style
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
