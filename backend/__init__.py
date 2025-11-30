from flask import Flask
import cloudinary
import os
from pathlib import Path
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Read the .env file in order to access to API call
env_path = Path(__file__).resolve().parent.parent.joinpath('.env')
load_dotenv()
secret_key = os.getenv("CLOUDINARY_SECRET_KEY")
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
cloud_api_key = os.getenv("CLOUDINARY_API_KEY")
database_url = os.environ.get("DATABASE_URI")

if secret_key is None:
    print("Lỗi: Không tìm thấy CLOUDINARY_SECRET_KEY")
    exit(1)

if database_url is None:
    print("Lỗi: Không tìm thấy DATABASE_URL")
    exit(1)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"{database_url}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 10

db = SQLAlchemy(app=app)
login = LoginManager(app=app)

cloudinary.config(cloud_name=f"{cloud_name}",
                  api_key=f"{cloud_api_key}",
                  api_secret=f"{secret_key}",
                  secure=True)
