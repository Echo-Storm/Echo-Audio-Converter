<div align="center">

![Echo Audio Converter](EAC_Banner.svg)

**Batch audio conversion with two-pass loudness normalization.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-41CD52?style=flat-square)](https://pypi.org/project/PyQt6/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)](https://github.com/Echo-Storm)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Auto--bundled-007808?style=flat-square&logo=ffmpeg&logoColor=white)](https://www.gyan.dev/ffmpeg/builds/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

<div align="center">

<img src="screenshot1.jpg" width="48%"> <img src="screenshot2.jpg" width="48%">

</div>

---

## What It Is

A portable Windows desktop tool for converting audio files in bulk. Drop in a folder, pick a format, click Convert. If you want loudness normalization, it does a proper two-pass loudnorm analysis first so the output is actually correct instead of a guess.

No installation required. FFmpeg downloads automatically on first run and lives in the app folder. No registry entries, no system-wide installs, no dependency on whatever version of FFmpeg you may or may not have on your PATH.

---

## Features

**Conversion**
- Batch queue with format, quality, sample rate, and loudness settings applied globally to all pending jobs
- Source info displayed per file — codec, bitrate, sample rate, channel count, duration
- Output summary columns mirror source columns: Output format → →kbps → →kHz → →LUFS
- Output path collision detection at queue time, not at ffmpeg time
- Converts video containers too (.mp4, .mkv, .webm, .avi) — strips video, keeps audio
- Parallel workers setting (1–8) to convert multiple files simultaneously

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
- Change format, quality, sample rate, or loudness mid-queue — all pending jobs update automatically
- Right-click or Delete key to remove individual items
- Clear Completed (keeps failed/cancelled visible) / Clear All (confirms for large queues)
- Relative path display for recursive folder scans

**File Handling**
- Add files, add folder (shallow or recursive), or drag and drop
- Album art preserved for supported formats (MP3, FLAC, M4A, ALAC)
- Metadata preserved via `-map_metadata 0`
- Output directory auto-created if it doesn't exist
- "Save to original directory" mode — converted file lands next to source
- Delete source after conversion (requires manual enable each session, confirmation dialog)

**FFmpeg Integration**
- FFmpeg downloads automatically on first run — no manual setup required
- Bundled locally, zero system dependency
- Async update check — UI stays responsive during version fetch
- Update check with version comparison against [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) builds
- Cancel mid-conversion — partial output files cleaned up on cancel
- Robust audio stream detection: two-stage probe with targeted fallback

**UI**
- Industrial dark theme — not trying to look like a SaaS product
- Drag & drop respects recursive setting
- Settings persistence: last format, output dir, loudness target, sample rate, worker count, checkbox states
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
> Opus always encodes at 48 kHz internally regardless of the sample rate override setting.

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

First run creates a venv, installs dependencies, launches the app, and downloads FFmpeg automatically — the progress bar at the top shows download status. Every run after that goes straight to the app, no waiting.

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

Pick a format, quality, and sample rate from the left panel. All pending jobs update live when you change any setting. Output goes to the folder in the *Folder* field, or tick *Save to original directory* to drop converted files alongside their sources.

The queue table mirrors source info on the left and output settings on the right:

| Left (source) | Right (output) |
|---------------|----------------|
| Src — detected codec | Output — target format |
| Bitrate — source kbps | →kbps — output quality |
| kHz — source sample rate | →kHz — output sample rate (`src` = keep) |
| LUFS — measured loudness | →LUFS — normalization target (`off` = none) |

**3. Loudness (optional)**

Select a LUFS target from the Loudness dropdown. Click **Analyze LUFS** to measure everything in the queue without converting — useful if you want to see what you're working with first. LUFS values are color-coded against your target. When you convert, each file gets a proper two-pass analysis automatically.

**4. Convert**

Click **Convert All**. The queue shows live status per file. Cancel at any time — partial outputs are removed. Set *Workers* to 2–4 to convert multiple files in parallel for large batches.

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

**Parallel conversion**

The *Workers* spinbox (Queue section) sets how many FFmpeg processes run simultaneously. Each job gets its own private FFmpegWrapper instance so process handles never collide. Cancel reaches all active processes. Default is 1 (sequential), which is identical to previous behaviour. 2–4 workers is a reasonable range for large queues; beyond that the gains diminish and CPU/disk contention increases.

**Progress estimation**

Progress is time-based (`elapsed / duration`), not parsed from FFmpeg's stderr. It's a linear estimate — fast disks and simple codecs track closely; heavy resampling or slow writes will drift. The bar hits 95% and waits for FFmpeg to finish rather than jumping to 100% early.

**FFmpeg process management**

Conversion runs in a background QThread. Each parallel job tracks its own `_current_process`. Cancel calls `cancel_current()` on every active wrapper, terminates all live FFmpeg processes, and cleans up partial output files.

**Audio stream detection**

The probe runs in two stages. First, a combined `-show_format -show_streams` query gets format data (duration, bitrate) and stream info together. If no audio stream is found in that result — which can happen with certain game audio encoders that produce valid format data but an empty streams array — a targeted fallback uses `-select_streams a:0 -show_entries stream=...` to ask explicitly for just the first audio stream. If that also fails, a warning appears in the log pane.

**Portability**

The app searches for FFmpeg at `./ffmpeg/ffmpeg.exe`, then `./ffmpeg/bin/ffmpeg.exe`, then system PATH — in that order. Keep the `ffmpeg/` folder in the same directory as `echo_audio_converter.py` and it's fully self-contained.

---

## What It Doesn't Do

- No Linux/macOS support (FFmpeg updater is Windows-specific; the UI will run but updating won't)
- No drag-and-drop reordering of the queue
- No output file size estimation
- No preset system for saving format+quality+loudness combinations
- No streaming progress from FFmpeg stderr — progress is time-based estimation
- No per-file output format override — format/quality/loudness applies to the whole queue

---

## Changelog

### v0.6.1
**New features**
- Parallel workers — convert multiple files simultaneously; set 1–8 workers in the Queue section (default 1, identical to previous behaviour)
- Sample rate output override — new *Sample rate* dropdown in the Output section (44.1 / 48 / 88.2 / 96 kHz or source passthrough)
- Output columns redesigned to mirror source columns: Output | →kbps | →kHz | →LUFS; verbose quality label replaced with clean short value (e.g. `320k`, `Q5`, `L5`, `24b`, `∞`)
- →LUFS column shows normalization target per job (`-14`, `-23`, `off`) in green when active, dim when off
- Missing source fields now show `n/a` instead of blank

**Bug fixes**
- Fixed cancel race condition: external `cancel_current()` could misclassify cancelled jobs as failures when it terminated the FFmpeg process between loop iterations
- Fixed `cancel_current()` leaving zombie processes: `kill()` was called without a subsequent `wait()` on timeout
- Fixed `clear_completed()` silently removing failed and cancelled jobs; now only removes successful jobs
- Fixed `AnalyzeWorker.job_failed` signal never connected to a slot — analysis failures were silently dropped from the UI
- Fixed update check blocking the main thread for up to 30 seconds; now runs in a background worker
- Fixed `_on_job_progress` rebuilding the entire table at ~20 Hz per converting worker; now only updates the affected row's progress cell
- Fixed `_refresh_log_view` joining 500 log lines on every 500ms tick; now uses a tail comparison
- Fixed `text=True` subprocess calls using Windows locale encoding (cp1252) to decode ffprobe's UTF-8 JSON, silently corrupting stream data for files with non-ASCII tags
- Fixed `data.get("streams", [])` not guarding against `"streams": null` in ffprobe JSON
- Fixed `probe_file` building the command outside the try block, causing `FFmpegNotFoundError` to bypass error handling
- Fixed `is_available()` only checking for `ffmpeg.exe`, not `ffprobe.exe`
- Fixed probe exception logged at DEBUG level (invisible in UI log pane); now WARNING
- Added targeted audio stream fallback probe using `-select_streams a:0` for files where the combined probe returns an empty streams list
- Fixed `_on_format_changed` triple-firing `_update_pending_jobs_settings` via signal cascade during combo repopulation
- Fixed `closeEvent` accepting window close without cancelling running workers first, causing "QThread destroyed while running"
- Fixed `_on_job_analyze_failed` logging a UUID instead of the filename
- Fixed redundant `import os as _os` inside a method body
- Added confirmation dialog to Clear All for queues larger than 5 files

### v0.6.0
- FFmpeg now downloads automatically on first run — no user action required, progress shown in the top bar
- Added subtle vertical stripe texture to app background, matching the banner aesthetic
- Left control panel darkened and separated with a border for visual depth
- Separator line added above the Convert/Cancel button row
- Left panel widened to prevent combo box text truncation
- Added Ko-fi donate button to the status bar (far right, unobtrusive)

### v0.5.5
- Fixed crash on startup: `_on_format_changed` method definition was accidentally dropped in v0.5.4, causing `AttributeError` at launch
- Fixed bat launcher: pip was running on every launch instead of first-install only, causing a visible delay and silently failing on some systems
- Added error handling to bat launcher — startup failures now show a message and keep the window open instead of closing silently
- Added cancelled job count to queue summary label

### v0.5.4
- Fixed update button staying enabled during network check, allowing double-invocation
- Fixed drag-and-drop silently ignoring drops with no supported audio files — now shows status message
- Fixed progress bar starting at 15% when loudness analysis fails (now correctly starts at 0%)

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

## Support

If this saves you time, a tip is always appreciated.  
[ko-fi.com/xechostormx](https://ko-fi.com/xechostormx/tip)

---

## License

MIT — do whatever you want with it.

---

<div align="center">

*Personal project. Private distribution.*  
[github.com/Echo-Storm](https://github.com/Echo-Storm)

</div>
