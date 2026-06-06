# ⚡ Project Argus — Quick Start

## 5 minutes to a running pipeline

### Step 1 — Clone
```bash
git clone https://github.com/yourusername/project-argus
cd project-argus
```

### Step 2 — Generate embeddings (requires your tile images)
```bash
# Put Sentinel-2 tiles in ./tiles/
# Naming convention: TILEID_LAT_LON.jpg
mkdir tiles
# ... copy your images ...

pip install timm torch pillow numpy tqdm
python cv/generate_embeddings.py
# → produces cv/embeddings.npy and cv/tile_metadata.json
```

**Don't have tiles?** Download free Sentinel-2 imagery from:
- https://browser.dataspace.copernicus.eu/
- https://earthexplorer.usgs.gov/

### Step 3 — Start everything
```bash
docker compose up --build -d
```

Wait ~30s for all services to be healthy:
```bash
docker compose ps
```

### Step 4 — Drop an image
```bash
cp any-satellite-image.jpg ./downlink_buffer/test_01.jpg
```

### Step 5 — Watch it process
```bash
# Follow processor logs
docker compose logs -f processor

# Open the TUI dashboard (requires Go)
cd dashboard && POSTGRES_DSN="host=localhost dbname=seopc user=argus password=argus sslmode=disable" go run main.go
```

### Step 6 — View dashboards
- **Grafana**: http://localhost:3000 (admin / argus)
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)
- **Prometheus**: http://localhost:9090

### Step 7 — Run the Sovereign View GUI (optional, needs display)
```bash
cd gui && LOCAL_SYNC_PATH=./local_sync/latest_processed.jpg go run main.go
```

---

## Tear down
```bash
docker compose down -v   # -v removes volumes (data)
```
