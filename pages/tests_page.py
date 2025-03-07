import json
import os
import pandas as pd
from PyQt5.QtWidgets import (
	QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
	QHBoxLayout, QLabel, QLineEdit, QHeaderView, QFrame, QInputDialog, QFileDialog, QMessageBox,QDialog,
	QListWidget,QTextEdit
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class SelectCommandDialog(QDialog):
    """Dialog pentru alegerea unei comenzi disponibile."""
    def __init__(self, commands_data):
        super().__init__()
        self.setWindowTitle("Select a Command")
        self.setGeometry(400, 300, 400, 300)
        self.selected_command = None
        layout = QVBoxLayout()
        self.command_list = QListWidget()
        self.command_list.addItems(commands_data.keys())
        self.command_list.itemDoubleClicked.connect(self.select_command)
        layout.addWidget(self.command_list)
        self.setLayout(layout)
    def select_command(self, item):
        self.selected_command = item.text()
        self.accept()

class SelectParameterDialog(QDialog):
    """Dialog pentru alegerea parametrilor necesari pentru o comandă."""
    def __init__(self, parameters_data, required_categories):
        super().__init__()
        self.setWindowTitle("Select Parameters")
        self.setGeometry(400, 300, 400, 300)
        self.selected_parameters = {}
        layout = QVBoxLayout()
        self.parameter_lists = {}
        for category in required_categories:
            param_list = QListWidget()
            param_list.addItems(parameters_data.get(category, []))
            param_list.itemDoubleClicked.connect(lambda item, cat=category: self.select_parameter(cat, item.text()))
            layout.addWidget(QLabel(f"Select {category}:"))
            layout.addWidget(param_list)
            self.parameter_lists[category] = param_list
        self.setLayout(layout)
    def select_parameter(self, category, value):
        self.selected_parameters[category] = value
        if len(self.selected_parameters) == len(self.parameter_lists):
            self.accept()

class PreviewTestStepDialog(QDialog):
    """Dialog pentru vizualizarea test step-ului și selectarea parametrilor."""
    def __init__(self, command_action, command_expected, parameters_data, required_categories):
        super().__init__()
        self.setWindowTitle("Preview Test Step")
        self.setGeometry(400, 300, 500, 400)
        self.selected_parameters = {}
        layout = QVBoxLayout()
        self.action_label = QLabel("<b>Action:</b>")
        layout.addWidget(self.action_label)
        self.action_text = QTextEdit(command_action if command_action else "No action defined")
        self.action_text.setReadOnly(True)
        layout.addWidget(self.action_text)
        self.expected_label = QLabel("<b>Expected:</b>")
        layout.addWidget(self.expected_label)
        self.expected_text = QTextEdit(command_expected if command_expected else "No expected result defined")
        self.expected_text.setReadOnly(True)
        layout.addWidget(self.expected_text)
        self.parameters_label = QLabel("<b>Select Parameters:</b>")
        layout.addWidget(self.parameters_label)
        self.parameter_lists = {}
        unique_categories = set([part.strip("{}") for part in command_action.split() if "{" in part] +
                                [part.strip("{}") for part in command_expected.split() if "{" in part])
        for category in unique_categories:
            param_list = QListWidget()
            param_list.addItems(parameters_data.get(category, []))
            param_list.itemDoubleClicked.connect(lambda item, cat=category: self.select_parameter(cat, item.text()))
            layout.addWidget(QLabel(f"Select {category}:"))
            layout.addWidget(param_list)
            self.parameter_lists[category] = param_list
        self.confirm_button = QPushButton("Apply Parameters")
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.accept)
        layout.addWidget(self.confirm_button)
        self.setLayout(layout)
    def select_parameter(self, category, value):
        """Salvează parametrul selectat și actualizează vizual textul fără a închide dialogul imediat."""
        self.selected_parameters[category] = value
        self.update_text_display(category, value)
    def update_text_display(self, category, value):
        """Actualizează vizual Action și Expected Result cu parametrii selectați."""
        self.action_text.setText(self.action_text.toPlainText().replace(f"{{{category}}}", value))
        self.expected_text.setText(self.expected_text.toPlainText().replace(f"{{{category}}}", value))
        if len(self.selected_parameters) == len(self.parameter_lists):
            self.confirm_button.setEnabled(True)


class TestsPage(QWidget):
	def __init__(self):
		super().__init__()

		self.json_file = os.path.join(os.path.dirname(__file__), "../data/tests.json")


		# 🔹 Asigurăm că datele sunt încărcate corect
		self.tests_data = self.load_json(self.json_file)

		self.setStyleSheet("""
            QWidget { background-color: #F8F9FA; }
            QLabel { font-size: 14px; color: #333; }
            QPushButton {
                background-color: #007BFF;
                color: white;
                font-size: 12px;
                padding: 6px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #0056b3; }
            QTableWidget { background-color: white; border: 1px solid #ddd; }
        """)

		layout = QVBoxLayout()

		title = QLabel("Manage Tests")
		title.setFont(QFont("Arial", 16, QFont.Bold))
		title.setAlignment(Qt.AlignCenter)
		layout.addWidget(title)

		line = QFrame()
		line.setFrameShape(QFrame.HLine)
		line.setFrameShadow(QFrame.Sunken)
		layout.addWidget(line)

		input_layout = QHBoxLayout()

		self.test_name_input = QLineEdit()
		self.test_name_input.setPlaceholderText("Enter Test Name...")
		input_layout.addWidget(self.test_name_input)

		self.add_test_button = QPushButton("Add Test")
		self.add_test_button.clicked.connect(self.add_test)
		input_layout.addWidget(self.add_test_button)

		layout.addLayout(input_layout)

		# Butoane pentru Import/Export
		button_layout = QHBoxLayout()
		self.import_button = QPushButton("Import from XLSX")
		self.import_button.clicked.connect(self.import_from_xlsx)
		button_layout.addWidget(self.import_button)

		self.export_button = QPushButton("Export to XLSX")
		self.export_button.clicked.connect(self.export_to_xlsx)
		button_layout.addWidget(self.export_button)

		layout.addLayout(button_layout)

		# 🔹 Tabel pentru afișarea testelor
		self.test_table = QTableWidget()
		self.test_table.setColumnCount(7)
		self.test_table.setHorizontalHeaderLabels([
			"Test Name", "Description", "Precondition", "Action", "Expected Results",
			"Test Data Description", "Description TCG"
		])
		self.test_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
		layout.addWidget(self.test_table)

		# 🔹 Butoane pentru acțiuni pe testele selectate
		action_buttons_layout = QHBoxLayout()

		self.add_step_button = QPushButton("Add Test Step")
		self.add_step_button.clicked.connect(self.add_test_step)
		action_buttons_layout.addWidget(self.add_step_button)

		self.delete_test_button = QPushButton("Delete Test")
		self.delete_test_button.clicked.connect(self.delete_selected_test)
		action_buttons_layout.addWidget(self.delete_test_button)

		layout.addLayout(action_buttons_layout)

		self.setLayout(layout)

		self.load_tests()

	def add_test(self):
		"""Adaugă un test nou în tabel și în JSON."""
		test_name = self.test_name_input.text().strip()
		if not test_name:
			return

		description, ok = QInputDialog.getText(self, "Enter Description", f"Enter description for {test_name}:")
		if not ok: description = ""

		precondition, ok = QInputDialog.getText(self, "Enter Precondition", f"Enter precondition for {test_name}:")
		if not ok: precondition = ""

		row_position = self.test_table.rowCount()
		self.test_table.insertRow(row_position)

		self.test_table.setItem(row_position, 0, QTableWidgetItem(test_name))
		self.test_table.setItem(row_position, 1, QTableWidgetItem(description))
		self.test_table.setItem(row_position, 2, QTableWidgetItem(precondition))

		for col in range(3, 7):
			self.test_table.setItem(row_position, col, QTableWidgetItem(""))

		self.tests_data[test_name] = {
			"Description": description,
			"Precondition": precondition,
			"Action": "",
			"Expected Results": "",
			"Test Data Description": "",
			"Description TCG": ""
		}

		self.save_tests()
		self.test_name_input.clear()

	def add_test_step(self):
		self.commands_file = os.path.join(os.path.dirname(__file__), "../data/generic_commands.json")
		self.parameters_file = os.path.join(os.path.dirname(__file__), "../data/parameters.json")

		self.commands_data = self.load_json(self.commands_file)  # Acum este definit
		self.parameters_data = self.load_json(self.parameters_file)
		try:
			print("🔹 add_test_step called")

			selected_row = self.test_table.currentRow()
			if selected_row == -1:
				QMessageBox.warning(self, "No Test Selected", "Please select a test to add a step.")
				return

			test_name = self.test_table.item(selected_row, 0).text()
			print(f"🔹 Selected test: {test_name}")

			if not self.commands_data:
				print("❌ Error: No commands available in generic_commands.json")
				QMessageBox.critical(self, "Error", "No generic commands available.")
				return

			command_dialog = SelectCommandDialog(self.commands_data)
			if not command_dialog.exec_() or not command_dialog.selected_command:
				print("❌ Error: No command selected")
				QMessageBox.warning(self, "No Command Selected", "You must select a command.")
				return

			selected_command = command_dialog.selected_command
			print(f"✅ Selected command: {selected_command}")

			if selected_command not in self.commands_data:
				QMessageBox.critical(self, "Error", f"Command '{selected_command}' not found in generic commands.")
				return

			command_action = self.commands_data[selected_command].get("Action", "").strip()
			command_expected = self.commands_data[selected_command].get("Expected Result", "").strip()

			print(f"🔹 Command Action: {command_action}")
			print(f"🔹 Command Expected: {command_expected}")

			if not command_action and not command_expected:
				print("❌ Error: Command action and expected result are empty!")
				QMessageBox.critical(self, "Error", "The selected command has no defined Action or Expected Result.")
				return

			required_categories = [part.strip("{}") for part in command_action.split() if "{" in part]
			print(f"🔹 Required categories: {required_categories}")

			if not self.parameters_data:
				QMessageBox.critical(self, "Error", "No parameters available.")
				return

			missing_categories = [cat for cat in required_categories if cat not in self.parameters_data]
			if missing_categories:
				QMessageBox.critical(self, "Error", f"Missing parameter categories: {', '.join(missing_categories)}")
				return

			preview_dialog = PreviewTestStepDialog(command_action, command_expected, self.parameters_data,
			                                       required_categories)
			if not preview_dialog.exec_():
				print("❌ Error: No parameters selected")
				QMessageBox.warning(self, "No Parameters Selected", "You must select parameters.")
				return

			selected_parameters = preview_dialog.selected_parameters
			print(f"✅ Selected parameters: {selected_parameters}")

			for category, value in selected_parameters.items():
				command_action = command_action.replace(f"{{{category}}}", value)
				command_expected = command_expected.replace(f"{{{category}}}", value)

			if test_name not in self.tests_data:
				QMessageBox.critical(self, "Error", f"Test '{test_name}' not found in tests data.")
				return

			self.tests_data[test_name]["Action"] = command_action
			self.tests_data[test_name]["Expected Results"] = command_expected
			self.test_table.setItem(selected_row, 3, QTableWidgetItem(command_action))
			self.test_table.setItem(selected_row, 4, QTableWidgetItem(command_expected))

			self.save_tests()
			QMessageBox.information(self, "Test Step Added", f"Step added for {test_name}: {selected_command}")

		except Exception as e:
			print(f"❌ Unexpected error: {e}")
			QMessageBox.critical(self, "Unexpected Error", f"An error occurred:\n{str(e)}")

	def delete_selected_test(self):
		"""Șterge testul selectat din tabel și JSON."""
		selected_row = self.test_table.currentRow()
		if selected_row == -1:
			QMessageBox.warning(self, "No Test Selected", "Please select a test to delete.")
			return

		test_name = self.test_table.item(selected_row, 0).text()

		reply = QMessageBox.question(self, "Delete Test",
		                             f"Are you sure you want to delete the test '{test_name}'?",
		                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

		if reply == QMessageBox.Yes:
			self.test_table.removeRow(selected_row)
			if test_name in self.tests_data:
				del self.tests_data[test_name]
				self.save_tests()

	def save_tests(self):
		"""Salvează testele în JSON."""
		with open(self.json_file, "w", encoding="utf-8") as file:
			json.dump(self.tests_data, file, indent=4)

	def load_tests(self):
		"""Încarcă testele din JSON."""
		if not os.path.exists(self.json_file):
			return

		try:
			with open(self.json_file, "r", encoding="utf-8") as file:
				self.tests_data = json.load(file)

			for test_name, details in self.tests_data.items():
				row_position = self.test_table.rowCount()
				self.test_table.insertRow(row_position)

				self.test_table.setItem(row_position, 0, QTableWidgetItem(test_name))
				for col, key in enumerate(["Description", "Precondition", "Action", "Expected Results",
				                           "Test Data Description", "Description TCG"], start=1):
					self.test_table.setItem(row_position, col, QTableWidgetItem(details.get(key, "")))
		except json.JSONDecodeError:
			print("Error loading JSON file.")

	def add_test_to_table(self, test_name, test_details):
		"""Adaugă un test în tabel doar dacă nu există deja."""
		if self.is_test_in_table(test_name):
			print(f"⚠️ Test '{test_name}' is already in the table. Skipping.")
			return

		row_position = self.test_table.rowCount()
		self.test_table.insertRow(row_position)

		self.test_table.setItem(row_position, 0, QTableWidgetItem(test_name))
		for col, key in enumerate(["Description", "Precondition", "Action", "Expected Results",
		                           "Test Data Description", "Description TCG"], start=1):
			value = test_details.get(key, "")
			self.test_table.setItem(row_position, col, QTableWidgetItem(value))

		self.save_tests()

	def import_from_xlsx(self):
		"""Importă testele dintr-un fișier XLSX și le adaugă doar dacă nu sunt deja în tabel și JSON."""
		file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx);;All Files (*)")
		if not file_path:
			return

		df = pd.read_excel(file_path, dtype=str).fillna("")

		for _, row in df.iterrows():
			test_name = row["Test Name"].strip()

			# Verificăm dacă testul există deja în JSON sau UI
			if test_name in self.tests_data or self.is_test_in_table(test_name):
				print(f"⚠️ Test '{test_name}' already exists. Skipping import.")
				continue  # Sărim peste acest test, deoarece este deja prezent

			# Adăugăm testul în JSON și UI
			self.tests_data[test_name] = row.to_dict()
			self.add_test_to_table(test_name, self.tests_data[test_name])

		self.save_tests()
		QMessageBox.information(self, "Import Completed", "Tests imported successfully from XLSX!")

	def is_test_in_table(self, test_name):
		"""Verifică dacă un test există deja în tabel."""
		for row in range(self.test_table.rowCount()):
			existing_test_name = self.test_table.item(row, 0).text().strip()
			if existing_test_name == test_name:
				return True
		return False

	def export_to_xlsx(self):
		"""Exportă testele într-un fișier XLSX."""
		df = pd.DataFrame.from_dict(self.tests_data, orient="index")
		file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)")
		if file_path:
			df.to_excel(file_path, index_label="Test Name")

	def load_json(self, file_path):
		"""Încarcă un JSON sau returnează un dicționar gol dacă nu există."""
		if os.path.exists(file_path):
			try:
				with open(file_path, "r", encoding="utf-8") as file:
					return json.load(file)
			except json.JSONDecodeError:
				print(f"❌ Error: JSON file '{file_path}' is corrupted. Returning empty dictionary.")
				return {}
		return {}

