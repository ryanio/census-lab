"""Collect small public token stills for the offline Pages card renderer."""
import argparse
import hashlib
import io
import json
import subprocess
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageOps


def thumbnail(url, cache):
    target = cache / (hashlib.sha256(url.encode()).hexdigest() + ".webp")
    if target.exists():
        return target
    for attempt in range(3):
        try:
            with urlopen(url, timeout=30) as response:
                raw = response.read()
            if url.split("?")[0].lower().endswith(".svg"):
                raw = subprocess.check_output(["rsvg-convert", "-a", "-w", "224", "-h", "224"], input=raw, timeout=40)
            try:
                image = Image.open(io.BytesIO(raw)).convert("RGBA")
            except OSError:
                with tempfile.NamedTemporaryFile(suffix=Path(url).suffix) as source:
                    source.write(raw)
                    source.flush()
                    frame = subprocess.check_output([
                        "ffmpeg", "-v", "error", "-i", source.name, "-frames:v", "1",
                        "-vf", "scale=224:224:force_original_aspect_ratio=decrease",
                        "-f", "image2pipe", "-vcodec", "png", "-"
                    ], timeout=40)
                image = Image.open(io.BytesIO(frame)).convert("RGBA")
            thumb = ImageOps.contain(image, (224, 224))
            canvas = Image.new("RGB", (224, 224), "#f4e6d7")
            canvas.paste(thumb, ((224-thumb.width)//2, (224-thumb.height)//2), thumb)
            tmp = target.with_suffix(".tmp")
            canvas.save(tmp, format="WEBP", quality=78)
            tmp.replace(target)
            return target
        except (OSError, subprocess.SubprocessError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("edition", type=Path)
    parser.add_argument("--cache", type=Path, default=Path(".cache/lineup-stills"))
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    examples = json.loads((args.edition / "trait-examples.json").read_text())
    urls = sorted({t["image"] for tokens in examples.values() for t in tokens})
    with ThreadPoolExecutor(max_workers=10) as pool:
        files = dict(zip(urls, pool.map(lambda url: thumbnail(url, args.cache), urls)))
    destination = args.edition / "lineup-art"
    destination.mkdir(exist_ok=True)
    for slug, tokens in examples.items():
        path = destination / (slug + ".zip")
        tmp = path.with_suffix(".tmp")
        with zipfile.ZipFile(tmp, "w") as archive:
            for token in tokens:
                entry = zipfile.ZipInfo(str(int(token["token"])) + ".webp")
                archive.writestr(entry, files[token["image"]].read_bytes())
        tmp.replace(path)


if __name__ == "__main__":
    main()
