from sqlalchemy import Integer, String, Date, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from models.base_model import Base

class Memberships(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    membership_id: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)

    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    dob: Mapped[str] = mapped_column(Date, nullable=False)

    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)

    gym_name: Mapped[str] = mapped_column(String(50))
    gym_access: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gym_addons: Mapped[str | None] = mapped_column(String(250), nullable=True)

    is_student: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pensioner: Mapped[bool] = mapped_column(Boolean, default=False)
    is_other: Mapped[bool] = mapped_column(Boolean, default=False)

    total_monthly: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    total_due_now: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)