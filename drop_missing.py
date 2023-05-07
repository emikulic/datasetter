#!/usr/bin/env python3
"""
Remove dataset entries where the file is missing.
Leaves gaps in "n" numbers.
"""
from util import Dataset
import argparse
import os


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    args = p.parse_args()

    for i in args.inputs:
        print(f"processing {i}")
        d = Dataset(i)
        keys = list(d._data.keys())
        for k in keys:
            md = d._data[k]
            fn = f'{d._dir}/{md["fn"]}'
            if not os.path.exists(fn):
                print(f" missing {fn}")
                del d._data[k]
        d.compact()


if __name__ == "__main__":
    main()
