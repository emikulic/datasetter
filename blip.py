#!/usr/bin/env python3
"""
Use BLIP to automatically add captions.
"""
print("importing")
import argparse
from util import Dataset
from PIL import Image
import io
import torch
from transformers import AutoProcessor, BlipForConditionalGeneration

# Trade-off: use default size to get cache hits, BLIP will scale images down to 384px.
SZ = 512


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    p.add_argument("--prefix", default="", help="Optional prefix.")
    p.add_argument(
        "--override",
        help="Regenerate existing autocaptions.",
        action="store_true",
    )
    args = p.parse_args()

    # Downloads 945MB to ~/.cache/huggingface/hub/models--Salesforce--blip-image...
    print("loading processor")
    processor = AutoProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    print("loading model")
    model = BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )
    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    model.to(device)
    print("done loading")

    for fn in args.inputs:
        print(f"loading {fn}")
        ds = Dataset(fn)

        for n, md in ds._data.items():
            if not args.override:
                if "autocaption" in md:
                    print("skipping", md)
                    continue
            jpg = ds.cropped_jpg(n, SZ)
            im = Image.open(io.BytesIO(jpg))

            with torch.no_grad():  # matters
                inputs = processor(images=im, return_tensors="pt").to(device)
                outputs = model.generate(
                    **inputs, max_new_tokens=80
                )  # , num_return_sequences=10, do_sample=True)
                caption = processor.decode(outputs[0], skip_special_tokens=True)

            md["autocaption"] = args.prefix + caption
            ds.add(md)
            print((n, md["fn"], md["autocaption"]))

        print("compacting")
        ds.compact()


if __name__ == "__main__":
    main()
