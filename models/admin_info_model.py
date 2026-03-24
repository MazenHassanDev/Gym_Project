from sqlalchemy import Integer, String, Date, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from models.base_model import Base

class AdminInfo(Base):
    __tablename__ = "admin_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
