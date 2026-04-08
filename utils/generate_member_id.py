import random
import string
from models.memberships_model import Memberships

# ===========================================================================
# Generate Memebership ID
# ===========================================================================

def generate_unique_member_id(sessiondb):
    while True:
        new_id = "GYM-" + "".join(random.choices(string.digits, k=6))
        exisiting_user = sessiondb.query(Memberships).filter_by(membership_id=new_id).first()
        if not exisiting_user:
            return new_id