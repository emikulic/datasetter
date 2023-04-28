#!/usr/bin/env python3
"""
Use CLIP to cluster inputs into groups.
Creates one directory per cluster.
Needs clip_server.py running.
"""
import logging

fmt = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
logging.basicConfig(format=fmt, level=logging.DEBUG)
logging.info("importing")

import argparse
from glob import glob
import os
import torch
import aiohttp
import asyncio
import numpy as np

# cite: https://huggingface.co/openai/clip-vit-large-patch14/blob/main/config.json#L116
SZ = 224


async def clip(fn):
    # TODO: argparse host:port maybe?
    port = 8002
    host = "127.0.0.1"
    data = {"file": open(fn, "rb")}
    url = f"http://{host}:{port}/clip"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            data = await resp.read()
    assert len(data) == 3 * 1024, data
    data = np.frombuffer(data, dtype=np.float32)
    return torch.tensor(data).unsqueeze(0)


class Clusterer:
    CACHE = "img_embeds.pt"

    def __init__(self, args):
        self.args = args
        self.img_embeds = {}  # Map from filename to tensor.
        self.clusters = torch.zeros(
            (0, 768)
        )  # Tensor of embeds, index is cluster number.
        self.suffix = {}  # Map from cluster number to suffix string.

        try:
            self.img_embeds = torch.load(self.CACHE)
        except FileNotFoundError:
            print(f"failed to load cache from {self.CACHE}")
            pass

    def save_cache(self):
        print(f"Saving cache to {self.CACHE} [len={len(self.img_embeds)}]")
        torch.save(self.img_embeds, self.CACHE)

    async def cluster(self, fn, force_new_cluster=None):
        """
        Cluster the given file.
        """
        embed = await self.get_embed(fn)
        if len(self.clusters) == 0 or force_new_cluster:
            self.new_cluster(fn, embed, force_new_cluster)
            return 0

        # Find the closest cluster.
        sims = torch.nn.functional.cosine_similarity(embed, self.clusters)
        best_idx = torch.argmax(sims).item()
        best = sims[best_idx]
        if best < self.args.thresh:
            self.new_cluster(fn, embed)
        else:
            self.add_to_cluster(fn, best_idx)
        return best

    async def get_embed(self, fn):
        """
        Get the embedding for the given file. Tries to load from cache first.
        """
        try:
            return self.img_embeds[fn]
        except KeyError:
            embed = await clip(fn)
            self.img_embeds[fn] = embed
            return embed

    def new_cluster(self, fn, embed, force_new_cluster=None):
        """
        Create a new cluster for the given file.
        """
        idx = len(self.clusters)
        if force_new_cluster:
            self.suffix[idx] = f"_{force_new_cluster}_{os.path.basename(fn)}"
        self.clusters = torch.cat([self.clusters, embed])
        print(f"New cluster {idx}")
        if not self.args.store_all and force_new_cluster:
            return
        dirname = self._dirname(idx)
        os.makedirs(dirname, exist_ok=True)
        os.link(fn, f"{dirname}/{os.path.basename(fn)}")

    def add_to_cluster(self, fn, idx):
        if not self.args.store_all and idx in self.suffix:
            return
        dirname = self._dirname(idx)
        os.makedirs(dirname, exist_ok=True)
        try:
            os.link(fn, f"{dirname}/{os.path.basename(fn)}")
        except FileExistsError:
            print(f"File exists: {fn} -> {dirname}")

    def _dirname(self, idx):
        suffix = self.suffix.get(idx, "")
        return f"{self.args.outdir}/{idx:06}{suffix}"


async def process_dir(dirname, cl, force_new_cluster=None):
    """
    Process one dir.
    """
    fns = glob(os.path.join(dirname, "*"))
    num_inputs = len(fns)
    for i, fn in enumerate(fns):
        sim = await cl.cluster(fn, force_new_cluster)
        print(f"{force_new_cluster}: {i+1}/{num_inputs} {fn} {sim:.4f}")


async def process(args, cl):
    """
    This is in a separate function just because it's async.
    """
    await process_dir(args.blockdir, cl, force_new_cluster="block")
    await process_dir(args.keepdir, cl, force_new_cluster="keep")
    for fn in args.inputs:
        if os.path.isdir(fn):
            await process_dir(fn, cl)
        else:
            sim = await cl.cluster(fn)
            print(f"{fn} {sim:.4f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("inputs", nargs="+", help="Input files and/or directories")
    p.add_argument("--thresh", type=float, default=0.9, help="Threshold for clustering")
    p.add_argument("--outdir", default="outdir", help="Output directory")
    p.add_argument(
        "--keepdir",
        default="keep",
        help="Directory of images to keep (i.e. start with as clusters)",
    )
    p.add_argument(
        "--blockdir",
        default="block",
        help="Directory of images to block (as clusters also)",
    )
    p.add_argument(
        "--store_all",
        action="store_true",
        help="Store all images, including keep and blocked.",
    )

    args = p.parse_args()
    cl = Clusterer(args)
    try:
        asyncio.run(process(args, cl))
    except KeyboardInterrupt:
        pass
    cl.save_cache()


if __name__ == "__main__":
    main()
