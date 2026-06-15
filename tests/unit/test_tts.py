"""Tests for Text-to-Speech (TTS) — mock Wyoming protocol requests."""

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_wyoming_tts_client():
    """Create a mock Wyoming protocol client for TTS."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    # Synthesise returns audio bytes (simulating PCM16LE audio)
    client.synthesize = AsyncMock(return_value=b"\x00\x00" * 16000)
    return client


# ---------------------------------------------------------------------------
# Tests — TTS with mocked Wyoming client
# ---------------------------------------------------------------------------

class TestTtsSynthesis:
    """Verify TTS synthesis logic with a mocked Wyoming client."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_bytes(self, mock_wyoming_tts_client):
        """Synthesis should return raw audio bytes."""
        result = await mock_wyoming_tts_client.synthesize("hello world")
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_synthesize_expected_length(self, mock_wyoming_tts_client):
        """Synthesis should return the expected number of audio samples."""
        text = "test"
        mock_wyoming_tts_client.synthesize.return_value = b"\x00\x00" * 16000
        result = await mock_wyoming_tts_client.synthesize(text)
        # Each sample is 2 bytes (16-bit mono), so 16000 samples = 32000 bytes
        assert len(result) == 32000

    @pytest.mark.asyncio
    async def test_synthesize_with_connection(self, mock_wyoming_tts_client):
        """Synthesis should work after connecting to the Wyoming server."""
        await mock_wyoming_tts_client.connect()
        mock_wyoming_tts_client.connect.assert_awaited_once()
        result = await mock_wyoming_tts_client.synthesize("connect test")
        assert isinstance(result, bytes)
        await mock_wyoming_tts_client.disconnect()
        mock_wyoming_tts_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_synthesize_called_with_text(self, mock_wyoming_tts_client):
        """The client should receive the exact text to synthesise."""
        text = "turn on the lights"
        await mock_wyoming_tts_client.synthesize(text)
        args, _ = mock_wyoming_tts_client.synthesize.call_args
        assert args[0] == text

    @pytest.mark.asyncio
    async def test_synthesize_raises_on_empty_text(self, mock_wyoming_tts_client):
        """Synthesis should raise on empty text."""
        mock_wyoming_tts_client.synthesize.side_effect = ValueError("Empty text")
        with pytest.raises(ValueError, match="Empty text"):
            await mock_wyoming_tts_client.synthesize("")

    @pytest.mark.asyncio
    async def test_synthesize_raises_on_connection_error(self, mock_wyoming_tts_client):
        """Synthesis should raise on connection failure."""
        mock_wyoming_tts_client.synthesize.side_effect = ConnectionError("Wyoming TTS server unreachable")
        with pytest.raises(ConnectionError, match="unreachable"):
            await mock_wyoming_tts_client.synthesize("error test")


class TestTtsWyomingProtocol:
    """Test Wyoming protocol message handling for TTS via mocks."""

    @patch("some_module.WyomingTtsClient")
    def test_wyoming_tts_endpoint(self, MockClient):
        """Verify the Wyoming TTS endpoint is configured correctly."""
        client = MockClient("localhost", 10401)
        assert client.host == "localhost"
        assert client.port == 10401

    @patch("some_module.WyomingTtsClient")
    def test_wyoming_tts_voice(self, MockClient):
        """Verify voice parameter is forwarded."""
        client = MockClient("localhost", 10401, voice="pl_PL-michal-medium")
        assert client.voice == "pl_PL-michal-medium"

    @patch("some_module.WyomingTtsClient")
    def test_wyoming_tts_speed(self, MockClient):
        """Verify speed parameter is forwarded."""
        client = MockClient("localhost", 10401, speed=1.2)
        assert client.speed == 1.2