# 🛠 Test Specification Tool

Test Specification Tool is a **desktop application** built with **Python and PyQt5**, designed to help users efficiently create, manage, and structure software test specifications.  
The tool allows users to define test cases, manage test parameters, and generate structured test documentation.

---

## 📂 Project Structure

The project is organized into different modules for better maintainability and scalability:

test-specification-tool/ 
│── data/# JSON files storing tests, parameters, and generic commands │ 
    ├── tests.json │ 
    ├── parameters.json │ 
    ├── generic_commands.json │ 
│── utils/ # Styling and auxiliary files │ 
    ├── style.qss │ 
│── pages/ # Individual pages of the application │ 
    ├── tests_page.py │ 
    ├── parameters_page.py │ 
    ├── generic_command_page.py │ 
│── ui/ # Main UI window │ 
    ├── main_window.py │ 
│── main.py # Application entry point 
│── build.bat # Build script for generating an executable 
│── requirements.txt # List of dependencies 
│── README.md # Project documentation
## ⚙️ **How to Build the Executable**

The project includes a **build script** (`build.bat`) that automates the entire process of creating a **standalone executable** for Windows.

### 🔹 **Steps to Build**
1. Clone the repository:
   ```sh
   git clone https://github.com/username/test-specification-tool.git
   cd test-specification-tool
2. Run the build script:
   build.bat
   This script will:
     1.Set up a virtual environment
     2.Install dependencies
     3.Use PyInstaller to generate an executable
     4.Copy required JSON files and stylesheets
     5.Create a ZIP package for distribution
### 🚀 Technologies Used
This project is developed using the following technologies:
--> Python (Core development)
--> PyQt5 (GUI framework)
--> JSON (Data storage)
--> PyInstaller (Executable packaging)
--> PowerShell / Batch Scripting (Automated build process)