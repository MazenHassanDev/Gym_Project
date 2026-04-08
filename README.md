# Gym Membership System

A university group project built for a Web Programming module. The application is a gym membership management system for two gyms — **UGym** and **PowerZone** — allowing users to sign up, compare membership prices, and manage their account, with an admin dashboard for staff.

## Team

Built by a group of 4 students. Responsibilities were split as follows:

- **Mazen** — Backend: Flask routing, MySQL database connection, SQLAlchemy ORM setup, business logic (pricing, discounts, membership ID generation)
- **Rest of group** — Frontend HTML templates and database model design

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy ORM
- **Database:** MySQL (via PyMySQL)
- **Frontend:** Jinja2 templates, Bootstrap 4, CSS

## Project Structure

```
GYM_PROJECT/
├── app.py                          # Flask routes and app entry point
├── config.py                       # Database URL and environment config
├── requirements.txt
├── .env.example                    # Environment variable template
├── .gitignore
├── models/
│   ├── base_model.py
│   ├── admin_info_model.py
│   ├── membership_options_model.py
│   └── memberships_model.py
├── static/
│   └── styles.css
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── ugym.html
│   ├── powerzone.html
│   ├── join_now.html
│   ├── pay_now.html
│   ├── join_details.html
│   ├── login.html
│   ├── memberDetails.html
│   ├── adminLogin.html
│   ├── submissions.html
│   └── edit.html
└── utils/
    ├── calculate_monthly_total.py  # Pricing and discount logic
    ├── generate_member_id.py       # Unique membership ID generator
    └── database.py                 # Table creation and seed data
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/gym-membership-system.git
cd gym-membership-system
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials and a Flask secret key.

### 5. Set up the database

Creates all tables and seeds membership options and a default admin account:

```bash
python utils/database.py
```

### 6. Run the app

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

## Admin Access

Navigate to `/admin_login`. Default credentials are defined in `utils/database.py` and should be changed before use.