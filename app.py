from flask import Flask, request, jsonify, render_template, g
import sqlite3
import datetime
from flask_cors import CORS

DATABASE = "beds.db"
app = Flask(__name__)
CORS(app)

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open("schema.sql", mode="r") as f:
            db.executescript(f.read())
        db.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/hospitals", methods=["GET"])
def get_hospital_data():
    db = get_db()
    rows = db.execute("SELECT h.id, h.name, h.city, br.total_beds, br.occupied_beds, br.updated_at FROM hospitals h LEFT JOIN bed_records br ON h.id = br.hospital_id ORDER BY br.updated_at DESC").fetchall()
    hospitals = []
    for r in rows:
        if r["total_beds"] is not None:
            available = r["total_beds"] - r["occupied_beds"]
            pct = 0 if r["total_beds"] == 0 else round(available / r["total_beds"] * 100, 1)
            if pct > 30:
                status = "Available"
                color = "green"
            elif pct > 10:
                status = "Limited"
                color = "yellow"
            else:
                status = "Full"
                color = "red"
            likely_full = "Yes" if pct < 20 else "No"
        else:
            available = None
            pct = None
            status = "No data"
            color = "gray"
            likely_full = "No data"

        hospitals.append({
            "id": r["id"],
            "name": r["name"],
            "city": r["city"],
            "total_beds": r["total_beds"],
            "occupied_beds": r["occupied_beds"],
            "available_beds": available,
            "percentage": pct,
            "status": status,
            "color": color,
            "likely_full": likely_full,
            "updated_at": r["updated_at"]
        })
    return jsonify(hospitals)

@app.route("/api/update", methods=["POST"])
def update_beds():
    payload = request.get_json()
    hospital_id = payload.get("hospital_id")
    total_beds = int(payload.get("total_beds", 0))
    occupied_beds = int(payload.get("occupied_beds", 0))
    icu_beds = int(payload.get("icu_beds", 0))
    note = payload.get("note", "")

    if total_beds < 0 or occupied_beds < 0 or occupied_beds > total_beds:
        return jsonify({"error": "Invalid bed counts"}), 400

    now = datetime.datetime.utcnow().isoformat()
    db = get_db()
    db.execute(
        "INSERT INTO bed_records (hospital_id, total_beds, occupied_beds, icu_beds, note, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (hospital_id, total_beds, occupied_beds, icu_beds, note, now),
    )
    db.commit()
    return jsonify({"status": "ok", "updated_at": now})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
