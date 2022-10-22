#!/usr/bin/env python3
"""
Generate a dataset directory.
"""
from PIL import Image, ImageFile
from util import Dataset
import argparse
import numpy as np
import os

# Don't throw exception when a file only partially loads.
ImageFile.LOAD_TRUNCATED_IMAGES = True


def rgbify(i):
    """
    Convert grayscale to RGB by duplicating into 3 channels.
    This is a no-op on images that already have 3 channels.
    If the image has an alpha channel, it's stripped.
    """
    i = np.atleast_3d(i)
    h, w, c = i.shape
    if c == 3:
        return i
    if c == 4:
        return i[:, :, :3]
    out = np.zeros((h, w, 3), dtype=i.dtype)
    out[:, :, :] = i[:, :]
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("outdir", help="Dataset directory to generate.")
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    p.add_argument("--size", type=int, default=512, help="Default output image size.")
    args = p.parse_args()

    os.makedirs(f"{args.outdir}/img", exist_ok=True)
    os.makedirs(f"{args.outdir}/txt", exist_ok=True)

    # Collect all inputs.
    objs = []
    for i in args.inputs:
        ds = Dataset(i)
        objs.extend(ds._data.values())

    # Process all inputs.
    for o in objs:
        assert os.path.getsize(o["fn"]) == o["fsz"]
        img = Image.open(o["fn"])
        assert img.width == o["orig_w"]
        assert img.height == o["orig_h"]
        x, y, w, h = o["x"], o["y"], o["w"], o["h"]
        img = img.crop((x, y, x + w, y + h))
        sz = args.size
        img = img.resize((sz, sz), Image.Resampling.BICUBIC)
        img = Image.fromarray(rgbify(img))
        ofn = f"{o['md5']}-{o['n']}"
        img.save(f"{args.outdir}/img/{ofn}.jpg", quality=95)

        caption = ""
        if "caption" in o:
            caption = o["caption"]

        with open(f"{args.outdir}/txt/{ofn}.txt", "w") as f:
            f.write(caption)


if __name__ == "__main__":
    main()
