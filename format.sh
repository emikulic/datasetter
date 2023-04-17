#!/bin/bash
# Autoformat the code.
#
# Pre-reqs:
# pip install black
# sudo apt install clang-format
set -x
black *.py
clang-format-10 -i index.js
