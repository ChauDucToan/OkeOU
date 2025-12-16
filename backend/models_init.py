from email.mime import image
import random

from backend import app, db
from backend.models import Category, Product, Room, RoomStatus, RoomType, User, UserRole
from utils import hash_password

if __name__ == '__main__':
    with app.app_context():
        random.seed(27)

        def_name = f'usr{random.random() * 10000:.0f}'
        def_password = f'pwd{random.random() * 10000:.0f}'
        print(def_name, def_password)

        default_user = User(
            name=def_name,
            username=def_name,
            password=hash_password(def_password),
            phone='0123456789',
            email='user@example.com',
        )

        admin_user = User(
            name='admin',
            username='admin',
            password=hash_password('okeou'),
            phone='3636363636',
            email='admin@ou.edu.vn',
            role=UserRole.ADMIN
        )

        db.session.add_all([default_user, admin_user])
        db.session.commit()

        rt_standard = RoomType(name="Phòng Thường", hourly_price=125000)
        rt_vip = RoomType(name="Phòng VIP", hourly_price=200000)
        rt_party = RoomType(name="Phòng Party", hourly_price=400000)

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
        for i in range(1, 11):
            room = Room(
                name=f"Phòng cơ bản {i:02d}",
                capacity=random.choice([4, 6, 8, 10, 12]),
                status=RoomStatus.AVAILABLE,
                room_type=rt_standard.id,
                image=random.choice(image_urls)
            )
            rooms.append(room)

        for i in range(1, 6):
            room = Room(
                name=f"Phòng VIP {i:02d}",
                capacity=random.choice([6, 10, 12, 14, 15]),
                status=RoomStatus.AVAILABLE,
                room_type=rt_vip.id,
                image=random.choice(image_urls)
            )
            rooms.append(room)

        for i in range(1, 4):
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
