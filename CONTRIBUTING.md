# Contributing to Project Argus

## Getting Started

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run tests: `make test` (coming soon)
5. Push and open a PR

## Code Style

- **Go**: `gofmt` + `go vet` before committing
- **Python**: `ruff check` for linting
- **Commits**: Conventional commits preferred (`feat:`, `fix:`, `docs:`)

## Project Structure

```
satellite/   → Go: fsnotify watcher + Kafka/MinIO producer
processor/   → Python: ViT inference + PostGIS writer
dashboard/   → Go: Bubbletea TUI
gui/         → Go: Raylib sovereign viewer
cv/          → Python: offline embedding generator
observability/ → Prometheus + Grafana configs
```

## Running Locally

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for full setup guide.

## Issues

Use GitHub Issues for bugs and feature requests. Please include:
- OS / Docker version
- Steps to reproduce
- Expected vs actual behavior
