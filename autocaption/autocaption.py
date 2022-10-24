#!/usr/bin/env python3
"""
Automatically generate captions.
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__) + "/..")
sys.path.insert(0, os.path.dirname(__file__) + "/BLIP")
import util
from models.blip import blip_decoder
import logging
import torch
from torchvision import transforms
from torchvision.transforms.functional import InterpolationMode
import numpy as np


def main():
    logging.basicConfig(level=logging.INFO)
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="One or more dataset JSON files.")
    args = p.parse_args()

    pre = "https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model*_base_caption.pth"
    vit = "base"
    # Try:
    # model_url = 'https://storage.googleapis.com/sfr-vision-language-research/BLIP/models/model_large_caption.pth'
    # and vit=large

    # Can't change size because the pre-trained model hardcodes it.
    sz = 384

    # Load model.
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info("got device %s, loading model", device)
    model = blip_decoder(
        pretrained=pre,
        image_size=sz,
        vit=vit,
        prompt="",
        med_config="BLIP/configs/med_config.json",
    )
    model.eval()
    model.to(device)
    logging.info("loaded model")

    transform = transforms.Compose(
        [
            transforms.Resize((sz, sz), interpolation=InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(
                (0.48145466, 0.4578275, 0.40821073),
                (0.26862954, 0.26130258, 0.27577711),
            ),
        ]
    )

    # Process datasets.
    for i in args.inputs:
        ds = util.Dataset(i)
        for o in ds._data.values():
            img = util.load_and_crop(o, sz)
            img = transform(img).unsqueeze(0).to(device)
            captions = model.generate(
                img,
                sample=False,
                num_beams=3,
                max_length=62,
                min_length=5,
                repetition_penalty=1.1,
            )
            logging.info("%s %s", o["fn"], captions[0])
            o["autocaption"] = captions[0]
            ds.add(o)


if __name__ == "__main__":
    main()
