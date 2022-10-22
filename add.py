#!/usr/bin/env python3
"""
Add images to a dataset.
"""
from PIL import Image, ImageFile
import argparse
import json
import os
import hashlib


class Dataset:
    def __init__(self, fn):
        self._data = {}  # Map from N to metadata object.
        self._fn = fn
        self._fns = set()  # Set of original filenames.
        if os.path.exists(fn):
            self._load(fn)

    def _load(self, fn):
        """
        Load dataset from the given filename.
        """
        with open(fn, "r") as f:
            for line in f.readlines():
                self._memadd(json.loads(line))

    def next_n(self):
        """
        Returns the next N.
        """
        return max([-1] + list(self._data.keys())) + 1

    def _memadd(self, obj):
        """
        Adds the specified object into the in-memory data, without updating the file
        on disk.
        """
        n = obj["n"]
        assert type(n) is int, n
        self._data[n] = obj
        self._fns.add(obj["fn"])

    def seen_fn(self, fn):
        return fn in self._fns

    def add(self, obj):
        if "n" not in obj:
            obj["n"] = self.next_n()
        self._memadd(obj)
        with open(self._fn, "a") as f:
            json.dump(obj, f)
            f.write("\n")


def walk_dir(path):
    """
    Recursively walk the given path and return a list of filenames.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        for fn in filenames:
            out.append(f"{dirpath}/{fn}")
    return out


def md5(fn):
    """
    Returns the hex md5sum of the given filename.
    """
    with open(fn, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def center_crop(obj):
    """
    Populate x,y,w,h for a center crop.
    """
    w = obj["orig_w"]
    h = obj["orig_h"]
    sz = min(w, h)
    obj["w"] = obj["h"] = sz
    obj["x"] = (w - sz) // 2
    obj["y"] = (h - sz) // 2


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--caption", default=None, help="Optional default caption.")
    p.add_argument("dsfile", help="JSON dataset file to add to.")
    p.add_argument("inputs", nargs="+", help="Dirs and files to add.")
    args = p.parse_args()

    ds = Dataset(args.dsfile)

    # Build list of inputs.
    fns = []
    for i in args.inputs:
        if os.path.isdir(i):
            fns += walk_dir(i)
        else:
            assert os.path.isfile(i), i
            fns.append(i)
    fns = [os.path.realpath(i) for i in fns]
    fns.sort()

    # Process.
    for fn in fns:
        if ds.seen_fn(fn):
            print(f"seen {fn}")
            continue
        print(f"processing {fn}")
        img = Image.open(fn)
        obj = {
            "fn": fn,
            "md5": md5(fn),
            "fsz": os.path.getsize(fn),
            "orig_w": img.width,
            "orig_h": img.height,
            # TODO: xywh
            "rot": 0,
            "needs_rebuild": 1,
        }
        if args.caption:
            obj["caption"] = caption
        center_crop(obj)
        ds.add(obj)


if __name__ == "__main__":
    main()
