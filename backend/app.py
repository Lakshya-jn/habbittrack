from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

SUPABASE_URL = "https://mgysuyanggfbtybtfhpv.supabase.co"
SUPABASE_KEY = "sb_publishable_lxp9nPGeL9pcQCv7e63PAA_DTHKJgpb"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def predict_priority(text):
    t = text.lower()
    if any(w in t for w in ["urgent","deadline","exam","submit","asap","due","final","test","quiz"]):
        return "high"
    elif any(w in t for w in ["maybe","someday","optional","later","eventually","chill"]):
        return "low"
    return "med"

def predict_category(text):
    t = text.lower()
    if any(w in t for w in ["study","assignment","exam","lecture","notes","homework","lab","course","learn"]):
        return "Study"
    if any(w in t for w in ["gym","exercise","eat","sleep","medicine","doctor","workout","run","yoga","diet"]):
        return "Health"
    if any(w in t for w in ["meeting","report","email","client","presentation","work","office","boss","call"]):
        return "Work"
    return "Personal"

# ── AUTH - SIGNUP ─────────────────────────────────────────────────────────────
@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "")
    res = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        },
        json={
            "email": email,
            "password": password,
            "data": { "full_name": name }
        }
    )
    result = res.json()
    print("SIGNUP response:", result)
    if "error" in result and result["error"]:
        return jsonify({"error": result.get("error_description", "Signup failed")}), 400
    if result.get("id"):
        return jsonify({"message": "Account created! Please check your email to confirm."})
    return jsonify({"message": "Account created! Please login."})

# ── AUTH - LOGIN ──────────────────────────────────────────────────────────────
@app.route("/api/auth/login", methods=["POST"])
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    res = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        },
        json={"email": email, "password": password}
    )
    result = res.json()
    print("LOGIN response:", result)
    if "error" in result or "error_code" in result:
        msg = result.get("msg", result.get("error_description", "Login failed"))
        return jsonify({"error": msg}), 401
    user = result.get("user", {})
    return jsonify({
        "token": result.get("access_token"),
        "user": {
            "id": user.get("id"),
            "email": user.get("email"),
            "name": user.get("user_metadata", {}).get("full_name", email)
        }
    })
    result = res.json()
    print("LOGIN response:", result)
    if "error" in result:
        return jsonify({"error": result.get("error_description", "Login failed")}), 401
    return jsonify({
        "token": result.get("access_token"),
        "user": {
            "id": result["user"]["id"],
            "email": result["user"]["email"],
            "name": result["user"].get("user_metadata", {}).get("full_name", email)
        }
    })

# ── ANALYZE ───────────────────────────────────────────────────────────────────
@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "")
    return jsonify({
        "priority": predict_priority(text),
        "category": predict_category(text)
    })

# ── GET TASKS (user specific) ─────────────────────────────────────────────────
@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    user_id = request.args.get("user_id")
    url = f"{SUPABASE_URL}/rest/v1/todos?select=*&order=id.desc"
    if user_id:
        url += f"&user_id=eq.{user_id}"
    res = requests.get(url, headers=HEADERS)
    return jsonify(res.json())

# ── ADD TASK ──────────────────────────────────────────────────────────────────
@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.json
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/todos",
        headers=HEADERS,
        json=data
    )
    print("ADD task status:", res.status_code)
    return jsonify(res.json())

# ── UPDATE TASK ───────────────────────────────────────────────────────────────
@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.json
    res = requests.patch(
        f"{SUPABASE_URL}/rest/v1/todos?id=eq.{task_id}",
        headers=HEADERS,
        json=data
    )
    return jsonify(res.json())

# ── DELETE TASK ───────────────────────────────────────────────────────────────
@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    requests.delete(
        f"{SUPABASE_URL}/rest/v1/todos?id=eq.{task_id}",
        headers=HEADERS
    )
    return jsonify({"success": True})

# ── GET STREAKS (user specific) ───────────────────────────────────────────────
@app.route("/api/streaks", methods=["GET"])
def get_streaks():
    user_id = request.args.get("user_id")
    url = f"{SUPABASE_URL}/rest/v1/streaks?select=*"
    if user_id:
        url += f"&user_id=eq.{user_id}"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    return jsonify(data[0] if data else {})

# ── SAVE STREAKS ──────────────────────────────────────────────────────────────
@app.route("/api/streaks", methods=["POST"])
def save_streaks():
    data = request.json
    user_id = data.get("user_id")
    # check if exists
    check = requests.get(
        f"{SUPABASE_URL}/rest/v1/streaks?select=*&user_id=eq.{user_id}",
        headers=HEADERS
    )
    existing = check.json()
    if existing:
        res = requests.patch(
            f"{SUPABASE_URL}/rest/v1/streaks?user_id=eq.{user_id}",
            headers=HEADERS,
            json=data
        )
    else:
        res = requests.post(
            f"{SUPABASE_URL}/rest/v1/streaks",
            headers=HEADERS,
            json=data
        )
    return jsonify(res.json())

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)