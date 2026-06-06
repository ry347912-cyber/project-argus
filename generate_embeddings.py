"""
cv/generate_embeddings.py
--------------------------
One-shot Sentinel-2 tile embedding generator.
Run once, commit embeddings.npy + tile_metadata.json, never run again.

Usage:
    python cv/generate_embeddings.py --tiles-dir ./tiles --output-dir ./cv

The tiles directory should contain JPEG/PNG satellite images named:
    <tile_id>_<lat>_<lon>.jpg   e.g.  TL-0042_29.153007_73.004760.jpg
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from timm import create_model
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform
from tqdm import tqdm


def parse_filename(fname: str):
    """Extract tile_id, lat, lon from filename like TL-0042_29.153007_73.004760.jpg"""
    stem = Path(fname).stem
    parts = stem.split("_")
    if len(parts) < 3:
        return stem, 0.0, 0.0
    try:
        lat = float(parts[-2])
        lon = float(parts[-1])
        tile_id = "_".join(parts[:-2])
    except ValueError:
        lat, lon, tile_id = 0.0, 0.0, stem
    return tile_id, lat, lon


def main():
    parser = argparse.ArgumentParser(description="Generate Sentinel-2 tile embeddings")
    parser.add_argument("--tiles-dir", default="./tiles", help="Directory of tile images")
    parser.add_argument("--output-dir", default="./cv", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    tiles_dir = Path(args.tiles_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect tile files
    exts = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
    tile_files = sorted([f for f in tiles_dir.iterdir() if f.suffix.lower() in exts])
    if not tile_files:
        print(f"❌ No tile images found in {tiles_dir}")
        return

    print(f"📁 Found {len(tile_files)} tiles")

    # Load ViT model
    print("Loading ViT-B/16...")
    model = create_model("vit_base_patch16_224", pretrained=True, num_classes=0)
    model.eval()
    config = resolve_data_config({}, model=model)
    transform = create_transform(**config)

    # Generate embeddings
    embeddings = []
    metadata = []
    t0 = time.time()

    for i, tile_path in enumerate(tqdm(tile_files, desc="Embedding tiles")):
        try:
            img = Image.open(tile_path).convert("RGB")
            tensor = transform(img).unsqueeze(0)
            with torch.no_grad():
                emb = model(tensor).squeeze(0).numpy()
            emb = emb / (np.linalg.norm(emb) + 1e-8)
            embeddings.append(emb)

            tile_id, lat, lon = parse_filename(tile_path.name)
            metadata.append({
                "tile_id": tile_id,
                "lat": lat,
                "lon": lon,
                "name": tile_path.stem,
                "file": tile_path.name,
            })
        except Exception as e:
            print(f"⚠️  Skipping {tile_path.name}: {e}")

    elapsed = time.time() - t0
    corpus = np.array(embeddings, dtype=np.float32)

    # Save
    emb_path = output_dir / "embeddings.npy"
    meta_path = output_dir / "tile_metadata.json"
    np.save(emb_path, corpus)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Done in {elapsed:.1f}s")
    print(f"   Corpus shape : {corpus.shape}")
    print(f"   Embeddings   : {emb_path}")
    print(f"   Metadata     : {meta_path}")


if __name__ == "__main__":
    main()
