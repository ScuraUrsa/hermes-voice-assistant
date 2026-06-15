#!/usr/bin/env python3
"""Generate synthetic test audio files for voice assistant tests."""

import argparse
import struct
import wave
from pathlib import Path

import numpy as np


def generate_sine_wave(
    frequency: float = 440.0,
    sample_rate: int = 16000,
    duration_sec: float = 1.0,
    amplitude: float = 0.5,
) -> np.ndarray:
    """Generate a sine wave as a float32 numpy array."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    samples = amplitude * np.sin(2 * np.pi * frequency * t)
    return samples.astype(np.float32)


def generate_silence(
    sample_rate: int = 16000,
    duration_sec: float = 1.0,
) -> np.ndarray:
    """Generate silence as a float32 numpy array."""
    num_samples = int(sample_rate * duration_sec)
    return np.zeros(num_samples, dtype=np.float32)


def save_wav(filename: str | Path, samples: np.ndarray, sample_rate: int = 16000) -> None:
    """Save float32 numpy array as a 16-bit mono WAV file."""
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    # Convert float32 [-1..1] to int16
    int_samples = (samples * 32767).clip(-32768, 32767).astype(np.int16)
    with wave.open(str(filename), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())


def save_raw(filename: str | Path, samples: np.ndarray) -> None:
    """Save float32 numpy array as raw PCM16LE bytes (no header)."""
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    int_samples = (samples * 32767).clip(-32768, 32767).astype(np.int16)
    filename.write_bytes(int_samples.tobytes())


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic test audio files")
    parser.add_argument("--output-dir", default="/tmp/hermes-voice-assistant/tests/fixtures/audio",
                        help="Output directory for generated audio")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Sample rate in Hz")
    parser.add_argument("--duration", type=float, default=1.0, help="Duration in seconds")
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Generating test audio files in {out}")

    # Wake word-like snippet (440 Hz, 1 sec)
    sine = generate_sine_wave(frequency=440.0, sample_rate=args.sample_rate,
                              duration_sec=args.duration)
    save_wav(out / "wake_word.wav", sine, args.sample_rate)
    save_raw(out / "wake_word.raw", sine)
    print(f"  {out/'wake_word.wav'}  ({len(sine)} samples)")

    # Silence
    silence = generate_silence(sample_rate=args.sample_rate, duration_sec=args.duration)
    save_wav(out / "silence.wav", silence, args.sample_rate)
    save_raw(out / "silence.raw", silence)
    print(f"  {out/'silence.wav'}  ({len(silence)} samples)")

    # Speech-like (low frequency hum to simulate voice, 200 Hz)
    speech = generate_sine_wave(frequency=200.0, sample_rate=args.sample_rate,
                                duration_sec=args.duration)
    save_wav(out / "speech.wav", speech, args.sample_rate)
    save_raw(out / "speech.raw", speech)
    print(f"  {out/'speech.wav'}  ({len(speech)} samples)")

    # Multi-tone signal (mixture of frequencies)
    t = np.linspace(0, args.duration, int(args.sample_rate * args.duration), endpoint=False)
    multi = (0.3 * np.sin(2 * np.pi * 300 * t) +
             0.3 * np.sin(2 * np.pi * 600 * t) +
             0.2 * np.sin(2 * np.pi * 1200 * t)).astype(np.float32)
    save_wav(out / "multi_tone.wav", multi, args.sample_rate)
    save_raw(out / "multi_tone.raw", multi)
    print(f"  {out/'multi_tone.wav'}  ({len(multi)} samples)")

    print("Done.")


if __name__ == "__main__":
    main()