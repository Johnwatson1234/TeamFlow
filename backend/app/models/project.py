from sqlalchemy import Column, Integer, String, Text, Date, DateTime, func, ForeignKey
from app.core.database import Base


class Project(Base):
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    cover_url = Column(String(512), nullable=True)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    course_name = Column(String(128), nullable=True)
    teacher_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    deadline = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="active")  # active, archived
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ProjectMember(Base):
    __tablename__ = "project_member"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    # project role: leader, member, teacher
    role = Column(String(32), nullable=False, default="member")
    skill_tags = Column(String(256), nullable=True)
    joined_at = Column(DateTime, nullable=False, server_default=func.now())
    status = Column(String(32), nullable=False, default="active")
