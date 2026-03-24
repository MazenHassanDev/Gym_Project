import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from models.base_model import Base
from models.membership_options_model import MembershipOption
from models.memberships_model import Memberships
from models.admin_info_model import AdminInfo

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

session = Session()

exisiting_admin = session.query(AdminInfo).filter_by(user_name="admin123").first()
if not exisiting_admin:
    session.add(AdminInfo(
        user_name="admin123",
        password="123321"
    ))
    print("Admin created.")

# ---------------------------------------------------------------------------
# UGYM OPTIONS
# ---------------------------------------------------------------------------
ugym_options = [
    MembershipOption(
        gym_name="ugym",
        option_code="SUPER_OFFPEAK",
        display_name="Gym: Super-off peak (10am-12pm & 2pm-4pm)",
        price_without_gym=16.00,
        price_with_gym=0.00,
        is_time_slot=True,
        discountable=True
    ),
    MembershipOption(
        gym_name="ugym",
        option_code="OFFPEAK",
        display_name="Gym: Off-peak (12-2pm & 8-11pm)",
        price_without_gym=21.00,
        price_with_gym=0.00,
        is_time_slot=True,
        discountable=True
    ),
    MembershipOption(
        gym_name="ugym",
        option_code="ANYTIME",
        display_name="Gym: Anytime",
        price_without_gym=30.00,
        price_with_gym=0.00,
        is_time_slot=True,
        discountable=True
    ),

# UGYM ADD-ONS
# ---------------------------------------------------------------------------

    MembershipOption(
        gym_name="ugym",
        option_code="SWIMMING",
        display_name="Swimming pool",
        price_without_gym=25.00,
        price_with_gym=15.00,
        is_time_slot=False,
        discountable=True
    ),
    MembershipOption(
        gym_name="ugym",
        option_code="CLASSES",
        display_name="Classes",
        price_without_gym=20.00,
        price_with_gym=10.00,
        is_time_slot=False,
        discountable=True
    ),
    MembershipOption(
        gym_name="ugym",
        option_code="MASSAGE",
        display_name="Massage therapy",
        price_without_gym=30.00,
        price_with_gym=25.00,
        is_time_slot=False,
        discountable=False
    ),
    MembershipOption(
        gym_name="ugym",
        option_code="PHYSIO",
        display_name="Physiotherapy",
        price_without_gym=25.00,
        price_with_gym=20.00,
        is_time_slot=False,
        discountable=False
    ),
]
 
# ---------------------------------------------------------------------------
# POWERZONE OPTIONS
# ---------------------------------------------------------------------------
powerzone_options = [
    MembershipOption(
        gym_name="powerzone",
        option_code="SUPER_OFFPEAK",
        display_name="Gym: Super-off peak (10am-12pm & 2pm-4pm)",
        price_without_gym=13.00,
        price_with_gym=0.00,
        is_time_slot=True,
        discountable=True
    ),
    MembershipOption(
        gym_name="powerzone",
        option_code="OFFPEAK",
        display_name="Gym: Off-peak (12-2pm & 8-11pm)",
        price_without_gym=19.00,
        price_with_gym=0.00,
        is_time_slot=True,
        discountable=True
    ),
    MembershipOption(
        gym_name="powerzone",
        option_code="ANYTIME",
        display_name="Gym: Anytime",
        price_without_gym=24.00,
        price_with_gym=0.00,
        is_time_slot=True,
        discountable=True
    ),

# POWERZONE ADD-ONS
# ---------------------------------------------------------------------------

    MembershipOption(
        gym_name="powerzone",
        option_code="SWIMMING",
        display_name="Swimming pool",
        price_without_gym=20.00,
        price_with_gym=12.50,
        is_time_slot=False,
        discountable=True
    ),
    MembershipOption(
        gym_name="powerzone",
        option_code="CLASSES",
        display_name="Classes",
        price_without_gym=20.00,
        price_with_gym=0.00,
        is_time_slot=False,
        discountable=True
    ),
    MembershipOption(
        gym_name="powerzone",
        option_code="MASSAGE",
        display_name="Massage therapy",
        price_without_gym=30.00,
        price_with_gym=25.00,
        is_time_slot=False,
        discountable=False
    ),
    MembershipOption(
        gym_name="powerzone",
        option_code="PHYSIO",
        display_name="Physiotherapy",
        price_without_gym=30.00,
        price_with_gym=25.00,
        is_time_slot=False,
        discountable=False
    ),
]

if session.query(MembershipOption).count() == 0:
    session.add_all(ugym_options + powerzone_options)
    print("Membership options added.")
else:
    print("Membership options already exist.")

session.commit()
session.close()