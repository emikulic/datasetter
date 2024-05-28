#!/usr/bin/env python3
"""
BLIP3 as a web service.
"""
# pip install flash-attn einops einops-exts
# pip install git+https://github.com/huggingface/transformers # need 4.41.0.dev0
import logging

fmt = "%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
logging.basicConfig(format=fmt, level=logging.INFO)
logging.info("importing")
import os

if "TRANSFORMERS_OFFLINE" not in os.environ:
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
import argparse
from PIL import Image
from transformers import (
    AutoModelForVision2Seq,
    AutoTokenizer,
    AutoImageProcessor,
    StoppingCriteria,
)
import torch
from aiohttp import web

routes = web.RouteTableDef()


def apply_prompt_template(prompt):
    s = (
        "<|system|>\nA chat between a curious user and an artificial intelligence assistant. "
        "The assistant gives helpful, detailed, and polite answers to the user's questions.<|end|>\n"
        f"<|user|>\n<image>\n{prompt}<|end|>\n<|assistant|>\n"
    )
    return s


class EosListStoppingCriteria(StoppingCriteria):
    def __init__(self, eos_sequence=[32007]):
        self.eos_sequence = eos_sequence

    def __call__(
        self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs
    ) -> bool:
        last_ids = input_ids[:, -len(self.eos_sequence) :].tolist()
        return self.eos_sequence in last_ids


@routes.post("/blip3")
async def blip3(request):
    device = request.config_dict["device"]
    image_processor = request.config_dict["image_processor"]
    tokenizer = request.config_dict["tokenizer"]
    model = request.config_dict["model"]

    post = await request.post()
    q = post["query"]
    img = post["img"].file
    img = Image.open(img)
    logging.info(f"query={q!r} img={img!r}")
    img = img.convert("RGB")
    inputs = image_processor([img], return_tensors="pt", image_aspect_ratio="anyres")
    prompt = apply_prompt_template(q)
    language_inputs = tokenizer([prompt], return_tensors="pt")
    inputs.update(language_inputs)
    inputs = {name: tensor.to(device) for name, tensor in inputs.items()}
    generated_text = model.generate(
        **inputs,
        image_size=[img.size],
        pad_token_id=tokenizer.pad_token_id,
        do_sample=False,
        max_new_tokens=768,
        top_p=None,
        num_beams=1,
        stopping_criteria=[EosListStoppingCriteria()],
    )
    prediction = tokenizer.decode(generated_text[0], skip_special_tokens=True).split(
        "<|end|>"
    )[0]
    logging.info(f"prediction={prediction!r}")
    return web.Response(text=prediction, content_type="text/plain")


async def strip_headers(request, response):
    del response.headers["Server"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8003)
    p.add_argument("--host", type=str, default="127.0.0.1", help="Bind address.")
    args = p.parse_args()

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    logging.info(f"device is {device}")

    logging.info("***********************************************************")
    logging.info("* To allow model downloads, use: env TRANSFORMERS_OFFLINE=0")
    logging.info("***********************************************************")

    logging.info("loading model")
    # Downloads 18GB to ~/.cache/huggingface/hub/models--Salesforce...
    model_name_or_path = "Salesforce/xgen-mm-phi3-mini-instruct-r-v1"
    model = AutoModelForVision2Seq.from_pretrained(
        model_name_or_path, trust_remote_code=True
    )
    model = model.to(device)
    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path, trust_remote_code=True, use_fast=False, legacy=False
    )
    image_processor = AutoImageProcessor.from_pretrained(
        model_name_or_path, trust_remote_code=True
    )
    tokenizer = model.update_special_tokens(tokenizer)

    app = web.Application(client_max_size=100 * 1024 * 1024)
    app.on_response_prepare.append(strip_headers)
    app.add_routes(routes)

    app["device"] = device
    app["image_processor"] = image_processor
    app["tokenizer"] = tokenizer
    app["model"] = model

    logging.info("serving")
    web.run_app(app, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
