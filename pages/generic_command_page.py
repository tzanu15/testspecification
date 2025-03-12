import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QLineEdit, QHeaderView, QFrame, QTextEdit, QListWidget,
    QDialog, QInputDialog,QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class CommandDialog(QDialog):
    """Dialog pentru introducerea Action, Expected Result și alegerea categoriilor de parametri."""
    def __init__(self, parameters_data):
        super().__init__()

        self.setWindowTitle("Configure Command")
        self.setGeometry(300, 300, 400, 400)

        self.last_focused = None  # Variabilă pentru a reține ultimul câmp activ

        self.setStyleSheet("""
            QLabel { font-size: 14px; }
            QTextEdit, QListWidget {
                background-color: white;
                border: 1px solid #ccc;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                font-size: 12px;
                padding: 6px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)

        layout = QVBoxLayout()

        # 🔹 Action Field
        self.action_label = QLabel("Action:")
        layout.addWidget(self.action_label)
        self.action_text = QTextEdit()
        self.action_text.installEventFilter(self)  # Adăugăm event filter pentru focus
        layout.addWidget(self.action_text)

        # 🔹 Expected Result Field
        self.expected_label = QLabel("Expected:")
        layout.addWidget(self.expected_label)
        self.expected_text = QTextEdit()
        self.expected_text.installEventFilter(self)  # Adăugăm event filter pentru focus
        layout.addWidget(self.expected_text)

        # 🔹 Listă cu categoriile de parametri
        self.parameters_label = QLabel("Parameters Categories:")
        layout.addWidget(self.parameters_label)
        self.param_list = QListWidget()
        self.param_list.addItems(parameters_data.keys())
        self.param_list.itemDoubleClicked.connect(self.insert_param)
        layout.addWidget(self.param_list)

        # 🔹 Buton pentru salvare
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def eventFilter(self, obj, event):
        """Detectează focusul pentru Action și Expected Result."""
        if event.type() == event.FocusIn:
            self.last_focused = obj
        return super().eventFilter(obj, event)

    def insert_param(self, item):
        """Inserează categoria selectată în ultimul câmp activ."""
        param_text = f"{{{item.text()}}}"

        if self.last_focused:
            self.last_focused.insertPlainText(param_text)
        else:
            QMessageBox.warning(self, "No Field Selected", "Click inside Action or Expected Result before selecting a parameter.")

class GenericCommandPage(QWidget):
    def __init__(self):
        super().__init__()
        self.parameters_file = None
        self.json_file = os.path.join(os.path.dirname(__file__), "../data/generic_commands.json")
        self.parameters_file = os.path.join(os.path.dirname(__file__), "../data/parameters.json")
        self.commands_data = {}
        self.parameters_data = {}

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
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                padding: 6px;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout()

        # 🔹 Titlu și separator
        title = QLabel("Generic Commands")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 🔹 Căsuță de căutare
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Commands...")
        self.search_input.textChanged.connect(self.filter_commands)
        layout.addWidget(self.search_input)

        # 🔹 Tabel pentru comenzi
        self.command_table = QTableWidget()
        self.command_table.setColumnCount(3)
        self.command_table.setHorizontalHeaderLabels(["Command Name", "Action", "Expected Result"])
        self.command_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.command_table)

        # 🔹 Butoane pentru acțiuni
        action_buttons_layout = QHBoxLayout()

        self.add_command_button = QPushButton("Add New Command")
        self.add_command_button.clicked.connect(self.add_command)
        action_buttons_layout.addWidget(self.add_command_button)

        self.delete_command_button = QPushButton("Delete Selected Command")
        self.delete_command_button.clicked.connect(self.delete_selected_command)
        action_buttons_layout.addWidget(self.delete_command_button)

        layout.addLayout(action_buttons_layout)

        self.setLayout(layout)

        self.load_parameters()
        self.load_commands()

    def load_parameters(self):
        """Încarcă categoriile de parametri din `parameters.json`."""
        if not os.path.exists(self.parameters_file):
            return

        try:
            with open(self.parameters_file, "r", encoding="utf-8") as file:
                self.parameters_data = json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Error loading parameters file.")

    def add_command(self):
        """Adaugă o nouă comandă și reîncărcăm categoriile de parametri pentru a include cele mai recente date."""

        # 🔹 Reîncărcăm datele parametrilor înainte de a deschide dialogul
        self.load_parameters()
        print("🔹 Parameters reloaded before creating command:", self.parameters_data.keys())
        """Adaugă o nouă comandă cu dialog personalizat."""
        command_name, ok = QInputDialog.getText(self, "New Command", "Enter command name:")
        if not ok or not command_name.strip():
            return

        # 🔹 Deschidem dialogul personalizat pentru acțiune și expected result
        dialog = CommandDialog(self.parameters_data)
        if dialog.exec_():
            action = dialog.action_text.toPlainText()
            expected_result = dialog.expected_text.toPlainText()

            # 🔹 Adăugăm în tabel și JSON
            row_position = self.command_table.rowCount()
            self.command_table.insertRow(row_position)

            self.command_table.setItem(row_position, 0, QTableWidgetItem(command_name))
            self.command_table.setItem(row_position, 1, QTableWidgetItem(action))
            self.command_table.setItem(row_position, 2, QTableWidgetItem(expected_result))

            self.commands_data[command_name] = {
                "Action": action,
                "Expected Result": expected_result
            }

            self.save_commands()

    def save_commands(self):
        """Salvează comenzile în JSON."""
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(self.commands_data, file, indent=4)

    def load_commands(self):
        """Încarcă comenzile din JSON."""
        if not os.path.exists(self.json_file):
            return

        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                self.commands_data = json.load(file)

            for command_name, details in self.commands_data.items():
                row_position = self.command_table.rowCount()
                self.command_table.insertRow(row_position)

                self.command_table.setItem(row_position, 0, QTableWidgetItem(command_name))
                self.command_table.setItem(row_position, 1, QTableWidgetItem(details.get("Action", "")))
                self.command_table.setItem(row_position, 2, QTableWidgetItem(details.get("Expected Result", "")))
        except json.JSONDecodeError:
            print("Error loading JSON file.")

    def filter_commands(self):
        """Filtrează comenzile în funcție de textul introdus în căutare."""
        filter_text = self.search_input.text().strip().lower()
        for row in range(self.command_table.rowCount()):
            command_name = self.command_table.item(row, 0).text().strip().lower()
            self.command_table.setRowHidden(row, filter_text not in command_name)

    def delete_selected_command(self):
        """Șterge comanda selectată din tabel și JSON."""
        selected_row = self.command_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "No Command Selected", "Please select a command to delete.")
            return

        command_name = self.command_table.item(selected_row, 0).text()

        reply = QMessageBox.question(self, "Delete Command",
                                     f"Are you sure you want to delete the command '{command_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.command_table.removeRow(selected_row)
            if command_name in self.commands_data:
                del self.commands_data[command_name]
                self.save_commands()

