<div align="center">

# 🛰️ Project Argus

### AI-Powered Satellite Geo-Localization Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Go](https://img.shields.io/badge/Go-1.22-blue.svg)](https://golang.org)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)

*End-to-end satellite intelligence — ingests raw EO imagery, predicts geographic location using Vision Transformers, streams live telemetry in real time.*

**[🌐 Live Demo](https://ry347912-cyber.github.io/project-argus) · [📖 Quick Start](#-quick-start)**

</div>

---

## 🖥️ Website Preview

![Website Preview](Screenshot%202026-06-06%20222725.png)

---

## 🛰️ Sovereign View — Live Interface

> Real satellite aerial imagery with green HUD overlay, GPS crosshair, detection boxes & live telemetry

![Sovereign View](Screenshot%202026-06-06%20222540.png)

---

## 🏗️ Architecture

![Architecture](Screenshot%202026-06-06%20222618.png)

---

## 🧩 Pipeline Flow

![Pipeline Flow](Screenshot%202026-06-06%20222602.png)

---

## 📦 Component Breakdown

![Components](Screenshot%202026-06-06%20222636.png)

---

## ✨ Features

- 🛰️ **Event-driven ingestion** — fsnotify → Kafka → MinIO in microseconds
- 🧠 **AI geo-localization** — ViT-B/16 cosine similarity against Sentinel-2 tile corpus
- 📊 **Real-time TUI** — Bubbletea dashboard polling PostGIS every 100ms
- 🖥️ **Sovereign View** — Raylib GUI with GPS crosshair & sub-millisecond hot-reload
- 🗺️ **Geospatial storage** — PostGIS with GIST-indexed geometry columns
- 📈 **Full observability** — Prometheus + Grafana dashboards out of the box
- 🐳 **One-command deploy** — `docker compose up`

---

## 🚀 Quick Start

### 1 — Clone

```bash
git clone https://github.com/ry347912-cyber/project-argus
cd project-argus
```

### 2 — Generate Embeddings *(one-time)*

```bash
# Put your Sentinel-2 tile images in ./tiles/
# Filename: TILEID_LAT_LON.jpg  e.g. TL-0042_29.153007_73.004760.jpg

pip install timm torch pillow numpy tqdm
python generate_embeddings.py --tiles-dir ./tiles --output-dir .
```

> 📥 **Free Sentinel-2 tiles:** [Copernicus Browser](https://browser.dataspace.copernicus.eu/)

### 3 — Launch Full Stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| MinIO Console | http://localhost:9001 *(minioadmin / minioadmin)* |
| Grafana | http://localhost:3000 *(admin / argus)* |
| Prometheus | http://localhost:9090 |

### 4 — Drop an Image & Watch it Process

```bash
cp satellite-image.jpg ./downlink_buffer/
docker compose logs -f processor
```

---

## 🔧 Tech Stack

| Component | Technology | Role |
|---|---|---|
| Satellite Service | Go + fsnotify | File watcher & event pump |
| Message Bus | Redpanda / Kafka | Event streaming |
| Object Storage | MinIO | Raw & processed images |
| AI Inference | Python + timm ViT-B/16 | Geo-localization model |
| Geospatial DB | PostGIS | Result storage & indexing |
| TUI Dashboard | Go + Bubbletea | Real-time terminal UI |
| Sovereign Viewer | Go + Raylib | GPU-accelerated image view |
| Metrics | Prometheus + Grafana | Observability |
| Containers | Docker Compose | One-command deploy |

---

## 🧠 How Geo-Localization Works

```python
# Online inference per image (~42ms total)
query_emb  = vit_encode(image)           # 768-dim vector  (~30ms)
sims       = corpus_embs @ query_emb     # cosine similarity (<1ms)
best_idx   = np.argmax(sims)
lat, lon   = metadata[best_idx]["lat"], metadata[best_idx]["lon"]
confidence = float(sims[best_idx])       # 0.0 → 1.0
```

The tile with **highest cosine similarity = predicted location**. No extra training needed.

---

## ⚡ Performance

| Metric | Value |
|---|---|
| File detect → Kafka event | < 1ms |
| MinIO upload (1MB) | ~15ms |
| ViT inference (CPU) | ~30ms |
| Cosine search (874 tiles) | < 1ms |
| **Total pipeline p95** | **~50ms** |
| Dashboard poll | 100ms |

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**Built with ❤️ by ry347912-cyber**

`#ProjectArgus` `#SatelliteImagery` `#ComputerVision` `#ViT` `#Kafka` `#Go` `#Python`

</div>
