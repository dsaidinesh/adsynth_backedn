#!/bin/bash

# Install Python if not available
if ! command -v python3 &> /dev/null; then
    apt-get update
    apt-get install -y python3
fi

# Install pip if not available
if ! command -v pip &> /dev/null; then
    apt-get install -y python3-pip
fi

# Install dependencies
pip install --no-cache-dir -r requirements.txt