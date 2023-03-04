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
        self._dir = os.path.dirname(os.path.abspath(fn))
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

    def update(self, obj, append):
        if append:
            # Append only mode: don't rewrite the whole file.
            self.add(obj)
            return
        self._memadd(obj)
        self.compact()

    def compact(self):
        with open(self._fn, "w") as f:
            for obj in self._data.values():
                json.dump(obj, f)
                f.write("\n")

    def cropped_jpg(self, n, sz):
        """
        Returns JPEG image data for object n, cropped and scaled and rotated.
        Populates the cache.
        """
        o = self._data[n]
        key = {
            "md5": o["md5"],
            "x": o["x"],
            "y": o["y"],
            "w": o["w"],
            "h": o["h"],
            "sz": sz,
            "rot": o.get("rot", 0),
        }
        key = json.dumps(key, sort_keys=True)
        try:
            return self._cache[key]
        except KeyError:
            # TODO: change this to verbose logging.
            print(f"cropped_jpg cache miss for {key}")
            img = load_and_crop(o, sz, dsdir=self._dir)
            s = io.BytesIO()
            img.save(s, format="jpeg", quality=95)
            img = s.getvalue()
            self._cache[key] = img
            return img

    def cropped_mask(self, n, sz):
        """
        Returns PNG image data for the mask for object n, cropped and scaled
        and rotated. Populates the cache. If no mask is applicable, returns
        None.
        """
        o = self._data[n]
        key = {
            "md5": o["md5"],
            "x": o["x"],
            "y": o["y"],
            "w": o["w"],
            "h": o["h"],
            "sz": sz,
            "rot": o.get("rot", 0),
            "mask": 1,
        }
        key = json.dumps(key, sort_keys=True)
        try:
            return self._cache[key]
        except KeyError:
            # TODO: change this to verbose logging.
            name, ext = os.path.splitext(o["fn"])
            o = o.copy()
            o["fn"] = f"{name}.mask.png"
            if not os.path.exists(f'{self._dir}/{o["fn"]}'):
                return None
            print(f"cropped_mask cache miss for {o['fn']}, {key}")
            img = load_and_crop(o, sz, dsdir=self._dir)
            if np.all(np.asarray(img) == [255, 255, 255]):
                return None  # Nothing is masked out.
            s = io.BytesIO()
            img.save(s, format="png")
            img = s.getvalue()
            self._cache[key] = img
            return img

    def crop_preview(self, n, x, y, wh, sz):
        """
        Returns JPEG image data for object n, cropped and scaled and rotated.
        This is for previews in the web UI and is not cached.
        """
        o = self._data[n].copy()
        o["x"] = x
        o["y"] = y
        o["w"] = wh
        o["h"] = wh
        o["sz"] = sz
        # TODO: change this to verbose logging.
        print(f"crop_preview for {o}")
        img = load_and_crop(o, sz, dsdir=self._dir)
        s = io.BytesIO()
        img.save(s, format="jpeg", quality=95)
        return s.getvalue()

    def rotate_preview(self, n, rot, sz):
        """
        Returns JPEG image data for object n, cropped and scaled and rotated.
        This is for previews in the web UI and is not cached.
        """
        o = self._data[n].copy()
        o["rot"] = rot
        o["sz"] = sz
        # TODO: change this to verbose logging.
        print(f"rotate_preview for {o}")
        img = load_and_crop(o, sz, dsdir=self._dir)
        s = io.BytesIO()
        img.save(s, format="jpeg", quality=95)
        return s.getvalue()


_load_cache = [("", None)]  # (fn, Image)


def load_image(fn, dsdir="."):
    """
    Load an image, apply EXIF rotation, convert to RGB.
    """
    if _load_cache[0][0] == fn:
        return _load_cache[0][1]
    img = Image.open(f"{dsdir}/{fn}")
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = ImageOps.exif_transpose(img)
    _load_cache[0] = (fn, img)
    return img


def load_and_crop(o, sz, dsdir="."):
    """
    Load the image from the given metadata (o), cropped and scaled and rotated.
    """
    img = load_image(o["fn"], dsdir)
    assert img.width == o["orig_w"]  # TODO: warn instead
    assert img.height == o["orig_h"]
    x, y, w, h = o["x"], o["y"], o["w"], o["h"]
    assert x >= 0, x
    assert y >= 0, y
    assert w > 0, w
    assert h > 0, h
    assert sz > 0, sz
    assert sz <= 1024, sz
    rot = o.get("rot", 0)
    assert rot in [0, 1, 2, 3], rot
    img = img.crop((x, y, x + w, y + h))
    img = img.resize((sz, sz), Image.Resampling.BICUBIC)
    img = img.rotate(rot * 90)
    return img
