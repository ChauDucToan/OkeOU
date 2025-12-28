from datetime import datetime, timedelta
import random
import uuid

from backend import app, db
from backend.models import Application, ApplicationStatus, Booking, BookingStatus, Category, Job, Order, OrderStatus, PaymentStatus, Product, ProductOrder, \
    Receipt, ReceiptDetails, Room, RoomStatus, RoomType, SessionStatus, StaffApplication, StaffWorkingHour, User, UserRole, Staff, Session
from backend.utils.general_utils import hash_password

if __name__ == '__main__':
    with app.app_context():
        random.seed(27)
        current_time = datetime.now()

        def_name = f'usr{random.random() * 10000:.0f}'
        def_password = f'pwd{random.random() * 10000:.0f}'
        print(def_name, def_password)

        default_user = User(
            name="Vãng lai",
            username=def_name,
            password=hash_password(def_password),
            phone='0123456789',
            email='user@example.com',
        )

        admin_user = Staff(
            name='admin',
            username='admin',
            password=hash_password('okeou'),
            phone='3636363636',
            email='admin@ou.edu.vn',
            role=UserRole.ADMIN,
            identity_card='123456789'
        )

        job_waiter = Job(
            title="Nhân viên Phục vụ phòng hát",
            description="Order đồ uống, trái cây, hướng dẫn khách sử dụng thiết bị, dọn dẹp phòng sau khi khách về. Có thể làm xoay ca.",
            target_quantity=10,
            hired_quantity=2,
            min_salary=5000000.0,
            max_salary=7000000.0,
            is_active=True,
            deadline=datetime.now() + timedelta(days=30)
        )

        job_tech = Job(
            title="Kỹ thuật viên Âm thanh & IT",
            description="Bảo trì hệ thống loa, mic, cập nhật bài hát mới vào đầu máy. Xử lý sự cố kỹ thuật khi khách đang hát.",
            target_quantity=2,
            hired_quantity=0,
            min_salary=8000000.0,
            max_salary=12000000.0,
            is_active=True,
            deadline=datetime.now() + timedelta(days=15)
        )

        job_reception = Job(
            title="Nhân viên Lễ tân & Thu ngân",
            description="Tiếp đón khách, sắp xếp phòng (booking), in hóa đơn và thanh toán tiền giờ/dịch vụ.",
            target_quantity=3,
            hired_quantity=1,
            min_salary=6000000.0,
            max_salary=9000000.0,
            is_active=True,
            deadline=datetime.now() + timedelta(days=20)
        )

        job_security = Job(
            title="Nhân viên Bảo vệ & Giữ xe",
            description="Trông giữ xe máy/ô tô cho khách, đảm bảo an ninh quán.",
            target_quantity=2,
            hired_quantity=2,
            min_salary=5000000.0,
            max_salary=6000000.0,
            is_active=False,
            deadline=datetime.now() - timedelta(days=5)
        )

        db.session.add(job_waiter)
        db.session.add(job_tech)
        db.session.add(job_reception)
        db.session.add(job_security)
        db.session.commit()

        apps = [
            Application(
                job_id=job_waiter.id,
                full_name="Nguyễn Văn An",
                email="nguyenvanan@gmail.com",
                phone="0909123456",
                cv_file="cv_nguyenvanan.pdf",
                status=ApplicationStatus.PENDING,
                submit_date=datetime.now() - timedelta(days=1)
            ),
            Application(
                job_id=job_tech.id,
                full_name="Trần Công Nghệ",
                email="tech.tran@gmail.com",
                phone="0988776655",
                cv_file="portfolio_trancong.pdf",
                status=ApplicationStatus.PENDING,
                submit_date=datetime.now() - timedelta(hours=4)
            ),
            Application(
                job_id=job_reception.id,
                full_name="Phạm Thị Chảnh",
                email="phamchanh@outlook.com",
                phone="0999888777",
                cv_file="cv_phamthi.pdf",
                status=ApplicationStatus.REJECTED,
                submit_date=datetime.now() - timedelta(days=10)
            )
        ]

        approved_apps = [
            Application(
                job_id=job_waiter.id,
                full_name="Lê Thị Bưởi",
                email="lethibuoi@yahoo.com",
                phone="0912345678",
                cv_file="cv_lethibuoi.docx",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=5)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Nguyễn Văn Hòa",
                email="nguyenvanhoa@gmail.com",
                phone="0903123456",
                cv_file="cv_nguyenvanhoa.pdf",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=4)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Trần Thị Mai",
                email="tranthimai@gmail.com",
                phone="0911222333",
                cv_file="cv_tranthimai.pdf",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=6)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Phạm Quốc Bảo",
                email="phamquocbao@gmail.com",
                phone="0988777666",
                cv_file="cv_phamquocbao.docx",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=3)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Lý Thanh Tâm",
                email="lythanhtam@yahoo.com",
                phone="0934556677",
                cv_file="cv_lythanhtam.pdf",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=7)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Võ Minh Trí",
                email="vominhtri@gmail.com",
                phone="0978111222",
                cv_file="cv_vominhtri.docx",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=2)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Đặng Thị Hồng",
                email="dangthihong@gmail.com",
                phone="0945667788",
                cv_file="cv_dangthihong.pdf",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=8)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Bùi Gia Khánh",
                email="buigiakhanh@gmail.com",
                phone="0967001122",
                cv_file="cv_buigiakhanh.docx",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=1)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Hoàng Thị Ngọc",
                email="hoangthingoc@yahoo.com",
                phone="0922334455",
                cv_file="cv_hoangthingoc.pdf",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=9)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Ngô Tuấn Anh",
                email="ngotuananh@gmail.com",
                phone="0909888777",
                cv_file="cv_ngotuananh.docx",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=10)
            ),
            Application(
                job_id=job_waiter.id,
                full_name="Phan Thị Lan",
                email="phanthilan@gmail.com",
                phone="0915666777",
                cv_file="cv_phanthilan.pdf",
                status=ApplicationStatus.APPROVED,
                submit_date=datetime.now() - timedelta(days=5)
            )
        ]

        db.session.add_all(apps + approved_apps)
        db.session.commit()

        dummy_staffs = []
        for idx, app in enumerate(approved_apps):
            staff_user = Staff(
                name=app.full_name,
                username=f'staff{idx}',
                password=hash_password('okeou'),
                phone=app.phone,
                email=app.email,
                identity_card=str(random.randint(100000000, 999999999)),
                role=UserRole.STAFF
            )
            dummy_staffs.append(staff_user)

        dummy_users = []
        for k in range(30):
            u_name = f'khachhang{k}'
            u = User(
                name=f'Khách Hàng {k}',
                username=u_name,
                password=hash_password('123456'),
                phone=f'0900900000',
                email=f'{u_name}@gmail.com',
                role=UserRole.CUSTOMER
            )
            dummy_users.append(u)

        all_customers = [default_user] + dummy_users
        db.session.add_all(all_customers + [admin_user] + dummy_staffs)
        db.session.commit()

        for staff in dummy_staffs:
            staff_app = next((a for a in approved_apps if a.email == staff.email), None)
            if staff_app:
                staff_application = StaffApplication(
                    id=staff.id,
                    application_id=staff_app.id,
                    hire_date=current_time - timedelta(days=random.randint(1, 3))
                )
                db.session.add(staff_application)

        staff_working_hours = []
        for staff_user in dummy_staffs:
            for day_offset in range(-30, 1):
                work_date = current_time.date() + timedelta(days=day_offset)
                start_hour = random.randint(8, 10)
                end_hour = random.randint(17, 20)

                start_time = datetime.combine(work_date, datetime.min.time()) + timedelta(hours=start_hour)
                end_time = datetime.combine(work_date, datetime.min.time()) + timedelta(hours=end_hour)

                working_hour = StaffWorkingHour(
                    staff_id=staff_user.id,
                    login_date=start_time,
                    logout_date=end_time
                )
                staff_working_hours.append(working_hour)

        db.session.add_all(staff_working_hours)
        db.session.commit()

        rt_standard = RoomType(name="Phòng Thường", hourly_price=125000)
        rt_vip = RoomType(name="Phòng VIP", hourly_price=200000)
        rt_party = RoomType(name="Phòng Party", hourly_price=400000)

        price_map = {
            rt_standard.id: rt_standard.hourly_price,
            rt_vip.id: rt_vip.hourly_price,
            rt_party.id: rt_party.hourly_price
        }

        db.session.add_all([rt_standard, rt_vip, rt_party])
        db.session.flush()

        rooms = []
        image_urls = [
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765792240/kararoom_peudkz.jpg",
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765796772/kararoom5_fvddfy.jpg",
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765796771/kararoom4_hdv9a7.jpg",
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765796771/kararoom1_frgbt5.jpg",
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765796771/kararoom2_ps4j9u.jpg",
            "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765796771/kararoom3_d7o77f.jpg"
        ]
        for i in range(1, 26):
            room = Room(
                name=f"Phòng cơ bản {i:02d}",
                capacity=random.choice([4, 6, 8, 10, 12]),
                status=RoomStatus.AVAILABLE,
                room_type=rt_standard.id,
                image=random.choice(image_urls)
            )
            rooms.append(room)

        for i in range(1, 12):
            room = Room(
                name=f"Phòng VIP {i:02d}",
                capacity=random.choice([6, 10, 12, 14, 15]),
                status=RoomStatus.AVAILABLE,
                room_type=rt_vip.id,
                image=random.choice(image_urls)
            )
            rooms.append(room)

        for i in range(1, 11):
            room = Room(
                name=f"Phòng Party {i:02d}",
                capacity=15,
                status=RoomStatus.AVAILABLE,
                room_type=rt_party.id,
                image=random.choice(image_urls)
            )
            rooms.append(room)

        db.session.add_all(rooms)
        db.session.commit()

        cat_food = Category(name="Đồ Ăn Nhẹ")
        cat_drink = Category(name="Đồ Uống")
        cat_fruit = Category(name="Trái Cây")

        db.session.add_all([cat_food, cat_drink, cat_fruit])
        db.session.flush()

        products_data = [
            {
                "name": "Khoai tây chiên",
                "price": 45000,
                "category_id": cat_food.id,
                "unit": "Dĩa",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765797610/khoai_tay_chien_nfzfaw.jpg",
                "description": "Khoai tây chiên giòn rụm kèm tương ớt"
            },
            {
                "name": "Khô bò xé chanh",
                "price": 85000,
                "category_id": cat_food.id,
                "unit": "Dĩa",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765797694/khobo_fqvlfc.jpg",
                "description": "Bò khô loại 1, vắt chanh chua cay"
            },
            {
                "name": "Mực nướng muối ớt",
                "price": 120000,
                "category_id": cat_food.id,
                "unit": "Con",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765797790/mucnuongmuoiot_lb5umi.jpg",
                "description": "Mực một nắng nướng muối ớt xanh"
            },
            {
                "name": "Xúc xích Đức",
                "price": 60000,
                "category_id": cat_food.id,
                "unit": "Dĩa",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765797905/xucxich_ynbmkm.jpg",
                "description": "Xúc xích nướng tiêu đen"
            },

            {
                "name": "Dĩa trái cây thập cẩm Lớn",
                "price": 150000,
                "category_id": cat_fruit.id,
                "unit": "Dĩa",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765797962/DiaTraiCay_pa1pgj.png",
                "description": "Dưa hấu, Ổi, Xoài, Nho, Táo"
            },
            {
                "name": "Dĩa trái cây nhỏ",
                "price": 80000,
                "category_id": cat_fruit.id,
                "unit": "Dĩa",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765798169/dianho_lplmzu.png",
                "description": "Trái cây theo mùa"
            },

            {
                "name": "Bia Tiger Bạc",
                "price": 25000,
                "category_id": cat_drink.id,
                "unit": "Lon",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765798237/biaTiger_ymikib.png",
                "description": "Bia Tiger Crystal mát lạnh"
            },
            {
                "name": "Bia Heineken",
                "price": 28000,
                "category_id": cat_drink.id,
                "unit": "Lon",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765798500/biaken_kxuufw.png",
                "description": "Heineken nhập khẩu"
            },
            {
                "name": "Coca Cola",
                "price": 15000,
                "category_id": cat_drink.id,
                "unit": "Lon",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765798944/coca_lq1rxv.png",
                "description": "Nước ngọt có ga"
            },
            {
                "name": "Nước Suối Aquafina",
                "price": 10000,
                "category_id": cat_drink.id,
                "unit": "Chai",
                "image": "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765798941/aquafina_uvwfer.png",
                "description": "Nước tinh khiết 500ml"
            }
        ]

        products = []
        for p_data in products_data:
            prod = Product(
                name=p_data["name"],
                description=p_data["description"],
                price=p_data["price"],
                category_id=p_data["category_id"],
                image=p_data["image"],
                amount=random.randint(0, 50),
                unit=p_data["unit"],
                active=True
            )
            products.append(prod)

        db.session.add_all(products)

        db.session.commit()

        bookings = []

        for room in rooms:
            for day_offset in range(-60, 1):
                if random.random() > 0.4:

                    start_hour = random.randint(10, 20)
                    start_minute = random.choice([0, 15, 30, 45])

                    base_date = datetime.now().date() + timedelta(days=day_offset)
                    start_time = datetime.combine(base_date, datetime.min.time()) + timedelta(hours=start_hour,
                                                                                              minutes=start_minute)

                    duration_hours = random.randint(1, 5)
                    end_time = start_time + timedelta(hours=duration_hours)

                    if end_time < datetime.now():
                        status = random.choices(
                            [BookingStatus.COMPLETED, BookingStatus.CANCELLED, BookingStatus.PENDING],
                            weights=[80, 15, 5]
                        )[0]
                    else:
                        status = random.choice(
                            [BookingStatus.CANCELLED, BookingStatus.PENDING, BookingStatus.CONFIRMED])

                    hourly_price = price_map.get(room.room_type, 100000)

                    deposit = int(hourly_price * duration_hours) if status == BookingStatus.CONFIRMED else 0

                    booking = Booking(
                        scheduled_start_time=start_time,
                        scheduled_end_time=end_time,
                        head_count=random.randint(2, room.capacity),

                        status=status,

                        deposit_amount=deposit,

                        user_id=random.choice(all_customers).id,
                        room_id=room.id
                    )
                    bookings.append(booking)

        db.session.add_all(bookings)
        db.session.commit()

        confirmed_bookings = [b for b in bookings if b.status == BookingStatus.COMPLETED]
        sessionss = []

        for booking in confirmed_bookings:

            if booking.scheduled_end_time < current_time:
                session = Session(
                    user_id=booking.user_id,
                    room_id=booking.room_id,
                    start_time=booking.scheduled_start_time,
                    end_time=booking.scheduled_end_time,
                    status=SessionStatus.FINISHED
                )
            else:
                session = Session(
                    user_id=booking.user_id,
                    room_id=booking.room_id,
                    start_time=booking.scheduled_start_time,
                    end_time=booking.scheduled_end_time,
                    status=SessionStatus.BOOKED
                )
            sessionss.append(session)

        db.session.add_all(sessionss)
        db.session.commit()

        receipts = []
        for session in sessionss:
            id = str(uuid.uuid4())
            if session.status == SessionStatus.FINISHED:
                receipt = Receipt(
                    id=id,
                    staff_id=random.choice(dummy_staffs).id,
                    session_id=session.id,
                    status=PaymentStatus.COMPLETED,
                    created_date=session.end_time
                )
                receipts.append(receipt)
            else:
                receipt = Receipt(
                    id=id,
                    session_id=session.id,
                    staff_id=admin_user.id,
                    status=PaymentStatus.COMPLETED,
                    created_date=session.end_time
                )
                receipts.append(receipt)

        db.session.add_all(receipts)
        db.session.flush()

        orders = []
        total_service_fee = 0.0
        for session in sessionss:
            order = Order(
                session_id=session.id,
                status=OrderStatus.SERVED
            )
            orders.append(order)

        db.session.add_all(orders)
        db.session.flush()

        prod_ord = []
        for order in orders:
            num_orders = random.randint(2, 7)
            ordered_products = random.sample(products, k=min(num_orders, len(products)))
            for prod in ordered_products:
                amount = random.randint(1, 3)
                p_order = ProductOrder(
                    order_id=order.id,
                    product_id=prod.id,
                    amount=amount,
                    price_at_time=prod.price
                )

                total_service_fee += amount * prod.price
                prod_ord.append(p_order)

        db.session.add_all(prod_ord)
        db.session.commit()

        receipt_details_list = []
        for receipt, session in zip(receipts, sessionss):
            duration = (session.end_time - session.start_time).total_seconds() / 3600
            room = Room.query.get(session.room_id)
            room_type = RoomType.query.get(room.room_type)
            total_room_fee = room_type.hourly_price * duration

            session_service_fee = 0.0
            for order in Order.query.filter_by(session_id=session.id).all():
                for po in ProductOrder.query.filter_by(order_id=order.id).all():
                    session_service_fee += po.amount * po.price_at_time

            receipt_details = ReceiptDetails(
                id=receipt.id,
                total_room_fee=total_room_fee,
                total_service_fee=session_service_fee
            )
            receipt_details_list.append(receipt_details)

        db.session.add_all(receipt_details_list)
        db.session.commit()