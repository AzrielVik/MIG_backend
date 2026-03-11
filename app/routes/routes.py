from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.models import User, Room, Guest, Booking
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash


routes = Blueprint('routes', __name__)

# USERS
# ---------------------

@routes.route("/users", methods=["POST"])
def create_user():
    data = request.json

    if not data.get("username") or not data.get("email") or not data.get("password"):
        return jsonify({
            "error": "username, email, and password required"
        }), 400

    # Pre-check for better UX
    existing_user = User.query.filter(
        (User.username == data["username"]) |
        (User.email == data["email"])
    ).first()

    if existing_user:
        return jsonify({
            "error": "User already exists",
            "details": "Username or email already in use"
        }), 409

    user = User(
        username=data["username"],
        email=data["email"]
    )

    # 🔐 HASH PASSWORD HERE
    user.set_password(data["password"])

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "User already exists",
            "details": "Username or email already in use"
        }), 409

    return jsonify({
        "message": "User created",
        "id": user.id
    }), 201


@routes.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email
        } for u in users
    ]), 200


@routes.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email
    }), 200


@routes.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json

    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)

    # Optional: allow password update
    if data.get("password"):
        user.set_password(data["password"])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "Update failed",
            "details": "Username or email already in use"
        }), 409

    return jsonify({"message": "User updated"}), 200


@routes.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200


# ---------------------
# --- ROOMS & STATISTICS ---

@routes.route("/rooms/stats", methods=["GET"])
def get_room_stats():
    """
    Returns counts for the three summary cards at the top of the Rooms screen.
    Matches the 'Available', 'Occupied', and 'Cleaning' cards.
    """
    return jsonify({
        "available": Room.query.filter_by(status="Available").count(),
        "occupied": Room.query.filter_by(status="Occupied").count(),
        "cleaning": Room.query.filter_by(status="Cleaning").count()
    }), 200


@routes.route("/rooms", methods=["POST"])
def create_room():
    data = request.json
    if not data.get("number") or not data.get("room_type"):
        return jsonify({"error": "number and room_type required"}), 400
    
    room = Room(
        number=data["number"],
        room_type=data["room_type"],
        capacity=data.get("capacity", 2),
        beds=data.get("beds", 1),
        status=data.get("status", "Available")
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
    results = []
    
    for r in rooms:
        # FIXED: Look for the active guest assigned to this room
        # We find a booking where checkout_time is still null
        active_booking = Booking.query.filter_by(room_id=r.id, checkout_time=None).first()
        
        results.append({
            "id": r.id, 
            "number": r.number, 
            "room_type": r.room_type, 
            "status": r.status,
            "capacity": r.capacity,
            "beds": r.beds,
            # These fields fix the "N/A" issue in your Flutter UI
            "current_guest_name": active_booking.guest.full_name if active_booking and active_booking.guest else None,
            "current_guest_phone": active_booking.guest.phone_number if active_booking and active_booking.guest else None
        })
        
    return jsonify(results), 200


@routes.route("/rooms/<int:room_id>", methods=["GET"])
def get_room(room_id):
    r = Room.query.get_or_404(room_id)
    # Also include occupant info for individual room lookups
    active_booking = Booking.query.filter_by(room_id=r.id, checkout_time=None).first()
    
    return jsonify({
        "id": r.id,
        "number": r.number,
        "room_type": r.room_type,
        "status": r.status,
        "capacity": r.capacity,
        "beds": r.beds,
        "current_guest_name": active_booking.guest.full_name if active_booking and active_booking.guest else None,
        "current_guest_phone": active_booking.guest.phone_number if active_booking and active_booking.guest else None
    }), 200


@routes.route("/rooms/<int:room_id>/status", methods=["PUT"])
def update_room_status(room_id):
    room = Room.query.get_or_404(room_id)
    data = request.json
    room.status = data.get("status", room.status)
    db.session.commit()
    return jsonify({"message": f"Room {room.number} status updated to {room.status}"}), 200


@routes.route("/rooms/<int:room_id>", methods=["PUT"])
def update_room(room_id):
    room = Room.query.get_or_404(room_id)
    data = request.json
    room.number = data.get("number", room.number)
    room.room_type = data.get("room_type", room.room_type)
    room.status = data.get("status", room.status)
    room.capacity = data.get("capacity", room.capacity)
    room.beds = data.get("beds", room.beds)
    db.session.commit()
    return jsonify({"message": "Room updated"}), 200


@routes.route("/rooms/<int:room_id>", methods=["DELETE"])
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({"message": "Room deleted"}), 200


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
    # Supports date filtering, period filtering (weekly), and ID searching
    filter_date = request.args.get('date')
    period = request.args.get('period')
    id_number = request.args.get('id_number')
    
    query = Guest.query

    # 1. Filter by specific ID if searching
    if id_number:
        query = query.filter(Guest.id_number.ilike(f"%{id_number}%"))

    # 2. Filter by specific calendar date
    if filter_date:
        try:
            start_day = datetime.strptime(filter_date, '%Y-%m-%d')
            query = query.filter(
                Guest.created_at >= start_day,
                Guest.created_at < start_day + timedelta(days=1)
            )
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
            
    # 3. Filter by period (e.g., 'weekly' view)
    elif period == 'weekly':
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Guest.created_at >= one_week_ago)

    # Order by newest registration first
    guests = query.order_by(Guest.created_at.desc()).all()

    results = []
    for g in guests:
        # Link the guest to their most recent room assignment
        active_booking = Booking.query.filter_by(guest_id=g.id).order_by(Booking.created_at.desc()).first()
        
        results.append({
            "id": g.id,
            "full_name": g.full_name,
            "id_number": g.id_number,
            "phone_number": g.phone_number,
            "vehicle_registration": g.vehicle_registration,
            "num_people": g.num_people,
            "created_at": g.created_at.isoformat() if g.created_at else None,
            "check_out": g.check_out,
            "room_number": active_booking.room.number if active_booking else "No Room" # Matches Vercel mock
        })
        
    return jsonify(results), 200

@routes.route("/guests/<int:guest_id>", methods=["GET"])
def get_guest(guest_id):
    g = Guest.query.get_or_404(guest_id)
    # Fetch room info for the specific guest details view
    active_booking = Booking.query.filter_by(guest_id=g.id).order_by(Booking.created_at.desc()).first()
    
    return jsonify({
        "id": g.id,
        "full_name": g.full_name,
        "id_number": g.id_number,
        "phone_number": g.phone_number,
        "vehicle_registration": g.vehicle_registration,
        "num_people": g.num_people,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "check_out": g.check_out,
        "room_number": active_booking.room.number if active_booking else "No Room"
    }), 200

@routes.route("/guests/<int:guest_id>", methods=["PUT"])
def update_guest(guest_id):
    g = Guest.query.get_or_404(guest_id)
    data = request.json
    
    g.full_name = data.get("full_name", g.full_name)
    g.id_number = data.get("id_number", g.id_number)
    g.phone_number = data.get("phone_number", g.phone_number)
    g.vehicle_registration = data.get("vehicle_registration", g.vehicle_registration)
    g.num_people = data.get("num_people", g.num_people)
    
    if "check_out" in data:
        g.check_out = data["check_out"]
        
    db.session.commit()
    return jsonify({"message": "Guest updated"}), 200

@routes.route("/guests/<int:guest_id>", methods=["DELETE"])
def delete_guest(guest_id):
    g = Guest.query.get_or_404(guest_id)
    db.session.delete(g)
    db.session.commit()
    return jsonify({"message": "Guest deleted"}), 200
# ---------------------
# --- BOOKINGS LOGIC (Linking Guests to Rooms) ---

def is_room_available(room_id, checkin_date, days_staying):
    """Checks if a room is available for the given date range"""
    checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
    checkout = checkin + timedelta(days=days_staying)
    bookings = Booking.query.filter_by(room_id=room_id).all()
    for b in bookings:
        b_checkin = b.checkin_time
        # Use existing checkout_time or calculate based on days staying
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

    # Safety check: Only 'Available' rooms can be booked
    if room.status != "Available":
        return jsonify({"error": f"Room {room.number} is {room.status} and cannot be booked"}), 400

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
    
    # AUTO-FLIP: Room becomes Occupied upon check-in
    room.status = "Occupied"

    db.session.add(booking)
    db.session.commit()
    return jsonify({"message": "Booking created", "id": booking.id, "room_status": room.status}), 201

@routes.route("/bookings/<int:booking_id>/checkout", methods=["PUT"])
def checkout(booking_id):
    """Handles guest checkout and flips room status to Cleaning"""
    b = Booking.query.get_or_404(booking_id)
    
    if b.checkout_time is not None:
        return jsonify({"error": "Already checked out"}), 400
    
    now = datetime.utcnow()
    b.checkout_time = now
    
    # Update Guest table string field for dashboard consistency
    if b.guest:
        b.guest.check_out = now.isoformat()
    
    # AUTO-FLIP: Room status to Cleaning (This triggers the blue card in Flutter)
    if b.room:
        b.room.status = "Cleaning"
        print(f"DEBUG: Room {b.room.number} status updated to: {b.room.status}")
    else:
        # Fallback if relationship fails
        room = Room.query.get(b.room_id)
        if room:
            room.status = "Cleaning"
            print(f"DEBUG: Manual Room lookup success: {room.number} is Cleaning")

    db.session.commit()
    
    return jsonify({
        "message": "Checked out successfully", 
        "room_status": "Cleaning",
        "checkout_time": now.isoformat()
    }), 200

@routes.route("/bookings", methods=["GET"])
def get_bookings():
    bookings = Booking.query.all()
    return jsonify([
        {
            "id": b.id,
            "guest": b.guest.full_name,
            "room": b.room.number,
            "checkin_time": b.checkin_time.isoformat() if b.checkin_time else None,
            "checkout_time": b.checkout_time.isoformat() if b.checkout_time else None,
            "days_staying": b.days_staying,
            "paid": b.paid,
            "amount_paid": b.amount_paid
        }
        for b in bookings
    ]), 200

@routes.route("/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    # Reset room to Available if a booking is deleted manually
    if b.room:
        b.room.status = "Available"
    db.session.delete(b)
    db.session.commit()
    return jsonify({"message": "Booking deleted", "room_status": "Available"}), 200