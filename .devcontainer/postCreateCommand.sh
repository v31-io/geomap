#!/bin/bash
set -e

# Create python virtual environment and install pacakages
sudo rm -rf base
python3 -m venv base
source base/bin/activate
pip install -r python/requirements.txt 
pip install -r python/requirements-dev.txt 

echo "source base/bin/activate" >> ~/.bashrc