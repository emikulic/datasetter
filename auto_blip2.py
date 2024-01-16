#!/usr/bin/env python3
"""
Use BLIP2 to automatically generate captions.
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
from PIL import Image, ImageOps
import io
import torch
import transformers

# Trade-off: use default size to get cache hits, BLIP will scale images down to 384px.
SZ = 512


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    p.add_argument(
        "--blip_prefix", default="", help="Prefix to feed to BLIP. (optional)"
    )
    p.add_argument(
        "--clip_prefix", default="", help="Prefix to add before CLIP. (optional)"
    )
    p.add_argument(
        "--num_gen", type=int, default=1, help="How many captions to generate."
    )
    p.add_argument("--num_beams", type=int, default=16, help="Beam search param.")
    p.add_argument("--max_length", type=int, default=80, help="Max caption length.")
    p.add_argument("--min_length", type=int, default=20, help="Min caption length.")
    p.add_argument(
        "--override",
        help="Regenerate existing autocaptions.",
        action="store_true",
    )
    args = p.parse_args()

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    logging.info(f"device is {device}")

    logging.info("***********************************************************")
    logging.info("* To allow model downloads, use: env TRANSFORMERS_OFFLINE=0")
    logging.info("***********************************************************")

    # Downloads 15GB to ~/.cache/huggingface/hub/models--Salesforce--blip2...
    blip_version = "Salesforce/blip2-opt-2.7b"
    logging.info("loading BLIP processor")
    blip_processor = transformers.Blip2Processor.from_pretrained(blip_version)
    print(blip_processor)
    logging.info("loading BLIP model")  # This takes a while.
    blip_model = transformers.Blip2ForConditionalGeneration.from_pretrained(
        blip_version, torch_dtype=torch.float16
    ).to(device)

    key = "auto_blip2"
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
            img = Image.open(io.BytesIO(jpg))
            sz = max(img.width, img.height)
            img = ImageOps.pad(img, (sz, sz))

            with torch.no_grad():  # matters
                # BLIP
                inputs = blip_processor(img, args.blip_prefix, return_tensors="pt").to(
                    device, torch.float16  # dtype is important
                )
                outputs = blip_model.generate(
                    **inputs,
                    max_length=args.max_length,
                    min_length=args.min_length,
                    num_beams=args.num_beams,
                    num_return_sequences=args.num_gen,
                    do_sample=True,
                )
                captions = blip_processor.batch_decode(
                    outputs, skip_special_tokens=True
                )  # List of strings.
                crop = len(args.blip_prefix)
                captions = [args.clip_prefix + i[crop:] for i in captions]
                captions = [i.strip() for i in captions]
                md[key] = captions

            ds.add(md)
            logging.info(f'{n+1}/{ln} {md["fn"]} {captions}')

        print("compacting")
        ds.compact()


if __name__ == "__main__":
    main()
