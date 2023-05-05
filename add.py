#!/usr/bin/env python3
"""
Add images to a dataset.

If a filename is already in the dataset, it will be skipped.
"""
import argparse
import os
import hashlib
import util
import PIL


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
    p.add_argument(
        "--onefile",
        help="Only add one file per input subdirectory.",
        action="store_true",
    )
    p.add_argument("dsfile", help="JSON dataset file to add to.")
    p.add_argument("inputs", nargs="+", help="Dirs and files to add.")
    args = p.parse_args()

    # Check inputs are relative to the dsfile.
    dsdir = os.path.dirname(os.path.abspath(args.dsfile))
    if dsdir == "":
        dsdir = "."
    print(f"working relative to {dsdir!r}")

    error = False
    for i in args.inputs:
        if not os.path.exists(i):
            print(f"error: input {i!r} doesn't exist")
            error = True
        rel = os.path.relpath(i, dsdir)
        if rel.startswith("../"):
            print(f"error: input {i!r} is outside {dsdir!r} (rel path {rel!r})")
            error = True
    if error:
        print("exiting due to bad inputs")

    # Load dataset.
    ds = util.Dataset(args.dsfile)

    # Build list of inputs.
    fns = []
    for i in args.inputs:
        if os.path.isdir(i):
            fns += walk_dir(i)
        else:
            assert os.path.isfile(i), i
            fns.append(i)
    fns = [os.path.relpath(i, dsdir) for i in fns]
    fns.sort()

    # Process.
    seen_dirs = set()
    for fn in fns:
        # Skip seen files.
        if ds.seen_fn(fn):
            print(f"seen {fn!r}")
            continue

        # Honor onefile if set.
        if args.onefile:
            subdir = os.path.dirname(fn)
            if subdir in seen_dirs:
                print(f"skipping {fn!r} because seen {subdir!r}")
                continue
            seen_dirs.add(subdir)

        print(f"processing {fn}")
        try:
            img = util.load_image(fn)
        except PIL.UnidentifiedImageError as e:
            print(f"WARN: skipping {fn} because {e}")
            continue
        obj = {
            "fn": fn,
            "md5": md5(fn),
            "fsz": os.path.getsize(fn),
            "orig_w": img.width,
            "orig_h": img.height,
            "rot": 0,
            "needs_rebuild": 1,
        }
        center_crop(obj)
        ds.add(obj)


if __name__ == "__main__":
    main()
