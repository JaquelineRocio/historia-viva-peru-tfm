import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.transcription import whisper
from app.transcription.youtube import TranscriptError


@pytest.mark.parametrize("authenticated", [False, True])
@pytest.mark.parametrize("failure", [None, "Sign in to confirm you're not a bot", "private-detail"])
def test_download_auth_cleanup_and_errors(monkeypatch, tmp_path, authenticated, failure):
    cookies = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tfake-test-value\n"
    monkeypatch.setattr(whisper.settings, "youtube_cookies", SecretStr(cookies) if authenticated else None)
    paths = []

    class Downloader:
        def __init__(self, options):
            if authenticated:
                path = Path(options["cookiefile"])
                paths.append(path)
                assert path.read_text() == cookies
            else:
                assert "cookiefile" not in options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def download(self, urls):
            assert urls == ["https://www.youtube.com/watch?v=deQdS69P4-0"]
            if failure:
                raise RuntimeError(failure + " fake-test-value")
            (tmp_path / "deQdS69P4-0.mp3").write_bytes(b"test")

    monkeypatch.setitem(sys.modules, "yt_dlp", SimpleNamespace(YoutubeDL=Downloader))
    if failure:
        with pytest.raises(TranscriptError) as caught:
            whisper._download_audio("deQdS69P4-0", str(tmp_path))
        assert "fake-test-value" not in str(caught.value)
        assert "private-detail" not in str(caught.value)
        if "Sign in" in failure:
            assert "YouTube bloqueó" in str(caught.value)
    else:
        assert Path(whisper._download_audio("deQdS69P4-0", str(tmp_path))).is_file()
    assert all(not path.exists() and not path.parent.exists() for path in paths)


def test_invalid_cookie_configuration_does_not_start_download(monkeypatch, tmp_path):
    monkeypatch.setattr(whisper.settings, "youtube_cookies", SecretStr("not-netscape"))
    monkeypatch.setitem(sys.modules, "yt_dlp", SimpleNamespace())
    with pytest.raises(TranscriptError, match="formato Netscape"):
        whisper._download_audio("deQdS69P4-0", str(tmp_path))


def test_failed_download_does_not_load_whisper(monkeypatch):
    def blocked(*args):
        raise TranscriptError("blocked")

    def unexpected_load():
        pytest.fail("Whisper should not load before a successful download")

    monkeypatch.setattr(whisper, "_download_audio", blocked)
    monkeypatch.setattr(whisper, "_load_model", unexpected_load)
    with pytest.raises(TranscriptError, match="blocked"):
        whisper.transcribe_with_whisper("deQdS69P4-0")
