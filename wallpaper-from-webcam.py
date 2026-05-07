#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

CONFIG_DIR = Path.home() / ".config" / "cosmic" / "com.system76.CosmicBackground" / "v1"
CONFIG_FILE = CONFIG_DIR / "all"
SAVE_DIR = Path.home() / ".local" / "share" / "wallpaper-thing"
RESOLUTION = "hu"


def get_latest_image_info(webcam_name: str) -> tuple[str, str]:
    url = f"https://www.foto-webcam.eu/webcam/{webcam_name}/"
    resp = requests.get(url)
    resp.raise_for_status()

    match = re.search(r'wcmain\.preloadData\s*=\s*new\s+Object\((\{.*?\})\s*\)\s*;', resp.text, re.DOTALL)
    if not match:
        raise ValueError("Could not find preloadData in page")

    data = json.loads(match.group(1))
    img_path = data["hugeimg"]  # e.g. "2026/05/07/0820_hu.jpg"
    base_img = img_path.replace("_hu.jpg", "")
    hash_val = data["h"]
    return base_img, hash_val


def download_image(webcam_name: str, base_img: str, hash_val: str, output_path: Path):
    dl_url = (
        f"https://www.foto-webcam.eu/webcam/include/dlimg.php"
        f"?wc={webcam_name}&img={base_img}&h={hash_val}&res={RESOLUTION}"
    )
    print(f"Downloading: {dl_url}")
    resp = requests.get(dl_url)
    resp.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    print(f"Saved to: {output_path}")


def set_cosmic_wallpaper(image_path: Path):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    ron = (
        "(\n"
        '    filter_by_theme: false,\n'
        "    filter_method: Lanczos,\n"
        '    output: "all",\n'
        "    rotation_frequency: 300,\n"
        "    sampling_method: Alphanumeric,\n"
        "    scaling_mode: Zoom,\n"
        f'    source: Path("{str(image_path)}"),\n'
        ")\n"
    )

    with open(CONFIG_FILE, "w") as f:
        f.write(ron)
    print(f"Updated COSMIC wallpaper config: {CONFIG_FILE}")

    subprocess.run(["pkill", "-f", "cosmic-bg"], check=False)
    print("Restarted cosmic-bg")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <webcam-name> [output-image-path]")
        print("Example: python wallpaper-from-webcam.py malcesine")
        sys.exit(1)

    webcam_name = sys.argv[1]
    timestamp = time.strftime("%Y%m%d-%H%M")
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = SAVE_DIR / webcam_name / f"{timestamp}.jpg"

    print(f"Webcam: {webcam_name}")
    base_img, hash_val = get_latest_image_info(webcam_name)
    print(f"Latest image: {base_img} (hash: {hash_val})")

    download_image(webcam_name, base_img, hash_val, output_path)
    set_cosmic_wallpaper(output_path)
    print("Done!")


if __name__ == "__main__":
    main()
