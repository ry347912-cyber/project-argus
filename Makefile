.PHONY: all up down build logs clean embeddings

# Start full stack
up:
	docker compose up --build -d
	@echo "✅ Stack up! Grafana: http://localhost:3000 | MinIO: http://localhost:9001"

# Stop stack
down:
	docker compose down

# Stop and remove volumes
clean:
	docker compose down -v
	@echo "✅ All volumes removed"

# View logs
logs:
	docker compose logs -f

# Rebuild specific service
build-%:
	docker compose build $*
	docker compose up -d $*

# Generate embeddings (run once)
embeddings:
	pip install timm torch pillow numpy tqdm
	python cv/generate_embeddings.py --tiles-dir ./tiles --output-dir ./cv
	@echo "✅ Embeddings saved to cv/embeddings.npy"

# Run TUI dashboard locally
dashboard:
	cd dashboard && go run main.go

# Run Sovereign View GUI locally  
gui:
	cd gui && go run main.go

# Drop a test image into downlink buffer
test-drop:
	@if [ -z "$(IMG)" ]; then echo "Usage: make test-drop IMG=path/to/image.jpg"; exit 1; fi
	cp $(IMG) ./downlink_buffer/test_$(shell date +%s).jpg
	@echo "✅ Image dropped into downlink buffer"

# Show status of all services
status:
	docker compose ps

help:
	@echo ""
	@echo "  Project Argus — Available Commands"
	@echo "  ──────────────────────────────────"
	@echo "  make up           Start full stack"
	@echo "  make down         Stop stack"
	@echo "  make clean        Stop + remove volumes"
	@echo "  make logs         Tail all logs"
	@echo "  make embeddings   Generate ViT embeddings (one-time)"
	@echo "  make dashboard    Run TUI locally"
	@echo "  make gui          Run Sovereign View locally"
	@echo "  make test-drop IMG=x.jpg  Drop test image"
	@echo "  make status       Show service status"
	@echo ""
