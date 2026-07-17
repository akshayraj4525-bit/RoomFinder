import re
import ollama
from smart_search import smart_search

MODEL_NAME = "llama3.2:3b"


def ask_ai(question):

    question_lower = question.lower()

    area = None

    areas = [
        "prem nagar",
        "kehri gaon",
        "sudhowala",
        "thakurpur",
        "nanda ki chowki"
    ]

    # Detect Area
    for a in areas:
        if a in question_lower:
            area = a.title()
            break

    # Detect Room Type
    room_type = None

    if "single" in question_lower:
        room_type = "Single Room"

    elif "double" in question_lower:
        room_type = "Double Room"

    # Detect Budget
    max_rent = None

    match = re.search(r"\d+", question)

    if match:
        max_rent = int(match.group())

    # Search Database
    print("Area:", area)
    print("Room Type:", room_type)
    print("Max Rent:", max_rent)

    rooms = smart_search(
        area=area,
        room_type=room_type,
        max_rent=max_rent
        )
    
    print("Rooms:", rooms)

    if len(rooms) == 0:
        return "Sorry, no matching property found."

    prompt = f"""
You are RoomFinder AI.

You must format the answer exactly like this.

For every room write:

🏠 Room ID: 2

Room Type: Single Room

Rent: ₹7000

Area: Kehri Gaon

Address: Near Petrol Pump

Contact: 977656565676

Status: Approved

----------------------------------

Do NOT write everything in one paragraph.

Put every field on a new line.

Do not add your own words.

Only use the database below.

Database:

{rooms}
"""
    
    response = ollama.chat(
    model=MODEL_NAME,
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

    return response["message"]["content"]