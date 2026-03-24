import os
import random
import string
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
 
from flask import Flask, redirect, render_template, request, url_for, session
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from models.base_model import Base
from models.memberships_model import Memberships
from models.membership_options_model import MembershipOption
from models.admin_info_model import AdminInfo

# ===========================================================================
# 1) Load environment variables from .env
# ===========================================================================
load_dotenv()

# ===========================================================================
# 2) Flask app
# ===========================================================================
app = Flask(__name__)

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not FLASK_SECRET_KEY:
    raise RuntimeError("Missing FLASK_SECRET_KEY. Generate one and put in .env.")

app.secret_key = FLASK_SECRET_KEY
app.permanent_session_lifetime = timedelta(minutes=15)

# ===========================================================================
# 3) MySQL connection
# ===========================================================================

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

SessionDB = sessionmaker(bind=engine)

# ===========================================================================
# 4) Discounts & Joining Fees
# ===========================================================================

JOINING_FEES = {
    'ugym': 10.00,
    'powerzone': 30.00
}

DISCOUNT_RATES = {
    'ugym': {
        'student': 0.20,
        'pensioner': 0.15
    },
    'powerzone': {
        'student': 0.15,
        'pensioner': 0.20
    }
}

# ===========================================================================
# 5) Generate Memebership ID
# ===========================================================================

def generate_unique_member_id(sessiondb):
    while True:
        new_id = "GYM-" + "".join(random.choices(string.digits, k=6))
        exisiting_user = sessiondb.query(Memberships).filter_by(membership_id=new_id).first()
        if not exisiting_user:
            return new_id
        
# ===========================================================================
# 6) Calculate Monthly Total
# ===========================================================================

def calculate_monthly_total(gym_name, gym_access, is_student, is_pensioner):
    session = SessionDB()

    total = 0.00
    user_items = []

    discount_type = 'student' if is_student else ('pensioner' if is_pensioner else None)
    discount_rate = DISCOUNT_RATES[gym_name.lower()].get(discount_type, 0) if discount_type else 0

    has_gym_access = gym_access is not None

    if gym_access:
        option = session.query(MembershipOption).filter_by(gym_name=gym_name.lower(), option_code=gym_access).first()

        if option:
            price = float(option.price_without_gym)
            
            if option.discountable and discount_rate:
                price = round(21.00 * (1 - discount_rate), 2)

            total += price
            user_items.append({'display_name': option.display_name, 'price': price})

    for addon_code in gym_addons:
        option = session.query(MembershipOption).filter_by(gym_name=gym_name.lower(), option_code=addon_code).first()

        if option:
            price = float(option.price_with_gym) if has_gym_access else float(option.price_without_gym)

            if option.discountable and discount_rate:
                price = round(price * (1 - discount_rate), 2)

            total += price
            user_items.append({'display_name': option.display_name, 'price': price})

    return round(total, 2), user_items


# ===========================================================================
# ADMIN ROUTES
# ===========================================================================
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        input_username = request.form.get('username', '').strip()
        input_password = request.form.get('password', '').strip()

        sessiondb = SessionDB()
        try:

            admin = sessiondb.query(AdminInfo).filter_by(user_name=input_username).first()

            if admin and admin.password == input_password:
                session['admin_logged_in'] = True
                return redirect(url_for('admin_submissions'))

            return render_template('adminLogin.html', error="Please enter valid credentials")
        
        finally:
            sessiondb.close()

    return render_template('adminLogin.html')

@app.route('/admin_submissions', methods=['GET'])
def admin_submissions():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    q = request.args.get('q', '').strip()

    sessiondb = SessionDB()
    try:

        if q:
            members = sessiondb.query(Memberships).filter(Memberships.first_name.like(f'%{q}%') | Memberships.last_name.like(f'%{q}%')).all()
        else:
            members = sessiondb.query(Memberships).all()

        return render_template('submissions.html', members=members)
    
    finally:
        sessiondb.close()

@app.route('/admin_edit/<string:submission_id>', methods=['GET', 'POST'])
def admin_edit(submission_id):

    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    sessiondb = SessionDB()
    try:

        members = sessiondb.query(Memberships).filter(Memberships.membership_id == submission_id).first()

        if not members:
            return render_template('edit.html', error="Record not found")

        if request.method == 'POST':
            members.first_name = request.form.get('first_name')
            members.last_name = request.form.get('last_name')
            members.gym_name = request.form.get('gym_name')
            members.gym_access = request.form.get('gym_access') or None
            members.gym_addons = ','.join(request.form.getlist('gym_addons')) or None
            sessiondb.commit()

            return redirect(url_for('admin_submissions'))
        
        return render_template('edit.html', members=members)

    finally:
        sessiondb.close()


@app.route('/admin_delete/<string:submission_id>', methods=['GET', 'POST'])
def admin_delete(submission_id):

    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    sessiondb = SessionDB()

    try:
        members = sessiondb.query(Memberships).filter(Memberships.membership_id == submission_id).first()

        if not members:
            return redirect(url_for('admin_submissions'))
        
        sessiondb.delete(members)
        sessiondb.commit()

    finally:
        sessiondb.close()

    return redirect(url_for('admin_submissions'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ===========================================================================
# MAIN ROUTES
# ===========================================================================
@app.route('/')
def root():  # put application's code here
    return redirect(url_for("home"))

@app.route('/home')
def home():
    return render_template("home.html")


# GYM ROUTES
# ===========================================================================

@app.route('/ugym')
def ugym():
    return render_template('ugym.html')

@app.route('/powerzone')
def powerzone():
    return render_template('powerzone.html')

@app.route('/compare')
def compare():
    return render_template('comparePage.html')


# ACTION ROUTES
# ===========================================================================

@app.route('/join_now', methods=['GET','POST'])
def join_now():
    if request.method == 'POST':
        gym_access = request.form.get('gym_access') or None
        gym_addons = request.form.getlist('gym_addons')
        discount = request.form.get('typeOf')

        if not gym_access and not gym_addons:
            return render_template('join_now.html', error="Please select at least one option.")

        session.permanent = True
        session['join_gym_access'] = gym_access
        session['join_gym_addons'] = gym_addons
        session['join_discount'] = discount

        return redirect(url_for('join_details'))
    
    return render_template('join_now.html')

@app.route('/join_details', methods=['GET', 'POST'])
def join_details():
    
    if 'join_gym_access' not in session or 'join_gym_addons' not in session:
        return redirect(url_for('join_now'))
    
    if request.method == 'POST':
        first_name = request.form.get('first_name').strip()
        last_name = request.form.get('last_name').strip()
        dob = request.form.get('dob')
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()

        if not first_name or not last_name or not dob or not email or not password:
            return render_template('join_details.html', error="Please fill in all fields.")
        
        date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
        age = relativedelta(date.today(), date_of_birth).years

        if age < 16:
            return render_template('join_details.html', error="You must be at least 16 years old to join.")
        
        discount = session.get('join_discount')

        if discount == 'student':
            is_student = True
            is_pensioner = False
        elif discount == 'pensioner':
            is_student = False
            is_pensioner = True
        else:
            is_student = False
            is_pensioner = False
        
        if is_student and age >= 26:
            return render_template('join_details.html', error="You are not eligible for student discount.")
        
        if is_pensioner and age < 66:
            return render_template('join_details.html', error="You are not eligible for pensioner discount.")
        
        sessiondb = SessionDB()

        try:

            existing_memeber = sessiondb.query(Memberships).filter_by(email=email).first()

            if existing_memeber:
                return render_template('join_details.html', error="Email already exists. Please login to continue.")
            
        finally:
            sessiondb.close()

        session['join_first_name'] = first_name
        session['join_last_name'] = last_name
        session['join_dob'] = dob
        session['join_email'] = email
        session['join_password'] = password

        return redirect(url_for('pay_now'))
    
    return render_template('join_details.html')


@app.route('/pay_now', methods=['GET','POST'])
def pay_now():

    required_date = ['join_gym_access', 'join_gym_addons', 'join_first_name', 'join_email']

    for val in required_date:
        if val not in session:
            return redirect(url_for('join_now)'))
        
    gym_access = session.get('join_gym_access')
    gym_addons = session.get('join_gym_addons')
    discount = session.get('join_discount')
    is_student = True if discount == 'student' else False
    is_pensioner = True if discount == 'pensioner' else False

    if request.method == 'POST':

        chosen_gym = request.form.get('chosen_gym')

        if not chosen_gym:
            return redirect(url_for('pay_now'))
        
        sessiondb = SessionDB()
        try:

            total_monthly = calculate_monthly_total(chosen_gym, gym_access, gym_addons, is_student, is_pensioner, sessiondb)
            joining_fee = JOINING_FEES[chosen_gym.lower()]

            member_id = generate_unique_member_id(sessiondb)

            new_member = Memberships(
                membership_id = member_id,
                first_name = session['join_first_name'],
                last_name = session['join_last_name'],
                dob = session['join_dob'],
                email = session['join_email'],
                password = session['join_password'],
                gym_name = chosen_gym,
                gym_access = gym_access,
                gym_addons = ','.join(gym_addons) if gym_addons else None,
                is_student = is_student,
                is_pensioner = is_pensioner,
                total_monthly = total_monthly,
                joining_fee = joining_fee
            )

            sessiondb.add(new_member)
            sessiondb.close()

            for val in required_date:
                session.pop(val, None)
        
        finally:
            sessiondb.close()

    sessiondb = SessionDB()
    try:
        
        ugym_monthly, ugym_items = calculate_monthly_total('ugym', gym_access, gym_addons, is_student, is_pensioner, sessiondb)
        powerzone_monthly, powerzone_items = calculate_monthly_total('powerzone', gym_access, gym_addons, is_student, is_pensioner, sessiondb)

    finally:
        sessiondb.close()

    ugym_joining_fee = JOINING_FEES['ugym']
    powerzone_joining_fee = JOINING_FEES['powerzone']

    ugym_total = ugym_monthly + ugym_joining_fee
    powerzone_total = powerzone_monthly + powerzone_joining_fee

    cheaper_gym = 'ugym' if ugym_total < powerzone_total else 'powerzone'

    return render_template('pay_now.html', ugym_items=ugym_items, ugym_monthly=ugym_monthly, ugym_joining_fee=ugym_joining_fee,
                           powerzone_items=powerzone_items, powerzone_monthly=powerzone_monthly, powerzone_joining_fee=powerzone_joining_fee,
                           cheaper_gym=cheaper_gym)

# USER AUTHENTICATION ROUTES
# ===========================================================================
@app.route('/login', methods=['GET','POST'])
def login():

    if 'logged_in_member_id' in session:
        return redirect(url_for("member_details"))

    new_member_id = session.pop('new_member_id', None)

    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password').strip()

        if not email or not password:
            return render_template('login.html', error="Please enter your email and password.")
        

        sessiondb = SessionDB()

        try:

            member = sessiondb.query(Memberships).filter_by(email=email).first()

            if not member or member.password != password:
                return render_template('login.html', error="Invalid email or password.", new_member_id = new_member_id)

            session.permanent = True
            session['logged_in_member_id'] = member.membership_id
            session['logged_in_first_name'] = member.first_name

            return redirect(url_for("member_details"))

        finally:
            sessiondb.close()

    return render_template('login.html', new_member_id=new_member_id)


@app.route('/member_details', methods=['GET','POST'])
def member_details():

    if 'logged_in_member_id' not in session:
        return redirect(url_for("login"))

    sessiondb = SessionDB()
    try:
        
        member = sessiondb.query(Memberships).filter_by(memberships.membership_id == session['logged_in_member_id']).first()

        addons_list = member.gym_addons.split(',') if member.gym_addons else None

        return render_template('memberDetails.html', member=member, addons_list=addons_list)

    finally:
        sessiondb.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

# RUN MAIN ONLY
# ===========================================================================
if __name__ == '__main__':
    app.run(debug=True)
