from backend import db
from backend.models import ApplicationStatus, Job, Application


def update_job_application_count(job_id):
    job = Job.query.get(job_id)
    if job:
        application_count = Application.query.filter_by(
            job_id=job_id,
            status=ApplicationStatus.APPROVED
        ).count()
        job.hired_quantity = application_count
        job.target_quantity = max(job.target_quantity - application_count, 0)

        if job.target_quantity == 0:
            job.is_active = False
        db.session.commit()