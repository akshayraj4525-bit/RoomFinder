import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
UPDATE properties
SET status='Approved'
""")

conn.commit()

print("All rooms approved successfully!")

cur.execute("""
SELECT id, room_type, area, status
FROM properties
""")

for row in cur.fetchall():
    print(row)

conn.close()