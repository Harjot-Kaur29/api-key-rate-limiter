from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime
from app.db.base import Base
from datetime import datetime, timezone

class User(Base):
     __tablename__ = "users"

     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
     username:Mapped[str] = mapped_column(String, nullable=False)
     email:Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
     hashed_password:Mapped[str] = mapped_column(String, nullable=False)






