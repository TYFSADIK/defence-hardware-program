#!/bin/sh
# One-time toolchain for the whole program (macOS). Linux: use apt equivalents.
set -e
brew install go eigen cmake opa cosign syft mosquitto
python3 -m venv ~/.venvs/defence && . ~/.venvs/defence/bin/activate
pip install numpy scipy pyyaml cryptography paho-mqtt pymavlink rosbags
pipx install platformio || pip install platformio
echo "activate with: . ~/.venvs/defence/bin/activate"
