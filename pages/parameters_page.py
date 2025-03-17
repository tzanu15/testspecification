from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QLineEdit, QHeaderView, QFrame, QTabWidget,
    QMessageBox, QInputDialog, QFileDialog, QAction, QMenu
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import json
import os
import pandas as pd
import sys

class ParametersPage(QWidget):
    def __init__(self):
        super().__init__()

        self.category_tables = {}

        self.json_file = self.get_resource_path("../data/parameters.json")
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

        self.copied_parameter = None  # ✅ Buffer pentru Copy/Paste

        self.setLayout(layout)

        self.populate_tabs()  # Populează UI-ul cu datele existente din JSON

    def show_context_menu(self, position, parameter_table, category_name):
        """Afișează meniul contextual pentru parametri."""
        index = parameter_table.indexAt(position)
        if not index.isValid():
            return

        row = index.row()
        param_name = parameter_table.item(row, 0).text()

        menu = QMenu(self)

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.copy_parameter(param_name, category_name))
        menu.addAction(copy_action)

        paste_action = QAction("Paste", self)
        paste_action.setEnabled(self.copied_parameter is not None)
        paste_action.triggered.connect(lambda: self.paste_parameter(row, parameter_table, category_name))
        menu.addAction(paste_action)

        duplicate_action = QAction("Duplicate", self)
        duplicate_action.triggered.connect(
            lambda: self.duplicate_parameter(param_name, row, parameter_table, category_name))
        menu.addAction(duplicate_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_parameter(param_name, row, parameter_table, category_name))
        menu.addAction(delete_action)

        edit_name_action = QAction("Edit Name", self)
        edit_name_action.triggered.connect(lambda: self.edit_parameter_name(row, parameter_table, category_name))
        menu.addAction(edit_name_action)

        menu.exec_(parameter_table.viewport().mapToGlobal(position))

    def copy_parameter(self, param_name, category_name):
	    """Copiem un parametru pentru a fi lipit într-o altă categorie."""
	    if category_name in self.parameters_data and param_name in self.parameters_data[category_name]:
		    self.copied_parameter = (param_name, self.parameters_data[category_name].copy())
		    self.copied_category = category_name
		    print(f"📋 Copied parameter: {param_name} from {category_name}")
	    else:
		    print(f"❌ ERROR: Cannot copy {param_name} from {category_name} - Parameter not found!")

    def paste_parameter(self, target_row, parameter_table, category_name):
        """Lipește parametrul copiat într-o altă categorie."""
        if not self.copied_parameter:
            print("❌ ERROR: No parameter copied!")
            return

        param_name, param_data = self.copied_parameter
        new_param_name = param_name

        # ✅ Evităm duplicarea numelui
        while new_param_name in self.parameters_data[category_name]:
            new_param_name += "_Copy"

        print(f"📋 Pasting parameter: {new_param_name} into {category_name}")

        self.parameters_data[category_name][new_param_name] = param_data
        self.add_parameter_to_table(target_row + 1, new_param_name, param_data, parameter_table)
        self.save_parameters()
        print(f"✅ Pasted parameter: {new_param_name} in {category_name}")

    def duplicate_parameter(self, param_name, row, parameter_table, category_name):
        """Duplicates a parameter and inserts it immediately below the original in UI and JSON."""
        try:
            if category_name not in self.parameters_data:
                print(f"❌ ERROR: Category '{category_name}' not found!")
                return

            if param_name not in self.parameters_data[category_name]:
                print(f"❌ ERROR: Parameter '{param_name}' not found in category '{category_name}'!")
                return

            # ✅ Generate a unique parameter name
            count = 1
            new_param_name = f"{param_name}_{count}"
            while new_param_name in self.parameters_data[category_name]:
                count += 1
                new_param_name = f"{param_name}_{count}"

            print(f"📑 Duplicating parameter: {new_param_name} from {param_name} in {category_name}")

            # ✅ Copy parameter data and avoid reference issues
            new_param_data = self.parameters_data[category_name][param_name].copy()

            # ✅ Insert the new parameter in the dictionary **immediately after the original**
            keys_list = list(self.parameters_data[category_name].keys())
            param_index = keys_list.index(param_name)
            updated_dict = {}

            for key in keys_list:
                updated_dict[key] = self.parameters_data[category_name][key]
                if key == param_name:  # ✅ Insert duplicate immediately after original
                    updated_dict[new_param_name] = new_param_data

            self.parameters_data[category_name] = updated_dict

            # ✅ Manually insert a new row in UI **without overwriting**
            self.insert_parameter_in_ui(row+1, new_param_name, new_param_data, parameter_table)

            # ✅ Save changes to JSON
            #self.save_parameters(update_ui=False)  # 🔹 Prevents unnecessary UI refresh

            print(f"✅ Duplicated parameter: {new_param_name} in category '{category_name}'")

        except Exception as e:
            print(f"❌ CRITICAL ERROR in `duplicate_parameter`: {e}")
            import traceback
            traceback.print_exc()

    def delete_parameter(self, param_name, row, parameter_table, category_name):
        """Ștergem parametrul selectat."""
        reply = QMessageBox.question(self, "Delete Parameter",
                                     f"Are you sure you want to delete '{param_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.parameters_data[category_name][param_name]
            parameter_table.removeRow(row)
            self.save_parameters()
            print(f"🗑 Deleted parameter: {param_name} from {category_name}")

    def edit_parameter_name(self, row, parameter_table, category_name):
        """Permite editarea numelui unui parametru doar prin click dreapta."""
        item = parameter_table.item(row, 0)
        if item:
            old_name = item.text()
            new_name, ok = QInputDialog.getText(self, "Edit Parameter Name", "Enter new parameter name:", text=old_name)

            if not ok or not new_name.strip():
                print("❌ ERROR: Empty or invalid name!")
                return

            if new_name in self.parameters_data[category_name]:
                QMessageBox.warning(self, "Error", "A parameter with this name already exists!")
                return

            print(f"✏️ Renaming parameter '{old_name}' to '{new_name}' in {category_name}")

            # ✅ Actualizăm JSON
            self.parameters_data[category_name][new_name] = self.parameters_data[category_name].pop(old_name)

            # ✅ Actualizăm UI
            item.setText(new_name)
            self.save_parameters()
            print(f"✅ Renamed parameter '{old_name}' to '{new_name}' in {category_name}")

    def handle_item_edit(self, item):
        """Previne editarea directă a numelui parametrului."""
        if item.column() == 0:  # ✅ Coloana `Parameter Name`
            QMessageBox.warning(self, "Edit Not Allowed", "Use right-click menu to edit parameter names.")
            self.table.blockSignals(True)
            item.setText(self.previous_param_name)  # ✅ Revenim la numele anterior
            self.table.blockSignals(False)

    def load_parameters(self):
        """Loads parameters from JSON, ensuring correct format and preventing errors."""
        self.parameters_data = {}

        if not os.path.exists(self.json_file):
            print(f"⚠️ Warning: {self.json_file} not found. Creating a new one.")
            return

        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            # ✅ Cleaning up any incorrect structure while loading
            for category, params in data.items():
                self.parameters_data[category] = {}
                for param_name, param_data in params.items():
                    if isinstance(param_data, dict):
                        self.parameters_data[category][param_name] = {
                            k: v for k, v in param_data.items() if k != "Parameter Name"
                        }
                    else:
                        print(f"⚠️ Skipping invalid parameter structure for '{param_name}' in '{category}'.")

            print("✅ Parameters loaded successfully.")

        except json.JSONDecodeError:
            print(f"⚠️ Error: {self.json_file} is corrupted or empty.")
            self.parameters_data = {}

    def save_parameters(self, update_ui=True):
        """Saves parameters correctly to JSON and updates UI if needed."""
        if not self.json_file:
            print("❌ ERROR: json_file path is not set!")
            return

        try:
            print("🔹 Saving parameters to JSON...")
            cleaned_data = {}
            for category, params in self.parameters_data.items():
                cleaned_data[category] = {
                    param_name: {k: v for k, v in param_data.items() if k != "Parameter Name"}
                    for param_name, param_data in params.items()
                }

            with open(self.json_file, "w", encoding="utf-8") as file:
                json.dump(cleaned_data, file, indent=4)

            print(f"✅ Parameters saved successfully in: {self.json_file}")

            # 🔹 Only reload UI if explicitly requested
            if update_ui:
                self.load_parameters()

        except Exception as e:
            print(f"❌ ERROR saving parameters: {e}")

    def populate_tabs(self):
        """Populează interfața cu datele din JSON la pornirea aplicației."""
        for category, params in self.parameters_data.items():
            self.add_category(category, params)

    def add_category(self, category_name=None, parameters=None):
        """Adds a new category with its parameter table and saves it to JSON."""
        if not category_name:
            category_name, ok = QInputDialog.getText(self, "New Category", "Enter category name:")
            if not ok or not category_name.strip():
                QMessageBox.warning(self, "Warning", "Category name cannot be empty!")
                return

        # ✅ Ensure `self.parameters_data` contains the new category
        if category_name not in self.parameters_data:
            self.parameters_data[category_name] = {}

        new_tab = QWidget()
        tab_layout = QVBoxLayout()



        # ✅ Layout for input field and add button
        input_layout = QHBoxLayout()

        parameter_name_input = QLineEdit()
        parameter_name_input.setPlaceholderText("Enter Parameter Name...")
        add_parameter_button = QPushButton("➕ Add Parameter")

        input_layout.addWidget(parameter_name_input)
        input_layout.addWidget(add_parameter_button)
        tab_layout.addLayout(input_layout)
        # ✅ Search Bar
        search_layout = QHBoxLayout()
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 Search parameters...")
        search_bar.textChanged.connect(
            lambda text: self.filter_parameters(text, parameter_table))  # Connect search function
        search_layout.addWidget(search_bar)
        tab_layout.addLayout(search_layout)

        # ✅ Create the parameter table
        parameter_table = QTableWidget()

        if parameters:
            column_headers = ["Parameter Name"]
            first_param = next(iter(parameters.values()), {})
            column_headers.extend(first_param.keys())

            parameter_table.setColumnCount(len(column_headers))
            parameter_table.setHorizontalHeaderLabels(column_headers)

            for param_name, values in parameters.items():
                row_position = parameter_table.rowCount()
                parameter_table.insertRow(row_position)
                param_item = QTableWidgetItem(param_name)
                param_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                parameter_table.setItem(row_position, 0, param_item )

                for col_index, (variant_name, variant_value) in enumerate(values.items(), start=1):
                    parameter_table.setItem(row_position, col_index, QTableWidgetItem(str(variant_value)))

        else:
            parameter_table.setColumnCount(2)
            parameter_table.setHorizontalHeaderLabels(["Parameter Name", "Default Value"])

        parameter_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tab_layout.addWidget(parameter_table)

        # ✅ Buttons for adding and deleting variants
        button_layout = QHBoxLayout()

        add_variant_button = QPushButton("➕ Add Variant")
        delete_variant_button = QPushButton("🗑 Delete Variant")
        export_button = QPushButton("📤 Export to XLSX")

        button_layout.addWidget(add_variant_button)
        button_layout.addWidget(delete_variant_button)
        button_layout.addWidget(export_button)

        tab_layout.addLayout(button_layout)

        # ✅ Connect buttons to functions
        add_parameter_button.clicked.connect(
            lambda: self.add_parameter(table=parameter_table, parameter_name_input=parameter_name_input))
        add_variant_button.clicked.connect(lambda: self.add_variant(parameter_table))
        delete_variant_button.clicked.connect(lambda: self.delete_variant(parameter_table))
        export_button.clicked.connect(lambda: self.export_to_xlsx(category_name, parameter_table))

        # ✅ Add context menu for the table
        parameter_table.setContextMenuPolicy(Qt.CustomContextMenu)
        parameter_table.customContextMenuRequested.connect(
            lambda position: self.show_context_menu(position, parameter_table, category_name))
        parameter_table.cellChanged.connect(
            lambda row, col: self.update_parameter_value(category_name, parameter_table, row, col))

        # ✅ Store the table reference for this category
        self.category_tables[category_name] = parameter_table

        new_tab.setLayout(tab_layout)
        self.tab_widget.addTab(new_tab, category_name)

        # ✅ Save the new category to JSON
        self.save_parameters()
        print(f"✅ Added new category '{category_name}' and saved to JSON.")

    def remove_category(self, index):
        """Șterge o categorie din interfață și din JSON."""
        category_name = self.tab_widget.tabText(index)

        reply = QMessageBox.question(self, "Delete Category",
                                     f"Are you sure you want to delete category '{category_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.tab_widget.removeTab(index)  # Eliminăm categoria vizual
            if category_name in self.parameters_data:
                del self.parameters_data[category_name]  # Ștergem și din JSON

            self.save_parameters()  # Salvăm JSON-ul actualizat

    def add_parameter(self, table, parameter_name_input):
        """Adds a new parameter to the table and correctly updates JSON."""
        parameter_name = parameter_name_input.text().strip()

        if not parameter_name:
            QMessageBox.warning(self, "Warning", "Parameter name cannot be empty!")
            return

        category_name = self.tab_widget.tabText(self.tab_widget.currentIndex())

        if category_name not in self.parameters_data:
            print(f"❌ ERROR: Category '{category_name}' not found in self.parameters_data!")
            return

        if parameter_name in self.parameters_data[category_name]:
            QMessageBox.warning(self, "Warning", "This parameter already exists in this category!")
            return

        try:
            # ✅ Store the parameter correctly without "Parameter Name" key
            self.parameters_data[category_name][parameter_name] = {"Default Value": ""}

            # ✅ Add parameter to the UI
            row_position = table.rowCount()
            table.insertRow(row_position)
            table.setItem(row_position, 0, QTableWidgetItem(parameter_name))
            table.setItem(row_position, 1, QTableWidgetItem(""))  # Default Value

            parameter_name_input.clear()
            self.save_parameters()
            print(f"✅ Added parameter '{parameter_name}' to category '{category_name}'.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while adding the parameter:\n{str(e)}")

    def insert_parameter_in_ui(self, row, param_name, param_data, parameter_table):
        """Inserts a new parameter at the correct row without affecting other rows."""
        try:
            print(f"✅ Inserting parameter '{param_name}' at row {row}.")

            # ✅ Step 1: Insert a new empty row **without affecting existing data**
            parameter_table.insertRow(row)

            # ✅ Step 2: Set the parameter name **ONLY in the new row**
            param_item = QTableWidgetItem(param_name)
            param_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Read-Only
            parameter_table.setItem(row, 0, param_item)

            # ✅ Step 3: Populate additional columns **ONLY for the new row**, using correct column indexing
            for col_index in range(1, parameter_table.columnCount()):  # Start at column 1 (skip "Parameter Name")
                variant_name = parameter_table.horizontalHeaderItem(col_index).text()

                # ✅ Get the correct value for this variant
                variant_value = param_data.get(variant_name, "")  # Use empty string if variant does not exist

                # ✅ Insert into the correct column
                table_item = QTableWidgetItem(str(variant_value))
                parameter_table.setItem(row, col_index, table_item)

            print(f"✅ Successfully inserted '{param_name}' at row {row}.")

        except Exception as e:
            print(f"❌ ERROR in `insert_parameter_in_ui`: {e}")
            import traceback
            traceback.print_exc()

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
        """Adds a new variant for all existing parameters in the table and updates JSON."""
        try:
            if table.rowCount() == 0:
                QMessageBox.warning(self, "Warning", "No parameters available to add a variant.")
                return

            category_name = self.tab_widget.tabText(self.tab_widget.currentIndex())

            if category_name not in self.parameters_data:
                print(f"❌ ERROR: Category '{category_name}' not found in self.parameters_data!")
                return

            variant_name, ok = QInputDialog.getText(self, "New Variant", "Enter variant name:")
            if not ok or not variant_name.strip():
                QMessageBox.warning(self, "Warning", "Variant name cannot be empty!")
                return

            col_position = table.columnCount()
            table.insertColumn(col_position)
            table.setHorizontalHeaderItem(col_position, QTableWidgetItem(variant_name))

            for row in range(table.rowCount()):
                param_name = table.item(row, 0).text()

                # ✅ Ensure parameter exists in JSON
                if param_name in self.parameters_data[category_name]:
                    self.parameters_data[category_name][param_name][variant_name] = ""

                # ✅ Update UI with a placeholder value
                table.setItem(row, col_position, QTableWidgetItem(""))

            self.save_parameters()
            print(f"✅ Added variant '{variant_name}' to category '{category_name}' and saved to JSON.")

        except Exception as e:
            print(f"❌ Error adding variant: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred while adding the variant:\n{str(e)}")

    def delete_variant(self, table):
        """Deletes the selected variant (column) from the table and updates JSON, then reloads UI."""
        if table.columnCount() <= 2:  # ✅ Keep at least "Parameter Name" and "Default Value"
            QMessageBox.warning(self, "Warning", "You cannot delete the default columns!")
            return

        selected_column = table.currentColumn()
        if selected_column < 2:  # ✅ Prevent deleting "Parameter Name" or "Default Value"
            QMessageBox.warning(self, "Warning", "Cannot delete default columns!")
            return

        # ✅ Get the name of the variant to delete
        variant_to_delete = table.horizontalHeaderItem(selected_column).text()
        category_name = self.tab_widget.tabText(self.tab_widget.currentIndex())

        if category_name not in self.parameters_data:
            print(f"❌ ERROR: Category '{category_name}' not found in self.parameters_data!")
            return

        # ✅ Remove the variant from all parameters in JSON
        for param_name in self.parameters_data[category_name]:
            if variant_to_delete in self.parameters_data[category_name][param_name]:
                del self.parameters_data[category_name][param_name][variant_to_delete]

        # ✅ Remove the column from UI
        table.removeColumn(selected_column)

        # ✅ Save the changes and reload the UI
        self.save_parameters()
        self.reload_ui()

        print(f"✅ Deleted variant '{variant_to_delete}' from category '{category_name}' and updated JSON.")

    def update_parameter_value(self, category_name, table, row, col):
        """Updates a parameter value in the internal dictionary and saves it to JSON, including variants."""
        try:
            param_name_item = table.item(row, 0)
            if not param_name_item:
                return  # ✅ Do nothing if the parameter name does not exist

            param_name = param_name_item.text().strip()
            value_item = table.item(row, col)
            value = value_item.text().strip() if value_item else ""

            # ✅ Get the variant name from the table header
            variant_name = table.horizontalHeaderItem(col).text().strip()

            # ✅ Check if category and parameter exist
            if category_name not in self.parameters_data:
                print(f"❌ ERROR: Category '{category_name}' not found in parameters_data!")
                return

            if param_name not in self.parameters_data[category_name]:
                print(f"❌ ERROR: Parameter '{param_name}' not found in category '{category_name}'!")
                return

            # ✅ Update default value or variant
            if variant_name == "Default Value":
                self.parameters_data[category_name][param_name]["Default Value"] = value
            else:
                self.parameters_data[category_name][param_name][variant_name] = value

            # ✅ Save changes to JSON
            self.save_parameters()
            print(f"✅ Updated '{variant_name}' of '{param_name}' in category '{category_name}' with value '{value}'.")

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

        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"An error occurred during import:\n{str(e)}")

    def reload_ui(self):
        """Reloads all parameter tables from JSON to reflect recent changes."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                self.parameters_data = json.load(file)

            # ✅ Clear existing tabs
            while self.tab_widget.count():
                self.tab_widget.removeTab(0)

            # ✅ Re-add categories with updated data
            for category, params in self.parameters_data.items():
                self.add_category(category, params)

            print("🔄 UI reloaded from JSON successfully.")

        except Exception as e:
            print(f"❌ ERROR reloading UI: {e}")

    def filter_parameters(self, text, table):
        """Filters parameters based on search input."""
        text = text.strip().lower()  # Convert search text to lowercase

        for row in range(table.rowCount()):
            param_name_item = table.item(row, 0)  # Get the parameter name
            if param_name_item:
                param_name = param_name_item.text().strip().lower()
                table.setRowHidden(row, text not in param_name)  # ✅ Hide rows that don't match

    def get_resource_path(self,relative_path):
        """Get the correct path whether running as a script or an executable."""
        if getattr(sys, 'frozen', False):  # Running as compiled .exe
            base_path = os.path.dirname(sys.executable) # Use folder where main.exe is
        else:
            base_path = os.path.abspath(os.path.dirname(__file__))  # Development mode

        return os.path.join(base_path, relative_path)





