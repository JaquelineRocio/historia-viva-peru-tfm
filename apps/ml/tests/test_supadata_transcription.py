from app.transcription.supadata import _result


def test_supadata_milliseconds_are_converted_to_seconds():
    transcript = _result(
        {
            "lang": "es",
            "content": [
                {"text": "San Martin llego al Peru", "offset": 1250, "duration": 2750}
            ],
        },
        "i1AoWYotyA8",
    )

    assert transcript.source == "api"
    assert transcript.cues[0].start == 1.25
    assert transcript.cues[0].duration == 2.75
