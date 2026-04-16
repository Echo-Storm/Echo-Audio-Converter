"""
Echo Audio Converter - Core module.
"""

from .ffmpeg_wrapper import FFmpegWrapper, FFmpegError, FFmpegNotFoundError
from .ffmpeg_updater import FFmpegUpdater, UpdateError
from .batch_processor import BatchProcessor, ConversionJob, JobStatus
from .audio_formats import (
    AUDIO_FORMATS,
    get_format_names,
    get_format_settings,
    get_quality_options,
    get_default_quality,
    is_supported_input,
    SUPPORTED_INPUT_EXTENSIONS,
)
from .logger import setup_logging, get_logger, log_buffer

__all__ = [
    "FFmpegWrapper", "FFmpegError", "FFmpegNotFoundError",
    "FFmpegUpdater", "UpdateError",
    "BatchProcessor", "ConversionJob", "JobStatus",
    "AUDIO_FORMATS", "get_format_names", "get_format_settings",
    "get_quality_options", "get_default_quality", "is_supported_input",
    "SUPPORTED_INPUT_EXTENSIONS",
    "setup_logging", "get_logger", "log_buffer",
]
