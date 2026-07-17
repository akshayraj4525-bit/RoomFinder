from smart_search import smart_search

rooms = smart_search(
    area=None,
    room_type="Single Room",
    max_rent=8000
)

print(rooms)