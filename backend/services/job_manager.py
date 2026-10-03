from datetime import datetime
from database.db import SessionLocal, ProcessingJob


def create_job(
    notebook_id: int,
    source_id: int | None,
    job_type: str,
    total_units: int = 0,
):
    db = SessionLocal()

    try:
        job = ProcessingJob(
            notebook_id=notebook_id,
            source_id=source_id,
            job_type=job_type,
            status="queued",
            total_units=total_units,
            completed_units=0,
            current_stage="queued",
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job.id

    finally:
        db.close()


def start_job(job_id: int):
    db = SessionLocal()

    try:
        job = db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).first()

        if not job:
            return False

        job.status = "processing"
        job.current_stage = "processing"
        job.started_at = datetime.utcnow()

        db.commit()

        return True

    finally:
        db.close()


def update_progress(
    job_id: int,
    completed_units: int,
    total_units: int | None = None,
    stage: str | None = None,
):
    db = SessionLocal()

    try:
        job = db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).first()

        if not job:
            return False

        job.completed_units = completed_units

        if total_units is not None:
            job.total_units = total_units

        if stage is not None:
            job.current_stage = stage

        db.commit()

        return True

    finally:
        db.close()


def complete_job(job_id: int):
    db = SessionLocal()

    try:
        job = db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).first()

        if not job:
            return False

        job.status = "completed"
        job.current_stage = "completed"
        job.completed_units = job.total_units
        job.completed_at = datetime.utcnow()

        db.commit()

        return True

    finally:
        db.close()


def fail_job(job_id: int, error_message: str):
    db = SessionLocal()

    try:
        job = db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).first()

        if not job:
            return False

        job.status = "failed"
        job.current_stage = "failed"
        job.error_message = str(error_message)

        db.commit()

        return True

    finally:
        db.close()


def get_job(job_id: int):
    db = SessionLocal()

    try:
        job = db.query(ProcessingJob).filter(
            ProcessingJob.id == job_id
        ).first()

        if not job:
            return None

        progress = 0

        if job.total_units > 0:
            progress = round(
                (job.completed_units / job.total_units) * 100,
                2,
            )

        return {
            "id": job.id,
            "notebook_id": job.notebook_id,
            "source_id": job.source_id,
            "job_type": job.job_type,
            "status": job.status,
            "current_stage": job.current_stage,
            "completed_units": job.completed_units,
            "total_units": job.total_units,
            "progress": progress,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }

    finally:
        db.close()
