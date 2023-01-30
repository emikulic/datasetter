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
    args = p.parse_args()

    os.makedirs(f"{args.outdir}/img", exist_ok=True)
    os.makedirs(f"{args.outdir}/txt", exist_ok=True)

    # Load datasets.
    datasets = [Dataset(i) for i in args.inputs]
    dsn = len(datasets)
    print(f"loaded {dsn} datasets")

    # Process all inputs.
    for dsi, ds in enumerate(datasets):
        on = len(ds._data)
        for oi, o in enumerate(ds._data.values()):
            # assert os.path.getsize(o["fn"]) == o["fsz"]
            if "skip" in o:
                print(f'skip {o["fn"]} because {o["skip"]!r}')
                continue

            # Use either manual or automatic caption.
            caption = ""
            if "caption" in o:
                caption = o["caption"]
            elif "autocaption" in o:
                caption = o["autocaption"]
            else:
                print(f'skip {o["fn"]} missing caption')
                continue

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
