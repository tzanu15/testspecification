import json
import os
import pandas as pd
from PyQt5.QtWidgets import (
	QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
	QHBoxLayout, QLabel, QLineEdit, QHeaderView, QFrame, QInputDialog, QFileDialog, QMessageBox,QDialog,
	QListWidget,QTextEdit,QTabWidget,QToolButton,QStyle
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
        self.setGeometry(400, 300, 600, 500)
        self.selected_parameters = {}

        layout = QVBoxLayout()

        # 🔹 Action
        self.action_label = QLabel("<b>Action:</b>")
        layout.addWidget(self.action_label)

        self.action_text = QTextEdit(self.highlight_placeholders(command_action))
        self.action_text.setReadOnly(True)
        layout.addWidget(self.action_text)

        # 🔹 Expected Result
        self.expected_label = QLabel("<b>Expected:</b>")
        layout.addWidget(self.expected_label)

        self.expected_text = QTextEdit(self.highlight_placeholders(command_expected))
        self.expected_text.setReadOnly(True)
        layout.addWidget(self.expected_text)

        # 🔹 Tabs pentru parametri
        self.tab_widget = QTabWidget()
        self.parameter_lists = {}

        for category in required_categories:
            tab = QWidget()
            tab_layout = QVBoxLayout()

            # 🔹 Căutare în fiecare tab
            search_input = QLineEdit()
            search_input.setPlaceholderText(f"Search in {category}...")
            search_input.textChanged.connect(lambda text, cat=category: self.filter_parameters(cat, text))
            tab_layout.addWidget(search_input)

            param_list = QListWidget()
            param_list.addItems(parameters_data.get(category, []))
            param_list.itemDoubleClicked.connect(lambda item, cat=category: self.select_parameter(cat, item.text()))

            tab_layout.addWidget(param_list)
            tab.setLayout(tab_layout)

            self.parameter_lists[category] = param_list
            self.tab_widget.addTab(tab, category)

        layout.addWidget(self.tab_widget)

        # 🔹 Confirm Button
        self.confirm_button = QPushButton("Apply Parameters")
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.accept)
        layout.addWidget(self.confirm_button)

        self.setLayout(layout)

    def highlight_placeholders(self, text):
        """Evidențiază placeholder-urile în text."""
        highlighted_text = text
        for placeholder in set(part.strip("{}") for part in text.split() if "{" in part):
            highlighted_text = highlighted_text.replace(
                f"{{{placeholder}}}", f"<span style='background-color: yellow; font-weight: bold;'>{'{'+placeholder+'}'}</span>"
            )
        return f"<html><body>{highlighted_text}</body></html>"

    def select_parameter(self, category, value):
        """Salvează parametrul selectat și actualizează vizual textul fără a închide dialogul imediat."""
        self.selected_parameters[category] = value
        self.update_text_display(category, value)

    def update_text_display(self, category, value):
        """Actualizează vizual Action și Expected Result cu parametrii selectați."""
        self.action_text.setHtml(self.action_text.toHtml().replace(f"{{{category}}}", value))
        self.expected_text.setHtml(self.expected_text.toHtml().replace(f"{{{category}}}", value))

        if len(self.selected_parameters) == len(self.parameter_lists):
            self.confirm_button.setEnabled(True)

    def filter_parameters(self, category, search_text):
        """Filtrăm parametrii în tab-ul selectat pe baza textului introdus."""
        param_list = self.parameter_lists.get(category)
        if param_list:
            for i in range(param_list.count()):
                item = param_list.item(i)
                item.setHidden(search_text.lower() not in item.text().lower())

class TestsPage(QWidget):
	def __init__(self):
		super().__init__()

		self.json_file = os.path.join(os.path.dirname(__file__), "../data/tests.json")
		self.commands_file = os.path.join(os.path.dirname(__file__), "../data/generic_commands.json")
		self.parameters_file = os.path.join(os.path.dirname(__file__), "../data/parameters.json")

		# 🔹 Asigurăm că datele sunt încărcate corect
		self.tests_data = self.load_json(self.json_file)
		self.commands_data = self.load_json(self.commands_file)  # ✅ Inițializăm `commands_data`
		self.parameters_data = self.load_json(self.parameters_file)

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
		"""Adaugă un test step și îl inserează direct sub test, menținând layout-ul curat."""
		try:
			print("🔹 add_test_step called")

			selected_row = self.test_table.currentRow()
			if selected_row == -1:
				QMessageBox.warning(self, "No Test Selected", "Please select a test to add a step.")
				return

			# 🔹 Găsim testul asociat acestui rând
			test_name = None
			test_row = selected_row
			for row in range(selected_row, -1, -1):
				test_name_item = self.test_table.item(row, 0)
				if test_name_item and test_name_item.text().strip():
					test_name = test_name_item.text().strip()
					test_row = row
					break

			if not test_name:
				QMessageBox.warning(self, "No Test Found", "Could not determine the selected test.")
				return

			print(f"✅ Selected test: {test_name}")

			self.load_parameters()
			self.load_commands()

			command_dialog = SelectCommandDialog(self.commands_data)
			if not command_dialog.exec_():
				return

			selected_command = command_dialog.selected_command
			command_action = self.commands_data[selected_command].get("Action", "")
			command_expected = self.commands_data[selected_command].get("Expected Result", "")

			required_categories = set([part.strip("{}") for part in command_action.split() if "{" in part] +
			                          [part.strip("{}") for part in command_expected.split() if "{" in part])

			parameter_dialog = PreviewTestStepDialog(command_action, command_expected, self.parameters_data,
			                                         required_categories)
			if not parameter_dialog.exec_():
				return

			selected_parameters = parameter_dialog.selected_parameters
			print(f"✅ Selected parameters: {selected_parameters}")

			for category, value in selected_parameters.items():
				command_action = command_action.replace(f"{{{category}}}", value)
				command_expected = command_expected.replace(f"{{{category}}}", value)

			if "Action" not in self.tests_data[test_name]:
				self.tests_data[test_name]["Action"] = []
			if "Expected Results" not in self.tests_data[test_name]:
				self.tests_data[test_name]["Expected Results"] = []

			step_number = len(self.tests_data[test_name]["Action"]) + 1
			action_text = f"{command_action}"
			expected_text = f"{command_expected}"

			self.tests_data[test_name]["Action"].append(action_text)
			self.tests_data[test_name]["Expected Results"].append(expected_text)

			print(f"✅ Step {step_number} added to test: {test_name}")

			step_row = test_row + 1
			while step_row < self.test_table.rowCount() and not self.test_table.item(step_row, 0):
				step_row += 1

			self.test_table.insertRow(step_row)
			self.test_table.setItem(step_row, 0, QTableWidgetItem(""))  # Rând gol pentru identificare
			self.test_table.setItem(step_row, 3, QTableWidgetItem(action_text))
			self.test_table.setItem(step_row, 4, QTableWidgetItem(expected_text))

			self.save_tests()

			QMessageBox.information(self, "Test Step Added",
			                        f"Step {step_number} added for {test_name}: {selected_command}")

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

	def delete_test_step(self):
		"""Șterge un test step specific dintr-un test existent."""
		selected_row = self.test_table.currentRow()
		if selected_row == -1:
			QMessageBox.warning(self, "No Test Selected", "Please select a test to delete a step from.")
			return

		test_name = self.test_table.item(selected_row, 0).text()
		step_index = self.test_table.currentRow() - 1  # 🔹 Indexul pasului selectat

		if step_index < 0 or step_index >= len(self.tests_data[test_name]["Action"]):
			return

		reply = QMessageBox.question(self, "Delete Step",
		                             f"Are you sure you want to delete step {step_index + 1} from '{test_name}'?",
		                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

		if reply == QMessageBox.Yes:
			del self.tests_data[test_name]["Action"][step_index]
			del self.tests_data[test_name]["Expected Results"][step_index]

			print(f"✅ Step {step_index + 1} deleted from test: {test_name}")

			self.load_tests()
			self.save_tests()

	def save_tests(self):
		"""Salvează testele în JSON."""
		with open(self.json_file, "w", encoding="utf-8") as file:
			json.dump(self.tests_data, file, indent=4)

	def load_tests(self):
		"""Încarcă testele din JSON și afișează pașii sub fiecare test, oferind opțiunea de expand/collapse."""
		print("🔹 Loading tests from JSON...")

		self.test_table.setRowCount(0)  # Resetăm tabelul

		for test_name, test_data in self.tests_data.items():
			row_position = self.test_table.rowCount()
			self.test_table.insertRow(row_position)

			# 🔹 Setăm background gri doar pentru rândul cu numele testului
			test_item = QTableWidgetItem(test_name)
			test_item.setBackground(Qt.lightGray)
			self.test_table.setItem(row_position, 0, test_item)
			self.test_table.setItem(row_position, 1, QTableWidgetItem(test_data.get("Description", "")))
			self.test_table.setItem(row_position, 2, QTableWidgetItem(test_data.get("Precondition", "")))

			# 🔹 Buton de expand/collapse
			expand_button = QToolButton()
			expand_button.setStyleSheet("background: none; border: none;")
			expand_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
			expand_button.setCheckable(True)
			expand_button.setChecked(True)
			expand_button.clicked.connect(lambda _, r=row_position: self.toggle_test_steps(r))

			self.test_table.setCellWidget(row_position, 5, expand_button)  # Coloana 5 pentru buton

			# 🔹 Adăugăm test steps sub acest rând
			actions = test_data.get("Action", [])
			expected_results = test_data.get("Expected Results", [])

			for step_index in range(len(actions)):
				step_row = self.test_table.rowCount()
				self.test_table.insertRow(step_row)

				self.test_table.setItem(step_row, 0, QTableWidgetItem(""))  # Lăsăm goală coloana test name
				self.test_table.setItem(step_row, 3, QTableWidgetItem(actions[step_index]))
				self.test_table.setItem(step_row, 4, QTableWidgetItem(expected_results[step_index]))

				# 🔹 Ascundem rândul inițial
				self.test_table.setRowHidden(step_row, False)

		print("✅ Tests loaded successfully.")

	def toggle_test_steps(self, test_row):
		"""Afișează sau ascunde pașii unui test."""
		expanded = self.test_table.cellWidget(test_row, 5).isChecked()
		self.test_table.cellWidget(test_row, 5).setIcon(
			self.style().standardIcon(QStyle.SP_ArrowDown if expanded else QStyle.SP_ArrowRight)
		)

		test_name = self.test_table.item(test_row, 0).text()
		row_count = self.test_table.rowCount()

		for row in range(test_row + 1, row_count):
			item = self.test_table.item(row, 0)
			if item and not item.text().strip():  # 🔹 Identificăm rândurile de steps
				self.test_table.setRowHidden(row, not expanded)
			else:
				break  # 🔹 Ne oprim când ajungem la alt test

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

	def move_test_step(self, direction):
		"""Mută un test step în sus sau în jos în Action și Expected Results."""
		selected_row = self.test_table.currentRow()
		if selected_row == -1:
			QMessageBox.warning(self, "No Test Selected", "Please select a test step to move.")
			return

		test_name = self.test_table.item(selected_row, 0).text()
		step_index = selected_row - 1

		if direction == "up" and step_index > 0:
			self.tests_data[test_name]["Action"][step_index], self.tests_data[test_name]["Action"][step_index - 1] = \
				self.tests_data[test_name]["Action"][step_index - 1], self.tests_data[test_name]["Action"][step_index]
			self.tests_data[test_name]["Expected Results"][step_index], self.tests_data[test_name]["Expected Results"][
				step_index - 1] = \
				self.tests_data[test_name]["Expected Results"][step_index - 1], \
				self.tests_data[test_name]["Expected Results"][step_index]

		elif direction == "down" and step_index < len(self.tests_data[test_name]["Action"]) - 1:
			self.tests_data[test_name]["Action"][step_index], self.tests_data[test_name]["Action"][step_index + 1] = \
				self.tests_data[test_name]["Action"][step_index + 1], self.tests_data[test_name]["Action"][step_index]
			self.tests_data[test_name]["Expected Results"][step_index], self.tests_data[test_name]["Expected Results"][
				step_index + 1] = \
				self.tests_data[test_name]["Expected Results"][step_index + 1], \
				self.tests_data[test_name]["Expected Results"][step_index]

		self.load_tests()
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
		"""Exportă testele într-un fișier XLSX, incluzând Test Data Description."""
		file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)")
		if not file_path:
			return

		test_list = []
		for test_name, test_data in self.tests_data.items():
			test_list.append({
				"Test Name": test_name,
				"Description": test_data.get("Description", ""),
				"Precondition": test_data.get("Precondition", ""),
				"Action": "\n".join(test_data.get("Action", [])),  # 🔹 Transformăm lista într-un string
				"Expected Results": "\n".join(test_data.get("Expected Results", [])),
				"Test Data Description": test_data.get("Test Data Description", "")
			})

		df = pd.DataFrame(test_list)
		df.to_excel(file_path, index=False)
		QMessageBox.information(self, "Export Completed", "Tests exported successfully to XLSX!")

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

	def load_commands(self):
		"""Încarcă comenzile din `generic_commands.json`."""
		if not os.path.exists(self.commands_file):
			print("❌ Commands file not found.")
			self.commands_data = {}
			return

		try:
			with open(self.commands_file, "r", encoding="utf-8") as file:
				self.commands_data = json.load(file)
			print("✅ Commands loaded successfully:", self.commands_data.keys())
		except json.JSONDecodeError:
			print("❌ Error loading commands file.")
			self.commands_data = {}

	def load_parameters(self):
		"""Încarcă parametrii din `parameters.json`."""
		if not os.path.exists(self.parameters_file):
			return

		try:
			with open(self.parameters_file, "r", encoding="utf-8") as file:
				self.parameters_data = json.load(file)
			print("✅ Parameters loaded successfully:", self.parameters_data.keys())
		except json.JSONDecodeError:
			print("❌ Error loading parameters file.")

