from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class LeaveRequest(db.Model):
    __tablename__ = "leaves"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    employee_name = db.Column(db.String(120))
    type = db.Column(db.String(20), nullable=False)  # MEDICAL, SICK, PIVELEGED
    start_date = db.Column(db.String(10), nullable=False)
    end_date = db.Column(db.String(10), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default="PENDING")  # PENDING/APPROVED/REJECTED
    approver_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    decision_remark = db.Column(db.String(255))
