from flask import Flask, request, jsonify
from models import db, LeaveRequest
import os, jwt, requests, time
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from datetime import date

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL", "mysql+pymysql://root:root@mysql:3306/lms_db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 280}
SECRET = os.getenv("JWT_SECRET", "dev_secret")

NOTIFY_URL = os.getenv("NOTIFY_URL", "http://notification_service:5002")
USER_SVC   = os.getenv("USER_SVC_URL", "http://user_service:5000")
MANAGER_EMAIL = os.getenv("MANAGER_EMAIL", "manager@example.com")

# Leave policy
LEAVE_TYPES = {"MEDICAL", "SICK", "PRIVILEGED"}
LEAVES_PER_YEAR = 12

db.init_app(app)

def init_db_with_retry(tries: int = 30, delay: float = 2.0):
    for i in range(1, tries + 1):
        try:
            with app.app_context():
                db.session.execute(text("SELECT 1"))
                db.create_all()
            print(f"[leave_service] DB ready after {i} attempt(s).", flush=True)
            return
        except OperationalError as e:
            print(f"[leave_service] DB not ready (attempt {i}/{tries}): {e}", flush=True)
            time.sleep(delay)
    with app.app_context():
        db.session.execute(text("SELECT 1"))
        db.create_all()

init_db_with_retry()

def claims():
    try:
        auth = request.headers.get("Authorization","")
        token = auth.split(" ")[1] if " " in auth else auth
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return None

def notify_email(to_email: str, subject: str, body: str):
    try:
        resp = requests.post(
            f"{NOTIFY_URL}/notify/email",
            json={"to": to_email, "subject": subject, "body": body},
            timeout=10,
        )
        _ = resp.json() if resp.content else {}
    except Exception as e:
        print(f"[WARN] notify failed: {e}", flush=True)

def user_email_by_id(uid: int) -> str:
    try:
        r = requests.get(f"{USER_SVC}/users/{uid}", timeout=5)
        if r.status_code == 200:
            return (r.json() or {}).get("email", "")
    except Exception as e:
        print(f"[WARN] user lookup failed: {e}", flush=True)
    return ""

def user_name_by_id(uid: int) -> str:
    """Try user-service for name; fallback to last known leave record."""
    try:
        r = requests.get(f"{USER_SVC}/users/{uid}", timeout=5)
        if r.status_code == 200:
            return (r.json() or {}).get("name", "") or ""
    except Exception as e:
        print(f"[WARN] user name lookup failed: {e}", flush=True)
    try:
        rec = LeaveRequest.query.filter_by(user_id=uid).order_by(LeaveRequest.id.desc()).first()
        if rec and rec.employee_name:
            return rec.employee_name
    except Exception as e:
        print(f"[WARN] fallback user name lookup failed: {e}", flush=True)
    return ""

# -------- helpers: dates, overlap, balances --------

def _to_date(v):
    # Accept date objects or strings; keep only YYYY-MM-DD if time present
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if len(s) >= 10:
        s = s[:10]
    return date.fromisoformat(s)

def _days_inclusive(a: date, b: date) -> int:
    return (b - a).days + 1

def _days_in_year_overlap(start: date, end: date, year: int) -> int:
    ys, ye = date(year, 1, 1), date(year, 12, 31)
    s = max(start, ys)
    e = min(end, ye)
    return _days_inclusive(s, e) if e >= s else 0

def _has_overlap(user_id: int, start_s: str, end_s: str, exclude_id: int | None = None):
    # Overlap if (start <= existing.end) and (end >= existing.start)
    q = LeaveRequest.query.filter(
        LeaveRequest.user_id == user_id,
        LeaveRequest.status.in_(("PENDING", "APPROVED")),
        LeaveRequest.start_date <= end_s,
        LeaveRequest.end_date >= start_s,
    )
    if exclude_id:
        q = q.filter(LeaveRequest.id != exclude_id)
    return q.first()

def _taken_days(user_id: int, year: int, leave_type: str) -> int:
    items = LeaveRequest.query.filter_by(user_id=user_id, type=leave_type, status="APPROVED").all()
    total = 0
    for x in items:
        xs = _to_date(x.start_date)
        xe = _to_date(x.end_date)
        total += _days_in_year_overlap(xs, xe, year)
    return total

def _balance_for_user(user_id: int, year: int):
    name = user_name_by_id(user_id)
    balances = {}
    for t in LEAVE_TYPES:
        taken = _taken_days(user_id, year, t)
        remaining = max(0, LEAVES_PER_YEAR - taken)
        balances[t] = {"allowed": LEAVES_PER_YEAR, "taken": taken, "remaining": remaining}
    return {"user_id": user_id, "name": name, "year": year, "balances": balances}

# ---------------- routes ----------------

@app.get("/health")
def health():
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "degraded", "error": str(e)}), 500

@app.get("/leaves/mine")
def my_leaves():
    c = claims()
    if not c:
        return jsonify({"message":"Unauthorized"}), 401
    items = LeaveRequest.query.filter_by(user_id=c["sub"]).order_by(LeaveRequest.id.desc()).all()
    return jsonify([{
        "id": x.id,
        "type": x.type,
        "start_date": x.start_date,
        "end_date": x.end_date,
        "reason": x.reason,
        "status": x.status,
        "decision_remark": (x.decision_remark or ""),
    } for x in items])

@app.get("/leaves/balance")
def my_balance():
    c = claims()
    if not c:
        return jsonify({"message":"Unauthorized"}), 401
    year = int(request.args.get("year", date.today().year))
    return jsonify(_balance_for_user(c["sub"], year)), 200

@app.get("/leaves/balance/<int:user_id>")
def balance_user(user_id: int):
    c = claims()
    if not c or c.get("role") != "MANAGER":
        return jsonify({"message": "Forbidden"}), 403
    year = int(request.args.get("year", date.today().year))
    return jsonify(_balance_for_user(user_id, year)), 200

@app.get("/leaves/balance/all")
def balance_all():
    c = claims()
    if not c or c.get("role") != "MANAGER":
        return jsonify({"message": "Forbidden"}), 403
    year = int(request.args.get("year", date.today().year))
    try:
        ids = [int(uid) for (uid,) in db.session.query(LeaveRequest.user_id).distinct().all()]
        result = [_balance_for_user(uid, year) for uid in ids]
        return jsonify(result), 200
    except Exception as e:
        print(f"[ERROR] /leaves/balance/all failed: {e}", flush=True)
        return jsonify({"message": "Failed to compute balances"}), 500

@app.post("/leaves")
def create_leave():
    c = claims()
    if not c:
        return jsonify({"message": "Unauthorized"}), 401
    p = request.get_json(silent=True) or {}

    ltype   = (p.get("type") or "").upper().strip()
    start_s = (p.get("start_date") or "").strip()
    end_s   = (p.get("end_date") or "").strip()
    reason  = p.get("reason")

    if ltype not in LEAVE_TYPES:
        return jsonify({"message": f"Invalid leave type. Allowed: {sorted(LEAVE_TYPES)}"}), 400
    try:
        start_d = _to_date(start_s)
        end_d   = _to_date(end_s)
    except Exception:
        return jsonify({"message": "start_date and end_date must be YYYY-MM-DD"}), 400
    if end_d < start_d:
        return jsonify({"message": "end_date cannot be before start_date"}), 400

    # Block overlapping leaves (pending/approved) for same user
    if _has_overlap(c["sub"], start_s, end_s):
        return jsonify({"message": "Overlapping leave exists for these dates"}), 409

    # Enforce annual quota; keep 1-year requests only (simpler accounting)
    if start_d.year != end_d.year:
        return jsonify({"message": "Leave request cannot span multiple calendar years"}), 400

    year = start_d.year
    requested_days = _days_inclusive(start_d, end_d)
    already_taken = _taken_days(c["sub"], year, ltype)
    remaining = max(0, LEAVES_PER_YEAR - already_taken)
    if requested_days > remaining:
        return jsonify({
            "message": "Insufficient balance for this leave type",
            "type": ltype,
            "year": year,
            "allowed": LEAVES_PER_YEAR,
            "taken": already_taken,
            "remaining": remaining,
            "requested": requested_days,
        }), 400

    lr = LeaveRequest(
        user_id=c["sub"], employee_name=c.get("name"), type=ltype,
        start_date=start_s, end_date=end_s, reason=reason,
    )
    db.session.add(lr); db.session.commit()

    details = (
        f"Leave Request Created\n"
        f"----------------------\n"
        f"Request ID : {lr.id}\n"
        f"Employee   : {lr.employee_name} (user_id={lr.user_id}, email={c.get('email','-')})\n"
        f"Type       : {lr.type}\n"
        f"Dates      : {lr.start_date} → {lr.end_date}\n"
        f"Reason     : {reason or '-'}\n"
        f"Status     : {lr.status}\n"
    )
    subj = f"New Leave from {lr.employee_name} (#{lr.id})"
    notify_email(MANAGER_EMAIL, subj, details)

    payload = {
        "id": lr.id, "user_id": lr.user_id, "employee_name": lr.employee_name,
        "type": lr.type, "start_date": lr.start_date, "end_date": lr.end_date,
        "reason": lr.reason, "status": lr.status, "approver_id": lr.approver_id,
        "created_at": lr.created_at.isoformat() if lr.created_at else None,
    }
    resp = jsonify(payload); resp.status_code = 201
    resp.headers["Location"] = f"/leaves/{lr.id}"
    return resp

@app.get("/leaves/pending")
def pending():
    c = claims()
    if not c or c.get("role")!="MANAGER":
        return jsonify({"message":"Forbidden"}), 403
    items = LeaveRequest.query.filter_by(status="PENDING").order_by(LeaveRequest.id.desc()).all()
    return jsonify([{
        "id": x.id,
        "employee_name": x.employee_name,
        "type": x.type,
        "start_date": x.start_date,
        "end_date": x.end_date,
        "reason": x.reason,
    } for x in items])

@app.post("/leaves/<int:lid>/approve")
def approve(lid):
    c = claims()
    if not c or c.get("role")!="MANAGER":
        return jsonify({"message":"Forbidden"}), 403
    x = LeaveRequest.query.get_or_404(lid)

    # Double-check quota and overlap at approval time
    year = _to_date(x.start_date).year
    add_days = _days_inclusive(_to_date(x.start_date), _to_date(x.end_date))
    taken = _taken_days(x.user_id, year, x.type)
    if taken + add_days > LEAVES_PER_YEAR:
        return jsonify({
            "message": "Approval would exceed annual quota",
            "type": x.type, "year": year,
            "allowed": LEAVES_PER_YEAR, "taken": taken,
            "requested_additional": add_days,
            "excess_by": taken + add_days - LEAVES_PER_YEAR,
        }), 400

    if _has_overlap(x.user_id, x.start_date, x.end_date, exclude_id=x.id):
        return jsonify({"message": "Overlapping leave exists for these dates"}), 409

    data = request.get_json(silent=True) or {}
    remark = (data.get("remark") or "").strip()
    x.status = "APPROVED"; x.approver_id = c["sub"]; x.decision_remark = remark
    db.session.commit()

    to = user_email_by_id(x.user_id)
    subj = f"Your Leave Request #{x.id} was APPROVED"
    body = (f"Hi {x.employee_name},\n\nYour {x.type} leave from {x.start_date} to {x.end_date} has been APPROVED."
            + (f"\n\nManager remark: {x.decision_remark}" if x.decision_remark else "")
            + "\n\nRegards,\nLeave Management System")
    if to: notify_email(to, subj, body)
    return jsonify({"ok": True})

@app.post("/leaves/<int:lid>/reject")
def reject(lid):
    c = claims()
    if not c or c.get("role")!="MANAGER":
        return jsonify({"message":"Forbidden"}), 403
    x = LeaveRequest.query.get_or_404(lid)
    data = request.get_json(silent=True) or {}
    remark = (data.get("remark") or "").strip()
    x.status = "REJECTED"; x.approver_id = c["sub"]; x.decision_remark = remark
    db.session.commit()
    to = user_email_by_id(x.user_id)
    subj = f"Your Leave Request #{x.id} was REJECTED"
    body = (f"Hi {x.employee_name},\n\nYour {x.type} leave from {x.start_date} to {x.end_date} has been REJECTED."
            + (f"\n\nManager remark: {x.decision_remark}" if x.decision_remark else "")
            + "\n\nRegards,\nLeave Management System")
    if to: notify_email(to, subj, body)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
