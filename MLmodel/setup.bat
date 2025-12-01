@echo off
echo -----------------------------------------
echo 🚀 Tube Inspection Setup Started (Windows)
echo -----------------------------------------

:: CHECK PYTHON 3.10
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Python is not installed or not in PATH
    echo 🔧 Install Python 3.10 from https://www.python.org/
    pause
    exit /b
)

:: CREATE VENV
echo 🔧 Creating virtual environment...
python -m venv tube-env

:: ACTIVATE VENV
echo 🔌 Activating virtual environment...
call tube-env\Scripts\activate.bat

:: UPGRADE PIP
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

:: INSTALL DEPENDENCIES
echo 📦 Installing dependencies...
pip install ultralytics opencv-python pandas numpy scikit-learn fastapi uvicorn cassandra-driver requests

:: INSTALL WINDOWS TENSORFLOW (Normal full TF for development)
echo 🤖 Installing TensorFlow for Windows...
pip install tensorflow==2.15

:: CREATE DATASET FOLDERS
echo 📁 Creating dataset folders...
mkdir dataset
mkdir dataset\images\train dataset\images\val
mkdir dataset\labels\train dataset\labels\val

echo 🎉 Setup Complete!
echo -----------------------------------------
echo 👉 To activate environment later, run:
echo call tube-env\Scripts\activate.bat
echo -----------------------------------------
pause
