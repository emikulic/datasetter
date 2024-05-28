#!/usr/bin/env python3
"""
CLI to use blip3_server.py.
"""
import argparse
import logging
import requests

logging.basicConfig(level=logging.INFO)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", type=str, default="127.0.0.1", help="Server address.")
    p.add_argument("--port", type=int, default=8003, help="Server port.")
    p.add_argument("img", type=argparse.FileType("rb"))
    p.add_argument("--query", type=str, default="Caption this image.")
    args = p.parse_args()

    url = f"http://{args.host}:{args.port}/blip3"
    files = {"img": args.img}
    data = {"query": args.query}
    print(f"Q: {args.query}")
    r = requests.post(url, files=files, data=data)
    if r.status_code != 200:
        print(f"ERROR {r.status_code}")
    else:
        print(f"A: {r.text}")


if __name__ == "__main__":
    main()
