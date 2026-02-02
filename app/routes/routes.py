from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.models import User, Room, Guest, Booking
from datetime import datetime, timedelta

routes = Blueprint('routes', __name__)

# ---------------------
# USERS
# ---------------------
@routes.route("/users", methods=["POST"])
def create_user():
    data = request.json
    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({"error": "username, email, and password required"}), 400
    user = User(
        username=data["username"],
        email=data["email"],
        password=data["password"]  # will hash later when integrating auth
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created", "id": user.id}), 201


@routes.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([
        {"id": u.id, "username": u.username, "email": u.email} for u in users
    ])


@routes.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({"id": user.id, "username": user.username, "email": user.email})


@routes.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    db.session.commit()
    return jsonify({"message": "User updated"})


@routes.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


# ---------------------
# ROOMS
# ---------------------
@routes.route("/rooms", methods=["POST"])
def create_room():
    data = request.json
    if not data.get("number") or not data.get("room_type"):
        return jsonify({"error": "number and room_type required"}), 400
    room = Room(
        number=data["number"],
        room_type=data["room_type"],
        status=data.get("status", "free")
    )
    db.session.add(room)
    db.session.commit()
    return jsonify({"message": "Room created", "id": room.id}), 201


@routes.route("/rooms", methods=["GET"])
def get_rooms():
    status_filter = request.args.get("status")
    query = Room.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    rooms = query.all()
    return jsonify([
        {"id": r.id, "number": r.number, "room_type": r.room_type, "status": r.status}
        for r in rooms
    ])


@routes.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    room = Room.query.get_or_404(room_id)
    return jsonify({
        "id": room.id,
        "number": room.number,
        "room_type": room.room_type,
        "status": room.status
    })


@routes.route("/rooms/<int:room_id>/status", methods=["PUT"])
def update_room_status(room_id):
    room = Room.query.get_or_404(room_id)
    data = request.json
    room.status = data.get("status", room.status)
    db.session.commit()
    return jsonify({"message": "Room status updated"})


@routes.route("/rooms/<int:room_id>", methods=["PUT"])
def update_room(room_id):
    room = Room.query.get_or_404(room_id)
    data = request.json
    room.number = data.get("number", room.number)
    room.room_type = data.get("room_type", room.room_type)
    room.status = data.get("status", room.status)
    db.session.commit()
    return jsonify({"message": "Room updated"})


@routes.route("/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({"message": "Room deleted"})


# ---------------------
# GUESTS
# ---------------------
@routes.route("/guests", methods=["POST"])
def create_guest():
    data = request.json
    if not data.get("full_name") or not data.get("id_number"):
        return jsonify({"error": "full_name and id_number required"}), 400
    guest = Guest(
        full_name=data["full_name"],
        id_number=data["id_number"],
        phone_number=data.get("phone_number"),
        vehicle_registration=data.get("vehicle_registration"),
        num_people=data.get("num_people", 1)
    )
    db.session.add(guest)
    db.session.commit()
    return jsonify({"message": "Guest created", "id": guest.id}), 201


@routes.route("/guests", methods=["GET"])
def get_guests():
    guests = Guest.query.all()
    return jsonify([
        {
            "id": g.id,
            "full_name": g.full_name,
            "id_number": g.id_number,
            "phone_number": g.phone_number,
            "vehicle_registration": g.vehicle_registration
        }
        for g in guests
    ])


@routes.route("/guests/<int:guest_id>", methods=["GET"])
def get_guest(guest_id):
    g = Guest.query.get_or_404(guest_id)
    return jsonify({
        "id": g.id,
        "full_name": g.full_name,
        "id_number": g.id_number,
        "phone_number": g.phone_number,
        "vehicle_registration": g.vehicle_registration
    })


@routes.route("/guests/<int:guest_id>", methods=["PUT"])
def update_guest(guest_id):
    g = Guest.query.get_or_404(guest_id)
    data = request.json
    g.full_name = data.get("full_name", g.full_name)
    g.id_number = data.get("id_number", g.id_number)
    g.phone_number = data.get("phone_number", g.phone_number)
    g.vehicle_registration = data.get("vehicle_registration", g.vehicle_registration)
    g.num_people = data.get("num_people", g.num_people)
    db.session.commit()
    return jsonify({"message": "Guest updated"})


@routes.route("/guests/<int:guest_id>", methods=["DELETE"])
def delete_guest(guest_id):
    g = Guest.query.get_or_404(guest_id)
    db.session.delete(g)
    db.session.commit()
    return jsonify({"message": "Guest deleted"})


# ---------------------
# BOOKINGS
# ---------------------
def is_room_available(room_id, checkin_date, days_staying):
    checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
    checkout = checkin + timedelta(days=days_staying)
    bookings = Booking.query.filter_by(room_id=room_id).all()
    for b in bookings:
        b_checkin = b.checkin_time
        b_checkout = b.checkout_time or (b.checkin_time + timedelta(days=b.days_staying))
        if not (checkout <= b_checkin or checkin >= b_checkout):
            return False
    return True


@routes.route("/bookings", methods=["POST"])
def create_booking():
    data = request.json
    room = Room.query.get_or_404(data["room_id"])
    guest = Guest.query.get_or_404(data["guest_id"])
    days_staying = data.get("days_staying")
    checkin_date = data.get("checkin_date", datetime.utcnow().strftime("%Y-%m-%d"))

    if not days_staying or days_staying <= 0:
        return jsonify({"error": "Invalid days_staying"}), 400

    if not is_room_available(room.id, checkin_date, days_staying):
        return jsonify({"error": "Room not available for selected dates"}), 400

    booking = Booking(
        guest_id=guest.id,
        room_id=room.id,
        days_staying=days_staying,
        paid=data.get("paid", False),
        amount_paid=data.get("amount_paid", 0.0),
        checkin_time=datetime.strptime(checkin_date, "%Y-%m-%d")
    )
    room.status = "booked"

    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Booking created", "id": booking.id}), 201


@routes.route("/bookings", methods=["GET"])
def get_bookings():
    bookings = Booking.query.all()
    return jsonify([
        {
            "id": b.id,
            "guest": b.guest.full_name,
            "room": b.room.number,
            "checkin_time": b.checkin_time,
            "checkout_time": b.checkout_time,
            "days_staying": b.days_staying,
            "paid": b.paid,
            "amount_paid": b.amount_paid
        }
        for b in bookings
    ])


@routes.route("/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    return jsonify({
        "id": b.id,
        "guest": b.guest.full_name,
        "room": b.room.number,
        "checkin_time": b.checkin_time,
        "checkout_time": b.checkout_time,
        "days_staying": b.days_staying,
        "paid": b.paid,
        "amount_paid": b.amount_paid
    })


@routes.route("/bookings/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    data = request.json
    # allow update of days_staying, paid, amount_paid
    b.days_staying = data.get("days_staying", b.days_staying)
    b.paid = data.get("paid", b.paid)
    b.amount_paid = data.get("amount_paid", b.amount_paid)
    db.session.commit()
    return jsonify({"message": "Booking updated"})


@routes.route("/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    b.room.status = "free"
    db.session.delete(b)
    db.session.commit()
    return jsonify({"message": "Booking deleted"})


@routes.route("/bookings/<int:booking_id>/checkout", methods=["PUT"])
def checkout(booking_id):
    b = Booking.query.get_or_404(booking_id)
    if b.checkout_time is not None:
        return jsonify({"error": "Already checked out"}), 400
    b.checkout_time = datetime.utcnow()
    b.room.status = "free"
    db.session.commit()
    return jsonify({"message": "Checked out successfully"})
