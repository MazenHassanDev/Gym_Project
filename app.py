import os
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import random
import string

from flask import Flask, flash, redirect, render_template, request, url_for, session
from dotenv import load_dotenv
from sqlalchemy.util import methods_equivalent
from werkzeug.serving import make_ssl_devcert
import mysql.connector

from sqlalchemy import DateTime, Integer, String, create_engine, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

# ===========================================================================
# 1) Load environment variables from .env
# ===========================================================================
load_dotenv()

# ===========================================================================
# 2) Flask app & MySQL connection
# ===========================================================================
app = Flask(__name__)

FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not FLASK_SECRET_KEY:
    raise RuntimeError("Missing FLASK_SECRET_KEY. Generate one and put in .env.")

app.secret_key = FLASK_SECRET_KEY
app.permanent_session_lifetime = timedelta(minutes=15)


def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/admin_login')
def admin_login():
    return render_template('adminPage.html')

@app.route('/db-test')
def db_test():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM membership_options')
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return f"Database connected. membership_options rows : {result}"

def calculate_monthly_total(gym_name, gym_access, is_student, is_pensioner):
    access_map = {
        'off-peak' : 'GYM_OFFPEAK',
        'anytime' : 'GYM_ANYTIME',
        'massage' : 'MASSAGE',
        'physio' : 'PHYSIO'
    }

    option_code = access_map[gym_access]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT price_monthly, discountable FROM membership_options WHERE gym_name = %s AND option_code = %s
    """, (gym_name.lower(), option_code))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return 0.00

    total = float(row['price_monthly'])

    if row['discountable']:
        if gym_name == 'UGYM':
            if is_student:
                total *= 0.80
            elif is_pensioner:
                total *= 0.85
        elif gym_name == 'PowerZone':
            if is_student:
                total *= 0.85
            elif is_pensioner:
                total *= 0.80

    return round(total, 2)

@app.route('/')
def root():  # put application's code here
    return redirect(url_for("home"))

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/ugym')
def ugym():
    return render_template('ugym.html')

@app.route('/powerzone')
def powerzone():
    return render_template('powerzone.html')

@app.route('/compare')
def compare():
    return render_template('comparePage.html')

@app.route('/join_now', methods=['GET','POST'])
def join_now():
    if request.method == 'POST':
        chosen_gym = request.form.get('gym')
        chosen_access = request.form.get('access')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob')
        type_of_discount = request.form.get('typeOf')
        is_student = 1 if type_of_discount == 'student' else 0
        is_pensioner = 1 if type_of_discount == 'pensioner' else 0

        if not chosen_gym or not chosen_access or not first_name or not last_name or not dob:
            return "Missing required fields. Make sure all fields are filled.", 400

        dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
        age = relativedelta(date.today(), dob_date).years
        if age < 16:
            return render_template('join_now.html', error="You must be at least 16 years old to join.")

        if is_student and age >= 26:
            return render_template('join_now.html', error="You are not applicable for student discount.")

        if is_pensioner and age < 66:
            return render_template('join_now.html', error="You are not applicable for pensioner discount.")




        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
           INSERT INTO memberships (gym_name, gym_access, first_name, last_name, dob,
                                    is_student, is_pensioner, total_monthly, total_due_now)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
           """, (chosen_gym, chosen_access, first_name, last_name, dob,
                 is_student, is_pensioner, 0.00, 0.00))

        pending_member_id = cursor.lastrowid
        session.permanent = True
        session["pending_member_id"] = pending_member_id

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("pay_now"))
    else:
        return render_template('join_now.html')


@app.route('/pay_now', methods=['GET','POST'])
def pay_now():

    def generate_unique_member_id(conn):
        cursor = conn.cursor()
        while True:
            new_id = "GYM-" + "".join(random.choices(string.digits, k=6))
            cursor.execute('SELECT COUNT(*) FROM memberships WHERE membership_id = %s', (new_id,))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.close()
                return new_id

    if request.method == 'POST':
        if "pending_member_id" not in session:
            return "No pending membership found. Please Join Now.", 400

        pending_member_id = session["pending_member_id"]

        conn = get_db()
        cursor = conn.cursor()

        member_id = generate_unique_member_id(conn)


        cursor.execute("SELECT gym_name, gym_access, is_student, is_pensioner FROM memberships WHERE id = %s", (pending_member_id,))
        row = cursor.fetchone()
        total = calculate_monthly_total(row[0],row[1], row[2], row[3])


        cursor.execute("""
            UPDATE memberships
            SET membership_id = %s, total_monthly = %s, total_due_now = %s
            WHERE id = %s
        """, (member_id, total, total, pending_member_id))

        conn.commit()
        cursor.close()
        conn.close()

        session.pop('pending_member_id', None)
        session['new_member_id'] = member_id
        return redirect(url_for("login"))
    else:
        pending_member_id = session.get('pending_member_id')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT gym_name, gym_access, is_student, is_pensioner FROM memberships WHERE id = %s", (pending_member_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        total = calculate_monthly_total(row[0], row[1], row[2], row[3])

        return render_template('payPage.html', total=total)



@app.route('/login', methods=['GET','POST'])
def login():

    if 'logged_in_member_id' in session:
        return redirect(url_for("member_details"))

    new_member_id = session.pop('new_member_id', None)

    if request.method == 'POST':
        member_id = request.form.get('memberID', '').strip()

        if not member_id:
            return render_template('login.html', error="Please enter a membership ID.", new_member_id = new_member_id)

        conn = get_db()
        cursor = conn.cursor(dictionary=True)  # returns rows as dicts
        cursor.execute("SELECT * FROM memberships WHERE membership_id = %s", (member_id,))
        member = cursor.fetchone()
        cursor.close()
        conn.close()

        if not member:
            return render_template('login.html', error="Membership ID not found.", new_member_id = new_member_id)

        session.permanent = True
        session['logged_in_member_id'] = member_id
        session['logged_in_first_name'] = member['first_name']

        return redirect(url_for("member_details"))

    return render_template('login.html', new_member_id = new_member_id)


@app.route('/member_details', methods=['GET','POST'])
def member_details():

    if 'logged_in_member_id' not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM memberships WHERE membership_id = %s", (session["logged_in_member_id"],))
    member = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('memberDetails.html', member=member)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.run(debug=True)
