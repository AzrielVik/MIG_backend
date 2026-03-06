from app.extensions import db
from datetime import datetime

# Staff users (receptionist, owners, managers)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Added password field to match database constraint
    password = db.Column(db.String(200), nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


# Rooms in the BnB
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # single, double, etc

    # status options: free | booked | cleaning
    status = db.Column(db.String(20), default="free")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="room", lazy=True)

    def __repr__(self):
        return f"<Room {self.number} ({self.status})>"


# Guests / customers
class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    id_number = db.Column(db.String(50), nullable=False) # National ID or passport
    phone_number = db.Column(db.String(20), nullable=True)
    vehicle_registration = db.Column(db.String(30), nullable=True)
    num_people = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="guest", lazy=True)

    def __repr__(self):
        return f"<Guest {self.full_name}>"


# Booking / Stay record
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey("guest.id"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("room.id"), nullable=False)

    # Automatically set when receptionist clicks "Check In"
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Set only when receptionist clicks "Check Out"
    checkout_time = db.Column(db.DateTime, nullable=True)

    days_staying = db.Column(db.Integer, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    amount_paid = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Booking Room:{self.room.number} Guest:{self.guest.full_name}>"