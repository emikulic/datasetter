#!/usr/bin/env python3
"""
Use BLIP to automatically generate captions, and CLIP to keep the best ones.
"""
import logging

fmt = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
logging.basicConfig(format=fmt, level=logging.DEBUG)
logging.info("importing")
import os

if "TRANSFORMERS_OFFLINE" not in os.environ:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
import argparse
from util import Dataset
from PIL import Image
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
    p.add_argument("--num_gen", default=100, help="How many captions to generate.")
    p.add_argument("--num_keep", default=10, help="How many captions to keep.")
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

    # Downloads 945MB to ~/.cache/huggingface/hub/models--Salesforce--blip-image...
    blip_version = "Salesforce/blip-image-captioning-base"
    # Downloads 1.8G.
    blip_version = "Salesforce/blip-image-captioning-large"
    logging.info("loading BLIP processor")
    blip_processor = transformers.AutoProcessor.from_pretrained(blip_version)
    logging.info("loading BLIP model")
    blip_model = transformers.BlipForConditionalGeneration.from_pretrained(
        blip_version
    ).to(device)

    # Downloads 1.6GB to ~/.cache/huggingface/hub/models--openai--clip-vit-large-patch14
    clip_version = "openai/clip-vit-large-patch14"  # This is what sd1.5 uses.
    logging.info("loading CLIP processor")
    clip_processor = transformers.CLIPImageProcessor()
    logging.info("loading CLIP image model")
    clip_image_model = transformers.CLIPVisionModelWithProjection.from_pretrained(
        clip_version
    ).to(device)
    tokenizer = transformers.AutoTokenizer.from_pretrained(clip_version)
    logging.info("loading CLIP text model")
    clip_text_model = transformers.CLIPTextModelWithProjection.from_pretrained(
        clip_version
    ).to(device)
    logging.info("done loading")

    for fn in args.inputs:
        logging.info(f"loading dataset {fn}")
        ds = Dataset(fn)

        for n, md in ds._data.items():
            if not args.override:
                if "autocaption" in md:
                    logging.info(
                        f"already has autocaption, skipping {md}, try --override"
                    )
                    continue
            jpg = ds.cropped_jpg(n, SZ)
            img = Image.open(io.BytesIO(jpg))

            with torch.no_grad():  # matters
                # BLIP
                inputs = blip_processor(img, args.blip_prefix, return_tensors="pt").to(
                    device
                )
                outputs = blip_model.generate(
                    **inputs,
                    max_new_tokens=80,
                    num_return_sequences=args.num_gen,
                    do_sample=True,
                )
                captions = blip_processor.batch_decode(
                    outputs, skip_special_tokens=True
                )  # List of strings.
                captions = [args.clip_prefix + i for i in captions]

                if "caption" in md:
                    captions.append(md["caption"])
                if "autocaption" in md:
                    ac = md["autocaption"]
                    if type(ac) is str:
                        ac = [ac]
                    captions.extend(ac)

                # CLIP image.
                pixel_values = clip_processor(img).pixel_values[0]
                pixel_values = torch.tensor(pixel_values).to(device)
                img_embed = clip_image_model(pixel_values.unsqueeze(0)).image_embeds[0]
                # img_embed.shape is torch.Size([768])

                # CLIP text.
                inputs = tokenizer(
                    captions, padding="max_length", truncation=True, return_tensors="pt"
                ).to(device)
                txt_embed = clip_text_model(**inputs).text_embeds

                # Sort into order.
                dist = torch.nn.functional.cosine_similarity(txt_embed, img_embed)
                captions = sorted(zip(dist.tolist(), captions), reverse=True)

            captions = captions[: args.num_keep]
            captions = [[f"{k:.03}", v] for k, v in captions]
            md["autocaption"] = captions
            logging.info(f'{n} {md["fn"]} {captions[0]}')

        print("compacting")
        ds.compact()


if __name__ == "__main__":
    main()
