# run.py
# CRM Core Runner (Operational Build with Action Mode)

import json
from pathlib import Path
from datetime import datetime, timedelta
import uuid

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data/prospects.json"

VALID_STATUSES = ["new", "contacted", "qualified", "won", "lost"]
TAGS = ["restaurant", "hotel", "bar", "retail", "distributor", "other"]

# ------------------------
# Data Handling
# ------------------------

def normalize_data(data):
    for p in data:
        if "notes" not in p:
            p["notes"] = []
        if "next_action" not in p:
            p["next_action"] = None
        if "history" not in p:
            p["history"] = []
        if "tags" not in p:
            p["tags"] = []
    return data

def load_data():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return normalize_data(data)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ------------------------
# Core Functions
# ------------------------

def create_prospect():
    name = input("Enter prospect name: ").strip()

    if not name:
        print("Name cannot be empty.")
        return

    print("\nSelect tag:")
    for i, t in enumerate(TAGS):
        print(f"{i+1}. {t}")

    try:
        tag_index = int(input("Choice: ")) - 1
        tag = TAGS[tag_index]
    except:
        tag = "other"

    prospect = {
        "id": str(uuid.uuid4()),
        "name": name,
        "status": "new",
        "tags": [tag],
        "history": [
            {"status": "new", "timestamp": datetime.now().isoformat()}
        ],
        "notes": [],
        "next_action": None,
        "created_at": datetime.now().isoformat()
    }

    data = load_data()
    data.append(prospect)
    save_data(data)

    print(f"[OK] Prospect '{name}' created with tag '{tag}'.")

def list_prospects():
    data = load_data()

    if not data:
        print("No prospects found.")
        return

    print("\nProspects:\n")
    for i, p in enumerate(data):
        next_action = p.get("next_action") or "None"
        tags = ", ".join(p.get("tags", [])) or "none"
        print(f"{i+1}. {p['name']} | {p['status']} | {tags} | Next: {next_action}")

def select_prospect(data):
    list_prospects()
    try:
        index = int(input("\nSelect prospect #: ")) - 1
        return data[index]
    except:
        print("Invalid selection.")
        return None

def update_status():
    data = load_data()
    if not data:
        print("No prospects available.")
        return

    prospect = select_prospect(data)
    if not prospect:
        return

    print("\nSelect new status:")
    for i, s in enumerate(VALID_STATUSES):
        print(f"{i+1}. {s}")

    try:
        status_index = int(input("Choice: ")) - 1
        new_status = VALID_STATUSES[status_index]
    except:
        print("Invalid status.")
        return

    prospect["status"] = new_status
    prospect["history"].append({
        "status": new_status,
        "timestamp": datetime.now().isoformat()
    })

    save_data(data)
    print(f"[OK] Updated to '{new_status}'")

def add_note():
    data = load_data()
    if not data:
        print("No prospects available.")
        return

    prospect = select_prospect(data)
    if not prospect:
        return

    note_text = input("Enter note: ").strip()

    if not note_text:
        print("Note cannot be empty.")
        return

    prospect["notes"].append({
        "text": note_text,
        "timestamp": datetime.now().isoformat()
    })

    save_data(data)
    print("[OK] Note added.")

def view_notes():
    data = load_data()
    if not data:
        print("No prospects available.")
        return

    prospect = select_prospect(data)
    if not prospect:
        return

    print(f"\nNotes for {prospect['name']}:\n")

    if not prospect["notes"]:
        print("(no notes)")
        return

    for n in prospect["notes"]:
        print(f"- {n['text']} ({n['timestamp']})")

def set_follow_up():
    data = load_data()
    if not data:
        print("No prospects available.")
        return

    prospect = select_prospect(data)
    if not prospect:
        return

    date_input = input("Enter follow-up date (YYYY-MM-DD HH:MM): ")

    try:
        dt = datetime.strptime(date_input, "%Y-%m-%d %H:%M")
        prospect["next_action"] = dt.isoformat()
        save_data(data)
        print("[OK] Follow-up set.")
    except:
        print("Invalid format.")

def view_due_followups():
    data = load_data()
    now = datetime.now()

    print("\nDue Follow-Ups:\n")

    found = False
    for p in data:
        if p.get("next_action"):
            dt = datetime.fromisoformat(p["next_action"])
            if dt <= now:
                print(f"- {p['name']} (was due {p['next_action']})")
                found = True

    if not found:
        print("(none)")

# ------------------------
# Pipeline View
# ------------------------

def pipeline_view():
    data = load_data()

    if not data:
        print("No prospects found.")
        return

    pipeline = {status: [] for status in VALID_STATUSES}

    for p in data:
        status = p.get("status", "new")
        name = p.get("name", "Unnamed")

        urgency = ""
        if p.get("next_action"):
            dt = datetime.fromisoformat(p["next_action"])
            if dt <= datetime.now():
                urgency = " 🔴"

        pipeline[status].append(name + urgency)

    print("\nPIPELINE VIEW\n")

    for stage in VALID_STATUSES:
        print(f"\n{stage.upper()}:")
        print("-" * len(stage))

        if pipeline[stage]:
            for item in pipeline[stage]:
                print(f"  • {item}")
        else:
            print("  (empty)")

    def calculate_priority(p):
        status_weight = {
            "new": 1,
            "contacted": 2,
            "qualified": 3,
            "won": 0,
            "lost": 0
        }

        base = status_weight.get(p.get("status"), 0)

        if not p.get("next_action"):
            return base

        now = datetime.now()
        dt = datetime.fromisoformat(p["next_action"])

        if dt <= now:
            overdue_days = (now - dt).days + 1
            return base + overdue_days

        return base

# ------------------------
# Today’s Work (View)
# ------------------------

def todays_work():
    data = load_data()
    now = datetime.now()

    print("\nTODAY'S WORK\n")

    for p in data:
        if p.get("next_action"):
            dt = datetime.fromisoformat(p["next_action"])
            if dt <= now:
                print(f"🔴 {p['name']} ({dt})")

def no_follow_up():
    data = load_data()

    print("\nNO FOLLOW-UP:\n")

    found = False

    for p in data:
        if not p.get("next_action"):
            print(f"⚫ {p['name']} | {p['status']}")
            found = True

    if not found:
        print("(none)")
# ------------------------
# Today’s Work (Action Mode)
# ------------------------

def todays_work_action():
    data = load_data()
    now = datetime.now()

    items = []

    # Build priority-scored list
    for p in data:
        if p.get("next_action"):
            dt = datetime.fromisoformat(p["next_action"])
            if dt <= now:
                score = calculate_priority(p)
                items.append((score, dt, p))

    # Sort: highest priority first, then oldest
    items.sort(key=lambda x: (-x[0], x[1]))

    if not items:
        print("\nNo overdue follow-ups.")
        return

    print("\nOVERDUE ACTIONS:\n")

    # Display list
    for i, (score, dt, p) in enumerate(items):
        print(f"{i+1}. {p['name']} | priority {score} | {dt}")

    # Select item
    try:
        index = int(input("\nSelect #: ")) - 1
        score, dt, prospect = items[index]
    except:
        print("Invalid selection.")
        return

    print(f"\n→ {prospect['name']}")

    # Note
    note = input("Note: ").strip()
    if note:
        prospect["notes"].append({
            "text": note,
            "timestamp": now.isoformat()
        })

    # Status shortcut
    s = input("Status (c/q/w/l or Enter): ").strip().lower()
    status_map = {"c": "contacted", "q": "qualified", "w": "won", "l": "lost"}

    if s in status_map:
        new_status = status_map[s]
        prospect["status"] = new_status
        prospect["history"].append({
            "status": new_status,
            "timestamp": now.isoformat()
        })

    # Smart follow-up (default = tomorrow 10am)
    nxt = input("Next [Enter=+1d @10:00 | +2d | custom]: ").strip().lower()

    if nxt == "":
        dt = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        prospect["next_action"] = dt.isoformat()

    elif nxt == "+2d":
        dt = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
        prospect["next_action"] = dt.isoformat()

    else:
        try:
            dt = datetime.strptime(nxt, "%Y-%m-%d %H:%M")
            prospect["next_action"] = dt.isoformat()
        except:
            print("Invalid date, unchanged.")

    save_data(data)

    print("[OK] Done.\n")
    data = load_data()
    now = datetime.now()

    items = []

    for p in data:
        if p.get("next_action"):
            dt = datetime.fromisoformat(p["next_action"])
            if dt <= now:
                score = calculate_priority(p)
                items.append((score, dt, p))

    items.sort(key=lambda x: (-x[0], x[1]))

    for i, (score, dt, p) in enumerate(items):
        print(f"{i+1}. {p['name']} | priority {score} | {dt}")

    try:
        index = int(input("\nSelect #: ")) - 1
        score, dt, prospect = items[index]
    except:
        print("Invalid selection.")
        return

    print(f"\n→ {prospect['name']}")

    note = input("Note: ").strip()
    if note:
        prospect["notes"].append({
            "text": note,
            "timestamp": now.isoformat()
        })

    s = input("Status (c/q/w/l or Enter): ").strip().lower()
    status_map = {"c": "contacted", "q": "qualified", "w": "won", "l": "lost"}

    if s in status_map:
        new_status = status_map[s]
        prospect["status"] = new_status
        prospect["history"].append({
            "status": new_status,
            "timestamp": now.isoformat()
        })

    nxt = input("Next [Enter=+1d @10:00 | +2d | custom]: ").strip().lower()

    if nxt == "":
        dt = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        prospect["next_action"] = dt.isoformat()

    elif nxt == "+2d":
        dt = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
        prospect["next_action"] = dt.isoformat()

    else:
        try:
            dt = datetime.strptime(nxt, "%Y-%m-%d %H:%M")
            prospect["next_action"] = dt.isoformat()
        except:
            print("Invalid date, unchanged.")
        save_data(data)
        print("[OK] Done.\n")

# ------------------------
# Delete
# ------------------------

def delete_prospect():
    data = load_data()

    if not data:
        print("No prospects available.")
        return

    prospect = select_prospect(data)
    if not prospect:
        return

    confirm = input(f"Delete {prospect['name']}? (yes): ").strip().lower()

    if confirm == "yes":
        data.remove(prospect)
        save_data(data)
        print("[OK] Deleted.")
    else:
        print("Cancelled.")

# ------------------------
# Main Menu
# ------------------------

def main():
    while True:
        print("\nCRM MENU")
        print("1. Add Prospect")
        print("2. List Prospects")
        print("3. Update Status")
        print("4. Add Note")
        print("5. View Notes")
        print("6. Set Follow-Up")
        print("7. View Due Follow-Ups")
        print("8. Pipeline View")
        print("9. Delete Prospect")
        print("10. Today's Work")
        print("11. Today's Work (Action Mode)")
        print("12. No Follow Up")
        print("13. Exit")

        choice = input("Select: ").strip()

        if choice == "1":
            create_prospect()
        elif choice == "2":
            list_prospects()
        elif choice == "3":
            update_status()
        elif choice == "4":
            add_note()
        elif choice == "5":
            view_notes()
        elif choice == "6":
            set_follow_up()
        elif choice == "7":
            view_due_followups()
        elif choice == "8":
            pipeline_view()
        elif choice == "9":
            delete_prospect()
        elif choice == "10":
            todays_work()
        elif choice == "11":
            todays_work_action()
        elif choice == "12":
            no_follow_up()
        elif choice == "13":
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()