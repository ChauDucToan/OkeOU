from backend import app, db
from backend.models import (
    User, Staff, LoyalCustomer, UserRole,
    RoomType, Room, RoomStatus,
    Category, Product,
    Session, SessionStatus,
    Order, OrderStatus, product_order
)
from datetime import datetime, timedelta
from backend.utils import hash_password

# Để tạo dữ liệu test thử thôi
def create_sample_data():
    with app.app_context():
        # 1. Làm sạch dữ liệu cũ
        print("🔄 Đang reset cơ sở dữ liệu...")
        db.drop_all()
        db.create_all()

        # ---------------------------------------------------------
        # 2. Tạo Loại phòng & Phòng
        # ---------------------------------------------------------
        print("🏠 Tạo dữ liệu Phòng...")
        type_normal = RoomType(name="Thường", hourly_price=100000)
        type_vip = RoomType(name="VIP", hourly_price=200000)
        db.session.add_all([type_normal, type_vip])
        db.session.commit()

        # P101 (Thường) - Đang có khách
        room1 = Room(name="P101", capacity=10, room_type=type_normal.id, status=RoomStatus.OCCUPIED)
        # VIP01 (VIP) - Trống
        room2 = Room(name="VIP01", capacity=15, room_type=type_vip.id, status=RoomStatus.AVAILABLE)
        # VIP02 (VIP) - Đang có khách
        room3 = Room(name="VIP02", capacity=15, room_type=type_vip.id, status=RoomStatus.OCCUPIED)
        # P102 (Thường) - Đang có khách
        room4 = Room(name="P102", capacity=12, room_type=type_normal.id, status=RoomStatus.OCCUPIED)

        db.session.add_all([room1, room2, room3, room4])
        db.session.commit()

        # ---------------------------------------------------------
        # 3. Tạo User
        # ---------------------------------------------------------
        print("👤 Tạo dữ liệu User...")

        # Nhân viên
        staff = Staff(
            name="Nguyễn Văn Thu Ngân", username="staff", password=hash_password('123456'),
            role=UserRole.STAFF, phone="0901234567", email="staff@okeou.com", identity_card="079123456789"
        )
        db.session.add(staff)

        # Khách VIP
        customer_vip = LoyalCustomer(
            name="Trần Văn Giàu (VIP)", username="khachvip", password=hash_password('123456'),
            role=UserRole.CUSTOMER, phone="0909888777", email="vip@okeou.com", customer_points=50
        )
        db.session.add(customer_vip)

        # Khách Vãng Lai (Thêm mới để test đa dạng user)
        customer_normal = User(
            name="Nguyễn Văn A (Khách Lẻ)", username="khachle", password=hash_password('123456'),
            role=UserRole.USER, phone="0911222333", email="khachle@gmail.com"
        )
        db.session.add(customer_normal)

        db.session.commit()

        # ---------------------------------------------------------
        # 4. Tạo Sản phẩm
        # ---------------------------------------------------------
        print("🍔 Tạo Menu món ăn...")
        cat_drink = Category(name="Đồ uống")
        cat_food = Category(name="Đồ ăn")
        db.session.add_all([cat_drink, cat_food])
        db.session.commit()

        p1 = Product(name="Bia Tiger", price=25000, amount=100, unit="Lon", category_id=cat_drink.id)
        p2 = Product(name="Coca Cola", price=15000, amount=100, unit="Lon", category_id=cat_drink.id)
        p3 = Product(name="Dĩa Trái Cây", price=100000, amount=50, unit="Dĩa", category_id=cat_food.id)
        p4 = Product(name="Khô Mực Nướng", price=150000, amount=20, unit="Con", category_id=cat_food.id)
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # ---------------------------------------------------------
        # 5. Tạo 3 Phiên hát (Sessions)
        # ---------------------------------------------------------
        print("🎤 Tạo 3 Phiên hát đang hoạt động...")

        # Session 1: Room 1 - Khách VIP - Hát 2 tiếng
        sess1 = Session(
            start_time=datetime.now() - timedelta(hours=2),
            session_status=SessionStatus.ACTIVE,
            user_id=customer_vip.id,
            room_id=room1.id
        )

        # Session 2: Room 3 (VIP02) - Khách VIP - Hát 30 phút
        sess2 = Session(
            start_time=datetime.now() - timedelta(minutes=30),
            session_status=SessionStatus.ACTIVE,
            user_id=customer_vip.id,  # Ông VIP này bao 2 phòng
            room_id=room3.id
        )

        # Session 3: Room 4 (P102) - Khách Lẻ - Hát 4 tiếng (Test tiền nhiều)
        sess3 = Session(
            start_time=datetime.now() - timedelta(hours=4, minutes=15),
            session_status=SessionStatus.ACTIVE,
            user_id=customer_normal.id,
            room_id=room4.id
        )

        db.session.add_all([sess1, sess2, sess3])
        db.session.commit()

        # ---------------------------------------------------------
        # 6. Tạo Order & Chi tiết món ăn
        # ---------------------------------------------------------
        print("📝 Tạo Order cho các phòng...")

        # Order 1 (Room 1): 10 Bia + 1 Mực
        ord1 = Order(session_id=sess1.id, status=OrderStatus.PENDING)
        db.session.add(ord1)

        # Order 2 (Room 3): 24 Bia (1 Thùng) + 2 Trái Cây (VIP nhậu lớn)
        ord2 = Order(session_id=sess2.id, status=OrderStatus.PENDING)
        db.session.add(ord2)

        # Order 3 (Room 4): 2 Coca (Khách lẻ uống nước ngọt)
        ord3 = Order(session_id=sess3.id, status=OrderStatus.PENDING)
        db.session.add(ord3)

        db.session.commit()

        # Insert chi tiết món (Dùng bulk insert cho nhanh)
        print("🍻 Lên món...")
        product_inserts = [
            # Room 1
            {"product_id": p1.id, "order_id": ord1.id, "amount": 10, "price_at_time": p1.price},
            {"product_id": p4.id, "order_id": ord1.id, "amount": 1, "price_at_time": p4.price},

            # Room 3 (VIP)
            {"product_id": p1.id, "order_id": ord2.id, "amount": 24, "price_at_time": p1.price},
            {"product_id": p3.id, "order_id": ord2.id, "amount": 2, "price_at_time": p3.price},

            # Room 4 (Lẻ)
            {"product_id": p2.id, "order_id": ord3.id, "amount": 2, "price_at_time": p2.price},
        ]

        db.session.execute(product_order.insert(), product_inserts)
        db.session.commit()

        print("✅ === HOÀN TẤT ===")
        print(f"👉 Active Sessions: Room {room1.id}, Room {room3.id}, Room {room4.id}")


if __name__ == "__main__":
    create_sample_data()