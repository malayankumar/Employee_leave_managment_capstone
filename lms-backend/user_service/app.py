from flask import Flask, request, jsonify
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import os, jwt, datetime, re, time
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL", "mysql+pymysql://root:root@mysql:3306/lms_db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = { "pool_pre_ping": True, "pool_recycle": 280 }

SECRET = os.getenv("JWT_SECRET", "dev_secret")
MANAGER_EMAIL = (os.getenv("MANAGER_EMAIL", "malayankumar@gmail.com") or "").strip().lower()

def verify_token(auth_header: str):
    if not auth_header:
        return None
    try:
        token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return None

def is_valid_email(email: str) -> bool:
    import re as _re
    return _re.match(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$", email or "") is not None

db.init_app(app)

def init_db_with_retry_and_seed(tries: int = 30, delay: float = 2.0):
    for i in range(1, tries + 1):
        try:
            with app.app_context():
                db.session.execute(text("SELECT 1"))
                db.create_all()
                mgr = User.query.filter_by(email=MANAGER_EMAIL).first()
                if not mgr:
                    db.session.add(User(
                        name="Manager",
                        email=MANAGER_EMAIL,
                        password_hash=generate_password_hash("12345"),
                        role="MANAGER"
                    ))
                    db.session.commit()
            print(f"[user_service] DB ready after {i} attempt(s).", flush=True)
            return
        except OperationalError as e:
            print(f"[user_service] DB not ready (attempt {i}/30): {e}", flush=True)
            time.sleep(delay)
    with app.app_context():
        db.session.execute(text("SELECT 1"))
        db.create_all()

init_db_with_retry_and_seed()

@app.get("/health")
def health():
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "degraded", "error": str(e)}), 500

@app.post("/auth/login")
def login():
    data = request.get_json() or {}
    email, password = (data.get("email") or "").strip().lower(), data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401
    payload = {
        "sub": user.id, "role": user.role, "name": user.name, "email": user.email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    token = jwt.encode(payload, SECRET, algorithm="HS256")
    return jsonify({"token": token, "role": user.role, "name": user.name})

@app.get("/users/<int:uid>")
def get_user(uid):
    u = User.query.get_or_404(uid)
    return jsonify({"id": u.id, "name": u.name, "email": u.email, "role": u.role})

@app.post("/users")
def create_user():
    claims = verify_token(request.headers.get("Authorization"))
    if not claims or claims.get("role") != "MANAGER":
        return jsonify({"message": "Forbidden"}), 403
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or "12345"
    role = (data.get("role") or "EMPLOYEE").upper()
    if not name or not is_valid_email(email):
        return jsonify({"message": "Name and valid email are required"}), 400
    if role not in ("EMPLOYEE", "MANAGER"):
        return jsonify({"message": "Invalid role"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409
    u = User(name=name, email=email, password_hash=generate_password_hash(password), role=role)
    db.session.add(u); db.session.commit()
    return jsonify({"id": u.id, "name": u.name, "email": u.email, "role": u.role}), 201

@app.get("/users")
def list_users():
    claims = verify_token(request.headers.get("Authorization"))
    if not claims or claims.get("role") != "MANAGER":
        return jsonify({"message": "Forbidden"}), 403
    rows = User.query.order_by(User.id.asc()).all()
    return jsonify([{"id":u.id, "name":u.name, "email":u.email, "role":u.role} for u in rows])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
