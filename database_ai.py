import sqlite3


def search_area(area):

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("""
        SELECT
            room_type,
            rent,
            area,
            address,
            contact,
            status
        FROM properties
        WHERE LOWER(area)=LOWER(?)
    """, (area,))

    rooms = cur.fetchall()

    conn.close()

    return [dict(room) for room in rooms]