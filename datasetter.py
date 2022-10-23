#!/usr/bin/env python3
"""
Web-based dataset editing.
"""
# from PIL import Image, ImageFile
import argparse
import os
from util import Dataset
from aiohttp import web

# import urllib.parse
import aiohttp
import logging

logging.basicConfig(level=logging.DEBUG)


routes = web.RouteTableDef()


@routes.get("/")
async def index(request):
    with open("index.html", "r") as f:
        s = f.read()
    return web.Response(
        text=s, content_type="text/html", headers={"Pragma": "no-cache"}
    )


@routes.get("/title")
async def title(request):
    fn = request.config_dict["args"].dsfile
    fn = os.path.basename(fn)
    return web.Response(text=fn)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8001)
    p.add_argument("--host", type=str, default="127.0.0.1", help="Bind address.")
    p.add_argument("dsfile", help="JSON dataset file to operate on.")
    args = p.parse_args()

    app = web.Application()
    app.add_routes(routes)
    app["args"] = args
    app["ds"] = Dataset(args.dsfile)
    web.run_app(app, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
