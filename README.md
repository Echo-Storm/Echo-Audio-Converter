![Echo Audio Converter](EAC_Banner.svg)

<p align="center">
  <img src="screenshot1.jpg" alt="Screenshot 1" width="48%">
  <img src="screenshot2.jpg" alt="Screenshot 2" width="48%">
</p>


## Features

- **Batch Processing** – Queue multiple files, convert all at once
- **LUFS Analysis** – Analyze button measures loudness of queued files; color-coded display shows if normalization is needed
- **Loudness Normalization** – Two-pass LUFS normalization (-14 streaming, -16 Apple, -23 broadcast)
- **Source Info Display** – Queue shows source format, bitrate, sample rate, LUFS, and duration
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
| OGG Vorbis | Q3–Q10 (VBR) | ✓ | ✗ |
| OPUS | 64–192 kbps | ✓ | ✗ |
| M4A (AAC) | 96–256 kbps | ✓ | ✓ |
| ALAC | Lossless | ✓ | ✓ |

**Note:** WAV doesn't support embedded metadata – it's a format limitation, not a bug.

## Changelog

### v0.5.2
- **Full bugsweep**
- Fixed: ffprobe fields that return `"N/A"` (common with WMA, some AIFF, raw streams) no longer crash probe and lose all source info
- Fixed: Progress bar formula `elapsed * 50 / duration` made it jump to 95% within seconds. Now `elapsed / duration` (linear)
- Fixed: Clicking Cancel during loudness analysis had no effect — analysis process now tracked in `_current_process` so Cancel works immediately
- Fixed: "FFmpeg updated successfully" status message was immediately erased by an unconditional `clearMessage()` call — never visible
- Fixed: Closing the window during LUFS analysis gave no warning and abandoned the ffmpeg process. `closeEvent` now guards `analyze_worker`
- Fixed: Overall progress bar stayed below 100% when jobs failed or were cancelled — those statuses now count as done
- Fixed: Changing format when two pending jobs shared a filename stem could assign both the same output path
- Fixed: Bare `except:` in cancellation cleanup replaced with `except OSError` — bare except catches `SystemExit`/`KeyboardInterrupt`
- Fixed: `BatchProcessor._cancel_requested` was set in two places but never read — dead flag removed
- Fixed: Duplicate `AAC` format entry removed (identical to `M4A (AAC)`)
- Fixed: `probe_file()` and `get_version()` had no timeout — hung ffprobe could freeze UI indefinitely
- Fixed: AIFF files showed raw codec string `PCM_S16BE` in Src column instead of `AIFF`
- Fixed: `_on_delete_selected` bypassed `remove_job()` API

### v0.5.1
- **Code Quality Audit**
- Fixed: Removed unused `import re` from ffmpeg_wrapper
- Fixed: Replaced bare `except:` clauses with `except Exception:` throughout codebase
- Fixed: Worker thread references now properly cleaned up after completion (prevents potential state issues)
- General code hygiene and defensive programming improvements

### v0.5.0
- **LUFS Analysis** – New "Analyze LUFS" button measures integrated loudness of queued files before conversion
- **LUFS Column** – Queue now displays measured loudness between kHz and Time columns
- **Color-Coded LUFS** – When a loudness target is selected, LUFS values are color-coded:
  - Green: within 1 LUFS of target (already good)
  - Yellow: louder than target (will be reduced)
  - Cyan: quieter than target (will be boosted)
- Analysis skips files that have already been measured; results persist in queue until cleared

### v0.4.0
- **Bug Sweep & Stability Pass**
- Fixed: Overall progress bar was double-counting completed jobs (could exceed 100%)
- Fixed: Loudness analysis crash on silent/near-silent audio (`-inf` handling)
- Fixed: Output directory now created automatically if it doesn't exist
- Fixed: FFmpeg process cancellation now properly initialized
- Code cleanup and defensive error handling throughout

### v0.3.0
- **Loudness Normalization** – Two-pass LUFS normalization using FFmpeg loudnorm filter; options: -14 LUFS (Streaming), -16 LUFS (Apple), -23 LUFS (Broadcast)
- **Source Info Columns** – Queue now displays source format, bitrate, sample rate (kHz), and duration; hover over bitrate for detailed info
- **Include Subdirectories** – New checkbox to recursively scan folders for audio files
- **Save to Original Directory** – New checkbox to save converted files alongside sources; disables output folder field when checked
- **Delete Source After Conversion** – New checkbox to remove originals after successful conversion (requires confirmation)
- **Directory-Aware Queue** – Queue now shows relative paths when files come from subdirectory scans, with full path in tooltip
- **Safety Features** – Delete source requires confirmation dialog; setting is never saved (must enable manually each session)
- Drag & drop now respects the recursive subdirectories setting
- Changing format/quality now updates pending jobs in the queue

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
