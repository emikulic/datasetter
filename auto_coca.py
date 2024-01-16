#!/usr/bin/env python3
"""
Use CoCa to automatically generate captions.
Needs ~6GB of VRAM.
"""
import logging

fmt = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
logging.basicConfig(format=fmt, level=logging.INFO)
logging.info("importing")
import os

if "TRANSFORMERS_OFFLINE" not in os.environ:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
import argparse
from util import Dataset
from PIL import Image
import io
import torch
import open_clip

# Trade-off: use default size to get cache hits, BLIP will scale images down to 384px.
SZ = 512


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    p.add_argument(
        "--override",
        help="Regenerate existing autocaptions.",
        action="store_true",
    )
    args = p.parse_args()

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    logging.info(f"device is {device}")

    # Downloads 2.55GB.
    model, _, transform = open_clip.create_model_and_transforms(
        model_name="coca_ViT-L-14", pretrained="mscoco_finetuned_laion2B-s13B-b90k"
    )
    model = model.to(device)

    key = "auto_coca"
    for fn in args.inputs:
        logging.info(f"loading dataset {fn}")
        ds = Dataset(fn)

        ln = len(ds._data.items())
        for n, md in ds._data.items():
            if not args.override:
                if key in md:
                    logging.info(f"already has {key!r}, skipping {md}, try --override")
                    continue
            jpg = ds.masked_thumbnail(n, SZ, color=(0, 0, 0))
            im = Image.open(io.BytesIO(jpg)).convert("RGB")
            im = transform(im).unsqueeze(0)
            im = im.to(device, torch.float16)

            with torch.no_grad(), torch.cuda.amp.autocast():
                generated = model.generate(im)
                p = (
                    open_clip.decode(generated[0])
                    .split("<end_of_text>")[0]
                    .replace("<start_of_text>", "")
                )
                if p.endswith(" . "):
                    p = p[:-3]
                p = p.strip()
                md[key] = [p]

            ds.add(md)
            logging.info(f'{n+1}/{ln} {md["fn"]} {p!r}')

        print("compacting")
        ds.compact()


if __name__ == "__main__":
    main()
