"""
FFmpeg auto-updater for Echo Audio Converter.
Downloads from gyan.dev.
"""

import os
import re
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Callable, Tuple

import requests

GYAN_RELEASE_ESSENTIALS = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
GYAN_RELEASE_VERSION = "https://www.gyan.dev/ffmpeg/builds/release-version"


class UpdateError(Exception):
    pass


class FFmpegUpdater:
    def __init__(self, ffmpeg_dir: str, timeout: int = 30):
        self.ffmpeg_dir = Path(ffmpeg_dir)
        self.timeout = timeout
        self.version_file = self.ffmpeg_dir / "VERSION.txt"
    
    def get_installed_version(self) -> Optional[str]:
        if not self.version_file.exists():
            return None
        try:
            return self.version_file.read_text().strip()
        except Exception:
            return None
    
    def get_latest_version(self) -> str:
        try:
            response = requests.get(GYAN_RELEASE_VERSION, timeout=self.timeout)
            response.raise_for_status()
            version = response.text.strip()
            if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
                raise UpdateError(f"Invalid version format: {version}")
            return version
        except requests.RequestException as e:
            raise UpdateError(f"Failed to fetch version info: {e}")
    
    def is_update_available(self) -> Tuple[bool, str, Optional[str]]:
        installed = self.get_installed_version()
        try:
            latest = self.get_latest_version()
        except UpdateError:
            return (False, "unknown", installed)
        
        if installed is None:
            return (True, latest, None)
        
        def version_tuple(v: str) -> tuple:
            return tuple(int(x) for x in v.split('.'))
        
        try:
            update_available = version_tuple(latest) > version_tuple(installed)
        except (ValueError, TypeError):
            update_available = False
        
        return (update_available, latest, installed)
    
    def download_and_install(
        self,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> str:
        def report(msg: str, progress: float):
            if progress_callback:
                progress_callback(msg, progress)
        
        report("Fetching version info...", 0.0)
        
        try:
            latest_version = self.get_latest_version()
        except UpdateError as e:
            raise UpdateError(f"Cannot determine latest version: {e}")
        
        report(f"Downloading FFmpeg {latest_version}...", 0.1)
        
        temp_dir = tempfile.mkdtemp(prefix="ffmpeg_update_")
        zip_path = Path(temp_dir) / "ffmpeg.zip"
        
        try:
            response = requests.get(GYAN_RELEASE_ESSENTIALS, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        dl_progress = 0.1 + (downloaded / total_size) * 0.6
                        size_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        report(f"Downloading... {size_mb:.1f} / {total_mb:.1f} MB", dl_progress)
            
            report("Extracting...", 0.75)
            
            extract_dir = Path(temp_dir) / "extracted"
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            
            extracted_folders = list(extract_dir.iterdir())
            if not extracted_folders:
                raise UpdateError("Zip file was empty")
            
            ffmpeg_folder = extracted_folders[0]
            bin_folder = ffmpeg_folder / "bin"
            
            if not bin_folder.exists():
                raise UpdateError(f"Expected bin folder not found")
            
            report("Installing...", 0.85)
            
            self.ffmpeg_dir.mkdir(parents=True, exist_ok=True)
            
            for binary in ["ffmpeg.exe", "ffprobe.exe"]:
                src = bin_folder / binary
                dst = self.ffmpeg_dir / binary
                if src.exists():
                    if dst.exists():
                        dst.unlink()
                    shutil.copy2(src, dst)
                else:
                    raise UpdateError(f"Binary not found: {binary}")
            
            self.version_file.write_text(latest_version)
            report(f"Installed FFmpeg {latest_version}", 1.0)
            return latest_version
            
        except requests.RequestException as e:
            raise UpdateError(f"Download failed: {e}")
        except zipfile.BadZipFile as e:
            raise UpdateError(f"Invalid zip file: {e}")
        except (OSError, shutil.Error) as e:
            raise UpdateError(f"Installation failed: {e}")
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
