from youtube_transcript_api._errors import RequestBlocked

from app.transcription.youtube import TranscriptError, fetch_transcript


def test_request_blocked_activates_whisper_fallback(monkeypatch):
    class BlockedApi:
        def list(self, video_id):
            raise RequestBlocked(video_id)

    monkeypatch.setattr(
        "app.transcription.youtube.YouTubeTranscriptApi",
        lambda: BlockedApi(),
    )

    try:
        fetch_transcript("zYlIJsNa4Bk")
    except TranscriptError as exc:
        assert "RequestBlocked" in str(exc)
        assert "fallback Whisper" in str(exc)
    else:
        raise AssertionError("El bloqueo de YouTube debio activar el fallback")
