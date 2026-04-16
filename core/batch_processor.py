"""
Batch processing queue for Echo Audio Converter.
"""

import os
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class JobStatus(Enum):
    PENDING = "pending"
    CONVERTING = "converting"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionJob:
    id: str
    input_path: str
    output_path: str
    format_name: str
    quality_option: str
    base_dir: Optional[str] = None  # For relative path display when loading from subdirs
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def input_filename(self) -> str:
        return os.path.basename(self.input_path)
    
    @property
    def display_name(self) -> str:
        """Returns relative path if base_dir is set, otherwise just filename."""
        if self.base_dir:
            try:
                rel_path = os.path.relpath(self.input_path, self.base_dir)
                return rel_path
            except ValueError:
                # Different drives on Windows
                return self.input_filename
        return self.input_filename
    
    @property
    def output_filename(self) -> str:
        return os.path.basename(self.output_path)


class BatchProcessor:
    def __init__(self):
        self.jobs: List[ConversionJob] = []
        self._is_processing = False
        self._cancel_requested = False
    
    def is_duplicate(self, input_path: str) -> bool:
        normalized = os.path.normpath(input_path).lower()
        for job in self.jobs:
            if job.status in (JobStatus.PENDING, JobStatus.CONVERTING):
                if os.path.normpath(job.input_path).lower() == normalized:
                    return True
        return False
    
    def add_job(
        self,
        input_path: str,
        output_dir: str,
        format_name: str,
        quality_option: str,
        output_extension: str,
        base_dir: Optional[str] = None,
    ) -> Optional[ConversionJob]:
        if self.is_duplicate(input_path):
            return None
        
        input_name = Path(input_path).stem
        output_filename = f"{input_name}{output_extension}"
        output_path = str(Path(output_dir) / output_filename)
        
        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{input_name}_{counter}{output_extension}"
            output_path = str(Path(output_dir) / output_filename)
            counter += 1
        
        job = ConversionJob(
            id=str(uuid.uuid4())[:8],
            input_path=input_path,
            output_path=output_path,
            format_name=format_name,
            quality_option=quality_option,
            base_dir=base_dir,
        )
        
        self.jobs.append(job)
        return job
    
    def remove_job(self, job_id: str) -> bool:
        for i, job in enumerate(self.jobs):
            if job.id == job_id and job.status == JobStatus.PENDING:
                self.jobs.pop(i)
                return True
        return False
    
    def clear_completed(self):
        self.jobs = [
            job for job in self.jobs
            if job.status in (JobStatus.PENDING, JobStatus.CONVERTING)
        ]
    
    def clear_all(self):
        if not self._is_processing:
            self.jobs = []
    
    def get_pending_jobs(self) -> List[ConversionJob]:
        return [job for job in self.jobs if job.status == JobStatus.PENDING]
    
    def get_job_by_id(self, job_id: str) -> Optional[ConversionJob]:
        for job in self.jobs:
            if job.id == job_id:
                return job
        return None
    
    @property
    def is_processing(self) -> bool:
        return self._is_processing
    
    @property
    def pending_count(self) -> int:
        return len(self.get_pending_jobs())
    
    def request_cancel(self):
        self._cancel_requested = True
    
    def get_summary(self) -> dict:
        summary = {status: 0 for status in JobStatus}
        for job in self.jobs:
            summary[job.status] += 1
        return {
            "pending": summary[JobStatus.PENDING],
            "converting": summary[JobStatus.CONVERTING],
            "complete": summary[JobStatus.COMPLETE],
            "failed": summary[JobStatus.FAILED],
            "cancelled": summary[JobStatus.CANCELLED],
            "total": len(self.jobs),
        }
