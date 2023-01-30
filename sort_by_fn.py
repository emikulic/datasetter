#!/usr/bin/env python3
"""
Sort a dataset by filename, this renumbers all the entries.
"""
from util import Dataset
import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    args = p.parse_args()

    for i in args.inputs:
        print(f"sorting {i}")
        ds = Dataset(i)
        fn_n = [(md["fn"], md["n"]) for md in ds._data.values()]
        fn_n.sort()

        d = {}
        idx = 0
        for _, n in fn_n:
            d[idx] = ds._data[n]
            d[idx]["n"] = idx  # Re-number.
            idx += 1

        ds._data = d
        ds.compact()


if __name__ == "__main__":
    main()
