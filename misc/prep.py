#!/usr/bin/env python3
from glob import glob
import os
import hashlib
from PIL import Image, ImageFile, ImageOps
import numpy as np

# Don't throw exception when a file only partially loads.
ImageFile.LOAD_TRUNCATED_IMAGES = True


def md5(fn):
    """
    Returns the hex md5sum of the given filename.
    """
    with open(fn, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def rgbify(i):
    """
    Convert grayscale to RGB by duplicating into 3 channels.
    This is a no-op on images that already have 3 channels.
    If the image has an alpha channel, it's stripped.
    """
    i = np.atleast_3d(i)
    h, w, c = i.shape
    if c == 3:
        return i
    if c == 4:
        return i[:, :, :3]
    out = np.zeros((h, w, 3), dtype=i.dtype)
    out[:, :, :] = i[:, :]
    return out


def crop_middle(img):
    h, w, c = img.shape
    l = min(h, w)
    x = (w - l) // 2
    y = (h - l) // 2
    return img[y : y + l, x : x + l, :]


def resample(img, w, h):
    """Resample via PIL."""
    return np.asarray(Image.fromarray(img).resize((w, h), Image.BICUBIC))


# main

os.makedirs("out", exist_ok=True)
fn = (
    glob("img/*.jpg")
    + glob("img/*.jpeg")
    + glob("img/*.png")
    + glob("img/*.jpg_large")
    + []
)

sz = 512
count = 0
for f in fn:
    m = md5(f)
    # outfn = f'out/{m}_mid.jpg'
    outfn = f"out/{count:06d}_{m}_mid.jpg"
    count += 1
    if os.path.exists(outfn):
        continue
    im = Image.open(f)
    im = ImageOps.exif_transpose(im)
    im = np.asarray(im)
    im = rgbify(im)
    im = crop_middle(im)
    im = resample(im, sz, sz)
    Image.fromarray(im).save(outfn, quality=95)
    print(f"{f} -> {outfn}")
