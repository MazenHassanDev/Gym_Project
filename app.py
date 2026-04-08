import os
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
 
from flask import Flask, redirect, render_template, request, url_for, session
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from utils.calculate_monthly_total import calculate_total, JOINING_FEES
from utils.generate_member_id import generate_unique_member_id

from config import *

from models.base_model import Base
from models.memberships_model import Memberships
from models.membership_options_model import MembershipOption
from models.admin_info_model import AdminInfo

# ===========================================================================
# Load environment variables from .env
# ===========================================================================
load_dotenv()

# ===========================================================================
# Flask app
# ===========================================================================
app = Flask(__name__)

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not FLASK_SECRET_KEY:
    raise RuntimeError("Missing FLASK_SECRET_KEY. Generate one and put in .env.")

app.secret_key = FLASK_SECRET_KEY
app.permanent_session_lifetime = timedelta(minutes=15)

# ===========================================================================
# MySQL connection
# ===========================================================================

engine = create_engine(DATABASE_URL)

SessionDB = sessionmaker(bind=engine)

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

            addons_list = request.form.getlist('gym_addons')
            new_total, _ = calculate_total(members.gym_name, members.gym_access, addons_list, members.is_student, members.is_pensioner, sessiondb)
            members.total_monthly = new_total
            
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
        

        return redirect(url_for('pay_now'))
    
    return render_template('join_now.html')

@app.route('/pay_now', methods=['GET','POST'])
def pay_now():

    required_keys = ['join_gym_access', 'join_gym_addons']
    for val in required_keys:
        if val not in session:
            return redirect(url_for('join_now'))
 
    gym_access = session.get('join_gym_access')
    gym_addons = session.get('join_gym_addons')
    discount = session.get('join_discount')
    if discount == 'student':
        is_student = True
    else:
        is_student = False
    if discount == 'pensioner':
        is_pensioner = True
    else:
        is_pensioner = False
 
    if request.method == 'POST':
        chosen_gym = request.form.get('chosen_gym')
        if not chosen_gym:
            return redirect(url_for('pay_now'))
 
        session['join_gym_name'] = chosen_gym
        return redirect(url_for('join_details'))
 
    sessiondb = SessionDB()
    try:
        ugym_monthly, ugym_items = calculate_total(
            'ugym', gym_access, gym_addons, is_student, is_pensioner, sessiondb
        )
        powerzone_monthly, powerzone_items = calculate_total(
            'powerzone', gym_access, gym_addons, is_student, is_pensioner, sessiondb
        )
    finally:
        sessiondb.close()
 
    ugym_joining_fee = JOINING_FEES['ugym']
    powerzone_joining_fee = JOINING_FEES['powerzone']
    ugym_total = ugym_monthly + ugym_joining_fee
    powerzone_total = powerzone_monthly + powerzone_joining_fee
    cheaper_gym = 'ugym' if ugym_total <= powerzone_total else 'powerzone'
 
    return render_template('pay_now.html',
        ugym_items=ugym_items,
        ugym_monthly=ugym_monthly,
        ugym_joining_fee=ugym_joining_fee,
        powerzone_items=powerzone_items,
        powerzone_monthly=powerzone_monthly,
        powerzone_joining_fee=powerzone_joining_fee,
        cheaper_gym=cheaper_gym
    )

@app.route('/join_details', methods=['GET', 'POST'])
def join_details():
    
    if 'join_gym_access' not in session or 'join_gym_addons' not in session:
        return redirect(url_for('join_now'))
    
    if 'join_gym_name' not in session:
        return redirect(url_for('pay_now'))
    
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
            is_other = False
        elif discount == 'pensioner':
            is_student = False
            is_pensioner = True
            is_other = False
        elif discount == 'other':
            is_student = False
            is_pensioner = False
            is_other = True
        else:
            is_student = False
            is_pensioner = False
            is_other = False
        
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
        session['join_is_other'] = is_other

        gym_name = session.get('join_gym_name')
        gym_access = session.get('join_gym_access')
        gym_addons = session.get('join_gym_addons', [])

        sessiondb2 = SessionDB()

        try:
            total_monthly, _ = calculate_total(gym_name, gym_access, gym_addons, is_student, is_pensioner,sessiondb2)
            joining_fee = JOINING_FEES[gym_name.lower()]
            member_id = generate_unique_member_id(sessiondb2)

            new_member = Memberships(
                membership_id = member_id,
                first_name    = first_name,
                last_name     = last_name,
                dob           = dob,
                email         = email,
                password      = password,
                gym_name      = gym_name,
                gym_access    = gym_access,
                gym_addons    = ','.join(gym_addons) if gym_addons else None,
                is_student    = is_student,
                is_pensioner  = is_pensioner,
                is_other      = is_other,
                total_monthly = total_monthly,
                total_due_now = joining_fee
            )
            sessiondb2.add(new_member)
            sessiondb2.commit()

            for val in ['join_gym_access', 'join_gym_addons', 'join_discount',
                        'join_gym_name', 'join_first_name', 'join_last_name',
                        'join_dob', 'join_email', 'join_password']:
                session.pop(val, None)
            
            session['new_member_id'] = member_id
            return redirect(url_for('login'))
        
        finally:
            sessiondb2.close()
    
    return render_template('join_details.html')


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
        
        member = sessiondb.query(Memberships).filter(Memberships.membership_id == session['logged_in_member_id']).first()

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
