#!/usr/bin/env python
"""
Encode and decode images with the Variational Autoencoder.
"""
from diffusers import StableDiffusionPipeline
import torch
import numpy as np
from PIL import Image
import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("images", nargs="+")
    args = p.parse_args()

    repo_id = "runwayml/stable-diffusion-v1-5"
    print("loading pipeline")
    # This downloads to ~/.cache/huggingface/diffusers/models--runwayml--stable-diffusion-v1-5
    pipe = StableDiffusionPipeline.from_pretrained(
        repo_id, use_safetensors=True, torch_dtype=torch.float16
    ).to("cuda")

    for fn in args.images:
        print(fn)
        img = Image.open(fn).convert("RGB")
        pre = pipe.image_processor.preprocess(img).cuda()
        with torch.no_grad():
            with torch.autocast("cuda"):
                enc = pipe.vae.tiled_encode(pre)
                dec = pipe.vae.tiled_decode(enc.latent_dist.sample())

        dec = dec.sample[0].permute(1, 2, 0)
        im2 = dec.cpu().numpy() * 127.5 + 127.5
        im2 = im2.clip(0, 255)
        im2 = Image.fromarray(im2.astype(np.uint8))
        im2.save(f"{fn}-vae.png")


if __name__ == "__main__":
    main()
