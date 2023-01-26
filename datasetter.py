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
import time

WWW = os.path.dirname(__file__)
logging.basicConfig(level=logging.INFO)
routes = web.RouteTableDef()


def now():
    return int(time.time())


@routes.get("/")
async def index_html(request):
    with open(f"{WWW}/index.html", "r") as f:
        s = f.read()
    return web.Response(
        text=s, content_type="text/html", headers={"Pragma": "no-cache"}
    )


@routes.get("/jquery.js")
async def jquery_js(request):
    with open(f"{WWW}/jquery.js", "r") as f:
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


@routes.post("/update")
async def update_receiver(request):
    received = await request.json()
    try:
        id = int(received["id"])
    except (KeyError, ValueError):
        return json_error('"id" must be int')
    try:
        obj = request.config_dict["ds"]._data[id]
    except KeyError:
        return json_error("specified id does not exist")
    if "caption" in received:
        try:
            caption = str(received["caption"])
        except KeyError:
            return json_error('"caption" was not provided')
        obj["caption"] = caption
        obj["manual_ts"] = now()
    if "skip" in received:
        obj["skip"] = received["skip"]
        obj["manual_ts"] = now()
    if "manual_crop" in received:
        for k in ["manual_crop", "x", "y", "w", "h"]:
            obj[k] = int(received[k])
        obj["manual_ts"] = now()
    request.config_dict["ds"].update(obj)
    return web.Response(status=204)


def json_error(reason):
    return web.json_response({"status": "error", "reason": reason})


@routes.get("/thumbnail/{n}/{sz}")
async def thumbnail_receiver(request):
    n = int(request.match_info.get("n", ""))
    sz = int(request.match_info.get("sz", ""))
    assert sz <= 1024
    img = request.config_dict["ds"].cropped_jpg(n, sz)
    return web.Response(body=img, content_type="image/jpeg")


@routes.get("/crop/{n}/{x}/{y}/{wh}/{sz}")
async def crop_receiver(request):
    n = int(request.match_info.get("n", ""))
    x = int(request.match_info.get("x", ""))
    y = int(request.match_info.get("y", ""))
    wh = int(request.match_info.get("wh", ""))
    sz = int(request.match_info.get("sz", ""))
    assert sz <= 1024
    assert x >= 0
    assert y >= 0
    img = request.config_dict["ds"].crop_preview(n, x, y, wh, sz)
    return web.Response(body=img, content_type="image/jpeg")


async def strip_headers(request, response):
    del response.headers["Server"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8001)
    p.add_argument("--host", type=str, default="127.0.0.1", help="Bind address.")
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
