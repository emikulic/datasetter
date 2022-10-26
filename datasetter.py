#!/usr/bin/env python3
"""
Web-based dataset editing.
"""
import json
from PIL import Image
import argparse
import os
from util import Dataset
import util
from aiohttp import web
import aiohttp
import logging
from io import BytesIO

# import urllib.parse


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


@routes.post("/caption")
async def caption_receiver(request):
    received = await request.json()
    try:
        id = int(received["id"])
    except (KeyError, ValueError):
        return json_error('"id" must be int')
    try:
        caption = str(received["caption"])
    except KeyError:
        return json_error('"caption" was not provided')
    try:
        obj = request.config_dict["ds"]._data[id]
    except KeyError:
        return json_error("specified id does not exist")
    obj["caption"] = caption
    request.config_dict["ds"].add(obj)
    return web.Response(status=204)


def json_error(reason):
    return web.json_response({"status": "error", "reason": reason})


@routes.get("/thumbnail/{sz}/{n}")
async def thumbnail(request):
    n = int(request.match_info.get("n", ""))
    sz = int(request.match_info.get("sz", ""))
    assert sz <= 1024
    img = request.config_dict["ds"].cropped_jpg(n, sz)
    return web.Response(body=img, content_type="image/jpeg")


async def strip_headers(request, response):
    del response.headers["Server"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8001)
    p.add_argument("--host", type=str, default="127.0.0.1", help="Bind address.")
    # p.add_argument("--size", type=int, default=512, help="Default output image size.")
    p.add_argument("dsfile", help="JSON dataset file to operate on.")
    args = p.parse_args()

    app = web.Application()
    app.on_response_prepare.append(strip_headers)
    app.add_routes(routes)
    app["args"] = args
    app["ds"] = Dataset(args.dsfile)
    web.run_app(app, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
