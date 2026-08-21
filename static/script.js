// ==========================================================
// MEDIPREDICT AI
// FRONTEND JAVASCRIPT
// ==========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeApplication();

    }
);


// ==========================================================
// INITIALIZE
// ==========================================================

function initializeApplication() {

    setupPrediction();

    setupHospitalSearch();

    setupPatientForm();

    loadPatients();

    loadStats();

    setupDoctorDisplay();

}


// ==========================================================
// DOCTOR DISPLAY
// ==========================================================

function setupDoctorDisplay() {

    const doctors =
        document.querySelector(
            'input[name="doctors_available"]'
        );

    const display =
        document.getElementById(
            "doctorDisplay"
        );

    if (!doctors || !display) {
        return;
    }

    function updateDoctors() {

        const value =
            parseInt(
                doctors.value
            ) || 0;

        display.textContent =
            value +
            (
                value === 1
                    ? " doctor available"
                    : " doctors available"
            );
    }

    doctors.addEventListener(
        "input",
        updateDoctors
    );

    updateDoctors();
}


// ==========================================================
// PREDICTION
// ==========================================================

function setupPrediction() {

    const form =
        document.getElementById(
            "predictionForm"
        );

    if (!form) {
        return;
    }

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const button =
                document.getElementById(
                    "predictButton"
                );

            const originalText =
                button.innerHTML;

            button.disabled = true;

            button.innerHTML =
                "⏳ AI is analyzing...";


            try {

                const formData =
                    new FormData(form);

                const response =
                    await fetch(
                        "/api/predict",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const data =
                    await response.json();


                if (
                    response.status === 401
                ) {

                    window.location.href =
                        "/login";

                    return;
                }


                if (!data.success) {

                    showMessage(
                        data.message ||
                        "Prediction failed."
                    );

                    return;
                }


                displayPrediction(
                    data
                );


            }

            catch (error) {

                console.error(
                    "Prediction error:",
                    error
                );

                showMessage(
                    "Could not connect to the Flask server."
                );

            }

            finally {

                button.disabled = false;

                button.innerHTML =
                    originalText;
            }

        }
    );
}


// ==========================================================
// DISPLAY PREDICTION
// ==========================================================

function displayPrediction(
    data
) {

    const result =
        document.getElementById(
            "predictionResult"
        );

    const waiting =
        document.getElementById(
            "waitingTime"
        );

    const pressure =
        document.getElementById(
            "pressure"
        );

    const patients =
        document.getElementById(
            "resultPatients"
        );

    const doctors =
        document.getElementById(
            "resultDoctors"
        );

    const recommendation =
        document.getElementById(
            "recommendation"
        );


    waiting.textContent =
        Number(
            data.waiting_time
        ).toFixed(1);


    pressure.textContent =
        data.pressure;


    patients.textContent =
        data.patients_waiting;


    doctors.textContent =
        data.doctors_available;


    recommendation.textContent =
        data.recommendation;


    result.classList.remove(
        "hidden"
    );


    result.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}


// ==========================================================
// HOSPITAL SEARCH
// ==========================================================

function setupHospitalSearch() {

    const form =
        document.getElementById(
            "hospitalSearchForm"
        );

    if (!form) {
        return;
    }

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const input =
                document.getElementById(
                    "hospitalQuery"
                );

            const status =
                document.getElementById(
                    "hospitalStatus"
                );

            const results =
                document.getElementById(
                    "hospitalResults"
                );


            const query =
                input.value.trim();


            if (!query) {

                status.textContent =
                    "Please enter a location.";

                return;
            }


            status.textContent =
                "🔎 Searching hospitals...";


            results.innerHTML = "";


            try {

                const response =
                    await fetch(
                        "/api/hospitals?q=" +
                        encodeURIComponent(query)
                    );


                const data =
                    await response.json();


                if (
                    response.status === 401
                ) {

                    window.location.href =
                        "/login";

                    return;
                }


                if (!data.success) {

                    status.textContent =
                        data.message ||
                        "Hospital search failed.";

                    return;
                }


                displayHospitals(
                    data.hospitals
                );


                if (
                    data.hospitals.length === 0
                ) {

                    status.textContent =
                        "No hospitals found for this search.";

                }
                else {

                    status.textContent =
                        data.hospitals.length +
                        " hospital(s) found.";

                }

            }

            catch (error) {

                console.error(
                    "Hospital search error:",
                    error
                );

                status.textContent =
                    "Could not connect to hospital search service.";

            }

        }
    );
}


// ==========================================================
// DISPLAY HOSPITALS
// ==========================================================

function displayHospitals(
    hospitals
) {

    const container =
        document.getElementById(
            "hospitalResults"
        );


    container.innerHTML = "";


    hospitals.forEach(
        function (hospital) {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "hospital-card";


            const latitude =
                Number(
                    hospital.latitude
                );


            const longitude =
                Number(
                    hospital.longitude
                );


            const mapURL =
                "https://www.google.com/maps/search/?api=1&query=" +
                encodeURIComponent(
                    latitude +
                    "," +
                    longitude
                );


            card.innerHTML = `

                <h3>
                    🏥 ${escapeHTML(
                        hospital.name
                    )}
                </h3>

                <p>
                    ${escapeHTML(
                        hospital.address
                    )}
                </p>

                <a
                    href="${mapURL}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    📍 Open in Google Maps
                </a>

            `;


            container.appendChild(
                card
            );

        }
    );
}


// ==========================================================
// PATIENT FORM
// ==========================================================

function setupPatientForm() {

    const form =
        document.getElementById(
            "patientForm"
        );

    if (!form) {
        return;
    }


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            const patient = {

                name:
                    document.getElementById(
                        "patientName"
                    ).value.trim(),

                department:
                    document.getElementById(
                        "patientDepartment"
                    ).value,

                appointment_type:
                    document.getElementById(
                        "patientAppointment"
                    ).value,

                priority:
                    document.getElementById(
                        "patientPriority"
                    ).value

            };


            try {

                const response =
                    await fetch(
                        "/api/patients",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    patient
                                )
                        }
                    );


                const data =
                    await response.json();


                if (
                    response.status === 401
                ) {

                    window.location.href =
                        "/login";

                    return;
                }


                if (!data.success) {

                    showMessage(
                        data.message
                    );

                    return;
                }


                form.reset();


                loadPatients();

                loadStats();


                showMessage(
                    "Patient added successfully."
                );

            }

            catch (error) {

                console.error(
                    error
                );

                showMessage(
                    "Could not add patient."
                );

            }

        }
    );
}


// ==========================================================
// LOAD PATIENTS
// ==========================================================

async function loadPatients() {

    const container =
        document.getElementById(
            "patientList"
        );

    if (!container) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/patients"
            );


        const data =
            await response.json();


        if (!data.success) {
            return;
        }


        container.innerHTML = "";


        if (
            data.patients.length === 0
        ) {

            container.innerHTML = `
                <p style="
                    color:#7b8799;
                    text-align:center;
                    padding:20px;
                ">
                    No patients currently registered.
                </p>
            `;

            return;
        }


        data.patients.forEach(
            function (patient) {

                const item =
                    document.createElement(
                        "div"
                    );

                item.className =
                    "patient-item";


                item.innerHTML = `

                    <div class="patient-info">

                        <strong>
                            ${escapeHTML(
                                patient.name
                            )}
                        </strong>

                        <span>
                            ${escapeHTML(
                                patient.department
                            )}
                            •
                            ${escapeHTML(
                                patient.appointment_type
                            )}
                            •
                            ${escapeHTML(
                                patient.priority
                            )}
                        </span>

                    </div>


                    <button
                        class="delete-patient"
                        onclick="deletePatient(
                            ${patient.id}
                        )"
                    >
                        Remove
                    </button>

                `;


                container.appendChild(
                    item
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Patient loading error:",
            error
        );

    }
}


// ==========================================================
// DELETE PATIENT
// ==========================================================

async function deletePatient(
    patientId
) {

    if (
        !confirm(
            "Remove this patient from the queue?"
        )
    ) {

        return;
    }


    try {

        const response =
            await fetch(
                "/api/patients/" +
                patientId,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (!data.success) {

            showMessage(
                data.message
            );

            return;
        }


        loadPatients();

        loadStats();


    }

    catch (error) {

        console.error(
            error
        );

        showMessage(
            "Could not remove patient."
        );

    }
}


// ==========================================================
// LOAD STATISTICS
// ==========================================================

async function loadStats() {

    try {

        const response =
            await fetch(
                "/api/stats"
            );


        if (
            response.status === 401
        ) {
            return;
        }


        const data =
            await response.json();


        if (!data.success) {
            return;
        }


        const total =
            document.getElementById(
                "totalPatients"
            );

        const emergency =
            document.getElementById(
                "emergencyPatients"
            );


        if (total) {

            total.textContent =
                data.total_patients;
        }


        if (emergency) {

            emergency.textContent =
                data.emergency_patients;
        }

    }

    catch (error) {

        console.error(
            "Stats error:",
            error
        );

    }
}


// ==========================================================
// MESSAGE
// ==========================================================

function showMessage(
    message
) {

    alert(
        message
    );
}


// ==========================================================
// SECURITY
// ==========================================================

function escapeHTML(
    value
) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        value == null
            ? ""
            : String(value);

    return div.innerHTML;
}