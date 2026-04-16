# Echo Audio Converter

![Echo Audio Converter Banner](EAC_Banner.png)

*Simple batch audio conversion. No bloat, no nonsense.*

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
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python echo_audio_converter.py
```

On first run, click **Download FFmpeg** to fetch the binaries (~30MB).

## Usage

1. **Add files** – Click buttons, drag & drop, or add entire folders
2. **Select format** – Choose output format and quality preset
3. **Convert** – Click "Convert All" and watch the queue
4. **Remove items** – Right-click or press Delete

Log file saved to `EAC_Log.txt` in app folder.

## Supported Formats

| Format | Quality Options | Album Art |
|--------|-----------------|-----------|
| MP3 | 96–320 kbps | ✓ |
| FLAC | Compression 0–8 | ✓ |
| WAV | 16/24/32-bit | ✗ |
| AAC | 96–256 kbps | ✓ |
| OGG Vorbis | Q3–Q10 (VBR) | ✗ |
| OPUS | 64–192 kbps | ✗ |
| M4A (AAC) | 96–256 kbps | ✓ |
| ALAC | Lossless | ✓ |

## License

MIT
