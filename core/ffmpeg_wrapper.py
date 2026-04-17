"""
FFmpeg wrapper for Echo Audio Converter.
"""

import os
import subprocess
import json
import shutil
import time
import threading
from math import isfinite
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

from .audio_formats import AUDIO_FORMATS
from .logger import get_logger


def _safe_float(val, default: float = 0.0) -> float:
    """Parse ffprobe values that may be 'N/A', '-inf', or missing."""
    try:
        f = float(val)
        return default if not isfinite(f) else f
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=None):
    """Parse ffprobe integer values that may be 'N/A' or missing."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


class FFmpegError(Exception):
    pass


class FFmpegNotFoundError(FFmpegError):
    pass


class FFmpegWrapper:
    def __init__(self, ffmpeg_dir: Optional[str] = None):
        if ffmpeg_dir is None:
            app_dir = Path(__file__).parent.parent
            ffmpeg_dir = app_dir / "ffmpeg"
        
        self.ffmpeg_dir = Path(ffmpeg_dir)
        self._ffmpeg_path: Optional[Path] = None
        self._ffprobe_path: Optional[Path] = None
        self._version: Optional[str] = None
        self._current_process = None  # Track running FFmpeg process for cancellation
    
    def _find_binary(self, name: str) -> Optional[Path]:
        if os.name == 'nt':
            name = f"{name}.exe"
        
        local_path = self.ffmpeg_dir / name
        if local_path.exists():
            return local_path
        
        bin_path = self.ffmpeg_dir / "bin" / name
        if bin_path.exists():
            return bin_path
        
        system_path = shutil.which(name.replace('.exe', ''))
        if system_path:
            return Path(system_path)
        
        return None
    
    @property
    def ffmpeg_path(self) -> Path:
        if self._ffmpeg_path is None:
            self._ffmpeg_path = self._find_binary("ffmpeg")
            if self._ffmpeg_path is None:
                raise FFmpegNotFoundError(
                    f"FFmpeg not found in {self.ffmpeg_dir} or system PATH."
                )
        return self._ffmpeg_path
    
    @property
    def ffprobe_path(self) -> Path:
        if self._ffprobe_path is None:
            self._ffprobe_path = self._find_binary("ffprobe")
            if self._ffprobe_path is None:
                raise FFmpegNotFoundError(
                    f"FFprobe not found in {self.ffmpeg_dir} or system PATH."
                )
        return self._ffprobe_path
    
    def is_available(self) -> bool:
        try:
            _ = self.ffmpeg_path
            _ = self.ffprobe_path
            return True
        except FFmpegNotFoundError:
            return False
    
    def get_version(self) -> str:
        if self._version is None:
            try:
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                
                result = subprocess.run(
                    [str(self.ffmpeg_path), "-version"],
                    capture_output=True,
                    timeout=15,
                    startupinfo=startupinfo
                )
                self._version = result.stdout.decode('utf-8', errors='replace').split('\n')[0]
            except Exception as e:
                self._version = f"Unknown (error: {e})"
        return self._version
    
    def probe_file(self, input_path: str) -> Dict[str, Any]:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        log = get_logger()

        try:
            # cmd must be inside the try so FFmpegNotFoundError from self.ffprobe_path
            # is caught and re-raised as FFmpegError, not silently swallowed upstream.
            cmd = [
                str(self.ffprobe_path),
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                input_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30,
                startupinfo=startupinfo,
            )

            if result.returncode != 0:
                err = result.stderr.decode('utf-8', errors='replace')
                raise FFmpegError(f"FFprobe failed: {err[:300]}")

            stdout = result.stdout.decode('utf-8', errors='replace')
            data = json.loads(stdout)
            fmt = data.get("format", {})
            # Use `or []` not `get(..., [])`: the latter passes through null if the
            # key exists but has value null, which would make the for-loop raise TypeError.
            streams = data.get("streams") or []

            audio_stream = None
            has_album_art = False
            for stream in streams:
                if stream.get("codec_type") == "audio" and audio_stream is None:
                    audio_stream = stream
                elif stream.get("codec_type") == "video":
                    if stream.get("disposition", {}).get("attached_pic", 0) == 1:
                        has_album_art = True

            # Fallback: if the general probe returned no audio stream (empty streams
            # list or no audio-type entry), run a targeted second probe that explicitly
            # selects the first audio stream.  Some builds/files return an empty streams
            # array in the combined query but work fine with a direct stream selection.
            if audio_stream is None:
                log.debug(
                    f"probe_file: general probe found {len(streams)} stream(s), none audio "
                    f"for {os.path.basename(input_path)} — trying targeted audio probe"
                )
                audio_stream = self._probe_audio_stream(input_path, startupinfo)
                if audio_stream is None:
                    log.warning(
                        f"probe_file: could not detect audio stream for "
                        f"'{os.path.basename(input_path)}' — Src and kHz will be blank"
                    )

            return {
                "duration": _safe_float(fmt.get("duration"), 0.0),
                "format_name": fmt.get("format_name", "unknown"),
                "bit_rate": _safe_int(fmt.get("bit_rate")),
                "audio_stream": audio_stream,
                "has_album_art": has_album_art,
                "tags": fmt.get("tags", {}),
                "streams": streams,
            }

        except json.JSONDecodeError as e:
            raise FFmpegError(f"Failed to parse ffprobe output: {e}")
        except subprocess.TimeoutExpired:
            raise FFmpegError("FFprobe timed out — file may be corrupt or inaccessible")
        except (subprocess.SubprocessError, FFmpegNotFoundError) as e:
            raise FFmpegError(f"Failed to run ffprobe: {e}")

    def _probe_audio_stream(
        self, input_path: str, startupinfo=None
    ) -> Optional[Dict[str, Any]]:
        """
        Targeted fallback probe: ask ffprobe explicitly for the first audio stream
        only.  Uses -select_streams a:0 so the result is always audio or nothing.
        """
        try:
            cmd = [
                str(self.ffprobe_path),
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries",
                "stream=codec_name,codec_type,sample_rate,channels,bit_rate",
                "-print_format", "json",
                input_path,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=15,
                startupinfo=startupinfo,
            )
            if result.returncode != 0:
                return None
            data = json.loads(result.stdout.decode('utf-8', errors='replace'))
            streams = data.get("streams") or []
            return streams[0] if streams else None
        except Exception:
            return None
    
    def analyze_loudness(self, input_path: str) -> Dict[str, float]:
        """
        Analyze file loudness using FFmpeg loudnorm filter (first pass).
        Returns measured values needed for second pass normalization.

        Uses Popen (not run) so that cancel_current() works during analysis
        and so a timeout properly kills the process rather than orphaning it.
        """
        cmd = [
            str(self.ffmpeg_path),
            "-i", input_path,
            "-af", "loudnorm=print_format=json",
            "-f", "null",
            "-"
        ]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        process = None
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
            )
            self._current_process = process

            try:
                _, stderr_bytes = process.communicate(timeout=300)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise FFmpegError("Loudness analysis timed out")
            finally:
                self._current_process = None

            if process.returncode != 0:
                raise FFmpegError("Loudness analysis failed")

            stderr = stderr_bytes.decode('utf-8', errors='replace')

            # loudnorm outputs JSON to stderr; find the last JSON block
            json_start = stderr.rfind('{')
            json_end = stderr.rfind('}')

            if json_start == -1 or json_end == -1:
                raise FFmpegError("Could not find loudnorm analysis output")

            json_str = stderr[json_start:json_end + 1]
            data = json.loads(json_str)

            # Use the module-level _safe_float; loudnorm returns "-inf" for silent audio
            return {
                "input_i": _safe_float(data.get("input_i"), -24.0),
                "input_tp": _safe_float(data.get("input_tp"), -1.0),
                "input_lra": _safe_float(data.get("input_lra"), 7.0),
                "input_thresh": _safe_float(data.get("input_thresh"), -34.0),
            }

        except json.JSONDecodeError as e:
            raise FFmpegError(f"Failed to parse loudnorm output: {e}")
        except subprocess.SubprocessError as e:
            raise FFmpegError(f"Failed to run loudness analysis: {e}")
        finally:
            # Inner finally already cleared _current_process; this is a safety net
            # for any unexpected path that bypasses it.
            self._current_process = None
    
    def build_conversion_command(
        self,
        input_path: str,
        output_path: str,
        format_name: str,
        quality_option: str,
        preserve_art: bool = False,
        audio_filter: Optional[str] = None,
        sample_rate: Optional[int] = None,
    ) -> List[str]:
        fmt = AUDIO_FORMATS.get(format_name)
        if not fmt:
            raise ValueError(f"Unknown format: {format_name}")
        
        quality_value = fmt["quality_options"].get(quality_option)
        
        cmd = [
            str(self.ffmpeg_path),
            "-y",
            "-i", input_path,
        ]
        
        # Metadata preservation - copy all metadata from input
        cmd.extend(["-map_metadata", "0"])
        
        # Handle video stream (album art)
        if preserve_art and fmt.get("supports_art", False):
            # Copy album art if format supports it
            cmd.extend(["-c:v", "copy"])
        else:
            # Strip video streams
            cmd.append("-vn")
        
        # Audio filter (loudness normalization, etc.)
        if audio_filter:
            cmd.extend(["-af", audio_filter])
        
        # Audio codec
        codec = fmt["codec"]
        if fmt["quality_mode"] == "bitdepth":
            codec = quality_value
        
        cmd.extend(["-c:a", codec])
        
        # Quality settings
        if fmt["quality_mode"] == "bitrate" and quality_value:
            cmd.extend(["-b:a", quality_value])
        elif fmt["quality_mode"] == "vbr" and quality_value:
            cmd.extend(["-q:a", quality_value])
        elif fmt["quality_mode"] == "compression" and quality_value:
            cmd.extend(["-compression_level", quality_value])
        
        # Format-specific extra args
        cmd.extend(fmt.get("extra_args", []))

        # Output sample rate override (-ar); None means keep source rate
        if sample_rate:
            cmd.extend(["-ar", str(sample_rate)])

        cmd.append(output_path)
        
        return cmd
    
    def convert(
        self,
        input_path: str,
        output_path: str,
        format_name: str,
        quality_option: str,
        progress_callback: Optional[Callable[[float], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        loudness_target: Optional[float] = None,
        output_sample_rate: Optional[int] = None,
    ) -> bool:
        log = get_logger()
        
        # Probe input file
        duration = 0
        has_album_art = False
        try:
            probe = self.probe_file(input_path)
            duration = probe.get("duration", 0)
            has_album_art = probe.get("has_album_art", False)
            tags = probe.get("tags", {})
            log.debug(f"Probed {input_path}: duration={duration:.2f}s, art={has_album_art}")
            if tags:
                tag_summary = ", ".join(f"{k}={v}" for k, v in list(tags.items())[:5])
                log.debug(f"Tags: {tag_summary}")
        except FFmpegError as e:
            log.warning(f"Could not probe {input_path}: {e}")
        
        # Loudness normalization (two-pass)
        audio_filter = None
        if loudness_target is not None:
            log.info(f"Analyzing loudness for {os.path.basename(input_path)}...")
            if progress_callback:
                progress_callback(0.05)  # Show we're doing something
            
            if cancel_check and cancel_check():
                raise FFmpegError("Conversion cancelled")
            
            try:
                measured = self.analyze_loudness(input_path)
                log.debug(f"Measured: I={measured['input_i']:.1f}, TP={measured['input_tp']:.1f}, LRA={measured['input_lra']:.1f}")
                
                # Build loudnorm filter with measured values for accurate second pass
                audio_filter = (
                    f"loudnorm=I={loudness_target}:TP=-1.0:LRA=11:"
                    f"measured_I={measured['input_i']}:"
                    f"measured_TP={measured['input_tp']}:"
                    f"measured_LRA={measured['input_lra']}:"
                    f"measured_thresh={measured['input_thresh']}:"
                    f"linear=true:print_format=summary"
                )
                log.info(f"  Normalizing to {loudness_target} LUFS (source: {measured['input_i']:.1f} LUFS)")
                
                if progress_callback:
                    progress_callback(0.15)  # Analysis done
                    
            except FFmpegError as e:
                log.warning(f"Loudness analysis failed, converting without normalization: {e}")
                audio_filter = None

            # Re-check cancel: analysis may have been terminated by cancel_current()
            if cancel_check and cancel_check():
                raise FFmpegError("Conversion cancelled")
        
        # Build command with metadata preservation
        fmt = AUDIO_FORMATS.get(format_name, {})
        preserve_art = has_album_art and fmt.get("supports_art", False)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                log.debug(f"Created output directory: {output_dir}")
            except OSError as e:
                raise FFmpegError(f"Cannot create output directory: {e}")
        
        cmd = self.build_conversion_command(
            input_path, output_path, format_name, quality_option, preserve_art,
            audio_filter=audio_filter,
            sample_rate=output_sample_rate,
        )
        
        log.info(f"Converting: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        if preserve_art:
            log.info("  (preserving album art)")
        log.debug(f"Command: {' '.join(cmd)}")
        
        process = None
        stderr_data = []
        
        def drain_stderr():
            try:
                while True:
                    chunk = process.stderr.read(4096)
                    if not chunk:
                        break
                    stderr_data.append(chunk)
            except Exception:
                pass
        
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
            )
            
            self._current_process = process
            
            stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
            stderr_thread.start()
            
            start_time = time.time()
            last_progress = 0.0
            # If we did loudness analysis successfully, progress starts at 0.15, otherwise 0
            progress_base = 0.15 if audio_filter is not None else 0.0
            progress_range = 1.0 - progress_base  # Remaining progress space
            
            while process.poll() is None:
                if cancel_check and cancel_check():
                    log.info("Cancellation requested, terminating FFmpeg")
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    try:
                        if os.path.exists(output_path):
                            os.remove(output_path)
                    except OSError as e:
                        log.warning(f"Could not delete partial output '{output_path}': {e}")
                    raise FFmpegError("Conversion cancelled")
                
                if duration > 0 and progress_callback:
                    elapsed = time.time() - start_time
                    # Estimate conversion progress as a linear fraction of duration
                    conversion_progress = min(elapsed / duration, 0.95)
                    estimated_progress = progress_base + (conversion_progress * progress_range)
                    if estimated_progress > last_progress:
                        last_progress = estimated_progress
                        progress_callback(estimated_progress)
                
                time.sleep(0.05)
            
            stderr_thread.join(timeout=2)

            # Guard against the race where cancel_current() killed the process
            # externally (from request_cancel) before the while loop's cancel_check
            # had a chance to handle it gracefully.  The process returncode will be
            # non-zero, but the real reason is cancellation — not an ffmpeg error.
            if cancel_check and cancel_check():
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except OSError as e:
                    log.warning(f"Could not delete partial output '{output_path}': {e}")
                raise FFmpegError("Conversion cancelled")

            if process.returncode != 0:
                stderr_text = b''.join(stderr_data).decode('utf-8', errors='replace')
                error_lines = []
                for line in stderr_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if any(line.startswith(x) for x in ('ffmpeg version', 'built with', 'configuration:', 'lib')):
                        continue
                    if line.startswith(' '):
                        continue
                    error_lines.append(line)
                
                log.error(f"FFmpeg failed with code {process.returncode}:")
                for line in error_lines[-8:]:
                    log.error(f"  {line}")
                
                raise FFmpegError(f"FFmpeg error: {error_lines[-1] if error_lines else 'Unknown error'}")
            
            if progress_callback:
                progress_callback(1.0)
            
            log.info(f"Completed: {os.path.basename(output_path)}")
            return True
            
        except subprocess.SubprocessError as e:
            log.error(f"Failed to run FFmpeg: {e}")
            raise FFmpegError(f"Failed to run FFmpeg: {e}")
        finally:
            self._current_process = None
            if process and process.poll() is None:
                process.kill()
                process.wait()
    
    def cancel_current(self):
        if self._current_process:
            try:
                self._current_process.terminate()
                self._current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # terminate() didn't stop it in time; escalate to kill() and
                # always wait() afterwards so the process doesn't become a zombie.
                try:
                    self._current_process.kill()
                    self._current_process.wait()
                except Exception:
                    pass
            except Exception:
                pass
    
    def clear_cache(self):
        self._ffmpeg_path = None
        self._ffprobe_path = None
        self._version = None
