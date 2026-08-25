from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime
from app.db.base import Base
from datetime import datetime, timezone

class APIKey(Base):
     __tablename__ = "api_keys"

     id:Mapped[int] = mapped_column(Integer,primary_key=True)
     hashed_key:Mapped[str] = mapped_column(String,nullable=False,index=True, unique=True)
     is_active:Mapped[bool] = mapped_column(Boolean, default=True)
     user_id:Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
     created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))

