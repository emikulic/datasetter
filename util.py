#!/usr/bin/env python3
"""
Utilities.
"""
import json
import os


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
