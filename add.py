#!/usr/bin/env python3
"""
Add images to a dataset.
"""
from PIL import Image, ImageFile
import argparse
import json


class Dataset:
    def __init__(self, fn):
        self.data = {}  # Map from N to metadata object.
        self._load(fn)

    def _load(self, fn):
        """
        Load dataset from the given filename.
        """
        with open(fn, "r") as f:
            for line in fp.readlines():
                obj = json.loads(line)
                assert "n" in obj, obj
                n = int(obj["n"])
                self.data[n] = obj


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--caption", default=None, help="Optional default caption.")
    p.add_argument("dsfile", help="JSON dataset file to add to.")
    p.add_argument("inputs", nargs="*", help="Dirs and files to add.")
    args = p.parse_args()

    ds = Dataset(args.dsfile)
