from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Tạo file tasks.db lưu trực tiếp ở thư mục hiện tại
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

# connect_args={"check_same_thread": False} là bắt buộc cho SQLite trong FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()