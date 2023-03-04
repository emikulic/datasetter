#!/usr/bin/env python3
"""
Generate a dataset directory.
"""
from util import Dataset
import argparse
import os


def main():
    p = argparse.ArgumentParser()
    p.add_argument("outdir", help="Dataset directory to generate.")
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    p.add_argument("--size", type=int, default=512, help="Default output image size.")
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

    os.makedirs(f"{args.outdir}/img", exist_ok=True)
    os.makedirs(f"{args.outdir}/txt", exist_ok=True)

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

            # Write img/ and txt/.
            img = ds.cropped_jpg(o["n"], args.size)
            ofn = f"{o['md5']}-{o['n']}"
            with open(f"{args.outdir}/img/{ofn}.jpg", "wb") as f:
                f.write(img)
            with open(f"{args.outdir}/txt/{ofn}.txt", "w") as f:
                f.write(caption.strip() + "\n")

            print(f'{dsi+1}/{dsn} {oi+1}/{on} {o["fn"]} {caption!r}')


if __name__ == "__main__":
    main()
