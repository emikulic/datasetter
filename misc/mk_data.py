#!/usr/bin/env python3
"""
Builds img/ and txt/ given a bunch of source dirs.
"""
import os
from glob import glob
import argparse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("indirs", nargs="+")
    args = p.parse_args()

    os.makedirs("img", exist_ok=True)
    os.makedirs("txt", exist_ok=True)

    for d in args.indirs:
        if not os.path.isdir(d):
            print(f"skip {d} - not a dir")
            continue
        print(f"process {d}")

        prompts = glob(f"{d}/*")
        # print(prompts)

        for p in prompts:
            fns = glob(f"{p}/*.jpg")
            pr = p.replace(f"{d}/", "")  # prompt text
            assert "/" not in pr, pr
            for fn in fns:
                bn = os.path.basename(fn)
                dst = f"img/{bn}"
                txt = f"txt/{bn}".replace(".jpg", ".txt")
                # print((fn, dst, txt))
                os.link(fn, dst)
                with open(txt, "w") as fp:
                    fp.write(f"{pr}\n")


if __name__ == "__main__":
    main()
