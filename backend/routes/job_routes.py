from datetime import datetime
import os
import uuid
from backend import allowed_file, app, db
from flask import redirect, render_template, request
from backend.utils.general_utils import redirect_to_error
from backend.models import Application, Job

@app.route('/jobs')
def jobs():
    jobs = Job.query.filter(Job.deadline >= datetime.now()).all()
    return render_template('jobs.html', jobs=jobs)

@app.route('/jobs/<int:job_id>', methods=['GET', 'POST'])
def job_detail(job_id):
    job = Job.query.get(job_id)
    if not job:
        return redirect_to_error(404, "Công việc không tồn tại.")
    
    data = request.form
    if request.method == 'POST':
        name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')

        if 'cv_file' not in request.files:
            return redirect(request.url, error="Vui lòng tải lên CV của bạn.")
        
        cv_file = request.files['cv_file']
        if cv_file.filename == '':
            return redirect(request.url, error="Vui lòng chọn tệp CV hợp lệ.")
        
        if cv_file and allowed_file(cv_file.filename):
            file_ext = cv_file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            cv_file.save(file_path)

            application = Application(
                job_id=job.id,
                full_name=name,
                email=email,
                phone=phone,
                cv_file=unique_filename
            )

            print(application.__dict__)
            db.session.add(application)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return redirect_to_error(500, "Đã có lỗi xảy ra khi nộp hồ sơ.")

    return render_template('job_detail.html', job=job)