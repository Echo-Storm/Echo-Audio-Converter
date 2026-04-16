# Echo Audio Converter — Handoff Document

**Version:** 0.5.1  
**Last Updated:** April 2025  
**Developer:** Echo (Echo-Storm)

---

## Project Overview

Echo Audio Converter is a PyQt6-based desktop application for batch audio format conversion with loudness normalization. It's designed as a portable Windows tool that bundles FFmpeg locally (no system install required).

**Key Value Proposition:**
- Simple batch conversion with queue management
- Two-pass LUFS normalization (analyze before converting)
- Source file info display (codec, bitrate, sample rate, duration, loudness)
- Metadata and album art preservation
- Portable — FFmpeg lives in the app folder

---

## Architecture

```
echo_converter/
├── echo_audio_converter.py    # Entry point (launches MainWindow)
├── EchoAudioConverter.bat     # Windows launcher script
├── requirements.txt           # PyQt6>=6.5.0, requests>=2.28.0
├── core/
│   ├── __init__.py            # Public exports
│   ├── audio_formats.py       # Format definitions (MP3, FLAC, WAV, etc.)
│   ├── batch_processor.py     # Job queue management, ConversionJob dataclass
│   ├── ffmpeg_wrapper.py      # FFmpeg/FFprobe interface, conversion logic
│   ├── ffmpeg_updater.py      # Auto-download from gyan.dev
│   └── logger.py              # Dual logging (file + in-memory buffer for UI)
└── ui/
    ├── __init__.py
    ├── main_window.py         # MainWindow, all UI, event handlers
    └── workers.py             # QThread workers (UpdateWorker, AnalyzeWorker, BatchWorker)
```

### Data Flow

```
User adds files → BatchProcessor.add_job() → ConversionJob created
                      ↓
              FFmpegWrapper.probe_file() populates source info
                      ↓
User clicks Convert → BatchWorker thread started
                      ↓
              For each job: FFmpegWrapper.convert()
                      ↓
              Signals update UI (job_progress, job_finished)
                      ↓
              BatchWorker.batch_finished signal → UI cleanup
```

---

## Key Classes

### ConversionJob (batch_processor.py)

Dataclass representing a single conversion task:

```python
@dataclass
class ConversionJob:
    id: str                          # UUID[:8]
    input_path: str
    output_path: str
    format_name: str                 # "MP3", "FLAC", etc.
    quality_option: str              # "320 kbps (High)", etc.
    base_dir: Optional[str]          # For relative path display
    loudness_target: Optional[float] # -14.0, -16.0, -23.0, or None
    
    # Source info (from ffprobe)
    source_format: Optional[str]
    source_bitrate: Optional[int]    # bits/sec
    source_duration: Optional[float] # seconds
    source_sample_rate: Optional[int]# Hz
    source_channels: Optional[int]
    source_lufs: Optional[float]     # From analyze_loudness()
    
    # State
    status: JobStatus                # PENDING, CONVERTING, COMPLETE, FAILED, CANCELLED
    progress: float                  # 0.0 to 1.0
    error_message: Optional[str]
```

**Display Properties:**
- `bitrate_display` → "320k" or "1.4M"
- `duration_display` → "3:45" or "1:02:30"
- `sample_rate_display` → "44.1" or "48"
- `lufs_display` → "-14.2"
- `display_name` → filename or relative path if base_dir set

### BatchProcessor (batch_processor.py)

Queue manager:
- `add_job()` — Creates job with collision-safe output path
- `is_duplicate()` — Checks if file already queued (PENDING/CONVERTING only)
- `update_pending_jobs()` — Bulk update format/quality/loudness on pending jobs
- `get_pending_jobs()` — Returns list of PENDING jobs
- `clear_completed()` / `clear_all()`

### FFmpegWrapper (ffmpeg_wrapper.py)

FFmpeg interface:
- `probe_file(path)` — Returns dict with duration, bitrate, codec, album art detection
- `analyze_loudness(path)` — First-pass loudnorm, returns measured I/TP/LRA/thresh
- `convert()` — Full conversion with optional two-pass loudness normalization
- `cancel_current()` — Terminates running FFmpeg process

**Loudness Normalization Flow:**
1. If `loudness_target` provided → call `analyze_loudness()` (progress 0.05→0.15)
2. Build loudnorm filter with measured values
3. Run conversion with filter (progress 0.15→1.0)

### Workers (workers.py)

All inherit from QThread:

**UpdateWorker** — Downloads FFmpeg from gyan.dev  
**AnalyzeWorker** — Measures LUFS for pending jobs without source_lufs  
**BatchWorker** — Runs conversions, handles delete-source-after-convert

---

## UI Layout

### Queue Table Columns (10 total)

| Col | Header | Content | Color |
|-----|--------|---------|-------|
| 0 | Src | Source codec (FLAC, MP3) | Gray |
| 1 | Bitrate | "320k", "1.4M" | Gray |
| 2 | kHz | Sample rate | Gray |
| 3 | LUFS | Measured loudness | Color-coded* |
| 4 | Time | Duration | Gray |
| 5 | File | Filename or relative path | Default |
| 6 | Output | Target format | Default |
| 7 | Quality | Target quality | Default |
| 8 | Status | Pending/Converting/Complete/Failed | Color-coded |
| 9 | % | Progress percentage | Default |

*LUFS colors (when loudness target selected):
- Green (#7cb342): within 1 LUFS of target
- Yellow (#c0a040): louder than target
- Cyan (#4a9fd4): quieter than target

### Checkboxes

| Checkbox | QSettings Key | Notes |
|----------|---------------|-------|
| Include Subdirectories | `recursive_subdirs` | Uses rglob vs iterdir |
| Save to Original Directory | `save_to_source` | Disables output folder field |
| Delete Source After Conversion | (not persisted) | Red text, requires confirmation dialog |

### Loudness Combo Options

- "Off" → None
- "-14 LUFS (Streaming)" → -14.0
- "-16 LUFS (Apple)" → -16.0
- "-23 LUFS (Broadcast)" → -23.0

---

## Settings Persistence (QSettings)

**Saved:**
- `last_format` — Last selected output format
- `last_output_dir` — Last output directory
- `loudness_setting` — Loudness combo selection
- `recursive_subdirs` — Include subdirectories checkbox
- `save_to_source` — Save to original directory checkbox

**NOT Saved (by design):**
- `delete_source` — Must enable manually each session for safety

---

## FFmpeg Integration

### Binary Location

Searched in order:
1. `{app_dir}/ffmpeg/ffmpeg.exe`
2. `{app_dir}/ffmpeg/bin/ffmpeg.exe`
3. System PATH

### Conversion Command Structure

```
ffmpeg -y -i {input} 
    -map_metadata 0           # Preserve metadata
    [-c:v copy | -vn]         # Album art or strip video
    [-af loudnorm=...]        # Optional loudness filter
    -c:a {codec}              # Audio codec
    [-b:a X | -q:a X | ...]   # Quality setting
    {extra_args}              # Format-specific
    {output}
```

### Supported Formats

| Format | Codec | Quality Mode | Supports Art |
|--------|-------|--------------|--------------|
| MP3 | libmp3lame | bitrate | Yes |
| FLAC | flac | compression | Yes |
| WAV | pcm_s16le | bitdepth | No |
| AAC | aac | bitrate | Yes |
| OGG Vorbis | libvorbis | vbr | No |
| OPUS | libopus | bitrate | No |
| M4A (AAC) | aac | bitrate | Yes |
| ALAC | alac | lossless | Yes |

### Supported Input Extensions

```
.mp3, .flac, .wav, .aac, .m4a, .ogg, .opus,
.wma, .aiff, .aif, .ape, .wv, .mpc, .tak,
.mp4, .mkv, .avi, .webm
```

---

## Error Handling

### Silent Audio

`analyze_loudness()` handles `-inf` values from FFmpeg loudnorm on silent tracks:
```python
def safe_float(val, default):
    f = float(val)
    if f == float('-inf') or f == float('inf'):
        return default
    return f
```

### Process Cancellation

1. User clicks Cancel → `BatchWorker.request_cancel()`
2. Sets `_cancel_requested = True`
3. Calls `FFmpegWrapper.cancel_current()` → terminates process
4. `convert()` checks `cancel_check()` callback in loop
5. Partial output file deleted on cancellation

### Output Directory

Created automatically if it doesn't exist (fixed in v0.4.0).

---

## Version History

| Version | Key Changes |
|---------|-------------|
| 0.5.1 | Code quality audit, bare except fixes, worker cleanup |
| 0.5.0 | LUFS analysis button, LUFS column with color coding |
| 0.4.0 | Bug sweep: progress bar fix, -inf handling, auto-create output dir |
| 0.3.0 | Loudness normalization, source info columns, recursive folders, delete source |

---

## Known Limitations

1. **WAV metadata** — WAV format doesn't support embedded metadata (format limitation)
2. **OGG/OPUS album art** — These formats don't support embedded images
3. **Progress estimation** — Uses time-based estimation, not actual FFmpeg progress parsing
4. **Windows only** — Updater downloads Windows FFmpeg builds from gyan.dev

---

## Future Considerations

Potential enhancements (not implemented):
- Parse actual FFmpeg progress from stderr (more accurate than time estimation)
- Linux/macOS support (different FFmpeg download sources)
- Preset system for saving format+quality+loudness combinations
- Drag-and-drop reordering in queue
- Output file size estimation
- Multi-threaded conversion (parallel jobs)

---

## Development Notes

### Testing Checklist

- [ ] Add single file, verify probe info populates
- [ ] Add folder with subdirs, verify recursive checkbox works
- [ ] Analyze LUFS, verify column populates and colors correctly
- [ ] Convert with loudness normalization, check two-pass works
- [ ] Cancel mid-conversion, verify cleanup
- [ ] Delete source after conversion, verify confirmation dialog
- [ ] Change format/quality mid-queue, verify pending jobs update
- [ ] Clear completed vs clear all

### Debugging

Log file: `{app_dir}/EAC_Log.txt` (overwritten each session)  
In-app log: Bottom panel shows INFO+ level messages

### Dependencies

```
PyQt6>=6.5.0
requests>=2.28.0
```

FFmpeg downloaded on first run or via "Download FFmpeg" button.

---

## Contact

GitHub: https://github.com/Echo-Storm  
Project is private/personal distribution only.
