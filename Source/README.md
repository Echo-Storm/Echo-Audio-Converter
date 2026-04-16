<div align="center">

![Echo Audio Converter](EAC_Banner.svg)

**Batch audio conversion with two-pass loudness normalization.**  
*Because everything else is a pain in the ass.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-41CD52?style=flat-square)](https://pypi.org/project/PyQt6/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)](https://github.com/Echo-Storm)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Bundled-007808?style=flat-square&logo=ffmpeg&logoColor=white)](https://www.gyan.dev/ffmpeg/builds/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

<div align="center">

<img src="screenshot1.jpg" width="48%"> <img src="screenshot2.jpg" width="48%">

</div>

---

## What It Is

A portable Windows desktop tool for converting audio files in bulk. Drop in a folder, pick a format, click Convert. If you want loudness normalization, it does a proper two-pass loudnorm analysis first so the output is actually correct instead of a guess.

No installation required. FFmpeg lives in the app folder. No registry entries, no system-wide installs, no dependency on whatever version of FFmpeg you may or may not have on your PATH.

---

## Features

**Conversion**
- Batch queue with format, quality, and loudness settings applied globally to all pending jobs
- Source info displayed per file — codec, bitrate, sample rate, channel count, duration
- Output path collision detection at queue time, not at ffmpeg time
- Converts video containers too (.mp4, .mkv, .webm, .avi) — strips video, keeps audio

**Loudness Normalization**
- Two-pass EBU R128 / ITU-R BS.1770 using FFmpeg's `loudnorm` filter
- First pass analyzes measured integrated loudness, true peak, LRA, and threshold
- Second pass applies correction with those measured values — linear mode, accurate result
- Separate "Analyze LUFS" button to measure the queue without converting
- LUFS column color-coded against your target: green = already there, yellow = too loud, cyan = too quiet
- Targets: −14 LUFS (streaming), −16 LUFS (Apple), −23 LUFS (broadcast)
- Silent/near-silent audio handled — no crash on −inf

**Queue Management**
- Duplicate input detection (case-insensitive on Windows paths)
- Change format or quality mid-queue — all pending jobs update automatically
- Right-click or Delete key to remove individual items
- Clear Completed / Clear All
- Relative path display for recursive folder scans

**File Handling**
- Add files, add folder (shallow or recursive), or drag and drop
- Album art preserved for supported formats (MP3, FLAC, M4A, ALAC)
- Metadata preserved via `-map_metadata 0`
- Output directory auto-created if it doesn't exist
- "Save to original directory" mode — converted file lands next to source
- Delete source after conversion (requires manual enable each session, confirmation dialog)

**FFmpeg Integration**
- Bundled FFmpeg — zero system dependency
- Auto-download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (essentials build)
- Update check with version comparison
- Cancel mid-conversion — partial output files cleaned up on cancel

**UI**
- Industrial dark theme — not trying to look like a SaaS product
- Drag & drop respects recursive setting
- Settings persistence: last format, output dir, loudness target, checkbox states
- Delete source checkbox intentionally never saved — must be re-enabled each session
- In-app log viewer + `EAC_Log.txt` written to the app folder on every run

---

## Supported Output Formats

| Format | Codec | Quality Options | Album Art | Metadata |
|--------|-------|-----------------|:---------:|:--------:|
| MP3 | libmp3lame | 96 / 128 / 192 / 256 / 320 kbps | ✓ | ✓ |
| FLAC | flac | Level 0 (fastest) / 5 (balanced) / 8 (smallest) | ✓ | ✓ |
| WAV | pcm | 16-bit / 24-bit / 32-bit float | — | — |
| OGG Vorbis | libvorbis | Q3 / Q5 / Q7 / Q10 (VBR) | — | ✓ |
| OPUS | libopus | 64 / 96 / 128 / 192 kbps | — | ✓ |
| M4A (AAC) | aac | 96 / 128 / 192 / 256 kbps | ✓ | ✓ |
| ALAC | alac | Lossless | ✓ | ✓ |

> WAV doesn't support embedded metadata or album art — that's a format limitation, not a bug.  
> OGG and OPUS don't support embedded images — same deal.

## Supported Input Formats

`.mp3` `.flac` `.wav` `.aac` `.m4a` `.ogg` `.opus` `.wma` `.aiff` `.aif` `.ape` `.wv` `.mpc` `.tak` `.mp4` `.mkv` `.avi` `.webm`

---

## Requirements

- Windows 10 / 11
- Python 3.10+
- FFmpeg (downloaded automatically on first run)

Python dependencies are handled by the launcher:

```
PyQt6>=6.5.0
requests>=2.28.0
```

---

## Installation

```
git clone https://github.com/Echo-Storm/EchoAudioConverter
cd EchoAudioConverter
```

Double-click `EchoAudioConverter.bat`.

First run creates a venv, installs dependencies, and launches. Every run after that goes straight to the app. On first launch, click **Download FFmpeg** — it pulls the latest essentials build from gyan.dev into the `ffmpeg/` folder.

**Manual launch:**
```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python echo_audio_converter.py
```

---

## Usage

**1. Add files**

- **Add Files** — file picker, multi-select supported
- **Add Folder** — scans a directory; enable *Include subdirectories* first if you want recursive
- **Drag & Drop** — files, folders, or a mix; respects the recursive setting

**2. Set output**

Pick a format and quality from the left panel. All pending jobs update live when you change either setting. Output goes to the folder in the *Folder* field, or tick *Save to original directory* to drop converted files alongside their sources.

**3. Loudness (optional)**

Select a LUFS target from the Loudness dropdown. Click **Analyze LUFS** to measure everything in the queue without converting — useful if you want to see what you're working with first. LUFS values are color-coded against your target. When you convert, each file gets a proper two-pass analysis automatically.

**4. Convert**

Click **Convert All**. The queue shows live status per file. Cancel at any time — partial outputs are removed.

**Keyboard shortcuts**

| Key | Action |
|-----|--------|
| `Delete` | Remove selected queue items |
| Right-click | Context menu on queue |

---

## Technical Notes

**Two-pass loudness normalization**

The loudness workflow is: analyze → normalize, not normalize → hope. Pass one runs the `loudnorm` filter in analysis mode (`-f null`) to measure integrated loudness (I), true peak (TP), loudness range (LRA), and threshold. Pass two uses those measured values in linear mode:

```
loudnorm=I={target}:TP=-1.0:LRA=11:measured_I=...:measured_TP=...:measured_LRA=...:measured_thresh=...:linear=true
```

This is the correct way to do it. Single-pass loudnorm without measured values uses a different algorithm (dynamic mode) that can produce inconsistent results across files.

**Progress estimation**

Progress is time-based (`elapsed / duration`), not parsed from FFmpeg's stderr. It's a linear estimate — fast disks and simple codecs track closely; heavy resampling or slow writes will drift. The bar hits 95% and waits for FFmpeg to finish rather than jumping to 100% early.

**FFmpeg process management**

Conversion runs in a background QThread. The FFmpeg process is tracked in `_current_process` so Cancel terminates it immediately, including during the loudness analysis pass. Partial output files are cleaned up on cancel.

**Portability**

The app searches for FFmpeg at `./ffmpeg/ffmpeg.exe`, then `./ffmpeg/bin/ffmpeg.exe`, then system PATH — in that order. Keep the `ffmpeg/` folder in the same directory as `echo_audio_converter.py` and it's fully self-contained.

---

## What It Doesn't Do

- No parallel/multi-threaded conversion — one file at a time
- No Linux/macOS support (FFmpeg updater is Windows-specific; the UI will run but updating won't)
- No drag-and-drop reordering of the queue
- No output file size estimation
- No preset system for saving format+quality+loudness combinations
- No streaming progress from FFmpeg stderr — see note above

---

## Changelog

### v0.5.5
- Fixed crash on startup: `_on_format_changed` method definition was accidentally dropped in the previous pass, causing `AttributeError` at launch
- Fixed bat launcher: pip was running on every launch instead of first-install only, causing a visible "check" delay and silently failing on some systems
- Added error handling to bat launcher — startup failures now show a message and keep the window open instead of closing silently
- Added cancelled job count to queue summary label

### v0.5.4
- Fixed update button staying enabled during network check, allowing double-invocation
- Fixed drag-and-drop silently ignoring drops with no supported audio files — now shows status message
- Fixed progress bar starting at 15% when loudness analysis fails (now correctly starts at 0%)
- Fixed pip not running for existing venv installs on re-launch *(reverted in 0.5.5)*

### v0.5.3
- Fixed `add_job()` output path collision check — only checked disk, not other pending jobs; two files with the same stem and output dir could get identical output paths
- Fixed `probe_file()` taking the last audio stream instead of the first (affected multi-track files)
- Added cancel re-check after loudness analysis failure — cancelling during analysis no longer causes an unnecessary conversion start before cancelling
- `AnalyzeWorker.request_cancel()` now propagates to `ffmpeg.cancel_current()` so mid-file analysis can actually be interrupted
- Moved in-function imports to module level in `workers.py`
- Removed six unused imports from `main_window.py`
- Removed redundant `convert_btn.setEnabled(True)` that was immediately overridden by `_refresh_queue_table()`
- Removed dead call to no-op `batch_processor.request_cancel()` in `BatchWorker`
- Simplified outer `finally` block in `analyze_loudness` — kill branch was unreachable

### v0.5.2
- Fixed ffprobe `"N/A"` fields crashing `float()`/`int()` conversion and losing all source metadata for affected files
- Fixed progress bar formula `elapsed * 50 / duration` — the `× 50` made it jump to 95% within seconds for any file
- Fixed cancellation being impossible during loudness analysis — `analyze_loudness` now uses `Popen` and assigns to `_current_process`
- Fixed "FFmpeg updated successfully" status message being immediately erased by an unconditional `clearMessage()` call
- Fixed window close during LUFS analysis giving no warning
- Fixed overall progress bar never reaching 100% when jobs fail or cancel
- Fixed `update_pending_jobs()` not preventing sibling pending jobs from sharing output paths
- Removed bare `except:` in cancellation cleanup
- Removed dead `BatchProcessor._cancel_requested` flag
- Removed duplicate `AAC` format entry (was identical to `M4A (AAC)`)
- Added 30s/15s timeouts to `probe_file()` and `get_version()`
- Added AIFF native codecs to `_friendly_codec_name()`
- `_on_delete_selected` now uses `remove_job()` API

### v0.5.1
- Code quality audit, bare except fixes, worker cleanup

### v0.5.0
- LUFS Analysis button — measure integrated loudness of queued files before converting
- LUFS column with color-coding against selected target

### v0.4.0
- Bug sweep: progress bar fix, `-inf` handling on silent audio, auto-create output directory

### v0.3.0
- Two-pass loudness normalization (−14 / −16 / −23 LUFS)
- Source info columns: format, bitrate, sample rate, duration
- Recursive folder scanning
- Save to original directory
- Delete source after conversion (with confirmation)
- Relative path display for subdirectory scans
- Changing format/quality updates all pending jobs live

### v0.2.0
- Industrial dark theme
- Scalable header banner
- Custom styled dropdowns
- Improved log viewer

### v0.1.0
- Initial release: batch conversion, metadata/art preservation, FFmpeg auto-download, drag & drop

---

## License

MIT — do whatever you want with it.

---

<div align="center">

*Personal project. Private distribution.*  
[github.com/Echo-Storm](https://github.com/Echo-Storm)

</div>
