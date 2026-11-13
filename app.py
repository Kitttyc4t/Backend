from flask import Flask, request, jsonify
from database import get_db, init_db
from predictions import get_statistics

app = Flask(__name__)

init_db()


WEEKDAYS = [
    "Maanantai",
    "Tiistai",
    "Keskiviikko",
    "Torstai",
    "Perjantai",
    "Lauantai",
    "Sunnuntai"
]


# -------------------------
# PERSONS
# -------------------------

@app.route("/api/persons", methods=["GET"])
def get_persons():

    conn = get_db()

    persons = conn.execute("""
        SELECT * FROM persons
        ORDER BY name
    """).fetchall()

    conn.close()

    return jsonify([
        dict(person) for person in persons
    ])


@app.route("/api/persons", methods=["POST"])
def add_person():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()

    if not name:
        return jsonify({"error": "Name required"}), 400

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO persons (name)
        VALUES (?)
    """, (name,))

    conn.commit()

    person_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "id": person_id,
        "name": name
    }), 201


@app.route("/api/persons/<int:person_id>", methods=["DELETE"])
def delete_person(person_id):

    conn = get_db()

    cursor = conn.execute("""
        DELETE FROM persons
        WHERE id = ?
    """, (person_id,))

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if not deleted:
        return jsonify({"error": "Person not found"}), 404

    return jsonify({"success": True})


# -------------------------
# OBSERVATIONS
# -------------------------

@app.route("/api/observations", methods=["POST"])
def add_observation():

    data = request.get_json(silent=True) or {}

    required = [
        "person_id",
        "weekday",
        "time_slot",
        "floor"
    ]

    if not all(key in data for key in required):
        return jsonify({"error": "Missing fields"}), 400

    try:
        person_id = int(data["person_id"])
        weekday = int(data["weekday"])
        time_slot = int(data["time_slot"])
        floor = int(data["floor"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid values"}), 400

    if not 0 <= weekday <= 6:
        return jsonify({"error": "Invalid weekday"}), 400

    if not 0 <= time_slot <= 3:
        return jsonify({"error": "Invalid time slot"}), 400

    if not 1 <= floor <= 6:
        return jsonify({"error": "Invalid floor"}), 400

    conn = get_db()

    try:
        cursor = conn.execute("""
            INSERT INTO observations
            (person_id, weekday, time_slot, floor)
            VALUES (?, ?, ?, ?)
        """, (person_id, weekday, time_slot, floor))

        conn.commit()

        observation_id = cursor.lastrowid

    except Exception:
        conn.close()
        return jsonify({"error": "Could not save observation"}), 400

    conn.close()

    return jsonify({
        "id": observation_id,
        "success": True
    }), 201


@app.route("/api/observations/<int:observation_id>", methods=["DELETE"])
def delete_observation(observation_id):

    conn = get_db()

    cursor = conn.execute("""
        DELETE FROM observations
        WHERE id = ?
    """, (observation_id,))

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    if not deleted:
        return jsonify({"error": "Observation not found"}), 404

    return jsonify({"success": True})


@app.route("/api/observations/<int:observation_id>", methods=["PUT"])
def update_observation(observation_id):

    data = request.get_json(silent=True) or {}

    try:
        weekday = int(data["weekday"])
        time_slot = int(data["time_slot"])
        floor = int(data["floor"])
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "Invalid values"}), 400

    if not 0 <= weekday <= 6:
        return jsonify({"error": "Invalid weekday"}), 400

    if not 0 <= time_slot <= 3:
        return jsonify({"error": "Invalid time slot"}), 400

    if not 1 <= floor <= 6:
        return jsonify({"error": "Invalid floor"}), 400

    conn = get_db()

    cursor = conn.execute("""
        UPDATE observations
        SET weekday = ?,
            time_slot = ?,
            floor = ?
        WHERE id = ?
    """, (weekday, time_slot, floor, observation_id))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    if not updated:
        return jsonify({"error": "Observation not found"}), 404

    return jsonify({"success": True})


# -------------------------
# STATISTICS
# -------------------------

@app.route("/api/statistics/<int:person_id>", methods=["GET"])
def statistics(person_id):

    weekday = request.args.get("weekday")
    time_slot = request.args.get("time_slot")

    try:
        weekday = int(weekday)
        time_slot = int(time_slot)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid parameters"}), 400

    if not 0 <= weekday <= 6 or not 0 <= time_slot <= 3:
        return jsonify({"error": "Invalid parameters"}), 400

    conn = get_db()

    person = conn.execute("""
        SELECT id, name FROM persons
        WHERE id = ?
    """, (person_id,)).fetchone()

    conn.close()

    if not person:
        return jsonify({"error": "Person not found"}), 404

    result = get_statistics(
        person_id,
        weekday,
        time_slot
    )

    return jsonify({
        "person": dict(person),
        "weekday": WEEKDAYS[weekday],
        "time_slot": time_slot,
        **result
    })


# -------------------------
# TIME SLOTS
# -------------------------

@app.route("/api/time-slots", methods=["GET"])
def get_time_slots():

    conn = get_db()

    slots = conn.execute("""
        SELECT * FROM time_slots
        ORDER BY id
    """).fetchall()

    conn.close()

    return jsonify([
        dict(slot) for slot in slots
    ])


@app.route("/api/time-slots/<int:slot_id>", methods=["PUT"])
def update_time_slot(slot_id):

    if not 0 <= slot_id <= 3:
        return jsonify({"error": "Invalid slot"}), 400

    data = request.get_json(silent=True) or {}

    label = data.get("label")
    time = data.get("time")

    if not isinstance(label, str) or not isinstance(time, str):
        return jsonify({"error": "Label and time required"}), 400

    import re

    if not re.fullmatch(r"\d{2}:\d{2}", time):
        return jsonify({"error": "Invalid time format"}), 400

    hour, minute = map(int, time.split(":"))

    if hour > 23 or minute > 59:
        return jsonify({"error": "Invalid time"}), 400

    conn = get_db()

    cursor = conn.execute("""
        UPDATE time_slots
        SET label = ?, time = ?
        WHERE id = ?
    """, (label.strip(), time, slot_id))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    if not updated:
        return jsonify({"error": "Time slot not found"}), 404

    return jsonify({"success": True})


# -------------------------
# RUN SERVER
# -------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )