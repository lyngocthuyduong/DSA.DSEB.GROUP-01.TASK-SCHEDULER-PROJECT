from sqlalchemy import Column, String, Integer, JSON
from database import Base

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    priority = Column(Integer, default=5)
    duration = Column(Integer, nullable=False)
    # SQLAlchemy JSON tự động chuyển List Python thành chuỗi JSON để lưu vào SQLite
    dependencies = Column(JSON, default=list) 
    deadline = Column(Integer, nullable=True)
    category = Column(String, default="General")
    status = Column(String, default="PENDING")