"""
processor/worker.py
-------------------
Argus Processor: Kafka consumer → ViT inference → cosine geo-search → PostGIS write

Dependencies: confluent-kafka, timm, torch, pillow, numpy, psycopg2-binary, minio
"""

import json
import logging
import os
import time
from io import BytesIO

import numpy as np
import psycopg2
import torch
from confluent_kafka import Consumer, KafkaError
from minio import Minio
from PIL import Image
from timm import create_model
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform

# ── Config ──────────────────────────────────────────────────────────────
KAFKA_BROKERS   = os.getenv("KAFKA_BROKERS", "localhost:9092")
KAFKA_GROUP     = os.getenv("KAFKA_GROUP",   "argus-processor")
KAFKA_TOPIC     = os.getenv("KAFKA_TOPIC",   "eo-events")
MINIO_ADDR      = os.getenv("MINIO_ADDR",    "localhost:9000")
MINIO_KEY       = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET    = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_RAW       = os.getenv("MINIO_BUCKET_RAW",       "satellite-raw")
MINIO_PROCESSED = os.getenv("MINIO_BUCKET_PROCESSED",  "satellite-processed")
PG_DSN          = os.getenv("POSTGRES_DSN",  "host=localhost dbname=seopc user=argus password=argus")
EMBEDDINGS_PATH = os.getenv("EMBEDDINGS_PATH", "./cv/embeddings.npy")
TILE_META_PATH  = os.getenv("TILE_META_PATH",  "./cv/tile_metadata.json")
LOCAL_SYNC_DIR  = os.getenv("LOCAL_SYNC_DIR",   "./local_sync")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("argus.processor")


# ── Model ────────────────────────────────────────────────────────────────
def load_model():
    log.info("Loading ViT-B/16...")
    model = create_model("vit_base_patch16_224", pretrained=True, num_classes=0)
    model.eval()
    config = resolve_data_config({}, model=model)
    transform = create_transform(**config)
    log.info("✅ ViT-B/16 ready")
    return model, transform


def embed_image(model, transform, img: Image.Image) -> np.ndarray:
    tensor = transform(img.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        embedding = model(tensor).squeeze(0).numpy()
    return embedding / (np.linalg.norm(embedding) + 1e-8)


# ── Cosine geo-search ─────────────────────────────────────────────────────
def load_corpus(embeddings_path: str, meta_path: str):
    corpus = np.load(embeddings_path)   # shape: (N, 768)
    with open(meta_path) as f:
        meta = json.load(f)             # list of {tile_id, lat, lon, name}
    log.info(f"✅ Corpus loaded: {corpus.shape[0]} tiles")
    return corpus, meta


def cosine_search(query: np.ndarray, corpus: np.ndarray, meta: list, top_k: int = 1):
    sims = corpus @ query               # (N,)
    idx = int(np.argmax(sims))
    return meta[idx], float(sims[idx])


# ── PostGIS ───────────────────────────────────────────────────────────────
def init_db(dsn: str):
    conn = psycopg2.connect(dsn)
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS seopc_metadata (
                id            SERIAL PRIMARY KEY,
                object_key    TEXT NOT NULL,
                tile_id       TEXT,
                lat           DOUBLE PRECISION,
                lon           DOUBLE PRECISION,
                confidence    DOUBLE PRECISION,
                processing_ms INTEGER,
                created_at    TIMESTAMPTZ DEFAULT NOW(),
                geom          GEOMETRY(Point, 4326)
            );
            CREATE INDEX IF NOT EXISTS idx_seopc_geom ON seopc_metadata USING GIST(geom);
        """)
    conn.commit()
    log.info("✅ PostGIS schema ready")
    return conn


def insert_result(conn, object_key, tile_id, lat, lon, confidence, processing_ms):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO seopc_metadata
                (object_key, tile_id, lat, lon, confidence, processing_ms, geom)
            VALUES
                (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        """, (object_key, tile_id, lat, lon, confidence, processing_ms, lon, lat))
    conn.commit()


# ── Main loop ─────────────────────────────────────────────────────────────
def main():
    model, transform = load_model()
    corpus, meta = load_corpus(EMBEDDINGS_PATH, TILE_META_PATH)
    conn = init_db(PG_DSN)

    mc = Minio(MINIO_ADDR, access_key=MINIO_KEY, secret_key=MINIO_SECRET, secure=False)
    os.makedirs(LOCAL_SYNC_DIR, exist_ok=True)
    os.makedirs(MINIO_PROCESSED, exist_ok=True)

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BROKERS,
        "group.id":          KAFKA_GROUP,
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([KAFKA_TOPIC])
    log.info(f"👂 Consuming from topic: {KAFKA_TOPIC}")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    log.error(f"Kafka error: {msg.error()}")
                continue

            event = json.loads(msg.value())
            object_key = event["object_key"]
            log.info(f"📥 Processing: {object_key}")
            t0 = time.time()

            try:
                # Fetch from MinIO
                response = mc.get_object(MINIO_RAW, object_key)
                img = Image.open(BytesIO(response.read()))
                response.close()

                # Embed + search
                query = embed_image(model, transform, img)
                best_tile, confidence = cosine_search(query, corpus, meta)
                processing_ms = int((time.time() - t0) * 1000)

                lat, lon = best_tile["lat"], best_tile["lon"]
                tile_id = best_tile["tile_id"]

                log.info(f"🗺️  GEO-LOCK [{processing_ms}ms] → {tile_id} "
                         f"lat={lat:.6f} lon={lon:.6f} confidence={confidence:.4f}")

                # Write to PostGIS
                insert_result(conn, object_key, tile_id, lat, lon, confidence, processing_ms)

                # Upload processed image
                buf = BytesIO()
                img.save(buf, format="JPEG", quality=90)
                buf.seek(0)
                processed_key = object_key.replace(MINIO_RAW, "processed")
                mc.put_object(MINIO_PROCESSED, processed_key, buf, length=buf.getbuffer().nbytes,
                              content_type="image/jpeg")

                # Atomic local sync for Raylib GUI
                local_path = os.path.join(LOCAL_SYNC_DIR, "latest_processed.jpg")
                tmp_path = local_path + ".tmp"
                img.save(tmp_path, format="JPEG", quality=90)
                os.replace(tmp_path, local_path)

            except Exception as e:
                log.error(f"Processing error for {object_key}: {e}", exc_info=True)

    except KeyboardInterrupt:
        log.info("Shutting down...")
    finally:
        consumer.close()
        conn.close()


if __name__ == "__main__":
    main()
