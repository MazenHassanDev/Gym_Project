import os
from datetime import datetime
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


def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT')),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/db-test')
def db_test():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM membership_options')
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return f"Database connected. membership_options rows : {result}"

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

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO memberships (membership_id, gym_name, gym_access, first_name, last_name, dob,
                                     is_student, is_pensioner, selections_json, total_monthly, total_due_now)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (None, chosen_gym, chosen_access, first_name, last_name, dob,
              is_student, is_pensioner, "[]", 0.00, 0.00))

        pending_member_id = cursor.lastrowid
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

        cursor.execute("""
            UPDATE memberships
            SET membership_id = %s
            WHERE membership_id = %s
        """, (member_id, pending_member_id))

        conn.commit()
        cursor.close()
        conn.close()

        session.pop('pending_member_id', None)
        session['new_member_id'] = member_id
        # flash(f"You have successfully paid!\n Membership ID: {member_id}")
        return redirect(url_for("login"))
    else:
        return render_template('payPage.html')



@app.route('/login')
def login():

    new_member_id = session["new_member_id"]

    if request.method == 'POST':
        member_id = session.get('member_id', '').strip()

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

        return render_template('memberDetails.html', member = member)

    return render_template('memberDetails.html', new_member_id = new_member_id)


if __name__ == '__main__':
    app.run(debug=True)
