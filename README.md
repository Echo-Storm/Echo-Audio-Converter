# Echo Audio Converter

![Echo Audio Converter](EAC_Banner.svg)

*Because Everything Else Is A Pain In The Ass*

## Features

- **Batch Processing** – Queue multiple files, convert all at once
- **Metadata Preservation** – Artist, album, title, track number, year copied to output
- **Album Art** – Preserved for supported formats (FLAC, M4A, MP3, ALAC)
- **Format Support** – MP3, FLAC, WAV, AAC, OGG Vorbis, OPUS, M4A, ALAC
- **FFmpeg Auto-Update** – Downloads latest build from gyan.dev
- **Drag & Drop** – Files or folders
- **Duplicate Detection** – Won't queue the same file twice
- **Portable** – FFmpeg lives in the app folder, no system install needed

## Requirements

- Python 3.10+
- Windows 10/11

## Installation

```
git clone https://github.com/Echo-Storm/EchoAudioConverter.git
cd EchoAudioConverter
```

Then just double-click `EchoAudioConverter.bat` – it handles venv creation and dependencies automatically.

Or manually:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python echo_audio_converter.py
```

On first run, click **Download FFmpeg** to fetch the binaries.

## Usage

1. **Add files** – Click buttons, drag & drop, or add entire folders
2. **Select format** – Choose output format and quality preset
3. **Convert** – Click "Convert All" and watch the queue
4. **Remove items** – Right-click or press Delete

Log file saved to `EAC_Log.txt` in app folder.

## Supported Formats

| Format | Quality Options | Metadata | Album Art |
|--------|-----------------|----------|-----------|
| MP3 | 96–320 kbps | ✓ | ✓ |
| FLAC | Compression 0–8 | ✓ | ✓ |
| WAV | 16/24/32-bit | ✗ | ✗ |
| AAC | 96–256 kbps | ✓ | ✓ |
| OGG Vorbis | Q3–Q10 (VBR) | ✓ | ✗ |
| OPUS | 64–192 kbps | ✓ | ✗ |
| M4A (AAC) | 96–256 kbps | ✓ | ✓ |
| ALAC | Lossless | ✓ | ✓ |

**Note:** WAV doesn't support embedded metadata – it's a format limitation, not a bug.

## Changelog

### v0.2.0
- New industrial dark theme UI
- Scalable header banner
- Compact FFmpeg status bar
- Custom styled dropdowns
- Improved log viewer placement
- One-click batch launcher

### v0.1.0
- Initial release
- Batch conversion with queue
- Metadata and album art preservation
- FFmpeg auto-download from gyan.dev
- Drag & drop support

## License

MIT
