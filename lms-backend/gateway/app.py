from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os, requests

app = Flask(__name__)

# CORS for the Angular app; restrict origins if you prefer
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type", "Authorization"],
)

# Upstream service URLs (resolved via docker-compose service names)
USER_SVC  = os.getenv("USER_SVC_URL",  "http://user_service:5000")
LEAVE_SVC = os.getenv("LEAVE_SVC_URL", "http://leave_service:5000")

# ----------------------------- Helpers --------------------------------------
FORWARD_HEADER_WHITELIST = {
    "authorization", "content-type", "accept", "accept-language", "x-requested-with"
}

def _pick_headers(src_headers):
    # keep only safe, needed headers
    return {k: v for k, v in src_headers.items() if k.lower() in FORWARD_HEADER_WHITELIST}

def _json_body_for_method(method: str):
    # Only attach JSON body for methods that normally have a body
    if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
        return request.get_json(silent=True)
    return None

def _forward(base_url: str, path: str = ""):
    # Build upstream URL
    if path:
        if not path.startswith("/"):
            path = "/" + path
    url = f"{base_url}{path}"

    # Forward method, headers, params, and JSON body
    method  = request.method
    headers = _pick_headers(request.headers)
    params  = request.args
    json    = _json_body_for_method(method)

    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            timeout=30,
        )
    except Exception as e:
        return jsonify({"error": "gateway-exception", "detail": str(e)}), 502

    # Try to return JSON; if non-JSON upstream, pass through bytes with content-type
    ct = resp.headers.get("Content-Type", "")
    if "application/json" in ct.lower():
        try:
            data = resp.json()
        except ValueError:
            data = {"error": "upstream-non-json", "status": resp.status_code, "body": resp.text[:2000]}
        return jsonify(data), resp.status_code
    else:
        # Pass through body and content-type for non-JSON responses
        out_headers = {}
        if ct:
            out_headers["Content-Type"] = ct
        # Avoid passing hop-by-hop headers
        return Response(resp.content, status=resp.status_code, headers=out_headers)

# ------------------------------ Health --------------------------------------
@app.get("/health")
def health_root():
    return jsonify({"status": "ok"}), 200

@app.get("/api/health")
def health_api():
    return jsonify({"status": "ok"}), 200

# ------------------------------ Auth ----------------------------------------
@app.post("/api/auth/login")
def auth_login():
    # POST /api/auth/login -> user_service /auth/login
    return _forward(USER_SVC, "/auth/login")

# Optional alias: Manager-only user creation via /api/auth/register
@app.post("/api/auth/register")
def auth_register():
    return _forward(USER_SVC, "/users")

# ------------------------------ Users ---------------------------------------
@app.route("/api/users", methods=["GET", "POST"])
def users_root():
    # GET /api/users  -> list (manager-only)
    # POST /api/users -> create (manager-only)
    return _forward(USER_SVC, "/users")

@app.route("/api/users/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def users_sub(subpath: str):
    # e.g. GET /api/users/123
    return _forward(USER_SVC, f"/users/{subpath}")

# ------------------------------ Leaves --------------------------------------
@app.route("/api/leaves", methods=["GET", "POST"])
def leaves_root():
    # GET not used (your API uses /leaves/mine and /leaves/pending), POST creates
    return _forward(LEAVE_SVC, "/leaves")

@app.route("/api/leaves/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def leaves_sub(subpath: str):
    # Covers:
    #   GET  /api/leaves/mine
    #   GET  /api/leaves/pending
    #   POST /api/leaves/<id>/approve  (JSON {remark})
    #   POST /api/leaves/<id>/reject   (JSON {remark})
    return _forward(LEAVE_SVC, f"/leaves/{subpath}")

# ------------------------------ Logout --------------------------------------
@app.post("/api/auth/logout")
def logout():
    # Stateless JWT: clients should discard their token
    return jsonify({"message": "Logged out. Please clear token on client side."}), 200

# ------------------------------ Main ----------------------------------------
if __name__ == "__main__":
    # For local dev; in Docker we run via gunicorn
    app.run(host="0.0.0.0", port=8080)
