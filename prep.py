#!/usr/bin/env python3
"""
Generate a dataset directory.
"""
from PIL import Image, ImageFile
from util import Dataset
import argparse
import os
import util

# Don't throw exception when a file only partially loads.
ImageFile.LOAD_TRUNCATED_IMAGES = True


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
        img = util.rgbify(img)
        x, y, w, h = o["x"], o["y"], o["w"], o["h"]
        img = img.crop((x, y, x + w, y + h))
        sz = args.size
        img = img.resize((sz, sz), Image.Resampling.BICUBIC)
        ofn = f"{o['md5']}-{o['n']}"
        img.save(f"{args.outdir}/img/{ofn}.jpg", quality=95)

        caption = ""
        if "caption" in o:
            caption = o["caption"]

        with open(f"{args.outdir}/txt/{ofn}.txt", "w") as f:
            f.write(caption)


if __name__ == "__main__":
    main()
