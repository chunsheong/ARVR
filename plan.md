# Plan: Smart Glass HUD with VLM SOP Step Detector

Build a Python (FastAPI) backend handling camera capture, Qwen2.5-VL 3B inference via llama.cpp (Intel XPU/SYCL), and SOP step detection — streaming real-time state over WebSocket to a Next.js + TailwindCSS HUD displayed fullscreen on the smart glasses (second monitor). Black background = transparent on glasses.

**Architecture:**
```
Camera (USB) → Python Backend (FastAPI)
                ├── Camera Thread (OpenCV)
                ├── VLM Inference (llama-cpp-python, Qwen2.5-VL, Intel SYCL)
                ├── SOP State Machine
                └── WebSocket Server ──→ Next.js HUD (fullscreen on glasses)
```

---

### Phase 1: Project Setup & Dependencies
1. Create project directory structure under `arvr/`
2. `backend/requirements.txt`: `fastapi`, `uvicorn[standard]`, `opencv-python`, `llama-cpp-python` (SYCL build), `websockets`, `pydantic`
3. `frontend/`: Next.js + TailwindCSS app via `create-next-app`
4. `models/` directory (gitignored) for GGUF files

### Phase 2: Camera Capture (`backend/camera.py`)
5. `CameraCapture` class — threaded OpenCV capture, `Queue(maxsize=2)`, daemon thread, `get_latest_frame()` that drops stale frames, JPEG base64 encoding for HUD transport

### Phase 3: VLM Inference (`backend/vlm.py`)
6. `VLMInference` class — `Qwen25VLChatHandler` + `Llama` from llama-cpp-python, loads Qwen2.5-VL-3B GGUF (`*text-model*.gguf` + `*mmproj*.gguf`), `n_gpu_layers=-1` for Intel XPU, `check_completion(frame, prompt) -> str` encodes frame as base64 JPEG and calls `create_chat_completion`, `temperature=0.1`

### Phase 4: SOP State Machine (`backend/sop.py`)
7. Pydantic recipe model: `{name, steps: [{id, action, description, vlm_completion_prompt, success_keywords[], timeout_seconds}]}`
8. `SOPStateMachine` — tracks `current_step_index`, `state` (IDLE/ACTIVE/COMPLETED/FAILED/TIMEOUT), `process_frame(vlm_response)` checks success_keywords, `advance()`, timeout tracking, emits events
9. Sample recipe `backend/recipes/sample_assembly.json`

### Phase 5: FastAPI Server (`backend/main.py`)
10. REST endpoints: `POST /api/recipe`, `GET /api/recipe`, `POST /api/start`, `POST /api/stop`, `POST /api/reset`
11. `WebSocket /ws` — pushes state updates to HUD: `{current_step, step_index, total_steps, state, vlm_last_response, frame_base64, elapsed_seconds}`
12. Background processing loop: camera at ~30fps, VLM every ~10 frames (~3 inferences/sec), feeds SOP state machine, broadcasts to WebSocket clients

### Phase 6: Next.js HUD (`frontend/`)
13. `app/page.tsx` — fullscreen black background, WebSocket client to `ws://localhost:8000/ws`
14. `StepDisplay.tsx` — large green text showing current step action + description, pulsing "detecting..." indicator
15. `ProgressBar.tsx` — horizontal bar showing step N of M
16. `CameraPreview.tsx` — small PiP camera feed (optional, bottom corner)
17. Green/cyan on black styling, monospace, semi-transparent panels, large readable text

### Phase 7: Integration & Config
18. `backend/config.py` — env-based: `CAMERA_ID`, `MODEL_PATH`, `CLIP_MODEL_PATH`, `VLM_INTERVAL_FRAMES`, `WS_PORT`
19. `run.sh` — sources oneAPI env, starts backend + frontend, optionally launches Chromium fullscreen on second display

---

## Directory Structure
```
arvr/
├── backend/
│   ├── main.py
│   ├── camera.py
│   ├── vlm.py
│   ├── sop.py
│   ├── config.py
│   ├── requirements.txt
│   └── recipes/
│       └── sample_assembly.json
├── frontend/          (Next.js + TailwindCSS)
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   └── components/
│       ├── StepDisplay.tsx
│       ├── ProgressBar.tsx
│       └── CameraPreview.tsx
├── models/            (GGUF files, gitignored)
├── run.sh
└── README.md
```

## Relevant Files
- `backend/main.py` — FastAPI + WebSocket + processing loop
- `backend/camera.py` — Threaded OpenCV capture
- `backend/vlm.py` — Qwen2.5-VL inference via `Qwen25VLChatHandler`
- `backend/sop.py` — Recipe Pydantic model + state machine
- `backend/config.py` — Environment config
- `backend/recipes/sample_assembly.json` — Sample manufacturing SOP
- `frontend/app/page.tsx` — Main HUD page
- `frontend/components/` — StepDisplay, ProgressBar, CameraPreview

## Verification
1. Standalone camera test — verify USB camera frames captured
2. Standalone VLM test — verify Qwen2.5-VL returns coherent image description
3. SOP unit test with mock VLM responses — verify state transitions
4. WebSocket integration — backend → browser state JSON streaming
5. End-to-end — load recipe, point camera, verify HUD step progression
6. Glasses test — Chromium fullscreen on second display, black = transparent, green text visible

## Decisions
- FastAPI backend + Next.js frontend (per user preferences)
- Qwen2.5-VL-3B via llama-cpp-python with `Qwen25VLChatHandler`
- Intel XPU/SYCL via `CMAKE_ARGS="-DGGML_SYCL=ON"` + oneAPI toolkit (falls back to CPU if unavailable)
- WebSocket for real-time HUD updates, base64 JPEG frame transport
- **In scope:** Camera, VLM, SOP engine, HUD, sample recipe, startup script
- **Out of scope:** Model training, multi-user, cloud, audio/voice, hand tracking

## Open Questions
1. Should the VLM prompt include a system-level wrapper (e.g., "Answer only YES or NO: {recipe_prompt}") or leave prompt engineering entirely to the recipe author? *Recommendation: Add a thin wrapper for consistency.*
2. Do you want a model download helper script, or manual download via `huggingface-cli`?
