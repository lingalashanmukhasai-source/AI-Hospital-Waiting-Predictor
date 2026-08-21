# ==========================================================
# MEDIPREDICT AI
# HOSPITAL QUEUE INTELLIGENCE SYSTEM
# ==========================================================

import os
import sqlite3
from datetime import datetime
from urllib.parse import quote

import joblib
import pandas as pd
import requests

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================================
# APPLICATION
# ==========================================================

app = Flask(__name__)

app.secret_key = "medipredict_ai_secret_key_2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "hospital.db"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "hospital_waiting_model.pkl"
)


# ==========================================================
# DATABASE
# ==========================================================

def get_db():
    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def create_tables():

    db = get_db()

    cursor = db.cursor()

    # ------------------------------------------------------
    # USERS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # ------------------------------------------------------
    # PATIENTS
    # ------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            appointment_type TEXT NOT NULL,
            priority TEXT DEFAULT 'Normal',
            arrival_time TEXT NOT NULL
        )
    """)

    db.commit()

    db.close()


# ==========================================================
# MODEL
# ==========================================================

model = None


def load_model():

    global model

    if os.path.exists(MODEL_PATH):

        try:
            model = joblib.load(MODEL_PATH)

            print("AI MODEL LOADED SUCCESSFULLY")

        except Exception as error:

            print(
                "MODEL LOAD ERROR:",
                error
            )

            model = None

    else:

        print(
            "MODEL FILE NOT FOUND:",
            MODEL_PATH
        )


# ==========================================================
# LOGIN REQUIRED
# ==========================================================

def login_required():

    return "user_id" in session


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():

    if not login_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "index.html",
        username=session.get("username")
    )


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter username and password.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        db.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            return redirect(
                url_for("home")
            )

        flash(
            "Invalid username or password.",
            "error"
        )

    return render_template(
        "index.html",
        auth_page="login"
    )


# ==========================================================
# REGISTER
# ==========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not username or not password:

            flash(
                "All fields are required.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if len(username) < 3:

            flash(
                "Username must contain at least 3 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        password_hash = generate_password_hash(
            password
        )

        db = get_db()

        try:

            db.execute(
                """
                INSERT INTO users
                (
                    username,
                    password,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    password_hash,
                    datetime.now().isoformat()
                )
            )

            db.commit()

        except sqlite3.IntegrityError:

            db.close()

            flash(
                "Username already exists.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        db.close()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "index.html",
        auth_page="register"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ==========================================================
# API - PREDICTION
# ==========================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    global model

    if model is None:

        load_model()

    if model is None:

        return jsonify({
            "success": False,
            "message": (
                "AI model is not available. "
                "Run train_model.py first."
            )
        }), 500

    try:

        patients_waiting = int(
            request.form.get(
                "patients_waiting",
                0
            )
        )

        doctors_available = int(
            request.form.get(
                "doctors_available",
                1
            )
        )

        average_consultation_time = float(
            request.form.get(
                "average_consultation_time",
                15
            )
        )

        emergency_patients = int(
            request.form.get(
                "emergency_patients",
                0
            )
        )

        department = request.form.get(
            "department",
            "General"
        )

        appointment_type = request.form.get(
            "appointment_type",
            "Walk-in"
        )

        # Current date/time
        now = datetime.now()

        hour = now.hour

        day_of_week = now.strftime("%A")

        # --------------------------------------------------
        # INPUT VALIDATION
        # --------------------------------------------------

        if patients_waiting < 0:
            patients_waiting = 0

        if doctors_available < 1:
            doctors_available = 1

        if average_consultation_time <= 0:
            average_consultation_time = 15

        if emergency_patients < 0:
            emergency_patients = 0

        # --------------------------------------------------
        # DATAFRAME
        # --------------------------------------------------

        input_data = pd.DataFrame([{

            "patients_waiting":
                patients_waiting,

            "doctors_available":
                doctors_available,

            "average_consultation_time":
                average_consultation_time,

            "emergency_patients":
                emergency_patients,

            "hour":
                hour,

            "day_of_week":
                day_of_week,

            "department":
                department,

            "appointment_type":
                appointment_type
        }])

        # --------------------------------------------------
        # AI PREDICTION
        # --------------------------------------------------

        prediction = model.predict(
            input_data
        )

        waiting_time = float(
            prediction[0]
        )

        waiting_time = max(
            0,
            waiting_time
        )

        # --------------------------------------------------
        # QUEUE PRESSURE
        # --------------------------------------------------

        patient_load = (
            patients_waiting /
            doctors_available
        )

        emergency_load = (
            emergency_patients * 1.5
        )

        pressure_score = (
            patient_load +
            emergency_load
        )

        if pressure_score < 5:

            pressure = "LOW"

        elif pressure_score < 10:

            pressure = "MODERATE"

        elif pressure_score < 20:

            pressure = "HIGH"

        else:

            pressure = "CRITICAL"

        # --------------------------------------------------
        # RECOMMENDATION
        # --------------------------------------------------

        if waiting_time <= 15:

            recommendation = (
                "Low expected waiting time. "
                "Queue conditions are currently favorable."
            )

        elif waiting_time <= 30:

            recommendation = (
                "Moderate waiting time expected. "
                "Please monitor the queue."
            )

        elif waiting_time <= 60:

            recommendation = (
                "High waiting time expected. "
                "Consider checking alternative departments "
                "or less busy periods when appropriate."
            )

        else:

            recommendation = (
                "Very high waiting time predicted. "
                "Hospital staff should review queue capacity."
            )

        return jsonify({

            "success": True,

            "waiting_time":
                round(waiting_time, 1),

            "pressure":
                pressure,

            "pressure_score":
                round(pressure_score, 2),

            "recommendation":
                recommendation,

            "patients_waiting":
                patients_waiting,

            "doctors_available":
                doctors_available,

            "emergency_patients":
                emergency_patients,

            "department":
                department,

            "appointment_type":
                appointment_type,

            "hour":
                hour,

            "day":
                day_of_week
        })

    except Exception as error:

        print(
            "PREDICTION ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Prediction failed: " +
                str(error)
        }), 400


# ==========================================================
# API - ADD PATIENT
# ==========================================================

@app.route(
    "/api/patients",
    methods=["POST"]
)
def add_patient():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    try:

        data = request.get_json()

        name = data.get(
            "name",
            ""
        ).strip()

        department = data.get(
            "department",
            "General"
        )

        appointment_type = data.get(
            "appointment_type",
            "Walk-in"
        )

        priority = data.get(
            "priority",
            "Normal"
        )

        if not name:

            return jsonify({
                "success": False,
                "message": "Patient name is required."
            }), 400

        db = get_db()

        db.execute(
            """
            INSERT INTO patients
            (
                name,
                department,
                appointment_type,
                priority,
                arrival_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                department,
                appointment_type,
                priority,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        db.commit()

        db.close()

        return jsonify({
            "success": True,
            "message": "Patient added successfully."
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 400


# ==========================================================
# API - GET PATIENTS
# ==========================================================

@app.route("/api/patients")
def get_patients():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    db = get_db()

    patients = db.execute(
        """
        SELECT *
        FROM patients
        ORDER BY id DESC
        """
    ).fetchall()

    db.close()

    return jsonify({

        "success": True,

        "patients": [
            dict(patient)
            for patient in patients
        ]
    })


# ==========================================================
# API - DELETE PATIENT
# ==========================================================

@app.route(
    "/api/patients/<int:patient_id>",
    methods=["DELETE"]
)
def delete_patient(patient_id):

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    db = get_db()

    db.execute(
        """
        DELETE FROM patients
        WHERE id = ?
        """,
        (patient_id,)
    )

    db.commit()

    db.close()

    return jsonify({
        "success": True,
        "message": "Patient removed."
    })


# ==========================================================
# API - QUEUE STATISTICS
# ==========================================================

@app.route("/api/stats")
def stats():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    db = get_db()

    total = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM patients
        """
    ).fetchone()["count"]

    emergency = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM patients
        WHERE priority = 'Emergency'
        """
    ).fetchone()["count"]

    db.close()

    return jsonify({

        "success": True,

        "total_patients":
            total,

        "emergency_patients":
            emergency
    })


# ==========================================================
# API - HOSPITAL SEARCH
# ==========================================================

@app.route(
    "/api/hospitals",
    methods=["GET"]
)
def search_hospitals():

    if not login_required():

        return jsonify({
            "success": False,
            "message": "Please login first."
        }), 401

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify({

            "success": False,

            "message":
                "Enter a location or hospital name."
        }), 400

    try:

        # --------------------------------------------------
        # OpenStreetMap Nominatim
        # --------------------------------------------------

        url = (
            "https://nominatim.openstreetmap.org/search"
        )

        params = {

            "q":
                query + " hospital",

            "format":
                "json",

            "limit":
                10,

            "addressdetails":
                1
        }

        headers = {

            "User-Agent":
                "MediPredictAI/1.0"
        }

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        results = response.json()

        hospitals = []

        for item in results:

            address = item.get(
                "display_name",
                "Address unavailable"
            )

            hospitals.append({

                "name":
                    item.get(
                        "name"
                    )
                    or "Hospital",

                "address":
                    address,

                "latitude":
                    float(
                        item["lat"]
                    ),

                "longitude":
                    float(
                        item["lon"]
                    ),

                "type":
                    item.get(
                        "type",
                        "hospital"
                    )
            })

        return jsonify({

            "success": True,

            "count":
                len(hospitals),

            "hospitals":
                hospitals
        })

    except requests.RequestException as error:

        print(
            "HOSPITAL SEARCH ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Hospital search service is temporarily unavailable."
        }), 503

    except Exception as error:

        print(
            "HOSPITAL SEARCH ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "message":
                "Could not search hospitals."
        }), 500


# ==========================================================
# API - HEALTH
# ==========================================================

@app.route("/api/health")
def health():

    return jsonify({

        "status":
            "online",

        "model_loaded":
            model is not None,

        "time":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    })


# ==========================================================
# STARTUP
# ==========================================================

create_tables()

load_model()


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "MEDIPREDICT AI"
    )

    print(
        "Hospital Queue Intelligence System"
    )

    print("=" * 60)

    print(
        "Server: http://127.0.0.1:5000"
    )

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )