import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
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

@app.route('/join_gym_form', methods=["GET", "POST"])
def join_gym():
    if request.method == "POST":
        selected_gym = request.form.get("gym")
        selected_option = request.form.get("options")

        if not selected_gym or not selected_option:
            flash("Please select an option before continuing")
            return redirect(url_for("join_gym"))

        return redirect(url_for("join_member", gym=selected_gym, options=selected_option))

    return render_template("joinFormGym.html")

@app.route('/join_member_form', methods=["GET", "POST"])
def join_member():
    selected_gym = request.args.get("gym")
    selected_option = request.args.get("options")

    if not selected_gym or not selected_option:
        return redirect(url_for("join_gym"))

    if selected_gym == "ugym" and selected_option:
        return render_template('joinFormMemberUGYM.html', gym=selected_gym, options=selected_option)
    elif selected_gym == "powerzone" and selected_option:
        return render_template('joinFormMemberPOWER.html', gym=selected_gym, options=selected_option)
    else:
        return redirect(url_for("join_gym"))




@app.route('/form_result')
def form_result():
    return render_template("formResult.html")


if __name__ == '__main__':
    app.run()
