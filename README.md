# Hermes Voice Assistant

A modular, self-hosted voice assistant stack that integrates **Open WebUI** (voice mode MVP via Tailscale), **Home Assistant** (Wyoming protocol satellites), and local LLM inference — all orchestrated by the **Hermes Agent** framework.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Phase 1 — Tailscale + Open WebUI Voice Mode (MVP)](#phase-1--tailscale--open-webui-voice-mode-mvp)
  - [Phase 2 — Home Assistant + Wyoming Protocol](#phase-2--home-assistant--wyoming-protocol)
  - [Phase 3 — Hermes Agent Integration](#phase-3--hermes-agent-integration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

Hermes Voice Assistant is a **privacy-first, fully on-premises voice assistant** designed to work without cloud dependencies. The project combines:

- **Open WebUI** as the chat + voice interface (Speech-to-Text, Text-to-Speech, LLM chat).
- **Home Assistant** with Wyoming protocol satellites for always-listening smart-home integration.
- **Tailscale** as the secure overlay network, enabling voice access from any device on the tailnet.
- **Hermes Agent** as the skill-based orchestrator that routes voice commands to plugins, cron jobs, and external APIs.
- **Local LLM inference** (via ollama or vLLM) running entirely on your own hardware.

The system progresses through three maturity phases:

| Phase | Focus | Components |
|-------|-------|-----------|
| 1 — MVP | Tailscale + Open WebUI voice | Tailscale, Open WebUI, ollama, Whisper STT, TTS |
| 2 — Smart Home | HASS + Wyoming satellites | Home Assistant, Wyoming STT/TTS, satellite hardware |
| 3 — Agentic | Hermes Agent orchestration | Hermes skills, plugins, cron, memory |

---

## Architecture

### High-Level Diagram

```
                           ┌──────────────────────────────┐
                           │        Tailscale Tailnet      │
                           │   (WireGuard-based overlay)   │
                           └────────┬─────────────────┬────┘
                                    │                 │
                    ┌───────────────┘                 └───────────────┐
                    │                                                 │
         ┌──────────▼──────────┐                         ┌──────────▼──────────┐
         │  Open WebUI         │                         │  Home Assistant     │
         │  (Voice Mode MVP)   │                         │  (Wyoming Server)   │
         │                     │                         │                     │
         │  ┌───────────────┐  │                         │  ┌───────────────┐  │
         │  │ Whisper STT   │  │                         │  │ Wyoming STT   │  │
         │  │ (faster-whis- │  │                         │  │ (whisper.cpp) │  │
         │  │  per / local) │  │                         │  └───────────────┘  │
         │  └───────────────┘  │                         │  ┌───────────────┐  │
         │  ┌───────────────┐  │                         │  │ Wyoming TTS   │  │
         │  │ TTS Engine    │  │                         │  │ (Piper TTS)   │  │
         │  │ (XTTS / OOTB) │  │                         │  └───────────────┘  │
         │  └───────────────┘  │                         │  ┌───────────────┐  │
         │  ┌───────────────┐  │                         │  │ Wyoming SAT   │  │
         │  │ LLM Backend   │  │                         │  │ (satellite)   │  │
         │  │ (ollama /     │  │                         │  └───────────────┘  │
         │  │  vLLM)        │  │                         │                     │
         │  └───────────────┘  │                         └──────────────────────┘
         └──────────────────────┘
                    │                                                 │
                    └────────────────────┬────────────────────────────┘
                                         │
                          ┌─────────────▼─────────────┐
                          │      Hermes Agent          │
                          │   (Skill Orchestrator)     │
                          │                            │
                          │  ┌────────┐ ┌──────────┐  │
                          │  │ Skills │ │ Plugins  │  │
                          │  └────────┘ └──────────┘  │
                          │  ┌────────┐ ┌──────────┐  │
                          │  │  Cron  │ │ Memories │  │
                          │  └────────┘ └──────────┘  │
                          └────────────────────────────┘
```

### Data Flow (Voice Query Example)

```
User speaks
    │
    ▼
[Wyoming Satellite / Open WebUI mic]
    │
    ▼ STT
[Whisper / faster-whisper] ──→ Text transcript
    │
    ▼ LLM
[ollama / vLLM] ──→ Response text
    │
    ▼ TTS
[Piper / XTTS] ──→ Audio playback
    │
    ▼ (optional)
[Hermes Agent skill] ──→ Action (light on, thermostat, web search, cron)
```

### Network Topology (Tailscale)

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Laptop      │       │  Phone       │       │  Satellite   │
│  (tailscale) │───────│  (tailscale) │───────│  (tailscale) │
└──────────────┘       └──────────────┘       └──────────────┘
        │                       │                       │
        └──────────────┬────────┘───────────────────────┘
                       │
              ┌────────▼────────┐
              │   Tailnet DERP  │
              │   Relay (if    │
              │   needed for   │
              │   NAT traversal)│
              └─────────────────┘
                       │
              ┌────────▼────────┐
              │   Server Node   │
              │  (this repo)    │
              │                 │
              │  Open WebUI:    │
              │  100.x.x.1:3000 │
              │  HASS:          │
              │  100.x.x.1:8123 │
              │  ollama:        │
              │  100.x.x.1:11434│
              └─────────────────┘
```

All services bind to `0.0.0.0` but are **only reachable through Tailscale's interface** (`tailscale0`, typically `100.x.x.x`). This eliminates the need for a reverse proxy with TLS for LAN-only use.

---

## Components

### 1. Tailscale
- **Purpose**: Secure WireGuard-based overlay network connecting all devices.
- **Key traits**: Zero-config NAT traversal, MagicDNS, ACLs, DERP relays.
- **Port**: N/A (operates at network layer; UDP 41641 for wireguard).

### 2. Open WebUI
- **Purpose**: Full-featured chat UI with built-in voice mode (STT + TTS).
- **Tech**: Python + Svelte, Ollama API-compatible.
- **Port**: `3000` (HTTP).
- **Voice mode**: Uses browser `MediaRecorder` → Whisper API endpoint for STT, and browser-native or server-side TTS.

### 3. Ollama
- **Purpose**: Local LLM inference server.
- **Models**: llama3.1, qwen2.5, deepseek-r1, etc. (8B–70B parameters).
- **Port**: `11434` (HTTP/1.1).
- **GPU support**: CUDA, ROCm, or CPU-only fallback.

### 4. Home Assistant
- **Purpose**: Smart-home automation and Wyoming protocol server.
- **Port**: `8123` (HTTP Web UI), `10700` (Wyoming server default).
- **Wyoming add-ons**: whisper (STT), piper (TTS), openWakeWord (wake word).

### 5. Wyoming Protocol
- **Purpose**: Open standard for voice pipeline components (STT, TTS, wake word, satellite).
- **Key traits**: gRPC-like streaming, text/audio frames, discovery via mDNS.
- **Satellites**: ESP32-S3 + microphone (ESPHome Wyoming firmware) or generic Linux clients.

### 6. Hermes Agent
- **Purpose**: Extensible skill/plugin runtime that routes voice intents to actions.
- **Location**: `~/.hermes/` (default profile).
- **Key dirs**: `skills/`, `plugins/`, `cron/`, `memories/`.
- **Integration**: Hermes Agent listens via Webhook or Wyoming protocol, runs skills, returns responses to TTS pipeline.

---

## Directory Structure

```
/tmp/hermes-voice-assistant/
├── README.md                        # This file
├── .git/                            # Git repository skeleton
│
├── ansible/                         # (planned) Ansible playbooks for provisioning
│   ├── tailscale.yml
│   ├── open-webui.yml
│   ├── home-assistant.yml
│   └── vars.yml
│
├── docker/                          # Docker Compose stacks
│   ├── compose.open-webui.yaml      # Open WebUI + ollama stack
│   ├── compose.home-assistant.yaml  # Home Assistant + Wyoming stack
│   └── compose.hybrid.yaml          # Combined stack (large deployments)
│
├── config/                          # Configuration templates
│   ├── open-webui/
│   │   └── docker_env.sh
│   ├── home-assistant/
│   │   └── configuration.yaml
│   │   └── wyoming/
│   │       └── satellites.yaml
│   └── tailscale/
│       └── tailscale-setup.sh
│
├── wyoming/                         # Wyoming protocol examples
│   ├── satellite/                   # ESPHome Wyoming satellite firmware
│   │   └── esp32-s3.yaml
│   └── client.py                    # Python Wyoming streaming client
│
├── hermes/                          # Hermes Agent integration
│   ├── skill_voice_assistant/       # Hermes skill for voice routing
│   │   ├── skill.py
│   │   └── skill.json
│   └── plugins/
│       └── home-assistant-wyoming/  # Plugin stubs
│
├── scripts/                         # Utility scripts
│   ├── bootstrap.sh                 # One-shot bootstrap (all phases)
│   ├── deploy.sh                    # Docker deployment script
│   ├── test_voice_pipeline.py       # End-to-end voice pipeline test
│   └── tailscale-status.sh          # Quick tailscale health check
│
└── docs/                            # (planned) Extended documentation
    ├── architecture.md
    ├── wyoming-protocol.md
    └── hardware-satellite-guide.md
```

---

## Prerequisites

### Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB (for 7B+ models) |
| GPU | — | NVIDIA GPU with 8+ GB VRAM (e.g., RTX 3060+) |
| Disk | 20 GB free | 100+ GB (model storage ~4–40 GB each) |
| Network | 50 Mbps LAN | Gigabit LAN for voice streaming |

### Software

| Tool | Version | Notes |
|------|---------|-------|
| Linux kernel | ≥ 5.x | Ubuntu 22.04+ or Debian 12+ recommended |
| Docker | ≥ 24.x | With `docker compose` plugin |
| Tailscale | ≥ 1.56 | Install from pkgs.tailscale.io |
| ollama | ≥ 0.3.x | Or run via Docker |
| Open WebUI | ≥ 0.3.x | Docker image: `ghcr.io/open-webui/open-webui` |
| Home Assistant | ≥ 2024.x | Core or Supervisor install |
| Python | ≥ 3.11 | For Wyoming client + testing |
| Hermes Agent | latest | Install via `pip install hermes-agent` |

---

## Setup Instructions

### Phase 1 — Tailscale + Open WebUI Voice Mode (MVP)

This phase gets you a working voice chat interface accessible from any device on your tailnet.

#### 1. Install and Configure Tailscale

```bash
# Install Tailscale (Ubuntu/Debian)
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate and connect
sudo tailscale up --accept-routes --accept-dns

# Verify
tailscale status
tailscale ip -4   # note this IP; it is your server's tailnet address
```

Enable MagicDNS (recommended):

```bash
sudo tailscale up --accept-dns --accept-routes
# Your services will be reachable at <hostname>.<tailnet>.ts.net
```

#### 2. Deploy Ollama (Local LLM Backend)

```bash
# Run with Docker
docker run -d --restart=unless-stopped \
  --name ollama \
  -v ollama_data:/root/.ollama \
  -p 127.0.0.1:11434:11434 \
  ollama/ollama

# Pull a voice-friendly model
docker exec -it ollama ollama pull llama3.1

# Test
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Hello in 5 words",
  "stream": false
}'
```

> **GPU acceleration**: Add `--gpus all` to the `docker run` command if you have an NVIDIA GPU with nvidia-container-toolkit installed.

#### 3. Deploy Open WebUI

```bash
# Create a data volume for persistent config
docker volume create open-webui-data

# Run Open WebUI connected to ollama
docker run -d --restart=unless-stopped \
  --name open-webui \
  -p 127.0.0.1:3000:8080 \
  -v open-webui-data:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ghcr.io/open-webui/open-webui:main
```

> **Note**: On Linux, `host.docker.internal` requires `--add-host host.docker.internal:host-gateway`.  
> On the same host, you can also use `http://172.17.0.1:11434` (default Docker bridge gateway).

#### 4. Expose Open WebUI via Tailscale

Edit the `docker run` or Docker Compose to bind to `0.0.0.0` (all interfaces). The Tailscale firewall will still protect it.

```bash
# Recreate with 0.0.0.0 binding
docker stop open-webui && docker rm open-webui
docker run -d --restart=unless-stopped \
  --name open-webui \
  --add-host host.docker.internal:host-gateway \
  -p 0.0.0.0:3000:8080 \
  -v open-webui-data:/app/backend/data \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  ghcr.io/open-webui/open-webui:main
```

Access at `http://<tailscale-ip>:3000` from any tailnet-connected device.

#### 5. Enable Voice Mode in Open WebUI

1. Open Web UI at `http://<tailscale-ip>:3000`.
2. Go to **Settings → Voice**.
3. Enable **Speech-to-Text** (built-in Whisper or custom endpoint).
4. Enable **Text-to-Speech** (built-in browser TTS or server-side).
5. For better STT quality, set a custom Whisper endpoint:
   - URL: `http://<tailscale-ip>:11434/v1/audio/transcriptions` (ollama Whisper) or run a dedicated `faster-whisper` server.

> **MVP achieved**: You can now speak to the browser, get transcription, receive an LLM response, and hear it spoken — all from any tailnet device.

---

### Phase 2 — Home Assistant + Wyoming Protocol

This phase adds an always-listening smart-home voice assistant with wake-word support.

#### 1. Deploy Home Assistant (Docker)

```bash
docker volume create hass-data

docker run -d --restart=unless-stopped \
  --name homeassistant \
  --network host \
  --privileged \
  -v hass-data:/config \
  ghcr.io/home-assistant/home-assistant:stable
```

Access at `http://<tailscale-ip>:8123`.

#### 2. Install Wyoming Add-Ons (via HACS or Manual)

The Wyoming stack runs as companion Docker containers. Use the official Wyoming containers:

```bash
# Wyoming Whisper (STT) — runs fast-whisper locally
docker run -d --restart=unless-stopped \
  --name wyoming-whisper \
  --network host \
  -v whisper-data:/data \
  rhasspy/wyoming-whisper:master \
  --uri tcp://0.0.0.0:10700 \
  --language en \
  --model tiny-int8

# Wyoming Piper (TTS) — fast, low-footprint neural TTS
docker run -d --restart=unless-stopped \
  --name wyoming-piper \
  --network host \
  -v piper-data:/data \
  rhasspy/wyoming-piper:master \
  --uri tcp://0.0.0.0:10701 \
  --voice en_US-lessac-medium

# Wyoming openWakeWord
docker run -d --restart=unless-stopped \
  --name wyoming-openwakeword \
  --network host \
  rhasspy/wyoming-openwakeword:master \
  --uri tcp://0.0.0.0:10702
```

#### 3. Configure Home Assistant to Use Wyoming

Add to `/config/configuration.yaml`:

```yaml
# Wyoming Protocol
wyoming:
  - name: "Local Whisper"
    host: 127.0.0.1
    port: 10700
    type: stt
  - name: "Local Piper"
    host: 127.0.0.1
    port: 10701
    type: tts
  - name: "Local Wake Word"
    host: 127.0.0.1
    port: 10702
    type: wake_word

# Voice assistant pipeline
voice_assistant:
  - name: "Local Voice"
    stt: "Local Whisper"
    tts: "Local Piper"
    wake_word: "Local Wake Word"
    conversation_agent: homeassistant  # or local LLM
```

Restart Home Assistant after editing configuration.

#### 4. Deploy a Wyoming Satellite (ESP32-S3)

An ESP32-S3 with an I2S microphone runs the ESPHome Wyoming firmware:

```yaml
# wyoming/satellite/esp32-s3.yaml
esphome:
  name: kitchen-satellite
  platformio_options:
    board_build.flash_mode: dio

esp32:
  board: esp32-s3-devkitc-1
  variant: esp32s3
  framework:
    type: esp-idf
    sdkconfig_options:
      CONFIG_ESP32S3_DEFAULT_CPU_FREQ_MHZ: "240"
      CONFIG_ESP32S3_DATA_CACHE_64KB: "y"
      CONFIG_ESP32S3_INSTRUCTION_CACHE_32KB: "y"

i2s_audio:
  i2s_lrclk_pin: GPIO9
  i2s_bclk_pin: GPIO8

microphone:
  - platform: i2s_audio
    adc_type: external
    i2s_din_pin: GPIO10
    pdm: true

speaker:
  - platform: i2s_audio
    i2s_dout_pin: GPIO11
    dac_type: external
    channel: mono

wyoming:
  server: 100.x.x.1   # your Home Assistant tailscale IP
  port: 10700

wake_word:
  model: okay_nabu
  on_wake_word_detected:
    - wyoming.send_audio:
        raw: false    # forward to Wyoming STT
```

Flash via ESPHome Web or `esphome run`.

> **Phase 2 achieved**: You have an always-listening voice satellite that streams audio to Wyoming → HASS processes STT → LLM → TTS → response back to satellite speaker.

---

### Phase 3 — Hermes Agent Integration

This phase connects the voice pipeline to Hermes Agent's skill/plugin system for extensible action routing.

#### 1. Install Hermes Agent

```bash
pip install hermes-agent
```

Or for bleeding edge:

```bash
pip install git+https://github.com/nousresearch/hermes-agent.git
```

#### 2. Create a Voice Assistant Skill

Create `~/.hermes/skills/voice_assistant/skill.py`:

```python
from hermes_agent import Skill, Event

class VoiceAssistantSkill(Skill):
    name = "voice_assistant"
    version = "1.0.0"
    description = "Routes voice pipeline results to plugins and actions."

    def on_event(self, event: Event) -> str:
        """Called by Hermes when a voice transcript or intent arrives."""
        transcript = event.data.get("text", "").lower()
        confidence = event.data.get("confidence", 0.0)

        if confidence < 0.5:
            return "Sorry, I didn't catch that clearly."

        # Route to plugins
        for plugin in self.plugins:
            response = plugin.handle(transcript)
            if response:
                return response

        # Fallback to LLM
        return self.llm_query(transcript)

    def on_speak(self, text: str) -> None:
        """Send text to Wyoming TTS pipeline."""
        # Wyoming client call would go here
        pass
```

Register the skill:

```bash
hermes skill install ~/.hermes/skills/voice_assistant/
```

#### 3. Connect Wyoming → Hermes Webhook

Use the Wyoming protocol endpoint to forward transcripts to Hermes. A simple Wyoming client in `wyoming/client.py`:

```python
"""Minimal Wyoming streaming client that pipes to Hermes Agent."""
import asyncio
import aiohttp
from wyoming.client import AsyncTcpClient
from wyoming.asr import Transcribe, Transcript

async def main():
    async with AsyncTcpClient("127.0.0.1", 10700) as client:
        async for event in client:
            if isinstance(event, Transcript):
                async with aiohttp.ClientSession() as session:
                    await session.post(
                        "http://127.0.0.1:9090/hermes/event",
                        json={"text": event.text, "confidence": event.confidence}
                    )

asyncio.run(main())
```

#### 4. Deploy as Systemd Service

```ini
# /etc/systemd/system/hermes-voice.service
[Unit]
Description=Hermes Voice Assistant Wyoming Bridge
After=network-online.target docker.service

[Service]
ExecStart=/usr/bin/python3 /opt/hermes-voice/wyoming/client.py
WorkingDirectory=/opt/hermes-voice
Restart=always
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-voice
```

> **Phase 3 achieved**: Voice commands flow through the full pipeline: Satellite → Wyoming STT → Hermes skill → Plugin action → Wyoming TTS → Satellite speaker.

---

## Testing

### 1. Tailscale Connectivity

```bash
# From any tailnet device
tailscale ping <server-hostname>
curl -s http://<tailscale-ip>:3000 | head -5   # Open WebUI reachable
curl -s http://<tailscale-ip>:8123 | head -5   # HASS reachable
curl -s http://<tailscale-ip>:11434/api/tags   # ollama reachable
```

### 2. Ollama LLM

```bash
curl http://127.0.0.1:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Say exactly: LLM is ready",
  "stream": false
}' | jq .response
```

Expected: `LLM is ready`

### 3. Wyoming STT/TTS Pipeline

```bash
# Install wyoming client
pip install wyoming

# Send a test audio file (must be 16kHz mono WAV)
python -c "
from wyoming.client import AsyncTcpClient
from wyoming.asr import Transcribe
import asyncio

async def test():
    async with AsyncTcpClient('127.0.0.1', 10700) as client:
        await client.write_event(Transcribe(audio=b'...'))  # raw PCM data
        result = await client.read_event()
        print('STT result:', result.text)

asyncio.run(test())
"
```

### 4. End-to-End Voice Pipeline Test

`scripts/test_voice_pipeline.py`:

```python
#!/usr/bin/env python3
"""End-to-end smoke test for the Hermes Voice Assistant pipeline.

Tests:
  1. Tailscale connectivity
  2. Ollama LLM response
  3. Wyoming STT availability
  4. Wyoming TTS availability
  5. Open WebUI health
  6. Home Assistant health
"""

import sys
import json
import subprocess
import urllib.request
import urllib.error

PASS = 0
FAIL = 1

def check(description: str, fn) -> bool:
    print(f"  [*] {description}... ", end="", flush=True)
    try:
        fn()
        print("PASS")
        return True
    except Exception as e:
        print(f"FAIL ({e})")
        return False

def main():
    results = []
    print("Hermes Voice Assistant — End-to-End Smoke Test")
    print("=" * 60)

    # 1. Tailscale
    def test_tailscale():
        r = subprocess.run(["tailscale", "status"], capture_output=True, text=True, timeout=10)
        assert "tailscale" in r.stdout.lower() or r.returncode == 0
    results.append(check("Tailscale status", test_tailscale))

    # 2. Ollama
    def test_ollama():
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/tags",
            method="GET"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        assert len(data.get("models", [])) > 0
    results.append(check("Ollama models reachable", test_ollama))

    # 3. Open WebUI
    def test_openwebui():
        resp = urllib.request.urlopen("http://127.0.0.1:3000", timeout=10)
        assert resp.status == 200
    results.append(check("Open WebUI health", test_openwebui))

    # 4. Home Assistant
    def test_hass():
        try:
            resp = urllib.request.urlopen("http://127.0.0.1:8123", timeout=10)
            assert resp.status in (200, 302)
        except urllib.error.HTTPError as e:
            # 302 redirect to login is expected
            assert e.code in (200, 302)
    results.append(check("Home Assistant health", test_hass))

    # 5. Wyoming Whisper
    def test_wyoming_whisper():
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("127.0.0.1", 10700))
        sock.close()
    results.append(check("Wyoming Whisper (port 10700)", test_wyoming_whisper))

    # 6. Wyoming Piper
    def test_wyoming_piper():
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(("127.0.0.1", 10701))
        sock.close()
    results.append(check("Wyoming Piper TTS (port 10701)", test_wyoming_piper))

    print("=" * 60)
    passed = sum(results)
    failed = len(results) - passed
    print(f"Result: {passed}/{len(results)} passed, {failed} failed")

    return FAIL if failed > 0 else PASS

if __name__ == "__main__":
    sys.exit(main())
```

Run:

```bash
python3 scripts/test_voice_pipeline.py
```

---

## Deployment

### Docker Compose (Recommended for Production)

`docker/compose.hybrid.yaml`:

```yaml
version: "3.8"

networks:
  tailnet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - tailnet
    ports:
      - "127.0.0.1:11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: unless-stopped
    depends_on:
      - ollama
    volumes:
      - open-webui-data:/app/backend/data
    networks:
      - tailnet
    ports:
      - "0.0.0.0:3000:8080"
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
      WEBUI_SECRET_KEY: "${WEBUI_SECRET_KEY}"
      WHISPER_MODEL: base
      ENABLE_VOICE: "true"

  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    network_mode: host
    privileged: true
    volumes:
      - hass_data:/config

  wyoming-whisper:
    image: rhasspy/wyoming-whisper:master
    container_name: wyoming-whisper
    restart: unless-stopped
    network_mode: host
    volumes:
      - whisper_data:/data
    command: --uri tcp://0.0.0.0:10700 --language en --model tiny-int8

  wyoming-piper:
    image: rhasspy/wyoming-piper:master
    container_name: wyoming-piper
    restart: unless-stopped
    network_mode: host
    volumes:
      - piper_data:/data
    command: --uri tcp://0.0.0.0:10701 --voice en_US-lessac-medium

  wyoming-openwakeword:
    image: rhasspy/wyoming-openwakeword:master
    container_name: wyoming-openwakeword
    restart: unless-stopped
    network_mode: host
    command: --uri tcp://0.0.0.0:10702

volumes:
  ollama_data:
  open-webui-data:
  hass_data:
  whisper_data:
  piper_data:
```

Deploy:

```bash
# Set a strong secret
export WEBUI_SECRET_KEY=$(openssl rand -hex 32)

# Start all services
docker compose -f docker/compose.hybrid.yaml up -d

# Monitor logs
docker compose -f docker/compose.hybrid.yaml logs -f
```

### One-Shot Bootstrap

`scripts/bootstrap.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== Hermes Voice Assistant Bootstrap ==="

# 1. System deps
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin curl jq python3-pip

# 2. Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --accept-routes --accept-dns

# 3. Pull models
docker exec ollama ollama pull llama3.1 2>/dev/null || true

# 4. Deploy stack
docker compose -f docker/compose.hybrid.yaml up -d

# 5. Test
python3 scripts/test_voice_pipeline.py

echo "=== Bootstrap complete ==="
echo "Open WebUI: http://$(tailscale ip -4):3000"
echo "Home Assistant: http://$(tailscale ip -4):8123"
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Open WebUI not loading on tailnet IP | Container bound to 127.0.0.1 | Recreate with `-p 0.0.0.0:3000:8080` |
| STT returns gibberish | Wrong audio format or sample rate | Ensure 16kHz 16-bit mono PCM |
| Wyoming satellite not connecting | Port not reachable / Tailscale ACL | Check `tailscale status`; allow port 10700–10702 in ACL |
| ollama model not responding | Insufficient GPU memory | Use smaller model (e.g., `qwen2.5:3b` instead of 14B) |
| Hermes skill not triggered | Webhook not configured | Verify `hermes webhook` is listening and Wyoming client posts to it |
| High latency (>5s per utterance) | CPU-only inference or large model | Enable GPU pass-through; use `tiny-int8` Whisper model |
| Docker compose `host.docker.internal` not resolving | Linux host | Use `--add-host host.docker.internal:host-gateway` or container network |

---

## License

This project is licensed under the MIT License. See `LICENSE` for details.

Hermes Agent is developed by **Nous Research**.

---

*Document version 1.0 — Generated for the Hermes Voice Assistant project.*