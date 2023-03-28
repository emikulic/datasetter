#!/usr/bin/env python3
"""
CLI to use clip_server.py.
"""
import argparse
from aiohttp import web
import aiohttp
import logging
import asyncio

logging.basicConfig(level=logging.INFO)


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8002)
    p.add_argument("--host", type=str, default="127.0.0.1", help="Server address.")
    p.add_argument("file", type=str)
    args = p.parse_args()

    data = {"file": open(args.file, "rb")}
    url = f"http://{args.host}:{args.port}/clip"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            data = await resp.read()
    print(len(data))


if __name__ == "__main__":
    asyncio.run(main())
