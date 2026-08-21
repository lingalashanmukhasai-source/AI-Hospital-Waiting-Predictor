# ==========================================================
# MEDIPREDICT AI 4.0
# AI HOSPITAL FLOW OPTIMIZATION SYSTEM
# ==========================================================

import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from model import (
    predict_waiting_time,
    explain_prediction,
    simulate_scenario,
    generate_recommendation
)


# ==========================================================
# APPLICATION
# ==========================================================

app = Flask(__name__)

app.secret_key = "medipredict-ai-4-secret"

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "hospital.db"
)


os.makedirs(
    os.path.dirname(DATABASE_PATH),
    exist_ok=True
)


# ==========================================================
# DATABASE
# ==========================================================

def get_db():

    db = sqlite3.connect(
        DATABASE_PATH
    )

    db.row_factory = sqlite3.Row

    return db


def initialize_database():

    db = get_db()

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            department TEXT NOT NULL,

            appointment_type TEXT NOT NULL,

            priority TEXT NOT NULL,

            arrival_time TEXT NOT NULL

        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS prediction_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patients_waiting INTEGER,

            doctors_available INTEGER,

            emergency_patients INTEGER,

            predicted_wait REAL,

            created_at TEXT

        )
        """
    )

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS hospitals (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT UNIQUE NOT NULL,

            city TEXT,

            departments TEXT,

            doctors INTEGER DEFAULT 0

        )
        """
    )

    hospitals = [

        (
            "Apollo Hospitals",
            "Hyderabad",
            "General,Cardiology,Pediatrics,Emergency",
            25
        ),

        (
            "CARE Hospitals",
            "Hyderabad",
            "General,Cardiology,Pediatrics,Emergency",
            20
        ),

        (
            "Yashoda Hospitals",
            "Hyderabad",
            "General,Cardiology,Pediatrics,Emergency",
            22
        ),

        (
            "KIMS Hospitals",
            "Hyderabad",
            "General,Cardiology,Pediatrics,Emergency",
            18
        ),

        (
            "Government General Hospital",
            "Hyderabad",
            "General,Cardiology,Pediatrics,Emergency",
            15
        )
    ]

    for hospital in hospitals:

        db.execute(
            """
            INSERT OR IGNORE INTO hospitals
            (
                name,
                city,
                departments,
                doctors
            )

            VALUES (?, ?, ?, ?)
            """,
            hospital
        )

    db.commit()

    db.close()


# ==========================================================
# QUEUE STATISTICS
# ==========================================================

def get_queue_statistics():

    db = get_db()

    patients = db.execute(
        """
        SELECT *
        FROM patients

        ORDER BY

            CASE

                WHEN priority = 'Emergency'
                THEN 0

                WHEN priority = 'High'
                THEN 1

                ELSE 2

            END,

            id ASC
        """
    ).fetchall()

    db.close()

    total = len(patients)

    emergency = sum(
        1
        for p in patients
        if p["priority"].lower()
        == "emergency"
    )

    high = sum(
        1
        for p in patients
        if p["priority"].lower()
        == "high"
    )

    normal = total - emergency - high

    return {
        "patients": patients,
        "total": total,
        "emergency": emergency,
        "high": high,
        "normal": normal
    }


# ==========================================================
# QUEUE PRESSURE
# ==========================================================

def queue_pressure(
    patients,
    doctors
):

    doctors = max(
        doctors,
        1
    )

    value = (
        patients /
        doctors
    ) * 20

    return round(
        min(
            max(value, 0),
            100
        ),
        1
    )


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def index():

    stats = get_queue_statistics()

    doctors = 5

    pressure = queue_pressure(
        stats["total"],
        doctors
    )

    return render_template(
        "index.html",

        patients=stats["patients"],

        total_patients=stats["total"],

        emergency_patients=stats["emergency"],

        high_priority=stats["high"],

        normal_patients=stats["normal"],

        doctors_available=doctors,

        queue_pressure_percentage=pressure,

        current_hour=datetime.now().hour,

        prediction=None,

        explanation=None,

        recommendation=None,

        simulation=None
    )


# ==========================================================
# ADD PATIENT
# ==========================================================

@app.route(
    "/add_patient",
    methods=["POST"]
)
def add_patient():

    name = request.form.get(
        "name",
        ""
    ).strip()

    department = request.form.get(
        "department",
        "General"
    )

    appointment_type = request.form.get(
        "appointment_type",
        "Appointment"
    )

    priority = request.form.get(
        "priority",
        "Normal"
    )

    if not name:

        flash(
            "Patient name is required.",
            "error"
        )

        return redirect(
            url_for("index")
        )

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

    flash(
        "Patient added successfully.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ==========================================================
# REMOVE PATIENT
# ==========================================================

@app.route(
    "/remove_patient/<int:patient_id>",
    methods=["POST"]
)
def remove_patient(
    patient_id
):

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

    flash(
        "Patient completed successfully.",
        "success"
    )

    return redirect(
        url_for("index")
    )


# ==========================================================
# AI PREDICTION
# ==========================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    try:

        patients = int(
            request.form.get(
                "patients_waiting",
                10
            )
        )

        doctors = int(
            request.form.get(
                "doctors_available",
                5
            )
        )

        consultation = float(
            request.form.get(
                "average_consultation_time",
                15
            )
        )

        emergency = int(
            request.form.get(
                "emergency_patients",
                0
            )
        )

        hour = int(
            request.form.get(
                "hour",
                datetime.now().hour
            )
        )

        day = request.form.get(
            "day_of_week",
            "Monday"
        )

        department = request.form.get(
            "department",
            "General"
        )

        appointment = request.form.get(
            "appointment_type",
            "Appointment"
        )


        # --------------------------------------------------
        # AI PREDICTION
        # --------------------------------------------------

        prediction = predict_waiting_time(

            patients,

            doctors,

            consultation,

            emergency,

            hour,

            day,

            department,

            appointment

        )


        # --------------------------------------------------
        # EXPLANATION
        # --------------------------------------------------

        explanation = explain_prediction(

            patients,

            doctors,

            consultation,

            emergency,

            hour

        )


        # --------------------------------------------------
        # RECOMMENDATION
        # --------------------------------------------------

        recommendation = generate_recommendation(

            patients,

            doctors,

            emergency,

            prediction

        )


        # --------------------------------------------------
        # SAVE HISTORY
        # --------------------------------------------------

        db = get_db()

        db.execute(
            """
            INSERT INTO prediction_history

            (
                patients_waiting,
                doctors_available,
                emergency_patients,
                predicted_wait,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                patients,
                doctors,
                emergency,
                prediction,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        db.commit()

        db.close()


        stats = get_queue_statistics()

        pressure = queue_pressure(
            patients,
            doctors
        )


        return render_template(

            "index.html",

            patients=stats["patients"],

            total_patients=stats["total"],

            emergency_patients=emergency,

            high_priority=stats["high"],

            normal_patients=stats["normal"],

            doctors_available=doctors,

            queue_pressure_percentage=pressure,

            current_hour=hour,

            prediction=round(
                prediction,
                1
            ),

            explanation=explanation,

            recommendation=recommendation,

            simulation=None

        )


    except Exception as error:

        print(
            "Prediction error:",
            error
        )

        flash(
            "Prediction failed. Check your input values.",
            "error"
        )

        return redirect(
            url_for("index")
        )


# ==========================================================
# WHAT-IF SIMULATION
# ==========================================================

@app.route(
    "/simulate",
    methods=["POST"]
)
def simulate():

    try:

        patients = int(
            request.form.get(
                "patients_waiting",
                20
            )
        )

        doctors = int(
            request.form.get(
                "doctors_available",
                5
            )
        )

        emergency = int(
            request.form.get(
                "emergency_patients",
                2
            )
        )

        consultation = float(
            request.form.get(
                "average_consultation_time",
                15
            )
        )

        additional_doctors = int(
            request.form.get(
                "additional_doctors",
                1
            )
        )


        result = simulate_scenario(

            patients,

            doctors,

            emergency,

            consultation,

            additional_doctors

        )


        stats = get_queue_statistics()


        return render_template(

            "index.html",

            patients=stats["patients"],

            total_patients=stats["total"],

            emergency_patients=stats["emergency"],

            high_priority=stats["high"],

            normal_patients=stats["normal"],

            doctors_available=doctors,

            queue_pressure_percentage=
                queue_pressure(
                    patients,
                    doctors
                ),

            current_hour=datetime.now().hour,

            prediction=None,

            explanation=None,

            recommendation=None,

            simulation=result

        )


    except Exception as error:

        print(
            "Simulation error:",
            error
        )

        flash(
            "Simulation failed.",
            "error"
        )

        return redirect(
            url_for("index")
        )


# ==========================================================
# QUEUE API
# ==========================================================

@app.route("/api/queue")
def queue_api():

    stats = get_queue_statistics()

    doctors = 5

    pressure = queue_pressure(
        stats["total"],
        doctors
    )

    return jsonify(
        {
            "success": True,

            "total_patients":
                stats["total"],

            "emergency_patients":
                stats["emergency"],

            "high_priority":
                stats["high"],

            "normal_patients":
                stats["normal"],

            "doctors_available":
                doctors,

            "queue_pressure_percentage":
                pressure,

            "server_time":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        }
    )


# ==========================================================
# HOSPITAL SEARCH
# ==========================================================

@app.route(
    "/api/hospital/search"
)
def search_hospital():

    query = request.args.get(
        "q",
        ""
    ).strip()


    db = get_db()


    if query:

        hospitals = db.execute(
            """
            SELECT *
            FROM hospitals

            WHERE name LIKE ?
            OR city LIKE ?

            ORDER BY name

            LIMIT 10
            """,
            (
                f"%{query}%",
                f"%{query}%"
            )
        ).fetchall()

    else:

        hospitals = db.execute(
            """
            SELECT *
            FROM hospitals

            ORDER BY name

            LIMIT 10
            """
        ).fetchall()


    db.close()


    return jsonify(
        {
            "success": True,

            "hospitals": [

                {
                    "id": h["id"],
                    "name": h["name"],
                    "city": h["city"],
                    "departments":
                        h["departments"],
                    "doctors":
                        h["doctors"]
                }

                for h in hospitals

            ]
        }
    )


# ==========================================================
# ANALYTICS API
# ==========================================================

@app.route(
    "/api/analytics"
)
def analytics():

    db = get_db()

    history = db.execute(
        """
        SELECT *

        FROM prediction_history

        ORDER BY id DESC

        LIMIT 20
        """
    ).fetchall()

    db.close()


    waits = [
        row["predicted_wait"]
        for row in history
    ]


    average_wait = (
        sum(waits) /
        len(waits)
        if waits
        else 0
    )


    return jsonify(
        {
            "success": True,

            "predictions":
                len(history),

            "average_predicted_wait":
                round(
                    average_wait,
                    1
                ),

            "history": [

                {
                    "patients":
                        row["patients_waiting"],

                    "doctors":
                        row["doctors_available"],

                    "emergency":
                        row["emergency_patients"],

                    "wait":
                        row["predicted_wait"],

                    "time":
                        row["created_at"]
                }

                for row in history

            ]
        }
    )


# ==========================================================
# HEALTH CHECK
# ==========================================================

@app.route("/health")
def health():

    return jsonify(
        {
            "status": "healthy",

            "system":
                "MediPredict AI 4.0",

            "capabilities": [

                "AI prediction",

                "What-if simulation",

                "AI recommendations",

                "Explainable AI",

                "Queue analytics"

            ]
        }
    )


# ==========================================================
# ERROR HANDLERS
# ==========================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify(
        {
            "success": False,
            "error": "Page not found"
        }
    ), 404


@app.errorhandler(500)
def server_error(error):

    return jsonify(
        {
            "success": False,
            "error": "Internal server error"
        }
    ), 500


# ==========================================================
# INITIALIZE
# ==========================================================

initialize_database()


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )
    print(
        "       MEDIPREDICT AI 4.0"
    )
    print(
        " AI HOSPITAL FLOW OPTIMIZATION SYSTEM"
    )
    print(
        "=========================================="
    )
    print(
        "Server: http://127.0.0.1:5000"
    )
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )