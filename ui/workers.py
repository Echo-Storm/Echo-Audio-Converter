"""
Background workers for Echo Audio Converter.
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtCore import QThread, pyqtSignal

from core import (
    FFmpegWrapper,
    FFmpegUpdater,
    FFmpegError,
    UpdateError,
    BatchProcessor,
    JobStatus,
)
from core.logger import get_logger


class CheckUpdateWorker(QThread):
    """
    Async worker: checks whether an FFmpeg update is available without blocking
    the UI.  Replaces the old synchronous network call in _on_update_clicked.

    Signals:
        result(available, latest_version, installed_version_or_None)
        error(message)
    """
    result = pyqtSignal(bool, str, object)
    error = pyqtSignal(str)

    def __init__(self, updater: FFmpegUpdater, parent=None):
        super().__init__(parent)
        self.updater = updater

    def run(self):
        try:
            available, latest, installed = self.updater.is_update_available()
            self.result.emit(available, latest, installed)
        except Exception as e:
            self.error.emit(str(e))


class UpdateWorker(QThread):
    progress = pyqtSignal(str, float)
    finished = pyqtSignal(bool, str)

    def __init__(self, updater: FFmpegUpdater, parent=None):
        super().__init__(parent)
        self.updater = updater

    def run(self):
        try:
            version = self.updater.download_and_install(
                progress_callback=lambda msg, prog: self.progress.emit(msg, prog)
            )
            self.finished.emit(True, f"FFmpeg {version} installed successfully")
        except UpdateError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            self.finished.emit(False, f"Unexpected error: {e}")


class AnalyzeWorker(QThread):
    """Worker thread for analyzing loudness of queued files."""
    job_analyzed = pyqtSignal(str, float)   # job_id, lufs value
    job_failed = pyqtSignal(str, str)        # job_id, error message
    progress = pyqtSignal(int, int)          # current, total
    finished = pyqtSignal(int, int)          # analyzed count, failed count

    def __init__(self, ffmpeg: FFmpegWrapper, batch_processor: BatchProcessor, parent=None):
        super().__init__(parent)
        self.ffmpeg = ffmpeg
        self.batch_processor = batch_processor
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True
        self.ffmpeg.cancel_current()

    def run(self):
        log = get_logger()

        jobs_to_analyze = [
            job for job in self.batch_processor.jobs
            if job.status == JobStatus.PENDING and job.source_lufs is None
        ]

        if not jobs_to_analyze:
            self.finished.emit(0, 0)
            return

        total = len(jobs_to_analyze)
        analyzed = 0
        failed = 0

        log.info(f"Analyzing loudness for {total} file(s)...")

        for i, job in enumerate(jobs_to_analyze):
            if self._cancel_requested:
                break

            self.progress.emit(i + 1, total)

            try:
                result = self.ffmpeg.analyze_loudness(job.input_path)
                lufs = result.get("input_i", -24.0)
                job.source_lufs = lufs
                analyzed += 1
                self.job_analyzed.emit(job.id, lufs)
                log.debug(f"Analyzed {job.input_filename}: {lufs:.1f} LUFS")
            except Exception as e:
                failed += 1
                error_msg = str(e)
                self.job_failed.emit(job.id, error_msg)
                log.warning(f"Failed to analyze {job.input_filename}: {error_msg}")

        log.info(f"Analysis complete: {analyzed} analyzed, {failed} failed")
        self.finished.emit(analyzed, failed)


class BatchWorker(QThread):
    """
    Runs pending conversion jobs, optionally in parallel.

    When max_workers == 1, jobs are processed sequentially in this QThread.
    When max_workers > 1, a ThreadPoolExecutor runs multiple FFmpeg processes
    simultaneously.

    Each job gets its own FFmpegWrapper instance so _current_process never
    collides between jobs, and request_cancel() correctly reaches all active
    processes.

    Thread-safety notes:
    - job.status / job.progress: simple attribute assignment is atomic under
      CPython's GIL, so no lock is needed for these fields.
    - _completed / _failed / _cancelled use += (read-modify-write), so they
      need a lock.
    - _active_wrappers is a list mutated from multiple threads — needs a lock.
    """

    job_started = pyqtSignal(str)
    job_progress = pyqtSignal(str, float)
    job_finished = pyqtSignal(str, bool, str)
    batch_finished = pyqtSignal(int, int, int)

    def __init__(
        self,
        ffmpeg: FFmpegWrapper,
        batch_processor: BatchProcessor,
        max_workers: int = 1,
        delete_source: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.ffmpeg = ffmpeg                   # Used only to read ffmpeg_dir
        self.batch_processor = batch_processor
        self.max_workers = max(1, max_workers)
        self.delete_source = delete_source
        self._cancel_requested = False

        # Track all wrappers that have an active FFmpeg process
        self._active_wrappers: list = []
        self._wrappers_lock = threading.Lock()

        # Counters written from multiple threads
        self._counters_lock = threading.Lock()
        self._completed = 0
        self._failed = 0
        self._cancelled = 0
        self._deleted_sources = 0

    def request_cancel(self):
        """Signal all active conversions to stop."""
        self._cancel_requested = True
        with self._wrappers_lock:
            for wrapper in self._active_wrappers:
                wrapper.cancel_current()

    def _convert_single(self, job) -> None:
        """
        Convert one job.  Thread-safe; may be called from any thread.
        Creates a private FFmpegWrapper so parallel jobs don't share
        process state.
        """
        log = get_logger()

        if self._cancel_requested:
            job.status = JobStatus.CANCELLED
            with self._counters_lock:
                self._cancelled += 1
            self.job_finished.emit(job.id, False, "Cancelled")
            return

        wrapper = FFmpegWrapper(str(self.ffmpeg.ffmpeg_dir))

        with self._wrappers_lock:
            self._active_wrappers.append(wrapper)

        job.status = JobStatus.CONVERTING
        job.progress = 0.0
        self.job_started.emit(job.id)

        try:
            def on_progress(p: float, jid=job.id):
                self.job_progress.emit(jid, p)

            def check_cancel() -> bool:
                return self._cancel_requested

            wrapper.convert(
                job.input_path, job.output_path,
                job.format_name, job.quality_option,
                progress_callback=on_progress,
                cancel_check=check_cancel,
                loudness_target=job.loudness_target,
                output_sample_rate=job.output_sample_rate,
            )

            job.status = JobStatus.COMPLETE
            job.progress = 1.0

            if self.delete_source:
                if os.path.exists(job.output_path) and os.path.getsize(job.output_path) > 0:
                    try:
                        os.remove(job.input_path)
                        with self._counters_lock:
                            self._deleted_sources += 1
                        log.info(f"Deleted source: {job.input_filename}")
                    except OSError as e:
                        log.warning(f"Failed to delete source {job.input_filename}: {e}")
                else:
                    log.warning(f"Output not verified, keeping source: {job.input_filename}")

            with self._counters_lock:
                self._completed += 1
            self.job_finished.emit(job.id, True, "Complete")

        except FFmpegError as e:
            if "cancelled" in str(e).lower():
                job.status = JobStatus.CANCELLED
                with self._counters_lock:
                    self._cancelled += 1
                self.job_finished.emit(job.id, False, "Cancelled")
            else:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                with self._counters_lock:
                    self._failed += 1
                self.job_finished.emit(job.id, False, str(e))

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            with self._counters_lock:
                self._failed += 1
            log.error(f"Job {job.id} failed unexpectedly: {e}")
            self.job_finished.emit(job.id, False, str(e))

        finally:
            with self._wrappers_lock:
                try:
                    self._active_wrappers.remove(wrapper)
                except ValueError:
                    pass

    def run(self):
        log = get_logger()
        self.batch_processor._is_processing = True
        self._cancel_requested = False
        self._completed = 0
        self._failed = 0
        self._cancelled = 0
        self._deleted_sources = 0

        try:
            pending_jobs = self.batch_processor.get_pending_jobs()
            log.info(
                f"Starting batch conversion: {len(pending_jobs)} file(s), "
                f"{self.max_workers} worker(s)"
            )
            if self.delete_source:
                log.info("Delete source mode: originals removed after successful conversion")

            if self.max_workers == 1:
                # Sequential path — no thread-pool overhead, simpler stack traces
                for job in pending_jobs:
                    self._convert_single(job)
            else:
                # Parallel path — multiple FFmpeg processes running at once
                with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                    futures = [pool.submit(self._convert_single, job) for job in pending_jobs]
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            # _convert_single catches everything internally;
                            # this branch is a safety net only
                            log.error(f"Unhandled job exception (should not reach here): {e}")

        finally:
            self.batch_processor._is_processing = False
            if self.delete_source and self._deleted_sources > 0:
                log.info(f"Deleted {self._deleted_sources} source file(s)")
            log.info(
                f"Batch complete: {self._completed} done, "
                f"{self._failed} failed, {self._cancelled} cancelled"
            )

        self.batch_finished.emit(self._completed, self._failed, self._cancelled)
