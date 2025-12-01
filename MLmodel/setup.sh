#!/bin/bash

echo "🚀 Tube Inspection Setup Started..."

# ---- CHECK PYTHON ----
if command -v python3.10 &> /dev/null
then
    PY=python3.10
else
    echo "❌ Python 3.10 not found. Install using:"
    echo "   brew install python@3.10"
    exit 1
fi

# ---- CREATE VENV ----
echo "🔧 Creating Virtual Environment..."
$PY -m venv tube-env
source tube-env/bin/activate

# ---- UPGRADE PIP ----
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# ---- INSTALL DEPENDENCIES ----
echo "📦 Installing dependencies..."
pip install ultralytics opencv-python pandas numpy scikit-learn fastapi uvicorn cassandra-driver requests

# ---- MAC TF SETUP ----
echo "🍎 Installing TensorFlow (Mac)..."
pip install "tensorflow-macos==2.15"

# ---- CREATE TRAIN DIR ----
echo "📁 Creating dataset folders..."
mkdir -p dataset/images/train dataset/images/val dataset/labels/train dataset/labels/val

# ---- FINISH ----
echo "🎉 Setup Complete!"
echo "👉 To activate environment next time, run:"
echo "source tube-env/bin/activate"
