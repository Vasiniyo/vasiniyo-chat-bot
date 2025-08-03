#!/bin/bash

python ./src/mods/connect_mods.py
black ./src/mods/__init__.py && isort ./src/mods/__init__.py
python ./src/main.py