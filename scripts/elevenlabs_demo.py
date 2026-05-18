from __future__ import annotations

import os
from pathlib import Path

import requests


def generate_voice_file(text: str, api_key: str, voice_id: str, output_path: Path, model_id: str = "eleven_multilingual_v2") -> Path:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.8,
            "style": 0.2,
            "use_speaker_boost": True,
        },
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(response.content)
    return output_path


def main() -> None:
    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
    text = os.getenv(
        "ELEVENLABS_TEXT",
        "Aegis Commander alert. The demo has detected elevated system activity and requires review.",
    )
    output_path = Path(os.getenv("ELEVENLABS_OUTPUT_PATH", "artifacts/elevenlabs_alert.mp3"))
    model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

    if not api_key:
        raise SystemExit("ELEVENLABS_API_KEY is required")
    if not voice_id:
        raise SystemExit("ELEVENLABS_VOICE_ID is required")

    generated_path = generate_voice_file(text=text, api_key=api_key, voice_id=voice_id, output_path=output_path, model_id=model_id)
    print(f"Generated voice file: {generated_path}")


if __name__ == "__main__":
    main()