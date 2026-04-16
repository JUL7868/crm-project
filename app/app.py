from flask import Flask, render_template, request, redirect
import os
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "crm.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# CREATE TABLES (RUNS ON STARTUP)
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prospects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        company TEXT,
        status TEXT,
        next_action TEXT,
        follow_up TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prospect_id INTEGER,
        text TEXT,
        timestamp TEXT
    );
    """)

    conn.commit()
    conn.close()


create_tables()


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except:
        return None


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


@app.route("/prospect/<int:pid>")
def prospect(pid):
    conn = get_db_connection()

    p = conn.execute("SELECT * FROM prospects WHERE id = ?", (pid,)).fetchone()

    notes = conn.execute(
        "SELECT text, timestamp FROM notes WHERE prospect_id = ? ORDER BY id DESC",
        (pid,)
    ).fetchall()

    conn.close()

    if not p:
        return "Not found", 404

    p_dict = dict(p)
    p_dict["notes"] = [{"text": n["text"], "timestamp": n["timestamp"]} for n in notes]

    return render_template("prospect.html", p=p_dict)


@app.route("/add")
def add_page():
    return render_template("add_prospect.html")


@app.route("/add_prospect", methods=["POST"])
def add_prospect():
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


@app.route("/add_note/<int:pid>", methods=["POST"])
def add_note(pid):
    note = request.form.get("note")

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO notes (prospect_id, text, timestamp) VALUES (?, ?, ?)",
        (pid, note, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

    return redirect(f"/prospect/{pid}")


@app.route("/update_status/<int:pid>", methods=["POST"])
def update_status(pid):
    status = request.form.get("status")

    conn = get_db_connection()
    conn.execute(
        "UPDATE prospects SET status = ? WHERE id = ?",
        (status, pid)
    )
    conn.commit()
    conn.close()

    return redirect(f"/prospect/{pid}")


@app.route("/set_followup/<int:pid>", methods=["POST"])
def set_followup(pid):
    date = request.form.get("date")

    conn = get_db_connection()
    conn.execute(
        "UPDATE prospects SET follow_up = ? WHERE id = ?",
        (date, pid)
    )
    conn.commit()
    conn.close()

    return redirect(f"/prospect/{pid}")


@app.route("/quick_contact/<int:pid>", methods=["POST"])
def quick_contact(pid):
    conn = get_db_connection()
    conn.execute(
        "UPDATE prospects SET status = ?, follow_up = NULL WHERE id = ?",
        ("contacted", pid)
    )
    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/quick_snooze/<int:pid>", methods=["POST"])
def quick_snooze(pid):
    conn = get_db_connection()

    p = conn.execute("SELECT follow_up FROM prospects WHERE id = ?", (pid,)).fetchone()

    dt = parse_date(p["follow_up"]) if p and p["follow_up"] else None

    if dt:
        dt = dt + timedelta(days=1)
    else:
        dt = datetime.now() + timedelta(days=1)

    conn.execute(
        "UPDATE prospects SET follow_up = ? WHERE id = ?",
        (dt.strftime("%Y-%m-%d %H:%M"), pid)
    )

    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)