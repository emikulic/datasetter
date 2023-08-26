#!/usr/bin/env python3
"""
Pad all images.
"""
import argparse
import os
import hashlib
import util
import PIL
from add import pad_to_square, md5


def main():
    p = argparse.ArgumentParser()
    p.add_argument("dsfile", help="JSON dataset to process.")
    args = p.parse_args()

    # Check inputs are relative to the dsfile.
    dsdir = os.path.dirname(os.path.abspath(args.dsfile))
    if dsdir == "":
        dsdir = "."
    print(f"working relative to {dsdir!r}")

    # Load dataset.
    ds = util.Dataset(args.dsfile)

    for md in ds._data.values():
        fn = md['fn']
        print(fn)
        try:
            img = util.load_image(fn, dsdir)
        except PIL.UnidentifiedImageError as e:
            print(f"WARN: skipping {fn} because {e}")
            continue

        fn = f'{dsdir}/{fn}'
        cksum = md5(fn)
        if cksum != md['md5']:
            print(' md5 changed!')

        md['md5'] = cksum
        md['fsz'] = os.path.getsize(fn)
        md['orig_w'] = img.width
        md['orig_h'] = img.height
        pad_to_square(md)

    ds.compact()


if __name__ == "__main__":
    main()
