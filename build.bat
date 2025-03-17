@echo off
setlocal

:: Definim numele aplicației
set APP_NAME=TestSpecification

echo 🔹 Setting up Virtual Environment...
python -m venv venv
call venv\Scripts\activate

echo 🔹 Installing Dependencies...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo 🔹 Cleaning old builds...
rmdir /s /q build
rmdir /s /q dist
del %APP_NAME%.spec

echo 🔹 Building Executable with PyInstaller...
pyinstaller --onefile --windowed ^
    --name %APP_NAME% ^
    --add-data "utils/style.qss;utils" ^
    --add-data "data/tests.json;data" ^
    --add-data "data/parameters.json;data" ^
    --add-data "data/generic_commands.json;data" ^
    main.py

echo 🔹 Copying JSON Files...
mkdir dist\%APP_NAME%\data
copy data\tests.json dist\%APP_NAME%\data\
copy data\parameters.json dist\%APP_NAME%\data\
copy data\generic_commands.json dist\%APP_NAME%\data\

echo 🔹 Copying Stylesheets...
mkdir dist\%APP_NAME%\utils
copy utils\style.qss dist\%APP_NAME%\utils\

echo 🔹 Creating ZIP Package...
powershell Compress-Archive -Path dist\%APP_NAME%\* -DestinationPath dist\%APP_NAME%_v1.0.zip -Force

echo ✅ Build Completed! ZIP ready for user distribution.
pause
