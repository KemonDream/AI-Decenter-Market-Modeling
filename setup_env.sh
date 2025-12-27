#!/usr/bin/env bash
set -euo pipefail

# Create and activate a virtual environment, then install dependencies.
# Note: On macOS you may need to run `xcode-select --install` first.

PY=python3
if ! command -v "$PY" >/dev/null 2>&1; then
  echo "python3 not found — please install Python 3 and re-run."
  exit 1
fi

echo "Creating virtualenv .venv..."
$PY -m venv .venv
echo "Activating virtualenv..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip and wheel..."
python -m pip install --upgrade pip setuptools wheel

ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
  echo "Detected Apple Silicon (arm64)."
  echo "Installing numpy and pandas; for TensorFlow on macOS use tensorflow-macos + tensorflow-metal." 
  pip install numpy pandas
  echo "To install TensorFlow for Apple Silicon, run:"
  echo "  pip install tensorflow-macos tensorflow-metal"
else
  echo "Installing from requirements.txt..."
  pip install -r requirements.txt
fi

echo "Setup complete. Activate with: source .venv/bin/activate"
