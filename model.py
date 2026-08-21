# ==========================================================
# MEDIPREDICT AI 4.0
# AI PREDICTION + EXPLAINABILITY + SIMULATION
# ==========================================================

import os

import joblib
import pandas as pd


# ==========================================================
# MODEL PATH
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "hospital_waiting_model.pkl"
)


model = None


# ==========================================================
# LOAD MODEL
# ==========================================================

def load_model():

    global model

    if model is not None:
        return model


    if not os.path.exists(
        MODEL_PATH
    ):

        print(
            "WARNING: ML model not found."
        )

        return None


    try:

        model = joblib.load(
            MODEL_PATH
        )

        print(
            "AI model loaded successfully."
        )

        return model


    except Exception as error:

        print(
            "Model loading error:",
            error
        )

        return None


# ==========================================================
# FALLBACK MODEL
# ==========================================================

def fallback_prediction(

    patients_waiting,

    doctors_available,

    consultation_time,

    emergency_patients

):

    doctors_available = max(
        doctors_available,
        1
    )


    normal_load = (

        patients_waiting /
        doctors_available

    ) * consultation_time


    emergency_penalty = (

        emergency_patients *
        5

    )


    result = (

        normal_load +
        emergency_penalty

    )


    return max(
        1,
        result
    )


# ==========================================================
# MAIN PREDICTION
# ==========================================================

def predict_waiting_time(

    patients_waiting,

    doctors_available,

    average_consultation_time,

    emergency_patients,

    hour,

    day_of_week,

    department,

    appointment_type

):

    predictor = load_model()


    if predictor is None:

        return fallback_prediction(

            patients_waiting,

            doctors_available,

            average_consultation_time,

            emergency_patients

        )


    data = pd.DataFrame(

        [
            {

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

            }
        ]

    )


    try:

        prediction = predictor.predict(
            data
        )


        return max(
            0,
            float(
                prediction[0]
            )
        )


    except Exception as error:

        print(
            "ML prediction error:",
            error
        )


        return fallback_prediction(

            patients_waiting,

            doctors_available,

            average_consultation_time,

            emergency_patients

        )


# ==========================================================
# EXPLAINABLE AI
# ==========================================================

def explain_prediction(

    patients,

    doctors,

    consultation,

    emergency,

    hour

):

    factors = []


    ratio = (
        patients /
        max(doctors, 1)
    )


    # ------------------------------------------------------
    # PATIENT/DOCTOR RATIO
    # ------------------------------------------------------

    if ratio >= 8:

        factors.append(
            {
                "name":
                    "High patient-to-doctor ratio",

                "value":
                    f"{ratio:.1f} patients/doctor",

                "impact":
                    "High"
            }
        )

    elif ratio >= 4:

        factors.append(
            {
                "name":
                    "Moderate patient load",

                "value":
                    f"{ratio:.1f} patients/doctor",

                "impact":
                    "Medium"
            }
        )

    else:

        factors.append(
            {
                "name":
                    "Low patient load",

                "value":
                    f"{ratio:.1f} patients/doctor",

                "impact":
                    "Low"
            }
        )


    # ------------------------------------------------------
    # EMERGENCY
    # ------------------------------------------------------

    if emergency >= 5:

        factors.append(
            {
                "name":
                    "Emergency case pressure",

                "value":
                    f"{emergency} emergency patients",

                "impact":
                    "High"
            }
        )

    elif emergency > 0:

        factors.append(
            {
                "name":
                    "Emergency cases present",

                "value":
                    f"{emergency} cases",

                "impact":
                    "Medium"
            }
        )


    # ------------------------------------------------------
    # CONSULTATION
    # ------------------------------------------------------

    if consultation >= 20:

        factors.append(
            {
                "name":
                    "Long consultation time",

                "value":
                    f"{consultation:.0f} min",

                "impact":
                    "High"
            }
        )

    else:

        factors.append(
            {
                "name":
                    "Consultation duration",

                "value":
                    f"{consultation:.0f} min",

                "impact":
                    "Normal"
            }
        )


    # ------------------------------------------------------
    # HOUR
    # ------------------------------------------------------

    if 10 <= hour <= 14:

        factors.append(
            {
                "name":
                    "Peak hospital period",

                "value":
                    f"{hour}:00",

                "impact":
                    "High"
            }
        )

    else:

        factors.append(
            {
                "name":
                    "Non-peak period",

                "value":
                    f"{hour}:00",

                "impact":
                    "Low"
            }
        )


    return factors


# ==========================================================
# AI RECOMMENDATION ENGINE
# ==========================================================

def generate_recommendation(

    patients,

    doctors,

    emergency,

    predicted_wait

):

    recommendations = []


    ratio = (
        patients /
        max(doctors, 1)
    )


    # ------------------------------------------------------
    # CRITICAL
    # ------------------------------------------------------

    if predicted_wait >= 60:

        recommendations.append(
            "Activate additional doctors."
        )

        recommendations.append(
            "Open an additional consultation room."
        )

        recommendations.append(
            "Prioritize emergency and high-risk cases."
        )


    elif predicted_wait >= 30:

        recommendations.append(
            "Consider assigning one additional doctor."
        )

        recommendations.append(
            "Monitor queue growth continuously."
        )


    else:

        recommendations.append(
            "Current staffing appears adequate."
        )


    # ------------------------------------------------------
    # EMERGENCY
    # ------------------------------------------------------

    if emergency >= 5:

        recommendations.append(
            "Create a dedicated emergency consultation stream."
        )


    # ------------------------------------------------------
    # PATIENT/DOCTOR RATIO
    # ------------------------------------------------------

    if ratio >= 8:

        recommendations.append(
            "Patient-to-doctor ratio is critically high."
        )


    return recommendations


# ==========================================================
# WHAT-IF SIMULATION
# ==========================================================

def simulate_scenario(

    patients,

    doctors,

    emergency,

    consultation,

    additional_doctors

):

    current_wait = fallback_prediction(

        patients,

        doctors,

        consultation,

        emergency

    )


    new_doctors = (

        doctors +
        additional_doctors

    )


    future_wait = fallback_prediction(

        patients,

        new_doctors,

        consultation,

        emergency

    )


    reduction = (

        current_wait -
        future_wait

    )


    improvement = (

        reduction /
        max(current_wait, 1)

    ) * 100


    return {

        "current_wait":
            round(
                current_wait,
                1
            ),

        "new_wait":
            round(
                future_wait,
                1
            ),

        "current_doctors":
            doctors,

        "new_doctors":
            new_doctors,

        "reduction":
            round(
                reduction,
                1
            ),

        "improvement":
            round(
                improvement,
                1
            ),

        "recommendation":

            (
                "Adding "
                + str(additional_doctors)
                + " doctor(s) could reduce "
                + f"waiting time by {reduction:.1f} minutes."
            )

    }