# OkeOU
Ứng dụng đặt phòng Karaoke

---
# Hướng dẫn sử dụng:
## Tạo data base (khuyến khích sử dụng docker)
Mọi người sử  dụng [Image docker tại đây](https://drive.google.com/file/d/1t5U4Fel_huqDtOLV-5CAkYrtmt1NTA4x/view?usp=drive_link) để tải về và load vào docker sử  dụng

```
docker load < okedb_image.tar.gz
docker run -d --name okeou_db -p 3306:3306 okedb:latest
```

Về cấu hình database:
- database: okedb
- username: okeou
- password: okeou

## Chạy dữ liệu mẫu
```
python -m backend.models
python -m backend.models_init
```