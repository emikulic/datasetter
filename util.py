#!/usr/bin/env python3
"""
Utilities.
"""
from PIL import Image, ImageFile, ImageOps
import json
import os
import numpy as np
import sqlite3
import io

# Don't throw exception when a file only partially loads.
ImageFile.LOAD_TRUNCATED_IMAGES = True


class DB:
    """
    Presents sqlite3 as a dict.
    """

    def __init__(self, fn):
        self._db = sqlite3.connect(fn)
        self._db.execute("CREATE TABLE IF NOT EXISTS db(key PRIMARY KEY, value)")

    def __getitem__(self, key):
        assert type(key) is str
        ret = self._db.execute("SELECT value FROM db WHERE key=?", (key,)).fetchone()
        if ret is None:
            raise KeyError()
        return ret[0]

    def __setitem__(self, key, value):
        assert type(key) is str
        assert type(value) is bytes
        self._db.execute("REPLACE INTO db VALUES(?, ?)", (key, value))
        self._db.commit()


class Dataset:
    def __init__(self, fn):
        self._data = {}  # Map from N to metadata object.
        self._fn = fn
        self._fns = set()  # Set of original filenames.
        if os.path.exists(fn):
            self._load(fn)
        self._cache = DB(f"{fn}.cache")

    def _load(self, fn):
        """
        Load dataset from the given filename.
        """
        with open(fn, "r") as f:
            for line in f.readlines():
                self._memadd(json.loads(line))

    def next_n(self):
        """
        Returns the next N.
        """
        return max([-1] + list(self._data.keys())) + 1

    def _memadd(self, obj):
        """
        Adds the specified object into the in-memory data, without updating the file
        on disk.
        """
        n = obj["n"]
        assert type(n) is int, n
        self._data[n] = obj
        self._fns.add(obj["fn"])

    def seen_fn(self, fn):
        return fn in self._fns

    def add(self, obj):
        if "n" not in obj:
            obj["n"] = self.next_n()
        self._memadd(obj)
        with open(self._fn, "a") as f:
            json.dump(obj, f)
            f.write("\n")

    def cropped_jpg(self, n, sz):
        """
        Returns JPEG image data for object n, cropped, and scaled to size sz.
        """
        o = self._data[n]
        key = {
            "md5": o["md5"],
            "x": o["x"],
            "y": o["y"],
            "w": o["w"],
            "h": o["h"],
            "sz": sz,
        }
        key = json.dumps(key, sort_keys=True)
        try:
            return self._cache[key]
        except KeyError:
            img = load_and_crop(o, sz)
            s = io.BytesIO()
            img.save(s, format="jpeg", quality=95)
            img = s.getvalue()
            self._cache[key] = img
            return img


def rgbify(i):
    """
    Convert grayscale to RGB by duplicating into 3 channels.
    This is a no-op on images that already have 3 channels.
    If the image has an alpha channel, it's stripped.
    """
    i = np.atleast_3d(i)
    h, w, c = i.shape
    if c == 3:
        return Image.fromarray(i)
    if c == 4:
        return Image.fromarray(i[:, :, :3])
    out = np.zeros((h, w, 3), dtype=i.dtype)
    out[:, :, :] = i[:, :]
    return Image.fromarray(out)


def load_image(fn):
    """
    Load an image, apply EXIF rotation, convert to RGB.
    """
    img = Image.open(fn)
    img = ImageOps.exif_transpose(img)
    return rgbify(img)


def load_and_crop(o, sz):
    """
    Load the image from the given metadata (o), crop, and resize to sz.
    """
    img = load_image(o["fn"])
    assert img.width == o["orig_w"]  # TODO: warn instead
    assert img.height == o["orig_h"]
    x, y, w, h = o["x"], o["y"], o["w"], o["h"]
    img = img.crop((x, y, x + w, y + h))
    img = img.resize((sz, sz), Image.Resampling.BICUBIC)
    return img
