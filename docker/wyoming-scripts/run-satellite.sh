#!/usr/bin/env bash
#
# run-satellite.sh — Wyoming Satellite Listener
#
# Starts a Wyoming Satellite instance that connects to the local
# voice pipeline (Whisper STT + Piper TTS + Home Assistant).
#
# Usage:
#   ./run-satellite.sh [--name NAME] [--uri URI] [--mic-device DEVICE] [--snd-device DEVICE]
#
# Defaults:
#   NAME:        hermes-satellite
#   URI:         tcp://localhost:10700
#   MIC_DEVICE:  default
#   SND_DEVICE:  default
#
# Environment variables (override defaults):
#   SATELLITE_NAME, SATELLITE_URI, SATELLITE_MIC_DEVICE, SATELLITE_SND_DEVICE
#

set -euo pipefail

# --- Defaults ---
NAME="${SATELLITE_NAME:-hermes-satellite}"
URI="${SATELLITE_URI:-tcp://localhost:10700}"
MIC_DEVICE="${SATELLITE_MIC_DEVICE:-default}"
SND_DEVICE="${SATELLITE_SND_DEVICE:-default}"

# --- Parse CLI overrides ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --name)
            NAME="$2"
            shift 2
            ;;
        --uri)
            URI="$2"
            shift 2
            ;;
        --mic-device)
            MIC_DEVICE="$2"
            shift 2
            ;;
        --snd-device)
            SND_DEVICE="$2"
            shift 2
            ;;
        *)
            echo "[ERROR] Unknown option: $1"
            echo "Usage: $0 [--name NAME] [--uri URI] [--mic-device DEVICE] [--snd-device DEVICE]"
            exit 1
            ;;
    esac
done

# --- Check prerequisites ---
if ! command -v docker &>/dev/null; then
    echo "[ERROR] docker is not installed. Please install Docker first."
    exit 1
fi

# --- Run Wyoming Satellite ---
echo "[INFO] Starting Wyoming Satellite..."
echo "       Name:       ${NAME}"
echo "       URI:        ${URI}"
echo "       Mic device: ${MIC_DEVICE}"
echo "       Snd device: ${SND_DEVICE}"

docker run -d \
    --name "${NAME}" \
    --restart unless-stopped \
    --net host \
    -e SATELLITE_NAME="${NAME}" \
    -e SATELLITE_URI="${URI}" \
    -e SATELLITE_MIC_DEVICE="${MIC_DEVICE}" \
    -e SATELLITE_SND_DEVICE="${SND_DEVICE}" \
    rhasspy/wyoming-satellite \
    --name "${NAME}" \
    --uri "${URI}" \
    --mic-device "${MIC_DEVICE}" \
    --snd-device "${SND_DEVICE}"

echo "[OK] Wyoming Satellite '${NAME}' started successfully."
echo "     Connect URI: ${URI}"