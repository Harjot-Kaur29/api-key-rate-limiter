from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime
from app.db.base import Base
from datetime import datetime, timezone



class RequestLog(Base):
     __tablename__ = "request_logs"
     id:Mapped[int] = mapped_column(Integer,primary_key=True)
     api_key_id:Mapped[int] = mapped_column(ForeignKey("api_keys.id"), index=True, nullable=True)
     user_id:Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable = True)
     status_code:Mapped[int] = mapped_column(Integer, nullable=False)
     timestamp:Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda:datetime.now(timezone.utc), index=True)

