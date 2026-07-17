from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from flask import request, jsonify
import sqlite3
import os
import random
import requests
import os
from werkzeug.utils import secure_filename
from voice_ai import speech_to_text

app = Flask(__name__)

app.secret_key = "roomfinder_secret_key"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=30)

API_KEY = "DRQdhZls6WjrqNvc3GOPIFByuMeEUb0Ko2Vmp5t9wHak7X1Cf8sxX9oDHtA1qRvGy8J64aNOLrVn0ECT"

def send_sms_otp(phone, otp):

    url = "https://www.fast2sms.com/dev/bulkV2"

    headers = {
        "authorization": API_KEY
    }

    params = {
        "route": "otp",
        "variables_values": str(otp),
        "flash": "0",
        "numbers": phone
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    print(response.text)

@app.route("/")
def landing():

    return render_template("landing.html")


@app.route("/buyer")
def buyer():

    session["role"] = "buyer"

    return redirect("/buyer-login")


@app.route("/seller")
def seller():

    session["role"] = "seller"

    return render_template(
        "seller_choice.html"
    )

@app.route("/seller-login")
def seller_login():
    return render_template("seller_choice.html")

@app.route("/buyer-login")
def buyer_login():

    return render_template(
        "buyer_login.html"
    )

@app.route("/send-otp", methods=["POST"])
def send_otp():

    phone = request.form["phone"]

    otp = random.randint(100000, 999999)

    session["buyer_phone"] = phone
    session["otp"] = str(otp)

    send_sms_otp(phone, otp)

   # print("OTP =", otp)

    return redirect("/verify-otp")

@app.route("/verify-otp")
def verify_otp():

    return render_template(
        "verify_otp.html"
    )

@app.route("/check-otp", methods=["POST"])
def check_otp():

    print("CHECK OTP ROUTE HIT")

    user_otp = request.form["otp"]

    print("Entered OTP =", user_otp)
    print("Session OTP =", session.get("otp"))

    if user_otp == session.get("otp"):

        session["buyer_logged_in"] = True
        session["role"] = "buyer"

        return redirect("/home")
    
    print("OTP FAILED")

    return "Invalid OTP"

# Database Create
def init_db():
    conn = sqlite3.connect("database.db",timeout=20)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
CREATE TABLE IF NOT EXISTS favorites(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    property_id INTEGER
)
""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS properties(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        room_type TEXT,
        rent TEXT,
        area TEXT,
        address TEXT,
        contact TEXT,
        image TEXT,
        map_link TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/home")
def home():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
    "SELECT * FROM properties"
)

    rooms = cur.fetchall()

    print(rooms)

    favorite_ids = []

    if "user_id" in session:

        cur.execute(
            "SELECT property_id FROM favorites WHERE user_id=?",
            (session["user_id"],)
        )

        favorite_ids = [x[0] for x in cur.fetchall()]

    conn.close()

    return render_template(
        "index.html",
        rooms=rooms,
        favorite_ids=favorite_ids
    )

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        role = "seller"

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        # Check email already exists
        cur.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        existing_user = cur.fetchone()

        if existing_user:

            conn.close()

            return "Email already registered. Please login."

        cur.execute(
            "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
            (name,email,hashed_password,role)
        )

        user_id = cur.lastrowid

        conn.commit()
        conn.close()

        session["user_id"] = user_id
        session["role"] = role

        return redirect("/dashboard")

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        print("EMAIL =", email)
        print("PASSWORD =", password)

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("SELECT * FROM users")
        
        print(cur.fetchall())

        cur.execute("SELECT * FROM users")
        print("ALL USERS =", cur.fetchall())

        cur.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cur.fetchone()

        print("USER =", user)

        conn.close()

        if user and check_password_hash(user[3], password):

            print("LOGIN SUCCESS")

            session.permanent = True
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["role"] = user[4]

            if user[4] == "seller":
             return redirect("/dashboard")

            return redirect("/home")

    return render_template("login.html")

@app.route("/add-property", methods=["GET", "POST"])
def add_property():

    # Seller Only
    if session.get("role") != "seller":
        return "Access Denied"

    # Login Required
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        # ===============================
        # Form Data
        # ===============================

        user_id = session["user_id"]

        room_type = request.form["room_type"]
        property_type = request.form.get("property_type")

        rent = request.form["rent"]
        area = request.form["area"]
        address = request.form["address"]
        contact = request.form["contact"]
        map_link = request.form["map_link"]

        facilities = ",".join(
            request.form.getlist("facilities")
        )

        occupancy = request.form.get("occupancy")

        status = "Pending"

        # ===============================
        # Images
        # ===============================

        images = request.files.getlist("images")

        first_image = ""

        if len(images) > 0 and images[0].filename != "":

            first_image = secure_filename(images[0].filename)

            images[0].save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    first_image
                )
            )

        # ===============================
        # Database
        # ===============================

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO properties(
            user_id,
            room_type,
            rent,
            area,
            address,
            contact,
            image,
            map_link,
            status,
            property_type,
            facilities,
            occupancy
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id,
            room_type,
            rent,
            area,
            address,
            contact,
            first_image,
            map_link,
            status,
            property_type,
            facilities,
            occupancy
        ))

        property_id = cur.lastrowid

        conn.commit()

        # ===============================
        # Save Multiple Images
        # ===============================

        for img in images:

            if img.filename != "":

                filename = secure_filename(img.filename)

                img.save(
                    os.path.join(
                        app.config["UPLOAD_FOLDER"],
                        filename
                    )
                )

                cur.execute("""
                INSERT INTO property_images(
                    property_id,
                    image_name
                )
                VALUES(?,?)
                """,
                (
                    property_id,
                    filename
                ))
            print("================================")
            print("Images Selected:", len(images))

            for img in images:
             print("Image:", img.filename)

            print("First Image:", first_image)
            print("================================")
        conn.commit()
        conn.close()

        return redirect("/home")

    return render_template("add_property.html")

@app.route("/property/<int:id>")
def property_details(id):

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
     "SELECT * FROM properties WHERE id=?",
    (id,)
)

    room = cur.fetchone()

    conn.close()

    return render_template(
        "property_details.html",
        room=room,
        session=session
    )

@app.route("/search")
def search():

    area = request.args.get("area")

    print("SEARCH AREA =", area)

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
    "SELECT * FROM properties WHERE area=?",
    (area,)
)

    rooms = cur.fetchall()

    print("ROOMS =", rooms)

    conn.close()

    return render_template(
        "index.html",
        rooms=rooms,
        favorite_ids=[]
    )

@app.route("/check-properties")
def check_properties():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT id, room_type, area, status
    FROM properties
    """)

    data = cur.fetchall()

    conn.close()

    return str(data)

@app.route("/dashboard")
def dashboard(): 

    if session.get("role") != "seller":
       return "Access Denied"
    
    print("SESSION =", session)

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
    "SELECT * FROM properties WHERE user_id=?",
    (session["user_id"],)
)

    rooms = cur.fetchall()

    conn.close()
    
    return render_template(
        "dashboard.html",
        rooms=rooms
    )

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    )

    user = cur.fetchone()

    cur.execute(
        "SELECT COUNT(*) FROM properties WHERE user_id=?",
        (session["user_id"],)
    )

    total_properties = cur.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user=user,
        total_properties=total_properties
    )

@app.route("/approve/<int:id>")
def approve(id):
     
     if session["role"] != "admin":
      return "Access Denied"

     print("APPROVING ID =", id)

     conn = sqlite3.connect("database.db")
     cur = conn.cursor()

     cur.execute(
        "UPDATE properties SET status='Approved' WHERE id=?",
        (id,)
    )
     print("Rows Updated =", cur.rowcount)

     conn.commit()
     conn.close()

     return redirect("/admin")

@app.route("/admin")
def admin():

    if "user_id" not in session:
     return redirect("/login")

    if session["role"] != "admin":
     return "Access Denied"

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM properties WHERE status='Pending'"
    )

    rooms = cur.fetchall()

    print(rooms)

    conn.close()

    return render_template(
        "admin.html",
        rooms=rooms
    )

@app.route("/approve/<int:property_id>")
def approve_property(property_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        UPDATE properties
        SET status='Approved'
        WHERE id=?
    """, (property_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/favorite/<int:property_id>")
def favorite(property_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM favorites
        WHERE user_id=? AND property_id=?
        """,
        (session["user_id"], property_id)
    )

    existing = cur.fetchone()

    if existing:

        cur.execute(
            """
            DELETE FROM favorites
            WHERE user_id=? AND property_id=?
            """,
            (session["user_id"], property_id)
        )

    else:

        cur.execute(
            """
            INSERT INTO favorites(user_id, property_id)
            VALUES(?,?)
            """,
            (session["user_id"], property_id)
        )

    conn.commit()
    conn.close()

    return redirect("/home")

@app.route("/check-favorites")
def check_favorites():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM favorites")

    data = cur.fetchall()

    conn.close()

    return str(data)

@app.route("/favorites")
def favorites():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT properties.*
    FROM properties
    JOIN favorites
    ON properties.id = favorites.property_id
    WHERE favorites.user_id=?
    """,
    (session["user_id"],)
    )

    rooms = cur.fetchall()

    conn.close()

    return render_template(
        "favorites.html",
        rooms=rooms
    )

@app.route("/check users")
def users():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")

    data = cur.fetchall()

    conn.close()

    return str(data)

@app.route("/delete/<int:id>")
def delete_property(id):

    if session.get("role") != "seller":
       return "Access Denied"

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
    """
    DELETE FROM properties
    WHERE id=? AND user_id=?
    """,
    (
        id,
        session["user_id"]
    )
)

    conn.commit()
    conn.close()

    return redirect("/home")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_property(id):

    if session.get("role") != "seller":
        return "Access Denied"

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":

        room_type = request.form["room_type"]
        property_type = request.form["property_type"]
        rent = request.form["rent"]
        area = request.form["area"]
        address = request.form["address"]
        contact = request.form["contact"]
        map_link = request.form["map_link"]

        facilities = ",".join(
            request.form.getlist("facilities")
        )

        occupancy = request.form["occupancy"]

        cur.execute("""
            UPDATE properties
            SET
                room_type=?,
                property_type=?,
                rent=?,
                area=?,
                address=?,
                contact=?,
                map_link=?,
                facilities=?,
                occupancy=?
            WHERE id=? AND user_id=?
        """,
        (
            room_type,
            property_type,
            rent,
            area,
            address,
            contact,
            map_link,
            facilities,
            occupancy,
            id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    cur.execute("""
        SELECT *
        FROM properties
        WHERE id=? AND user_id=?
    """,
    (
        id,
        session["user_id"]
    ))

    room = cur.fetchone()

    conn.close()

    if room is None:
        return "Property Not Found or Access Denied"

    return render_template(
        "edit.html",
        room=room
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route("/check")
def check():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT id, room_type, status FROM properties"
    )

    data = cur.fetchall()

    conn.close()

    return str(data)

@app.route("/create-admin")
def create_admin():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO users(
    name,
    email,
    password,
    role
    )
    VALUES(?,?,?,?)
    """,
    (
        "Admin",
        "admin@gmail.com",
        "admin123",
        "admin"
    ))

    conn.commit()
    conn.close()

    return "Admin Created"

@app.route("/test")
def test():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(properties)")

    print(cur.fetchall())

    conn.close()

    return "Done"

@app.route("/create-property-images")
def create_property_images():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS property_images(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        property_id INTEGER,
        image_name TEXT
    )
    """)

    conn.commit()
    conn.close()

    return "property_images table created successfully!"

@app.route("/add-views-column")
def add_views_column():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    try:
        cur.execute(
            "ALTER TABLE properties ADD COLUMN views INTEGER DEFAULT 0"
        )

        conn.commit()

    except Exception as e:
        return str(e)

    conn.close()

    return "Views Column Added Successfully!"

import os

@app.route("/tables")
def tables():

    print("DB PATH =", os.path.abspath("database.db"))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    """)

    tables = cur.fetchall()

    print("TABLES =", tables)

    conn.close()

    return str(tables)

@app.route("/db-path")
def db_path():
    return os.path.abspath("database.db")

from ai import ask_ai

@app.route("/ask_ai", methods=["POST"])
def ask_ai_route():

    data = request.get_json()

    question = data.get("question", "")

    answer = ask_ai(question)
     
    print("AI Answer:", answer)

    return jsonify({
        "answer": answer
    })

@app.route("/voice_upload", methods=["POST"])
def voice_upload():

    if "audio" not in request.files:
        return jsonify({
            "success": False,
            "message": "No audio file received."
        }), 400

    audio = request.files["audio"]

    if audio.filename == "":
        return jsonify({
            "success": False,
            "message": "No file selected."
        }), 400

    # Allowed extensions
    allowed_extensions = {"wav", "mp3", "m4a", "webm", "ogg"}

    extension = audio.filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        return jsonify({
            "success": False,
            "message": "Unsupported audio format."
        }), 400

    filename = secure_filename(audio.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    audio.save(filepath)

    try:

        text = speech_to_text(filepath)

        return jsonify({
            "success": True,
            "text": text
        })

    finally:

        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == "__main__":
    app.run(debug=True)

    UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)




