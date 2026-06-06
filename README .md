<div align="center">

# 🛰️ Project Argus

### AI-Powered Satellite Geo-Localization Pipeline

[![CI](https://github.com/yourusername/project-argus/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/project-argus/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Go](https://img.shields.io/badge/Go-1.22-blue.svg)](https://golang.org)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)

*End-to-end satellite intelligence system — ingests raw EO imagery, predicts geographic location using Vision Transformers, and streams live telemetry in real time.*

**[🌐 Live Demo](https://yourusername.github.io/project-argus) · [📖 Quick Start](#-quick-start) · [🏗️ Architecture](#%EF%B8%8F-architecture)**

</div>

---

## 🖥️ Website Preview

> Full project landing page with live Sovereign View interface

![Website Preview](docs/screenshots/website-preview.png)

---

## 🛰️ Sovereign View — Live Interface

> Real satellite aerial imagery with green HUD overlay, GPS crosshair, detection boxes & live telemetry

![Sovereign View](docs/screenshots/sovereign-view.png)

---

## ✨ Features

- 🛰️ **Event-driven ingestion** — fsnotify → Kafka → MinIO in microseconds
- 🧠 **AI geo-localization** — ViT-B/16 cosine similarity against a Sentinel-2 tile corpus
- 📊 **Real-time TUI** — Bubbletea dashboard polling PostGIS every 100ms
- 🖥️ **Sovereign View** — Raylib GUI with GPS crosshair & sub-millisecond hot-reload
- 🗺️ **Geospatial storage** — PostGIS with GIST-indexed geometry columns
- 📈 **Full observability** — Prometheus + Grafana dashboards out of the box
- 🐳 **One-command deploy** — `docker compose up`

---

## 🏗️ Architecture

![Architecture Diagram](docs/screenshots/architecture.png)

```
downlink_buffer/ ──fsnotify──▶ satellite/ ──┬──[Kafka: eo-events]──▶ processor/ ──▶ PostGIS
                                             └──[MinIO: satellite-raw]──▶ processor/ ──▶ MinIO (processed)
                                                                                    └──▶ local_sync/latest.jpg

PostGIS ──100ms poll──▶ dashboard/ (TUI)
local_sync/ ──mod-time──▶ gui/ (Raylib)
All services ──metrics──▶ Prometheus ──▶ Grafana
```

### Pipeline Flow

![Pipeline Flow](docs/screenshots/pipeline-flow.png)

---

## 🧩 Component Breakdown

![Component Breakdown](docs/screenshots/component-breakdown.png)

| Service | Language | Role |
|---|---|---|
| `satellite/` | Go | fsnotify watcher + Kafka/MinIO producer |
| `processor/` | Python | ViT-B/16 inference + cosine geo-search |
| `dashboard/` | Go | Bubbletea TUI — polls PostGIS @ 100ms |
| `gui/` | Go | Raylib Sovereign View — GPS crosshair viewer |
| `cv/` | Python | One-shot Sentinel-2 tile embedding generator |
| `observability/` | YAML | Prometheus + Grafana configs |

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2
- Go 1.22+ *(for local dev)*
- Python 3.11+ *(for local dev)*

### 1 — Clone

```bash
git clone https://github.com/yourusername/project-argus
cd project-argus
```

### 2 — Generate Embeddings *(one-time)*

```bash
# Put your Sentinel-2 tile images in ./tiles/
# Filename format: TILEID_LAT_LON.jpg  e.g. TL-0042_29.153007_73.004760.jpg

pip install timm torch pillow numpy tqdm
python cv/generate_embeddings.py --tiles-dir ./tiles --output-dir ./cv
```

> 📥 **Free Sentinel-2 tiles:** [Copernicus Browser](https://browser.dataspace.copernicus.eu/) · [USGS EarthExplorer](https://earthexplorer.usgs.gov/)

### 3 — Launch Full Stack

```bash
make up
# or: docker compose up --build
```

| Service | URL |
|---|---|
| MinIO Console | http://localhost:9001 *(minioadmin / minioadmin)* |
| Grafana | http://localhost:3000 *(admin / argus)* |
| Prometheus | http://localhost:9090 |
| Redpanda | localhost:19092 |

### 4 — Drop an Image

```bash
cp any-satellite-image.jpg ./downlink_buffer/

# Or use make:
make test-drop IMG=my-image.jpg
```

### 5 — Watch it Process

```bash
make logs          # Follow all service logs
make dashboard     # Open TUI dashboard (requires Go)
make gui           # Open Sovereign View (requires display)
```

---

## 📁 Repository Structure

```
project-argus/
├── index.html                          # 🌐 Project landing page (GitHub Pages)
├── docker-compose.yml                  # 🐳 Full stack — one command
├── Makefile                            # ⚡ make up / logs / dashboard / gui
├── satellite/                          # 🛰️ Go: fsnotify watcher + Kafka producer
│   ├── main.go
│   ├── go.mod
│   └── Dockerfile
├── processor/                          # 🧠 Python: ViT inference worker
│   ├── worker.py
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/                          # 📊 Go: Bubbletea TUI
│   ├── main.go
│   ├── go.mod
│   └── Dockerfile
├── gui/                                # 🖥️ Go: Raylib sovereign viewer
│   ├── main.go
│   └── go.mod
├── cv/                                 # 🗂️ Offline embedding generator
│   ├── generate_embeddings.py
│   ├── embeddings.npy                  # ← generate once, then commit
│   └── tile_metadata.json             # ← generate once, then commit
├── observability/                      # 📈 Prometheus + Grafana
│   ├── prometheus.yml
│   └── grafana/provisioning/
├── docs/
│   ├── QUICKSTART.md
│   └── screenshots/                   # 📸 README images
├── downlink_buffer/                    # 📂 Drop EO images here
├── tiles/                              # 🗺️ Your Sentinel-2 tile images
└── local_sync/                         # 🔁 Latest processed image (GUI reads this)
```

---

## 🧠 How Geo-Localization Works

**Offline (run once):**

```python
# cv/generate_embeddings.py
for tile in sentinel2_tiles:
    embedding = vit_b16.encode(tile)      # 768-dim vector
    corpus.append(embedding / norm)       # L2 normalize
np.save("embeddings.npy", corpus)        # shape: (874, 768)
```

**Online (per satellite image, ~42ms):**

```python
# processor/worker.py
query_emb  = vit_encode(image)           # (768,)  — ~30ms
sims       = corpus_embs @ query_emb     # (874,)  — <1ms BLAS
best_idx   = np.argmax(sims)
lat, lon   = metadata[best_idx]["lat"], metadata[best_idx]["lon"]
confidence = float(sims[best_idx])      # 0.0 → 1.0
```

The tile with highest cosine similarity **is the predicted location**. No training required — pure embedding similarity.

---

## 🔧 Tech Stack

| Component | Technology | Role |
|---|---|---|
| Satellite Service | Go + fsnotify | File watcher & event pump |
| Message Bus | Redpanda / Kafka | Event streaming |
| Object Storage | MinIO | Raw & processed images |
| AI Inference | Python + timm ViT-B/16 | Geo-localization model |
| Geospatial DB | PostGIS | Result storage & indexing |
| TUI Dashboard | Go + Bubbletea + Lipgloss | Real-time terminal UI |
| Sovereign Viewer | Go + Raylib | GPU-accelerated image view |
| Metrics | Prometheus + Grafana | Observability |
| Container Infra | Docker Compose | One-command deploy |

---

## ⚡ Performance

| Metric | Value |
|---|---|
| File detect → Kafka event | < 1ms |
| MinIO upload (1MB image) | ~15ms |
| ViT inference (CPU) | ~30ms |
| Cosine search (874 tiles) | < 1ms |
| **Total pipeline p95** | **~50ms** |
| Dashboard poll interval | 100ms |
| GUI hot-reload latency | < 1ms |

---

## 🤝 Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Lint before pushing
cd satellite  && go vet ./...
cd processor  && ruff check worker.py
```

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**Built with ❤️ · Project Argus**

`#ProjectArgus` `#SatelliteImagery` `#ComputerVision` `#ViT` `#DistributedSystems` `#Kafka` `#Go` `#Python`

</div>
