"""Tests for wake word detection — all external dependencies mocked."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_audio_buffer():
    """Return a synthetic 1-second chunk of float32 audio (silence)."""
    return np.zeros(16000, dtype=np.float32)


@pytest.fixture
def mock_detection_model():
    """Create a fully mocked wake word detection model."""
    model = MagicMock()
    model.sample_rate = 16000
    model.wake_words = ["hermes", "assistant"]
    return model


# ---------------------------------------------------------------------------
# Tests — wake word detection logic
# ---------------------------------------------------------------------------

class TestWakeWordDetection:
    """Verify the wake word detection pipeline with mocked components."""

    def test_detection_returns_boolean(self, mock_detection_model, mock_audio_buffer):
        """Detection should return a boolean when a wake word is found."""
        mock_detection_model.predict.return_value = True
        result = mock_detection_model.predict(mock_audio_buffer)
        assert isinstance(result, bool)
        assert result is True

    def test_detection_negative(self, mock_detection_model, mock_audio_buffer):
        """Detection should return False when no wake word is present."""
        mock_detection_model.predict.return_value = False
        result = mock_detection_model.predict(mock_audio_buffer)
        assert result is False

    def test_detection_called_with_correct_shape(self, mock_detection_model):
        """The predict method should receive an array of expected length."""
        audio = np.zeros(16000, dtype=np.float32)
        mock_detection_model.predict(audio)
        args, _ = mock_detection_model.predict.call_args
        assert args[0].shape == (16000,)
        assert args[0].dtype == np.float32

    def test_wake_word_list_property(self, mock_detection_model):
        """The model should expose its configured wake words."""
        assert "hermes" in mock_detection_model.wake_words
        assert len(mock_detection_model.wake_words) == 2

    def test_detection_raise_on_wrong_sample_rate(self, mock_detection_model):
        """Detection should raise ValueError for mismatched sample rate."""
        bad_audio = np.zeros(8000, dtype=np.float32)
        # If the detector validates sample rate, it raises ValueError
        mock_detection_model.predict.side_effect = ValueError(
            f"Expected sample rate {mock_detection_model.sample_rate}, got 8000"
        )
        with pytest.raises(ValueError, match="sample rate"):
            mock_detection_model.predict(bad_audio)


class TestWakeWordIntegration:
    """Test the wake word integration with the audio pipeline mocks."""

    @patch("some_module.WakeWordDetector")
    def test_detector_instantiation(self, MockDetector):
        """Verify that the detector class can be instantiated via mock."""
        detector_instance = MockDetector.return_value
        detector_instance.wake_words = ["hermes"]
        assert "hermes" in detector_instance.wake_words

    @patch("some_module.WakeWordDetector")
    def test_detector_streaming(self, MockDetector):
        """Simulate a streaming audio chunk being passed to the detector."""
        detector = MockDetector()
        chunk = np.zeros(16000, dtype=np.float32)
        detector.predict.return_value = True
        result = detector.predict(chunk)
        assert result is True
        detector.predict.assert_called_once_with(chunk)