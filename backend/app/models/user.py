from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, func
from app.core.database import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    nickname = Column(String(64), nullable=False)
    avatar_url = Column(String(512), nullable=True)
    email = Column(String(128), unique=True, nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    # system_role: admin, teacher, user
    role = Column(String(32), nullable=False, default="user")
    status = Column(SmallInteger, nullable=False, default=1)  # 1=active, 0=disabled
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
