"""
Audio format definitions for Echo Audio Converter.
"""

import os

AUDIO_FORMATS = {
    "MP3": {
        "codec": "libmp3lame",
        "extension": ".mp3",
        "quality_mode": "bitrate",
        "quality_options": {
            "320 kbps (High)": "320k",
            "256 kbps": "256k",
            "192 kbps (Standard)": "192k",
            "128 kbps": "128k",
            "96 kbps (Low)": "96k",
        },
        "default_quality": "192 kbps (Standard)",
        "extra_args": ["-id3v2_version", "3"],  # Ensure ID3v2 tags
        "supports_art": True,
    },
    "FLAC": {
        "codec": "flac",
        "extension": ".flac",
        "quality_mode": "compression",
        "quality_options": {
            "Level 0 (Fastest)": "0",
            "Level 5 (Balanced)": "5",
            "Level 8 (Smallest)": "8",
        },
        "default_quality": "Level 5 (Balanced)",
        "extra_args": [],
        "supports_art": True,
    },
    "WAV": {
        "codec": "pcm_s16le",
        "extension": ".wav",
        "quality_mode": "bitdepth",
        "quality_options": {
            "16-bit": "pcm_s16le",
            "24-bit": "pcm_s24le",
            "32-bit Float": "pcm_f32le",
        },
        "default_quality": "16-bit",
        "extra_args": [],
        "supports_art": False,  # WAV doesn't support embedded metadata well
    },
    "OGG Vorbis": {
        "codec": "libvorbis",
        "extension": ".ogg",
        "quality_mode": "vbr",
        "quality_options": {
            "Q10 (Highest)": "10",
            "Q7 (High)": "7",
            "Q5 (Standard)": "5",
            "Q3 (Low)": "3",
        },
        "default_quality": "Q5 (Standard)",
        "extra_args": [],
        "supports_art": False,
    },
    "OPUS": {
        "codec": "libopus",
        "extension": ".opus",
        "quality_mode": "bitrate",
        "quality_options": {
            "192 kbps (High)": "192k",
            "128 kbps (Standard)": "128k",
            "96 kbps": "96k",
            "64 kbps (Low)": "64k",
        },
        "default_quality": "128 kbps (Standard)",
        "extra_args": ["-vbr", "on"],
        "supports_art": False,
    },
    "M4A (AAC)": {
        "codec": "aac",
        "extension": ".m4a",
        "quality_mode": "bitrate",
        "quality_options": {
            "256 kbps (High)": "256k",
            "192 kbps": "192k",
            "128 kbps (Standard)": "128k",
            "96 kbps": "96k",
        },
        "default_quality": "128 kbps (Standard)",
        "extra_args": [],
        "supports_art": True,
    },
    "ALAC": {
        "codec": "alac",
        "extension": ".m4a",
        "quality_mode": "lossless",
        "quality_options": {
            "Lossless": None,
        },
        "default_quality": "Lossless",
        "extra_args": [],
        "supports_art": True,
    },
}

SUPPORTED_INPUT_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".aac", ".m4a", ".ogg", ".opus",
    ".wma", ".aiff", ".aif", ".ape", ".wv", ".mpc", ".tak",
    ".mp4", ".mkv", ".avi", ".webm",
}


def get_format_names() -> list:
    return list(AUDIO_FORMATS.keys())


def get_format_settings(format_name: str) -> dict:
    return AUDIO_FORMATS.get(format_name)


def get_quality_options(format_name: str) -> list:
    fmt = AUDIO_FORMATS.get(format_name)
    if fmt:
        return list(fmt["quality_options"].keys())
    return []


def get_default_quality(format_name: str) -> str:
    fmt = AUDIO_FORMATS.get(format_name)
    if fmt:
        return fmt["default_quality"]
    return ""


def is_supported_input(filepath: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_INPUT_EXTENSIONS
