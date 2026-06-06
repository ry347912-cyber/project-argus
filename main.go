package main

import (
	"fmt"
	"log"
	"os"
	"time"

	rl "github.com/gen2brain/raylib-go/raylib"
)

const (
	ScreenW      = 1280
	ScreenH      = 720
	TargetFPS    = 120
	PollInterval = 100 * time.Millisecond
)

var (
	localSyncPath = envOr("LOCAL_SYNC_PATH", "./local_sync/latest_processed.jpg")

	colorGreen = rl.Color{R: 0, G: 255, B: 136, A: 255}
	colorAmber = rl.Color{R: 255, G: 179, B: 0, A: 255}
	colorCyan  = rl.Color{R: 0, G: 229, B: 255, A: 255}
	colorRed   = rl.Color{R: 255, G: 59, B: 59, A: 255}
	colorDark  = rl.Color{R: 2, G: 13, B: 10, A: 255}
	colorDim   = rl.Color{R: 74, G: 122, B: 98, A: 180}
)

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

type State struct {
	texture   rl.Texture2D
	modTime   time.Time
	loaded    bool
	frameNum  uint64
	lastPoll  time.Time
	lat       float64
	lon       float64
	confidence float64
	tileID    string
	secure    bool
}

func main() {
	rl.SetConfigFlags(rl.FlagWindowResizable | rl.FlagMsaa4xHint)
	rl.InitWindow(ScreenW, ScreenH, "SEOPC — Sovereign View")
	defer rl.CloseWindow()
	rl.SetTargetFPS(TargetFPS)

	s := &State{
		lat:       29.153007,
		lon:       73.004760,
		confidence: 0.9821,
		tileID:    "SENTINEL-2-TL-0042",
		secure:    true,
	}

	// Load initial texture if file exists
	if _, err := os.Stat(localSyncPath); err == nil {
		s.texture = rl.LoadTexture(localSyncPath)
		s.loaded = true
		s.modTime = fileModTime(localSyncPath)
	}

	var rotation float32
	startTime := time.Now()

	for !rl.WindowShouldClose() {
		s.frameNum++
		rotation += 0.5
		elapsed := time.Since(startTime).Seconds()

		// Poll for new image
		if time.Since(s.lastPoll) >= PollInterval {
			s.lastPoll = time.Now()
			if mt := fileModTime(localSyncPath); mt.After(s.modTime) {
				if s.loaded {
					rl.UnloadTexture(s.texture)
				}
				s.texture = rl.LoadTexture(localSyncPath)
				s.loaded = true
				s.modTime = mt
				log.Printf("🔄 Image refreshed: %s", localSyncPath)
			}
		}

		rl.BeginDrawing()
		rl.ClearBackground(colorDark)

		// ── Draw satellite image ──────────────────────────────────────────
		if s.loaded {
			sw := float32(rl.GetScreenWidth())
			sh := float32(rl.GetScreenHeight())
			scale := min32(sw/float32(s.texture.Width), sh/float32(s.texture.Height))
			iw := float32(s.texture.Width) * scale
			ih := float32(s.texture.Height) * scale
			ix := (sw - iw) / 2
			iy := (sh - ih) / 2
			rl.DrawTextureEx(s.texture,
				rl.Vector2{X: ix, Y: iy}, 0, scale, rl.White)
		} else {
			// Placeholder grid
			for y := 0; y < rl.GetScreenHeight(); y += 40 {
				rl.DrawLine(0, int32(y), int32(rl.GetScreenWidth()), int32(y), colorDim)
			}
			for x := 0; x < rl.GetScreenWidth(); x += 40 {
				rl.DrawLine(int32(x), 0, int32(x), int32(rl.GetScreenHeight()), colorDim)
			}
			rl.DrawText("AWAITING DOWNLINK...", int32(rl.GetScreenWidth()/2-140), int32(rl.GetScreenHeight()/2), 20, colorDim)
		}

		// ── Scan line ─────────────────────────────────────────────────────
		scanY := int32(float64(rl.GetScreenHeight()) * (elapsed - float64(int(elapsed))))
		rl.DrawRectangle(0, scanY, int32(rl.GetScreenWidth()), 2,
			rl.Color{R: 0, G: 255, B: 136, A: 40})

		// ── Crosshair ─────────────────────────────────────────────────────
		cx := int32(rl.GetScreenWidth() / 2)
		cy := int32(rl.GetScreenHeight() / 2)
		rl.DrawLine(cx-30, cy, cx+30, cy, colorGreen)
		rl.DrawLine(cx, cy-30, cx, cy+30, colorGreen)
		rl.DrawRectangleLines(cx-20, cy-20, 40, 40, colorGreen)
		// Rotating outer square
		rot := rl.Vector2{X: float32(cx), Y: float32(cy)}
		_ = rot
		_ = rotation

		// ── Title bar ─────────────────────────────────────────────────────
		rl.DrawRectangle(0, 0, int32(rl.GetScreenWidth()), 28,
			rl.Color{R: 0, G: 20, B: 10, A: 220})
		rl.DrawLine(0, 28, int32(rl.GetScreenWidth()), 28, colorGreen)
		rl.DrawText("SEOPC — SOVEREIGN VIEW", 10, 6, 16, colorGreen)
		rl.DrawText(fmt.Sprintf("FPS: %d  FRAME: %d", rl.GetFPS(), s.frameNum),
			int32(rl.GetScreenWidth()-180), 6, 14, colorDim)

		// ── Secure connection banner ───────────────────────────────────────
		if s.secure {
			rl.DrawText("◈ SECURE CONNECTION", 10, 38, 14, colorRed)
		}

		// ── HUD: top-left ─────────────────────────────────────────────────
		hudX, hudY := int32(10), int32(60)
		rl.DrawText("🛰 ARGUS-1", hudX, hudY, 14, colorGreen)
		rl.DrawText(fmt.Sprintf("STATUS: NOMINAL"), hudX, hudY+18, 12, colorGreen)
		rl.DrawText(fmt.Sprintf("TILE:   %s", s.tileID), hudX, hudY+34, 12, colorGreen)

		// ── HUD: top-right ────────────────────────────────────────────────
		confText := fmt.Sprintf("ViT CONF: %.2f%%", s.confidence*100)
		rl.DrawText(confText, int32(rl.GetScreenWidth()-200), 38, 14, colorCyan)

		// ── Status bar ────────────────────────────────────────────────────
		sh := int32(rl.GetScreenHeight())
		rl.DrawRectangle(0, sh-26, int32(rl.GetScreenWidth()), 26,
			rl.Color{R: 0, G: 20, B: 10, A: 220})
		rl.DrawLine(0, sh-26, int32(rl.GetScreenWidth()), sh-26, colorGreen)

		geoText := fmt.Sprintf("▶ TARGET GEO-LOCKED   LAT: %.6f   LON: %.6f", s.lat, s.lon)
		rl.DrawText(geoText, 10, sh-20, 14, colorAmber)
		rl.DrawText(time.Now().Format("15:04:05.000 UTC"), int32(rl.GetScreenWidth()-160), sh-20, 12, colorDim)

		rl.EndDrawing()
	}

	if s.loaded {
		rl.UnloadTexture(s.texture)
	}
}

func fileModTime(path string) time.Time {
	info, err := os.Stat(path)
	if err != nil {
		return time.Time{}
	}
	return info.ModTime()
}

func min32(a, b float32) float32 {
	if a < b {
		return a
	}
	return b
}
