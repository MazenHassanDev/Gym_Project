from sqlalchemy import Integer, String, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from models.base_model import Base
 
class MembershipOption(Base):
    __tablename__ = "membership_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    gym_name: Mapped[str] = mapped_column(String(50), nullable=False)
    option_code: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    price_without_gym: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_with_gym: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    is_time_slot: Mapped[bool] = mapped_column(Boolean, nullable=False)

    discountable: Mapped[bool] = mapped_column(Boolean, nullable=False)
