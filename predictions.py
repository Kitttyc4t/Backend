from database import get_db


def get_statistics(person_id, weekday, time_slot):

    conn = get_db()

    observations = conn.execute("""
        SELECT floor, COUNT(*) AS amount
        FROM observations
        WHERE person_id = ?
        AND weekday = ?
        AND time_slot = ?
        GROUP BY floor
    """, (person_id, weekday, time_slot)).fetchall()

    conn.close()

    counts = {floor: 0 for floor in range(1, 7)}

    for observation in observations:
        counts[observation["floor"]] = observation["amount"]

    total = sum(counts.values())

    if total == 0:
        return {
            "observations": 0,
            "distribution": None
        }

    distribution = {
        str(floor): round(
            (amount / total) * 100, 2
        )
        for floor, amount in counts.items()
    }

    return {
        "observations": total,
        "distribution": distribution
    }