# FILE: /app/app.py

from flask import Flask, render_template, request, redirect
import json
import os
import sqlite3

from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "crm.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_prospects_from_db():
    conn = get_db_connection()
    
    prospects = conn.execute("SELECT * FROM prospects").fetchall()

    result = []

    for p in prospects:
        notes = conn.execute(
            "SELECT text, timestamp FROM notes WHERE prospect_id = ? ORDER BY id DESC",
            (p["id"],)
        ).fetchall()

        result.append({
            "id": p["id"],
            "name": p["name"],
            "company": p["company"],
            "status": p["status"],
            "next_action": p["next_action"],
            "follow_up": p["follow_up"],
            "notes": [{"text": n["text"], "timestamp": n["timestamp"]} for n in notes]
        })

    conn.close()
    return result

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'prospects.json')


def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def generate_id():
    return str(uuid.uuid4())


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except:
        return None


@app.route("/")
def dashboard():
    data = load_prospects_from_db()
    now = datetime.now()

    overdue, upcoming, no_follow = [], [], []

    for p in data:
        dt = parse_date(p.get("follow_up")) if p.get("follow_up") else None

        if dt:
            temp = dict(p)
            temp["_dt"] = dt
            if dt < now:
                overdue.append(temp)
            else:
                upcoming.append(temp)
        else:
            no_follow.append(p)

    overdue.sort(key=lambda x: x["_dt"])
    upcoming.sort(key=lambda x: x["_dt"])
    no_follow.sort(key=lambda x: x.get("id"), reverse=True)

    for x in overdue + upcoming:
        x.pop("_dt", None)

    return render_template("dashboard.html",
        overdue=overdue,
        upcoming=upcoming,
        no_follow=no_follow
    )


@app.route("/prospect/<pid>")
def prospect(pid):
    data = load_data()
    p = next((x for x in data if x["id"] == pid), None)
    return render_template("prospect.html", p=p)


@app.route("/add")
def add_page():
    return render_template("add_prospect.html")


@app.route("/add_prospect", methods=["GET", "POST"])
def add_prospect():
    if request.method == "POST":
        name = request.form.get("name")
        company = request.form.get("company")

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO prospects (name, company, status) VALUES (?, ?, ?)",
            (name, company, "new")
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_prospect.html")


@app.route("/add_note/<pid>", methods=["POST"])
def add_note(pid):
    data = load_data()

    for p in data:
        if p["id"] == pid:
            p.setdefault("notes", []).append({
                "text": request.form.get("note"),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    save_data(data)
    return redirect(f"/prospect/{pid}")


@app.route("/update_status/<pid>", methods=["POST"])
def update_status(pid):
    data = load_data()
    for p in data:
        if p["id"] == pid:
            p["status"] = request.form.get("status")
    save_data(data)
    return redirect(f"/prospect/{pid}")


@app.route("/set_followup/<pid>", methods=["POST"])
def set_followup(pid):
    data = load_data()
    for p in data:
        if p["id"] == pid:
            p["follow_up"] = request.form.get("date")
    save_data(data)
    return redirect(f"/prospect/{pid}")


# QUICK ACTIONS

@app.route("/quick_contact/<pid>", methods=["POST"])
def quick_contact(pid):
    data = load_data()

    for p in data:
        if p["id"] == pid:
            p["status"] = "contacted"
            p["follow_up"] = None

    save_data(data)
    return redirect("/")


@app.route("/quick_snooze/<pid>", methods=["POST"])
def quick_snooze(pid):
    data = load_data()

    for p in data:
        if p["id"] == pid:
            dt = parse_date(p.get("follow_up"))

            if dt:
                dt = dt + timedelta(days=1)
            else:
                dt = datetime.now() + timedelta(days=1)

            p["follow_up"] = dt.strftime("%Y-%m-%d %H:%M")

    save_data(data)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)