#!/usr/bin/env python3
"""
Get all frames out of a video.
"""
import argparse
import os
import cv2  # pip install opencv-python
from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument("infile", type=str)
    args = p.parse_args()
    d = os.path.dirname(args.infile)
    if not d:
        d = "."
    print(f'output in "{d!r}"')
    cap = cv2.VideoCapture(args.infile)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print(f"there are {frames} frames")
    frame_no = 0
    output_no = 0
    i = 0.0
    while True:
        running, frame = cap.read()
        if not running:
            break
        frame_no += 1
        i += 1.0
        if True:
            output_no += 1
            fn = f"{d}/{output_no:06d}.jpg"
            print(f"save frame {frame_no} as {fn}")
            frame = frame[:, :, ::-1]  # BGR -> RGB
            img = Image.fromarray(frame)
            img.save(fn, quality=99)


if __name__ == "__main__":
    main()

# vim:set ai ts=4 sw=4 et:
