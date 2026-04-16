"""
Background workers for Echo Audio Converter.
"""

from PyQt6.QtCore import QThread, pyqtSignal

from core import (
    FFmpegWrapper,
    FFmpegUpdater,
    FFmpegError,
    UpdateError,
    BatchProcessor,
    JobStatus,
)


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


class BatchWorker(QThread):
    job_started = pyqtSignal(str)
    job_progress = pyqtSignal(str, float)
    job_finished = pyqtSignal(str, bool, str)
    batch_finished = pyqtSignal(int, int, int)
    
    def __init__(self, ffmpeg: FFmpegWrapper, batch_processor: BatchProcessor, 
                 delete_source: bool = False, parent=None):
        super().__init__(parent)
        self.ffmpeg = ffmpeg
        self.batch_processor = batch_processor
        self.delete_source = delete_source
        self._cancel_requested = False
    
    def request_cancel(self):
        self._cancel_requested = True
        self.batch_processor.request_cancel()
        self.ffmpeg.cancel_current()
    
    def run(self):
        from core.logger import get_logger
        import os
        log = get_logger()
        
        self.batch_processor._is_processing = True
        self._cancel_requested = False
        
        completed = 0
        failed = 0
        cancelled = 0
        deleted_sources = 0
        
        try:
            pending_jobs = self.batch_processor.get_pending_jobs()
            log.info(f"Starting batch conversion: {len(pending_jobs)} files")
            if self.delete_source:
                log.info("Delete source mode enabled - originals will be removed after successful conversion")
            
            for job in pending_jobs:
                if self._cancel_requested:
                    job.status = JobStatus.CANCELLED
                    cancelled += 1
                    continue
                
                job.status = JobStatus.CONVERTING
                job.progress = 0.0
                self.job_started.emit(job.id)
                
                try:
                    def on_progress(p: float, jid=job.id):
                        self.job_progress.emit(jid, p)
                    
                    def check_cancel():
                        return self._cancel_requested
                    
                    self.ffmpeg.convert(
                        job.input_path,
                        job.output_path,
                        job.format_name,
                        job.quality_option,
                        progress_callback=on_progress,
                        cancel_check=check_cancel
                    )
                    
                    job.status = JobStatus.COMPLETE
                    job.progress = 1.0
                    completed += 1
                    
                    # Delete source file if enabled and output verified
                    if self.delete_source:
                        if os.path.exists(job.output_path) and os.path.getsize(job.output_path) > 0:
                            try:
                                os.remove(job.input_path)
                                deleted_sources += 1
                                log.info(f"Deleted source: {job.input_filename}")
                            except OSError as e:
                                log.warning(f"Failed to delete source {job.input_filename}: {e}")
                        else:
                            log.warning(f"Output not verified, keeping source: {job.input_filename}")
                    
                    self.job_finished.emit(job.id, True, "Complete")
                    
                except FFmpegError as e:
                    if "cancelled" in str(e).lower():
                        job.status = JobStatus.CANCELLED
                        cancelled += 1
                        self.job_finished.emit(job.id, False, "Cancelled")
                    else:
                        job.status = JobStatus.FAILED
                        job.error_message = str(e)
                        failed += 1
                        self.job_finished.emit(job.id, False, str(e))
                    
                except Exception as e:
                    job.status = JobStatus.FAILED
                    job.error_message = str(e)
                    failed += 1
                    log.error(f"Job {job.id} failed: {e}")
                    self.job_finished.emit(job.id, False, str(e))
        
        finally:
            self.batch_processor._is_processing = False
            self.batch_processor._cancel_requested = False
            if self.delete_source and deleted_sources > 0:
                log.info(f"Deleted {deleted_sources} source file(s)")
            log.info(f"Batch complete: {completed} done, {failed} failed, {cancelled} cancelled")
        
        self.batch_finished.emit(completed, failed, cancelled)
