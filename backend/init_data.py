from datetime import datetime, timedelta
import random
import uuid

from backend import app, db
from backend.models import (
    Booking, BookingStatus, Category, Order, OrderStatus,
    PaymentStatus, PaymentMethod, Product, ProductOrder, Receipt, ReceiptDetails,
    Room, RoomStatus, RoomType, SessionStatus, User, UserRole,
    Staff, Session
)
from backend.utils.general_utils import hash_password

if __name__ == '__main__':
    with app.app_context():
        # 1. Reset Database
        db.drop_all()
        db.create_all()
        print("Database initialized.")

        random.seed(27)
        current_time = datetime.now()

        # ==========================================
        # 1. USERS
        # ==========================================
        admin_user = User(
            name='Quản trị viên',
            username='admin',
            password=hash_password('123456'),
            phone='0909000001',
            email='admin@ou.edu.vn',
            role=UserRole.ADMIN
        )

        staff_user = Staff(
            name='Nhân viên Thu Ngân',
            username='staff',
            password=hash_password('123456'),
            phone='0909000002',
            email='staff@ou.edu.vn',
            identity_card='0123456789123',
            role=UserRole.STAFF
        )

        dummy_users = []
        for k in range(5):
            u = User(
                name=f'Khách Hàng {k}',
                username=f'customer{k}',
                password=hash_password('123456'),
                phone=f'090090000{k}',
                email=f'customer{k}@gmail.com',
                role=UserRole.CUSTOMER
            )
            dummy_users.append(u)

        db.session.add_all([admin_user, staff_user] + dummy_users)
        db.session.commit()
        print("Users created.")

        # ==========================================
        # 2. ROOMS & TYPES
        # ==========================================
        rt_standard = RoomType(name="Phòng Thường", hourly_price=125000)
        rt_vip = RoomType(name="Phòng VIP", hourly_price=200000)
        rt_party = RoomType(name="Phòng Party", hourly_price=400000)

        db.session.add_all([rt_standard, rt_vip, rt_party])
        db.session.commit()

        rooms = []
        image_urls = [
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765792240/kararoom_peudkz.jpg",
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765796772/kararoom5_fvddfy.jpg"
        ]


        def create_rooms(count, prefix, cap_list, r_type):
            for i in range(1, count + 1):
                rooms.append(Room(
                    name=f"{prefix} {i:02d}",
                    capacity=random.choice(cap_list),
                    status=RoomStatus.AVAILABLE,
                    room_type=r_type.id,
                    image=random.choice(image_urls)
                ))


        create_rooms(10, "Standard", [4, 6, 8], rt_standard)
        create_rooms(5, "VIP", [10, 12], rt_vip)
        create_rooms(3, "Party", [15], rt_party)

        db.session.add_all(rooms)
        db.session.commit()
        print("Rooms created.")

        # ==========================================
        # 3. PRODUCTS
        # ==========================================
        cat_food = Category(name="Đồ Ăn Nhẹ")
        cat_drink = Category(name="Đồ Uống")

        db.session.add_all([cat_food, cat_drink])
        db.session.commit()

        products_data = [
            {"name": "Khoai tây chiên", "price": 45000, "cat": cat_food.id, "unit": "Dĩa"},
            {"name": "Khô bò", "price": 85000, "cat": cat_food.id, "unit": "Dĩa"},
            {"name": "Tiger Beer", "price": 25000, "cat": cat_drink.id, "unit": "Lon"},
            {"name": "Coca Cola", "price": 15000, "cat": cat_drink.id, "unit": "Lon"},
        ]

        products = []
        for p in products_data:
            products.append(Product(
                name=p["name"], price=p["price"], category_id=p["cat"],
                unit=p["unit"], amount=100, image="default.jpg"
            ))

        db.session.add_all(products)
        db.session.commit()
        print("Products created.")

        # ==========================================
        # 4. BOOKINGS & SESSIONS
        # ==========================================
        bookings = []
        sessions = []

        all_rooms = Room.query.all()
        random.shuffle(all_rooms)
        all_customers = User.query.filter(User.role == UserRole.CUSTOMER).all()

        # --- A. 5 Sessions đang ACTIVE (Đang hát) ---
        for i in range(5):
            room = all_rooms.pop()
            user = random.choice(all_customers)

            # Bắt đầu cách đây 1 tiếng
            start_time = current_time - timedelta(minutes=random.randint(30, 90))
            # Kết thúc dự kiến trong tương lai
            end_time = current_time + timedelta(minutes=60)

            room.status = RoomStatus.OCCUPIED  # Phòng đang có người
            db.session.add(room)

            s = Session(
                start_time=start_time,
                end_time=end_time,
                session_status=SessionStatus.ACTIVE,
                user_id=user.id,
                room_id=room.id
            )
            sessions.append(s)

            b = Booking(
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                head_count=random.randint(2, room.capacity),
                booking_status=BookingStatus.COMPLETED,
                user_id=user.id,
                room_id=room.id,
                ref=str(uuid.uuid4())[:8]
            )
            bookings.append(b)

        # --- B. 10 Sessions đã FINISHED (Đã xong) ---
        for i in range(10):
            if not all_rooms: break
            room = all_rooms.pop()
            user = random.choice(all_customers)

            start_time = current_time - timedelta(days=random.randint(1, 3), hours=2)
            end_time = start_time + timedelta(hours=2)

            s = Session(
                start_time=start_time,
                end_time=end_time,
                session_status=SessionStatus.FINISHED,
                user_id=user.id,
                room_id=room.id
            )
            sessions.append(s)

            b = Booking(
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
                head_count=random.randint(2, room.capacity),
                booking_status=BookingStatus.COMPLETED,
                user_id=user.id,
                room_id=room.id,
                ref=str(uuid.uuid4())[:8]
            )
            bookings.append(b)

        db.session.add_all(bookings)
        db.session.add_all(sessions)
        db.session.commit()
        print(f"Created Bookings & Sessions.")

        # ==========================================
        # 5. ORDER & RECEIPT LOGIC (UPDATED)
        # ==========================================
        for session in sessions:
            # 1. Tạo Order (Món ăn)
            order = Order(
                session_id=session.id,
                status=OrderStatus.SERVED
            )
            db.session.add(order)
            db.session.commit()

            # Thêm món
            session_service_fee = 0.0
            num_items = random.randint(1, 4)
            chosen_products = random.sample(products, num_items)
            for prod in chosen_products:
                qty = random.randint(1, 5)
                po = ProductOrder(
                    product_id=prod.id,
                    order_id=order.id,
                    amount=qty,
                    price_at_time=prod.price
                )
                db.session.add(po)
                session_service_fee += (qty * prod.price)

            # 2. TÍNH TIỀN PHÒNG & TRẠNG THÁI RECEIPT
            room_obj = db.session.get(Room, session.room_id)
            room_type_obj = db.session.get(RoomType, room_obj.room_type)

            receipt_status = PaymentStatus.PENDING
            payment_method = PaymentMethod.CASH  # Mặc định

            if session.session_status == SessionStatus.FINISHED:
                # Đã xong: Tính full thời gian thực tế
                duration_hours = (session.end_time - session.start_time).total_seconds() / 3600
                receipt_status = PaymentStatus.COMPLETED
                payment_method = random.choice(list(PaymentMethod))
            else:
                # Đang hát (ACTIVE): Tính từ lúc bắt đầu đến HIỆN TẠI (tạm tính)
                duration_hours = (current_time - session.start_time).total_seconds() / 3600
                receipt_status = PaymentStatus.PENDING  # <--- Quan trọng: Trạng thái chờ
                payment_method = PaymentMethod.CASH  # Chưa thanh toán nên để mặc định

            room_fee = duration_hours * room_type_obj.hourly_price

            # 3. TẠO RECEIPT (Cho cả Active và Finished)
            receipt = Receipt(
                session_id=session.id,
                staff_id=staff_user.id,
                status=receipt_status,  # PENDING hoặc COMPLETED
                ref=str(uuid.uuid4())
            )
            db.session.add(receipt)
            db.session.commit()

            # 4. TẠO RECEIPT DETAILS
            # Lưu ý: Với ACTIVE, đây là hoá đơn tạm tính tại thời điểm hiện tại
            rd = ReceiptDetails(
                id=receipt.id,
                total_room_fee=room_fee,
                total_service_fee=session_service_fee,
                payment_method=payment_method
            )
            db.session.add(rd)

        db.session.commit()
        print("Done! Active sessions now have PENDING receipts.")