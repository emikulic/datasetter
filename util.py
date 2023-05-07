#!/usr/bin/env python3
"""
Utilities.
"""
from PIL import Image, ImageFile, ImageOps, ImageChops
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
        # Full path to fn's parent dir.
        self._dir = os.path.dirname(os.path.abspath(fn))
        # Relative (to _dir) path to the mask dir.
        self._maskdir = os.path.basename(os.path.abspath(fn)) + ".masks"
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

    def prep_mask(self, n, append):
        """
        Creates {fn}.masks/{n}_{md5}.prep.mask.png
        """
        obj = self._data[n]
        assert "mask_fn" not in obj
        os.makedirs(f"{self._dir}/{self._maskdir}", exist_ok=True)
        maskfn = f'{self._maskdir}/{obj["n"]}_{obj["md5"]}.prep.mask.png'
        img = load_image(obj["fn"], dsdir=self._dir).convert("RGB")
        img = np.asarray(img).copy()  # copy to make it not readonly
        rgb = np.asarray([255, 0, 255])
        precision = 255 - (1 + 2 + 4 + 8)  # bitmask
        # Darken full purple if it's present in the image.
        cond = (img & precision) == (rgb & precision)
        cond = cond.all(axis=2)
        img[cond] = [200, 0, 200]
        Image.fromarray(img).save(f"{self._dir}/{maskfn}")
        obj["mask_fn"] = maskfn
        obj["mask_state"] = "prep"
        self.update(obj, append)

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
            img = load_and_transform(o, sz, sz, dsdir=self._dir)
            img = img.convert("RGB")  # Drop alpha.
            s = io.BytesIO()
            img.save(s, format="jpeg", quality=95)
            img = s.getvalue()
            self._cache[key] = img
            return img

    def cropped_mask(self, n, sz):
        """
        Returns PNG image data for the mask for object n, cropped and scaled
        and rotated. Populates the cache.
        """
        o = self._data[n].copy()
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
            img = load_and_transform(o, sz, sz, dsdir=self._dir)
            r, g, b, a = img.split()
            del img

            # Apply a custom mask if present.
            if o.get("mask_state", "") == "done":
                om = o.copy()
                om["fn"] = o["mask_fn"]
                mask = load_and_transform(om, sz, sz, dsdir=self._dir)
                mask = mask.convert("L")
                a = ImageChops.multiply(a, mask)

            s = io.BytesIO()
            a.save(s, format="png")
            img = s.getvalue()
            self._cache[key] = img
            return img

    def masked_thumbnail(self, n, sz, color=(255, 0, 255)):
        """
        Like cropped_jpg but draws the mask on if present.
        """
        o = self._data[n]
        img = Image.open(io.BytesIO(self.cropped_jpg(n, sz)))
        mask = Image.open(io.BytesIO(self.cropped_mask(n, sz)))
        color = Image.new("RGB", img.size, color=color)
        img = Image.composite(img, color, mask).convert("RGB")
        s = io.BytesIO()
        img.save(s, format="jpeg", quality=95)
        return s.getvalue()

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
        img = load_and_transform(o, sz, sz, dsdir=self._dir).convert("RGB")
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
        img = load_and_transform(o, sz, sz, dsdir=self._dir).convert("RGB")
        s = io.BytesIO()
        img.save(s, format="jpeg", quality=95)
        return s.getvalue()


# A cache to speed up e.g. multiple crops of the same original.
_load_cache = [("", None)]  # (fn, Image object)


def load_image(fn, dsdir="."):
    """
    Load image and apply EXIF rotation. Returns an RGBA Image object.
    """
    if _load_cache[0][0] == fn:
        return _load_cache[0][1]

    img = Image.open(f"{dsdir}/{fn}")
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGBA")
    _load_cache[0] = (fn, img)
    return img


def load_and_transform(o, out_w, out_h, dsdir="."):
    """
    load_image for the given metadata object `o` and transform it: crop, scale to out_w x out_h,
    and rotate. Returns an RGBA Image object.
    """
    img = load_image(o["fn"], dsdir)
    assert img.width == o["orig_w"]  # TODO: warn instead
    assert img.height == o["orig_h"]
    x, y, w, h = o["x"], o["y"], o["w"], o["h"]
    assert w > 0, w
    assert h > 0, h
    assert out_w > 0, out_w
    assert out_h > 0, out_h
    assert out_w <= 1024, out_w
    assert out_h <= 1024, out_h
    rot = o.get("rot", 0)
    assert rot in [0, 1, 2, 3], rot
    img = img.crop((x, y, x + w, y + h))
    img = img.resize((out_w, out_h), Image.Resampling.BICUBIC)
    img = img.rotate(rot * 90)
    return img
