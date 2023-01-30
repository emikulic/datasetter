#!/bin/bash
# Autoformat the code.
#
# Pre-reqs:
# pip install black
# sudo apt install clang-format
set -x
black add.py util.py prep.py datasetter.py blip.py compact.py
clang-format-10 -i index.js
