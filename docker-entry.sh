#!/bin/bash

cd /usr/src/app
pip install --no-cache-dir -q -r requirements.txt

# Run using module entry point (new ucapi-framework pattern)
python -m uc_intg_skyq