#!/usr/bin/env python3
"""
Web-based dataset editing.
"""
from PIL import Image, ImageFile
import argparse
import os
from util import Dataset
import util
from aiohttp import web

# import urllib.parse
import aiohttp
import logging
from io import BytesIO

# Don't throw exception when a file only partially loads.
ImageFile.LOAD_TRUNCATED_IMAGES = True  # TODO: factor out loading into util.py

logging.basicConfig(level=logging.INFO)


routes = web.RouteTableDef()


@routes.get("/")
async def index_html(request):
    with open("index.html", "r") as f:
        s = f.read()
    return web.Response(
        text=s, content_type="text/html", headers={"Pragma": "no-cache"}
    )


@routes.get("/jquery.js")
async def jquery_js(request):
    with open("jquery.js", "r") as f:
        s = f.read()
    return web.Response(text=s, content_type="text/javascript")


@routes.get("/title.txt")
async def title(request):
    fn = request.config_dict["args"].dsfile
    fn = os.path.basename(fn)
    return web.Response(text=fn)


@routes.get("/data.json")
async def data(request):
    return web.json_response(
        request.config_dict["ds"]._data, headers={"Pragma": "no-cache"}
    )


@routes.get("/thumbnail/{sz}/{n}")
async def thumbnail(request):
    n = int(request.match_info.get("n", ""))
    sz = int(request.match_info.get("sz", ""))
    o = request.config_dict["ds"]._data[n]
    # TODO: factor out loading into util.py:
    img = Image.open(o["fn"])
    # TODO: exif rotation
    img = util.rgbify(img)
    x, y, w, h = o["x"], o["y"], o["w"], o["h"]
    img = img.crop((x, y, x + w, y + h))
    img = img.resize((sz, sz), Image.Resampling.BICUBIC)
    s = BytesIO()
    img.save(s, format="jpeg", quality=95)
    # TODO: caching
    return web.Response(body=s.getvalue(), content_type="image/jpeg")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8001)
    p.add_argument("--host", type=str, default="127.0.0.1", help="Bind address.")
    # p.add_argument("--size", type=int, default=512, help="Default output image size.")
    p.add_argument("dsfile", help="JSON dataset file to operate on.")
    args = p.parse_args()

    app = web.Application()
    app.add_routes(routes)
    app["args"] = args
    app["ds"] = Dataset(args.dsfile)
    web.run_app(app, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
