# ==========================================================
# MEDIPREDICT AI
# MODEL TRAINING
# ==========================================================

import os

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    r2_score
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "dataset",
    "hospital_data.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "hospital_waiting_model.pkl"
)


# ==========================================================
# FEATURES
# ==========================================================

FEATURES = [

    "patients_waiting",

    "doctors_available",

    "average_consultation_time",

    "emergency_patients",

    "hour",

    "day_of_week",

    "department",

    "appointment_type"
]

TARGET = "waiting_time"


# ==========================================================
# LOAD DATASET
# ==========================================================

if not os.path.exists(DATA_PATH):

    raise FileNotFoundError(
        f"Dataset not found: {DATA_PATH}"
    )

data = pd.read_csv(
    DATA_PATH
)

print(
    "\nDataset loaded:"
)

print(
    data.shape
)


# ==========================================================
# CHECK COLUMNS
# ==========================================================

required_columns = FEATURES + [TARGET]

missing_columns = [

    column

    for column in required_columns

    if column not in data.columns
]

if missing_columns:

    raise ValueError(
        "Missing columns: "
        +
        ", ".join(missing_columns)
    )


# ==========================================================
# CLEAN DATA
# ==========================================================

data = data.dropna(
    subset=required_columns
)

# Numeric columns

numeric_columns = [

    "patients_waiting",

    "doctors_available",

    "average_consultation_time",

    "emergency_patients",

    "hour"
]

for column in numeric_columns:

    data[column] = pd.to_numeric(
        data[column],
        errors="coerce"
    )

data[TARGET] = pd.to_numeric(
    data[TARGET],
    errors="coerce"
)

data = data.dropna(
    subset=required_columns
)


# ==========================================================
# INPUT / OUTPUT
# ==========================================================

X = data[FEATURES]

y = data[TARGET]


# ==========================================================
# CATEGORICAL FEATURES
# ==========================================================

categorical_features = [

    "day_of_week",

    "department",

    "appointment_type"
]


# ==========================================================
# PREPROCESSOR
# ==========================================================

preprocessor = ColumnTransformer(

    transformers=[

        (
            "categorical",

            OneHotEncoder(
                handle_unknown="ignore"
            ),

            categorical_features
        )

    ],

    remainder="passthrough"
)


# ==========================================================
# RANDOM FOREST
# ==========================================================

model = RandomForestRegressor(

    n_estimators=300,

    max_depth=18,

    min_samples_split=2,

    min_samples_leaf=1,

    random_state=42,

    n_jobs=-1
)


# ==========================================================
# PIPELINE
# ==========================================================

pipeline = Pipeline(

    steps=[

        (
            "preprocessor",
            preprocessor
        ),

        (
            "model",
            model
        )
    ]
)


# ==========================================================
# TRAIN / TEST
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.2,

    random_state=42
)


print(
    "\nTraining AI model..."
)


pipeline.fit(
    X_train,
    y_train
)


# ==========================================================
# EVALUATION
# ==========================================================

predictions = pipeline.predict(
    X_test
)

mae = mean_absolute_error(
    y_test,
    predictions
)

r2 = r2_score(
    y_test,
    predictions
)


print(
    "\nMODEL PERFORMANCE"
)

print(
    "MAE:",
    round(mae, 2)
)

print(
    "R2:",
    round(r2, 4)
)


# ==========================================================
# SAVE MODEL
# ==========================================================

os.makedirs(
    MODEL_DIR,
    exist_ok=True
)

joblib.dump(
    pipeline,
    MODEL_PATH
)


print(
    "\nModel saved successfully:"
)

print(
    MODEL_PATH
)

print(
    "\nTraining completed."
)