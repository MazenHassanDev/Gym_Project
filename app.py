from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from dotenv import load_dotenv
from werkzeug.serving import make_ssl_devcert

from sqlalchemy import DateTime, Integer, String, create_engine, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
app = Flask(__name__)


@app.route('/')
def root():  # put application's code here
    return redirect(url_for("home"))

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/join_form')
def join():
    return render_template("joinForm.html")

@app.route('/form_result')
def form_result():
    return render_template("formResult.html")


if __name__ == '__main__':
    app.run()
