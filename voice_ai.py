from faster_whisper import WhisperModel
import os

# Model sirf ek baar load hoga
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

def speech_to_text(audio_path):

    segments, info = model.transcribe(
        audio_path,
        beam_size=5
    )

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text.strip()