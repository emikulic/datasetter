#!/usr/bin/env python3
"""
Converts *.prep.mask.png to *.mask.png and updates the dataset.

Areas in purple (#FF00FF) in the input mask are masked out (converted to dark),
other areas are kept (converted to light) in the output mask.
"""
import argparse
from util import Dataset
from PIL import Image
import numpy as np
import os


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    args = p.parse_args()

    for fn in args.inputs:
        print(f"loading {fn}")
        ds = Dataset(fn)

        for n, md in ds._data.items():
            if md.get("mask_state", "") != "prep":
                continue
            mask_fn = md["mask_fn"]
            assert ".prep.mask.png" in mask_fn, mask_fn
            out_fn = mask_fn.replace(".prep.mask.png", ".mask.png")
            print(f"{mask_fn} -> {out_fn}")
            img = Image.open(f"{ds._dir}/{mask_fn}")
            img = np.asarray(img)
            cond = img == [255, 0, 255]
            cond = cond.all(axis=2)
            h, w, c = img.shape
            mask = np.zeros((h, w), dtype=np.uint8)
            mask += 255
            mask[cond] = 0
            Image.fromarray(mask).save(f"{ds._dir}/{out_fn}")
            os.unlink(f"{ds._dir}/{mask_fn}")

            md["mask_fn"] = out_fn
            md["mask_state"] = "done"
            ds.add(md)

        print("compacting")
        ds.compact()


if __name__ == "__main__":
    main()
