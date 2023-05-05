#!/usr/bin/env python3
"""
Generate a dataset directory, but re-crops to s different size.
"""
from util import Dataset
import argparse
import os
import numpy as np
import io
from PIL import Image
import util


def make_empty_mask(w, h):
    """
    Returns a PNG mask that doesn't mask anything out.
    """
    mask = np.zeros((h, w), dtype=np.uint8)
    mask += 255
    s = io.BytesIO()
    Image.fromarray(mask).save(s, format="png")
    return s.getvalue()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("outdir", help="Dataset directory to generate.")
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    p.add_argument("--w", type=int, default=640, help="Default output image size.")
    p.add_argument("--h", type=int, default=448, help="Default output image size.")
    p.add_argument("--limit", type=int, default=0, help="Stop after this many inputs.")
    p.add_argument("--caption", type=str, default="", help="If set, rewrite caption.")
    p.add_argument(
        "--need_crop",
        help="If set, skip any input that isn't manually cropped.",
        action="store_true",
    )
    p.add_argument(
        "--need_caption",
        help="If set, skip any input that doesn't have a caption set.",
        action="store_true",
    )
    args = p.parse_args()

    os.makedirs(f"{args.outdir}", exist_ok=True)
    no_mask = make_empty_mask(args.w, args.h)

    # Load datasets.
    datasets = [Dataset(i) for i in args.inputs]
    dsn = len(datasets)
    print(f"loaded {dsn} datasets")

    # Process all inputs.
    count = 0
    for dsi, ds in enumerate(datasets):
        on = len(ds._data)
        for oi, o in enumerate(ds._data.values()):
            # assert os.path.getsize(o["fn"]) == o["fsz"]
            if "skip" in o:
                print(f'skip {o["fn"]} because {o["skip"]!r}')
                continue
            if args.need_crop and "manual_crop" not in o:
                print(f'skip {o["fn"]} because no manual crop')
                continue
            if args.need_caption and "caption" not in o:
                print(f'skip {o["fn"]} because no caption')
                continue

            # Manual vs automatic vs override caption.
            caption = o.get("caption", "")
            autocaption = o.get("autocaption", "")
            if args.caption:
                caption = args.caption.replace("AUTOCAPTION", autocaption).replace(
                    "CAPTION", caption
                )
            else:
                if caption == "":
                    caption = autocaption

            if caption == "":
                print(f'skip {o["fn"]} missing caption and autocaption')
                continue

            # Stop at limit.
            count += 1
            if args.limit > 0 and count > args.limit:
                return

            # Mess with cropping.
            out_aspect = args.w / args.h
            in_aspect = o["orig_w"] / o["orig_h"]
            x_pct = (o["x"] + o["w"] / 2) / o["orig_w"]
            y_pct = (o["y"] + o["h"] / 2) / o["orig_h"]

            if out_aspect >= in_aspect:
                # input is narrow and tall
                w = o["orig_w"]
                h = int(w / out_aspect)
            else:
                # input is wider than output
                h = o["orig_h"]
                w = int(out_aspect * h)

            x = int(x_pct * o["orig_w"] - (w / 2))
            y = int(y_pct * o["orig_h"] - (h / 2))

            if x < 0:
                x = 0
            if y < 0:
                y = 0
            if x + w > o["orig_w"]:
                x = o["orig_w"] - w
            assert y + h <= o["orig_h"]
            o["x"] = x
            o["y"] = y
            o["w"] = w
            o["h"] = h

            # Write out.
            img = util.load_and_transform(o, args.w, args.h, ds._dir)
            s = io.BytesIO()
            img.save(s, format="jpeg", quality=95)
            img = s.getvalue()
            mask = None
            if o.get("mask_state") == "done":
                o["fn"] = o["mask_fn"]
                mask = util.load_and_transform(o, args.w, args.h, ds._dir)
                s = io.BytesIO()
                mask.save(s, format="jpeg", quality=95)
                mask = s.getvalue()
            if mask is None:
                mask = no_mask
            ofn = f"{count:06d}_{o['md5']}"
            with open(f"{args.outdir}/{ofn}.jpg", "wb") as f:
                f.write(img)
            with open(f"{args.outdir}/{ofn}.mask.png", "wb") as f:
                f.write(mask)
            with open(f"{args.outdir}/{ofn}.txt", "w") as f:
                f.write(caption.strip() + "\n")

            print(f'ds {dsi+1}/{dsn} n {oi+1}/{on} fn {o["fn"]!r} {caption!r}')


if __name__ == "__main__":
    main()
