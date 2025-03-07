from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QLineEdit, QHeaderView, QFrame, QTabWidget,
    QMessageBox, QInputDialog, QFileDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import json
import os
import pandas as pd


class ParametersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                font-size: 12px;
                padding: 6px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #ccc;
                padding: 6px;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
            }
        """)

        self.json_file = os.path.join(os.path.dirname(__file__), "../data/parameters.json")
        self.load_parameters()

        layout = QVBoxLayout()

        title = QLabel("Manage Parameters")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.remove_category)
        layout.addWidget(self.tab_widget)

        self.add_category_button = QPushButton("+ Add Category")
        self.add_category_button.clicked.connect(self.add_category)
        layout.addWidget(self.add_category_button)

        self.import_button = QPushButton("Import from XLSX")
        self.import_button.clicked.connect(self.import_from_xlsx)
        layout.addWidget(self.import_button)

        self.setLayout(layout)

        self.populate_tabs()  # Populează UI-ul cu datele existente din JSON

    def load_parameters(self):
        """Încarcă parametrii din fișierul JSON, prevenind erorile de citire."""
        self.parameters_data = {}

        if not os.path.exists(self.json_file):
            print(f"⚠️ Warning: {self.json_file} not found. Creating a new one.")
            return

        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                self.parameters_data = json.load(file)
        except json.JSONDecodeError:
            print(f"⚠️ Error: {self.json_file} is corrupted or empty.")
            self.parameters_data = {}

    def save_parameters(self):
        """Salvează parametrii în fișierul JSON."""
        try:
            with open(self.json_file, "w", encoding="utf-8") as file:
                json.dump(self.parameters_data, file, indent=4)
            print(f"✅ Parameters saved successfully to {self.json_file}")  # DEBUGGING
        except Exception as e:
            print(f"❌ Error saving parameters: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while saving parameters:\n{str(e)}")

    def populate_tabs(self):
        """Populează interfața cu datele din JSON la pornirea aplicației."""
        for category, params in self.parameters_data.items():
            self.add_category(category, params)

    def add_category(self, category_name=None, parameters=None):
        """Adaugă o categorie nouă cu tabelul său de parametri și încarcă variantele."""
        if not category_name:
            category_name, ok = QInputDialog.getText(self, "New Category", "Enter category name:")
            if not ok or not category_name.strip():
                QMessageBox.warning(self, "Warning", "Category name cannot be empty!")
                return

        new_tab = QWidget()
        tab_layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        parameter_name_input = QLineEdit()
        parameter_name_input.setPlaceholderText("Enter Parameter Name...")
        add_parameter_button = QPushButton("+ Add Parameter")
        input_layout.addWidget(parameter_name_input)
        input_layout.addWidget(add_parameter_button)
        tab_layout.addLayout(input_layout)

        # Inițializăm tabelul de parametri
        parameter_table = QTableWidget()

        # Verificăm dacă există parametri pentru această categorie
        if parameters:
            # Obținem lista tuturor coloanelor (Default Value + variantele)
            column_headers = ["Parameter Name"]
            first_param = next(iter(parameters.values()), {})
            column_headers.extend(first_param.keys())

            parameter_table.setColumnCount(len(column_headers))
            parameter_table.setHorizontalHeaderLabels(column_headers)

            # Adăugăm parametrii în tabel
            for param_name, values in parameters.items():
                row_position = parameter_table.rowCount()
                parameter_table.insertRow(row_position)
                parameter_table.setItem(row_position, 0, QTableWidgetItem(param_name))

                for col_index, (variant_name, variant_value) in enumerate(values.items(), start=1):
                    parameter_table.setItem(row_position, col_index, QTableWidgetItem(variant_value))
        else:
            parameter_table.setColumnCount(2)
            parameter_table.setHorizontalHeaderLabels(["Parameter Name", "Default Value"])

        parameter_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tab_layout.addWidget(parameter_table)
        parameter_table.cellChanged.connect(
            lambda row, col: self.update_parameter_value(category_name, parameter_table, row, col))

        delete_parameter_button = QPushButton("Delete Selected Parameter")
        tab_layout.addWidget(delete_parameter_button)

        add_variant_button = QPushButton("+ Add Variant")
        tab_layout.addWidget(add_variant_button)

        export_button = QPushButton("Export to XLSX")
        export_button.clicked.connect(lambda: self.export_to_xlsx(category_name, parameter_table))
        tab_layout.addWidget(export_button)

        new_tab.setLayout(tab_layout)
        self.tab_widget.addTab(new_tab, category_name)

        add_parameter_button.clicked.connect(lambda: self.add_parameter(parameter_table, parameter_name_input))
        delete_parameter_button.clicked.connect(lambda: self.delete_selected_parameter(parameter_table))
        add_variant_button.clicked.connect(lambda: self.add_variant(parameter_table))

    def remove_category(self, index):
        """Șterge o categorie selectată."""
        reply = QMessageBox.question(self, "Delete Category", "Are you sure you want to delete this category?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tab_widget.removeTab(index)
            self.save_parameters()

    def add_parameter(self, table, parameter_name_input):
        """Adaugă un nou parametru în tabel."""
        parameter_name = parameter_name_input.text().strip()

        if not parameter_name:
            QMessageBox.warning(self, "Warning", "Parameter name cannot be empty!")
            return

        try:
            row_position = table.rowCount()
            table.insertRow(row_position)
            table.setItem(row_position, 0, QTableWidgetItem(parameter_name))
            table.setItem(row_position, 1, QTableWidgetItem(""))

            parameter_name_input.clear()
            self.save_parameters()  # Salvăm automat

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while adding the parameter:\n{str(e)}")

    def export_to_xlsx(self, category_name, table):
        """Exportă parametrii unei categorii într-un fișier XLSX."""
        try:
            df = pd.DataFrame(columns=[table.horizontalHeaderItem(col).text() for col in range(table.columnCount())])
            for row in range(table.rowCount()):
                df.loc[row] = [table.item(row, col).text() if table.item(row, col) else "" for col in range(table.columnCount())]
            df.to_excel(f"{category_name}.xlsx", index=False)
            QMessageBox.information(self, "Export Successful", f"Category {category_name} exported to {category_name}.xlsx")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred during export:\n{str(e)}")

    def add_variant(self, table):
        """Adaugă o nouă variantă pentru parametrii existenți în tabel."""
        try:
            if table.rowCount() == 0:
                QMessageBox.warning(self, "Warning", "No parameters available to add a variant.")
                return

            # Obține numele variantei de la utilizator
            variant_name, ok = QInputDialog.getText(self, "New Variant", "Enter variant name:")
            if not ok or not variant_name.strip():
                QMessageBox.warning(self, "Warning", "Variant name cannot be empty!")
                return

            # Adaugă noua coloană în tabel
            col_position = table.columnCount()
            table.insertColumn(col_position)
            table.setHorizontalHeaderItem(col_position, QTableWidgetItem(variant_name))

            # Inițializează fiecare celulă din noua coloană cu un placeholder (poate fi schimbat ulterior)
            for row in range(table.rowCount()):
                table.setItem(row, col_position, QTableWidgetItem(""))

            # Salvează modificările
            self.save_parameters()

        except Exception as e:
            print(f"❌ Error adding variant: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while adding the variant:\n{str(e)}")

    def update_parameter_value(self, category_name, table, row, col):
        """Actualizează valoarea unui parametru în dicționarul intern și salvează în JSON."""
        try:
            param_name_item = table.item(row, 0)
            if not param_name_item:
                return  # Nu face nimic dacă numele parametrului nu există

            param_name = param_name_item.text()
            value_item = table.item(row, col)
            value = value_item.text() if value_item else ""

            # Obține numele variantei din headerul tabelului
            variant_name = table.horizontalHeaderItem(col).text()

            # Actualizează structura de date
            if category_name in self.parameters_data and param_name in self.parameters_data[category_name]:
                self.parameters_data[category_name][param_name][variant_name] = value
            else:
                self.parameters_data.setdefault(category_name, {}).setdefault(param_name, {})[variant_name] = value

            # Salvează în JSON
            self.save_parameters()

        except Exception as e:
            print(f"❌ Error updating parameter value: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while updating the parameter value:\n{str(e)}")

    def import_from_xlsx(self):
        """Importă parametrii dintr-un fișier XLSX și creează o categorie cu numele fișierului."""
        from PyQt5.QtWidgets import QFileDialog
        import pandas as pd
        import os

        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx);;All Files (*)")

        if not file_path:
            return  # Dacă utilizatorul nu a selectat un fișier, ieșim din funcție

        try:
            df = pd.read_excel(file_path)

            if df.empty:
                QMessageBox.warning(self, "Warning", "The selected Excel file is empty!")
                return

            # Extragem numele fișierului fără extensie pentru a-l folosi ca nume de categorie
            category_name = os.path.splitext(os.path.basename(file_path))[0]

            # Creăm categoria dacă nu există deja
            if category_name in self.parameters_data:
                QMessageBox.warning(self, "Warning",
                                    f"A category named '{category_name}' already exists! Overwriting data.")

            self.parameters_data[category_name] = {}

            # Prima coloană trebuie să fie "Parameter Name"
            if "Parameter Name" not in df.columns:
                QMessageBox.critical(self, "Error", "The Excel file must have a 'Parameter Name' column!")
                return

            # Adăugăm parametrii și variantele din Excel în dicționarul intern
            for index, row in df.iterrows():
                param_name = str(row["Parameter Name"]).strip()

                if not param_name:
                    continue  # Sărim peste rândurile goale

                self.parameters_data[category_name][param_name] = {}

                for variant in df.columns[1:]:  # Ignorăm prima coloană (numele parametrului)
                    value = str(row[variant]).strip() if pd.notna(row[variant]) else ""
                    self.parameters_data[category_name][param_name][variant] = value

            # 🔹 DEBUGGING: Afișăm datele înainte de salvare
            print(f"📁 Imported category: {category_name}")
            print(json.dumps(self.parameters_data[category_name], indent=4))
            # 🔹 Salvăm categoria în parameters.json
            self.save_parameters()

            # 🔹 Adăugăm categoria și în interfață
            self.add_category(category_name, self.parameters_data[category_name])

            QMessageBox.information(self, "Success",
                                    f"Parameters from '{os.path.basename(file_path)}' have been imported successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"An error occurred during import:\n{str(e)}")


