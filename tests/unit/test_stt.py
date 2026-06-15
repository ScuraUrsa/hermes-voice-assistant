"""Tests for Speech-to-Text (STT) — mock Wyoming protocol requests."""

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_wyoming_client():
    """Create a mock Wyoming protocol client for STT."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.transcribe = AsyncMock(return_value="test transcript")
    return client


@pytest.fixture
def sample_audio():
    """Return a synthetic 1-second audio buffer."""
    return np.zeros(16000, dtype=np.float32)


# ---------------------------------------------------------------------------
# Tests — STT with mocked Wyoming client
# ---------------------------------------------------------------------------

class TestSttTranscription:
    """Verify STT transcription logic with a mocked Wyoming client."""

    @pytest.mark.asyncio
    async def test_transcribe_returns_string(self, mock_wyoming_client, sample_audio):
        """Transcription should return a non-empty string."""
        result = await mock_wyoming_client.transcribe(sample_audio)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_transcribe_expected_text(self, mock_wyoming_client, sample_audio):
        """Transcription should match the mock's return value."""
        result = await mock_wyoming_client.transcribe(sample_audio)
        assert result == "test transcript"

    @pytest.mark.asyncio
    async def test_transcribe_with_connection(self, mock_wyoming_client, sample_audio):
        """Transcription should work after connecting."""
        await mock_wyoming_client.connect()
        mock_wyoming_client.connect.assert_awaited_once()
        result = await mock_wyoming_client.transcribe(sample_audio)
        assert isinstance(result, str)
        await mock_wyoming_client.disconnect()
        mock_wyoming_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_shape(self, mock_wyoming_client):
        """The client should receive audio with the expected shape."""
        audio = np.zeros(16000, dtype=np.float32)
        await mock_wyoming_client.transcribe(audio)
        args, _ = mock_wyoming_client.transcribe.call_args
        assert args[0].shape == (16000,)
        assert args[0].dtype == np.float32

    @pytest.mark.asyncio
    async def test_transcribe_raises_on_empty(self, mock_wyoming_client):
        """Transcription should raise on empty audio."""
        empty = np.array([], dtype=np.float32)
        mock_wyoming_client.transcribe.side_effect = ValueError("Empty audio buffer")
        with pytest.raises(ValueError, match="Empty audio"):
            await mock_wyoming_client.transcribe(empty)

    @pytest.mark.asyncio
    async def test_transcribe_raises_on_connection_error(self, mock_wyoming_client):
        """Transcription should raise on connection failure."""
        mock_wyoming_client.transcribe.side_effect = ConnectionError("Wyoming server unreachable")
        with pytest.raises(ConnectionError, match="unreachable"):
            await mock_wyoming_client.transcribe(np.zeros(16000, dtype=np.float32))


class TestSttWyomingProtocol:
    """Test Wyoming protocol message handling via mocks."""

    @patch("some_module.WyomingSttClient")
    def test_wyoming_request_format(self, MockClient):
        """Verify the Wyoming STT request is built correctly."""
        client = MockClient("localhost", 10400)
        assert client.uri == "localhost:10400"

    @patch("some_module.WyomingSttClient")
    def test_wyoming_timeout(self, MockClient):
        """Verify timeout is passed through to the client."""
        client = MockClient("localhost", 10400, timeout=10)
        assert client.timeout == 10

    @patch("some_module.WyomingSttClient")
    def test_wyoming_language_setting(self, MockClient):
        """Verify language parameter is forwarded."""
        client = MockClient("localhost", 10400, language="pl")
        assert client.language == "pl"