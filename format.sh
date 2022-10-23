#!/bin/bash
# Autoformat the code.
#
# Pre-reqs:
# pip install black
set -x
black add.py util.py prep.py datasetter.py
