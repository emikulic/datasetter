#!/usr/bin/env python3
"""
Web-based dataset editing.
"""
# from PIL import Image, ImageFile
import argparse

# import os
# import hashlib
from util import Dataset
from aiohttp import web

# import urllib.parse
import aiohttp
import logging

logging.basicConfig(level=logging.DEBUG)


class Server:
    routes = web.RouteTableDef()

    def __init__(self, args):
        self._port = args.port
        self._bind = args.bind
        self._ds = Dataset(args.dsfile)

    @routes.get("/")
    async def hello(request):
        with open("index.html", "r") as f:
            s = f.read()
        return web.Response(
            text=s, content_type="text/html", headers={"Pragma": "no-cache"}
        )

    def run(self):
        app = web.Application()
        app.add_routes(self.routes)
        web.run_app(app, port=self._port, host=self._bind)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8001)
    p.add_argument("--bind", type=str, default="127.0.0.1")
    p.add_argument("dsfile", help="JSON dataset file to operate on.")
    args = p.parse_args()

    s = Server(args)
    s.run()


if __name__ == "__main__":
    main()
