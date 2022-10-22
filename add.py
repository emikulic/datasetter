#!/usr/bin/env python3
"""
Add images to a dataset.
"""
from PIL import Image, ImageFile
import argparse
import json
import os


class Dataset:
    def __init__(self, fn):
        self._data = {}  # Map from N to metadata object.
        self._fn = fn
        if os.path.exists(fn):
            self._load(fn)

    def _load(self, fn):
        """
        Load dataset from the given filename.
        """
        with open(fn, "r") as f:
            for line in fp.readlines():
                obj = json.loads(line)
                assert "n" in obj, obj
                n = int(obj["n"])
                self._data[n] = obj

    def next_n(self):
        """
        Returns the next N.
        """
        return max([-1] + list(self._data.keys())) + 1


def walk_dir(path):
    """
    Recursively walk the given path and return a list of filenames.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        for fn in filenames:
            out.append(f"{dirpath}/{fn}")
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--caption", default=None, help="Optional default caption.")
    p.add_argument("dsfile", help="JSON dataset file to add to.")
    p.add_argument("inputs", nargs="*", help="Dirs and files to add.")
    args = p.parse_args()

    ds = Dataset(args.dsfile)

    fns = []
    for i in args.inputs:
        if os.path.isdir(i):
            fns += walk_dir(i)
        else:
            assert os.path.isfile(i), i
            fns.append(i)

    print(fns)
    # print(args.inputs)
    # print(ds._data)
    # print(ds.next_n())


if __name__ == "__main__":
    main()
