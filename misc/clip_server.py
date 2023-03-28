#!/usr/bin/env python3
"""
CLIP in a webserver.
"""
import logging

fmt = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
logging.basicConfig(format=fmt, level=logging.DEBUG)
logging.info("importing")
import os

if "TRANSFORMERS_OFFLINE" not in os.environ:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
import argparse
from PIL import Image
import torch
import transformers
from aiohttp import web
import aiohttp

logging.basicConfig(level=logging.INFO)
routes = web.RouteTableDef()


@routes.post("/clip")
async def clip_receiver(request):
    clip_processor = request.config_dict["clip_processor"]
    clip_image_model = request.config_dict["clip_image_model"]
    device = request.config_dict["device"]
    post = await request.post()
    data = post["file"].file
    img = Image.open(data)
    logging.info(f"{img!r}")
    with torch.no_grad():  # matters
        pixel_values = clip_processor(img).pixel_values[0]
        pixel_values = torch.tensor(pixel_values).to(device)
        img_embed = clip_image_model(pixel_values.unsqueeze(0)).image_embeds[0]
        # img_embed.shape is torch.Size([768])
    img_embed = img_embed.cpu().numpy().tobytes()
    return web.Response(body=img_embed, content_type="application/octet-stream")


async def strip_headers(request, response):
    del response.headers["Server"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8002)
    p.add_argument("--host", type=str, default="127.0.0.1", help="Bind address.")
    args = p.parse_args()

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    logging.info(f"device is {device}")

    logging.info("***********************************************************")
    logging.info("* To allow model downloads, use: env TRANSFORMERS_OFFLINE=0")
    logging.info("***********************************************************")

    # Downloads 1.6GB to ~/.cache/huggingface/hub/models--openai--clip-vit-large-patch14
    clip_version = "openai/clip-vit-large-patch14"  # This is what sd1.5 uses.
    logging.info("loading CLIP processor")
    clip_processor = transformers.CLIPImageProcessor()
    logging.info(clip_processor)
    logging.info("loading CLIP image model")
    clip_image_model = transformers.CLIPVisionModelWithProjection.from_pretrained(
        clip_version
    ).to(device)
    tokenizer = transformers.AutoTokenizer.from_pretrained(clip_version)
    logging.info("done loading")

    app = web.Application(client_max_size=1024 * 1024 * 100)
    app.on_response_prepare.append(strip_headers)
    app.add_routes(routes)
    app["clip_processor"] = clip_processor
    app["clip_image_model"] = clip_image_model
    app["device"] = device
    web.run_app(app, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
