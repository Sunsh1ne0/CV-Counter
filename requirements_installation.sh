# Create a virtual environment named .venv
python -m venv .venv
source .venv/bin/activate

# Update and upgrade system packages
sudo apt update && sudo apt upgrade

# Install CMake
sudo apt install cmake

# Upgrade pip
pip install --upgrade pip

# Install Poetry with the option to break system packages
pip install --break-system-packages poetry

# Install development libraries for libkms++, libfmt, and libdrm
sudo apt install -y libkms++-dev libfmt-dev libdrm-dev
# Install rpi-kms package with the option to break system packages
pip install --break-system-packages rpi-kms

# Install libcamera development libraries
sudo apt install -y libcamera-dev
# Install rpi-libcamera package with the option to break system packages
pip install --break-system-packages rpi-libcamera

# Install libhdf5 development libraries
sudo apt-get install -y libhdf5-dev

# Set the PYTHON_KEYRING_BACKEND environment variable
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring

# Install python-prctl
sudo apt-get install libcap-dev python3-setuptools

# Install dependencies using Poetry
poetry install