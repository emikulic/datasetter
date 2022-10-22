#!/usr/bin/env python3
"""
Add images to a dataset.
"""
from PIL import Image, ImageFile
import argparse
import os
import hashlib
from util import Dataset


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
