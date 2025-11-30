from datetime import datetime, timedelta
from backend import db, app
from backend.models import User, Booking, Room, RoomType, Product, Category
import unittest

class ModelTest(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_unique_username(self):
        u1 = User(name="User 1", username="duplicate_user", password="123")
        db.session.add(u1)
        db.session.commit()

        u2 = User(name="User 2", username="duplicate_user", password="456")
        db.session.add(u2)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Found error in user 2: ", repr(e))

    def test_product_nullable_fields(self):
        cat = Category(name="Food")
        db.session.add(cat)
        db.session.commit()

        p_fail = Product(name="Coke", category_id=cat.id, unit="can")
        db.session.add(p_fail)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Found error at Coke: ", repr(e))

    def test_booking_end_time_check(self):
        user = User(name="Test User", username="booking_user", password="123")
        r_type = RoomType(name="VIP", hourly_price=100)
        db.session.add_all([user, r_type])
        db.session.commit()

        room = Room(name="Room 101", capacity=10, room_type=r_type.id)
        db.session.add(room)
        db.session.commit()

        start = datetime.now()
        end = start - timedelta(hours=1)

        booking = Booking(
            scheduled_start_time=start,
            scheduled_end_time=end,
            user_id=user.id,
            room_id=room.id,
            head_count=5
        )
        db.session.add(booking)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Found error at booking time: ", repr(e))

    def test_room_foreign_key(self):
        non_existent_type_id = 9999

        room = Room(name="Ghost Room", capacity=5, room_type=non_existent_type_id)
        db.session.add(room)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Found error at non exist id: ", repr(e))


if __name__ == "__main__":
    unittest.main()