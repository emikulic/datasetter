#!/usr/bin/env python3
"""
Utilities.
"""
from PIL import Image
import json
import os
import numpy as np


class Dataset:
    def __init__(self, fn):
        self._data = {}  # Map from N to metadata object.
        self._fn = fn
        self._fns = set()  # Set of original filenames.
        if os.path.exists(fn):
            self._load(fn)

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
