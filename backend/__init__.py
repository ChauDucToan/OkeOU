from flask import Flask
import cloudinary
import os
from pathlib import Path
from dotenv import load_dotenv

# Read .env file to get config
env_path = Path(__file__).resolve().parent.parent.joinpath('.env')
load_dotenv()
secret_key = os.getenv("CLOUDINARY_SECRET_KEY")
database_url = os.environ.get("DATABASE_URI")

if secret_key is None:
    print("Lỗi: Không tìm thấy CLOUDINARY_SECRET_KEY")

if database_url is None:
    print("Lỗi: Không tìm thấy DATABASE_URL")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"{database_url}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

cloudinary.config(cloud_name="dtcjixfyd",
                  api_key="898564552716539",
                  api_secret=f"{secret_key}",
                  secure=True)
