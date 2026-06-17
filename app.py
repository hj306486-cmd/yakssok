from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import uuid
import json
from datetime import datetime

app = Flask(__name__, template_folder="templates")
app.secret_key = "yakssok-secret-key-2024"
CORS(app)

appointments = {}
users = {}

@app.route("/")
def index():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())[:8]
        session["username"] = f"친구{session['user_id'][:4]}"
    return render_template("index.html", username=session["username"])

@app.route("/set_name", methods=["POST"])
def set_name():
    data = request.json
    session["username"] = data["name"]
    return jsonify({"ok": True, "name": session["username"]})

@app.route("/create", methods=["POST"])
def create():
    data = request.json
    aid = str(uuid.uuid4())[:8]
    appointments[aid] = {
        "id": aid,
        "type": data["type"],
        "host": session["username"],
        "host_id": session["user_id"],
        "times": data.get("times", []),
        "date": data.get("date", ""),
        "place": data.get("place", "미정"),
        "message": data.get("message", ""),
        "participants": [session["username"]],
        "confirmed": False,
        "pending": [],
        "vote_places": [],
        "votes": {},
        "created_at": datetime.now().strftime("%H:%M"),
    }
    return jsonify({"ok": True, "id": aid})

@app.route("/get/<aid>")
def get_appointment(aid):
    appt = appointments.get(aid)
    if not appt:
        return jsonify({"ok": False, "error": "없는 약속"}), 404
    return jsonify({"ok": True, "appointment": appt})

@app.route("/respond/<aid>", methods=["POST"])
def respond(aid):
    appt = appointments.get(aid)
    if not appt:
        return jsonify({"ok": False}), 404
    data = request.json
    name = session["username"]
    if data["action"] == "accept":
        if name not in appt["pending"]:
            appt["pending"].append(name)
        return jsonify({"ok": True, "status": "pending"})
    else:
        return jsonify({"ok": True, "status": "rejected"})

@app.route("/approve/<aid>", methods=["POST"])
def approve(aid):
    appt = appointments.get(aid)
    if not appt:
        return jsonify({"ok": False}), 404
    if session["user_id"] != appt["host_id"]:
        return jsonify({"ok": False, "error": "주최자만 가능"}), 403
    data = request.json
    name = data["name"]
    if name in appt["pending"]:
        appt["pending"].remove(name)
        appt["participants"].append(name)
    return jsonify({"ok": True, "participants": appt["participants"]})

@app.route("/confirm/<aid>", methods=["POST"])
def confirm(aid):
    appt = appointments.get(aid)
    if not appt:
        return jsonify({"ok": False}), 404
    if session["user_id"] != appt["host_id"]:
        return jsonify({"ok": False, "error": "주최자만 가능"}), 403
    appt["confirmed"] = True
    return jsonify({"ok": True})

@app.route("/vote_place/<aid>", methods=["POST"])
def vote_place(aid):
    appt = appointments.get(aid)
    if not appt:
        return jsonify({"ok": False}), 404
    data = request.json
    if data.get("suggest"):
        place = data["suggest"]
        if place not in appt["vote_places"]:
            appt["vote_places"].append(place)
    if data.get("vote"):
        appt["votes"][session["username"]] = data["vote"]
    return jsonify({"ok": True, "places": appt["vote_places"], "votes": appt["votes"]})

@app.route("/vote_result/<aid>")
def vote_result(aid):
    appt = appointments.get(aid)
    if not appt:
        return jsonify({"ok": False}), 404
    votes = appt["votes"]
    tally = {}
    for v in votes.values():
        tally[v] = tally.get(v, 0) + 1
    if not tally:
        return jsonify({"ok": True, "result": None, "tally": {}})
    max_v = max(tally.values())
    winners = [p for p, c in tally.items() if c == max_v]
    return jsonify({"ok": True, "result": winners, "tally": tally, "tie": len(winners) > 1})

if __name__ == "__main__":
    app.run(debug=True)
