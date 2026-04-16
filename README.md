![Echo Audio Converter](EAC_Banner.svg)

<p align="center">
  <img src="screenshot1.jpg" alt="Screenshot 1" width="48%">
  <img src="screenshot2.jpg" alt="Screenshot 2" width="48%">
</p>


## Features

- **Batch Processing** – Queue multiple files, convert all at once
- **Source Info Display** – Queue shows source format, bitrate, and duration for each file
- **Recursive Folder Scanning** – Include subdirectories when adding folders
- **Save to Original Directory** – Keep converted files alongside sources (grays out output folder)
- **Delete Source Option** – Remove original files after successful conversion
- **Directory-Aware Queue** – Shows relative paths when scanning subdirectories
- **Metadata Preservation** – Artist, album, title, track number, year copied to output
- **Album Art** – Preserved for supported formats (FLAC, M4A, MP3, ALAC)
- **Format Support** – MP3, FLAC, WAV, AAC, OGG Vorbis, OPUS, M4A, ALAC
- **FFmpeg Auto-Update** – Downloads latest build from gyan.dev
- **Drag & Drop** – Files or folders (respects recursive setting)
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

### v0.3.0
- **Source Info Columns** – Queue now displays source format, bitrate, and duration; hover over bitrate for detailed info (sample rate, channels)
- **Include Subdirectories** – New checkbox to recursively scan folders for audio files
- **Save to Original Directory** – New checkbox to save converted files alongside sources; disables output folder field when checked
- **Delete Source After Conversion** – New checkbox to remove originals after successful conversion (requires confirmation)
- **Directory-Aware Queue** – Queue now shows relative paths when files come from subdirectory scans, with full path in tooltip
- **Safety Features** – Delete source requires confirmation dialog; setting is never saved (must enable manually each session)
- Drag & drop now respects the recursive subdirectories setting

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
