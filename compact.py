#!/usr/bin/env python3
"""
Compact one or more dataset JSON files: rewrites the file and removes un-needed lines.
"""
from util import Dataset
import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    args = p.parse_args()

    for i in args.inputs:
        print(f"compacting {i}")
        Dataset(i).compact()


if __name__ == "__main__":
    main()
