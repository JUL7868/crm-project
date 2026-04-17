from flask import Flask, render_template, request, redirect
import os
import psycopg2
from datetime import datetime, timedelta

app = Flask(__name__)


# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    return psycopg2.connect(
    os.environ["DATABASE_URL"],
    sslmode="require"
)

# =========================
# CREATE TABLES (RUN ON START)
# =========================
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prospects (
        id SERIAL PRIMARY KEY,
        name TEXT,
        company TEXT,
        status TEXT,
        next_action TEXT,
        follow_up TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        prospect_id INTEGER,
        text TEXT,
        timestamp TEXT
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

try:
    create_tables()
except Exception as e:
    print("DB INIT FAILED:", e)

# =========================
# HELPERS
# =========================
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except:
        return None


def load_prospects_from_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM prospects")
    prospects = cur.fetchall()

    result = []

    for p in prospects:
        pid = p[0]

        cur.execute(
            "SELECT text, timestamp FROM notes WHERE prospect_id = %s ORDER BY id DESC",
            (pid,)
        )
        notes = cur.fetchall()

        result.append({
            "id": p[0],
            "name": p[1],
            "company": p[2],
            "status": p[3],
            "next_action": p[4],
            "follow_up": p[5],
            "notes": [{"text": n[0], "timestamp": n[1]} for n in notes]
        })

    cur.close()
    conn.close()
    return result


# =========================
# ROUTES
# =========================
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
    cur = conn.cursor()

    cur.execute("SELECT * FROM prospects WHERE id = %s", (pid,))
    p = cur.fetchone()

    if not p:
        return "Not found", 404

    cur.execute(
        "SELECT text, timestamp FROM notes WHERE prospect_id = %s ORDER BY id DESC",
        (pid,)
    )
    notes = cur.fetchall()

    cur.close()
    conn.close()

    p_dict = {
        "id": p[0],
        "name": p[1],
        "company": p[2],
        "status": p[3],
        "next_action": p[4],
        "follow_up": p[5],
        "notes": [{"text": n[0], "timestamp": n[1]} for n in notes]
    }

    return render_template("prospect.html", p=p_dict)


@app.route("/add")
def add_page():
    return render_template("add_prospect.html")


@app.route("/add_prospect", methods=["GET", "POST"])
def add_prospect():
    if request.method == "POST":
        name = request.form.get("name")
        company = request.form.get("company")
        status = request.form.get("status")
        next_action = request.form.get("next_action")
        follow_up = request.form.get("follow_up")

        # 🔥 Normalize datetime-local → your existing format
        if follow_up:
            follow_up = follow_up.replace("T", " ")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO prospects 
            (name, company, status, next_action, follow_up)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, company, status, next_action, follow_up)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/")

    return render_template("add_prospect.html")

@app.route("/add_note/<int:pid>", methods=["POST"])
def add_note(pid):
    note = request.form.get("note")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO notes (prospect_id, text, timestamp) VALUES (%s, %s, %s)",
        (pid, note, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/prospect/{pid}")


@app.route("/update_status/<int:pid>", methods=["POST"])
def update_status(pid):
    status = request.form.get("status")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE prospects SET status = %s WHERE id = %s",
        (status, pid)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/prospect/{pid}")


@app.route("/set_followup/<int:pid>", methods=["POST"])
def set_followup(pid):
    date = request.form.get("date")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE prospects SET follow_up = %s WHERE id = %s",
        (date, pid)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/prospect/{pid}")


@app.route("/quick_contact/<int:pid>", methods=["POST"])
def quick_contact(pid):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE prospects SET status = %s, follow_up = NULL WHERE id = %s",
        ("contacted", pid)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


@app.route("/quick_snooze/<int:pid>", methods=["POST"])
def quick_snooze(pid):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT follow_up FROM prospects WHERE id = %s", (pid,))
    p = cur.fetchone()

    dt = parse_date(p[0]) if p and p[0] else None

    if dt:
        dt = dt + timedelta(days=1)
    else:
        dt = datetime.now() + timedelta(days=1)

    cur.execute(
        "UPDATE prospects SET follow_up = %s WHERE id = %s",
        (dt.strftime("%Y-%m-%d %H:%M"), pid)
    )

    conn.commit()
    cur.close()
    conn.close()

@app.route('/archive_prospect/<int:id>', methods=['POST'])
def archive_prospect(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE prospects SET archived = TRUE WHERE id = %s", (id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect('/')

def get_connection():
    print(f"DEBUG: Connecting with URL starting with: {os.environ.get('DATABASE_URL')[:20]}...") 
    return psycopg2.connect(os.environ['DATABASE_URL'])
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)