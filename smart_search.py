import sqlite3


DATABASE = "database.db"

import os
print("Database Path:", os.path.abspath(DATABASE))


def get_connection():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn

def search_by_area(area):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
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

def search_by_rent(max_rent):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            room_type,
            rent,
            area,
            address,
            contact,
            status
        FROM properties
        WHERE CAST(rent AS INTEGER) <= ?
    """, (max_rent,))

    rooms = cur.fetchall()

    conn.close()

    return [dict(room) for room in rooms]

def search_by_room_type(room_type):

    conn = get_connection()

    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            room_type,
            rent,
            area,
            address,
            contact,
            status
        FROM properties
        WHERE LOWER(room_type)=LOWER(?)
    """, (room_type,))

    rooms = cur.fetchall()

    conn.close()

    return [dict(room) for room in rooms]

def smart_search(area=None, room_type=None, max_rent=None):

    conn = get_connection()

    cur = conn.cursor()

    query = """
        SELECT
            id,
            room_type,
            rent,
            area,
            address,
            contact,
            status
        FROM properties
        WHERE status='Approved'
    """

    params = []

    if area:

        query += " AND LOWER(area)=LOWER(?)"
        params.append(area)

    if room_type:

        query += " AND LOWER(room_type)=LOWER(?)"
        params.append(room_type)

    if max_rent is not None:

        query += " AND CAST(rent AS INTEGER)<=?"
        params.append(max_rent)

    cur.execute(query, params)

    rooms = cur.fetchall()

    conn.close()

    return [dict(room) for room in rooms]

def cheapest_room(area=None):

    conn = get_connection()

    cur = conn.cursor()

    query = """
        SELECT
            id,
            room_type,
            rent,
            area,
            address,
            contact,
            status
        FROM properties
        WHERE status='Approved'
    """

    params = []

    if area:
        query += " AND LOWER(area)=LOWER(?)"
        params.append(area)

    query += " ORDER BY CAST(rent AS INTEGER) ASC LIMIT 1"

    print(query)
    print(params)

    cur.execute(query, params)

    room = cur.fetchone()

    conn.close()

    if room:
        return dict(room)

    return None