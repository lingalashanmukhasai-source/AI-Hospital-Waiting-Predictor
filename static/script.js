// ==========================================================
// MEDIPREDICT AI 4.0
// FRONTEND ENGINE
// ==========================================================


// ==========================================================
// START
// ==========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        updatePressure();

        updateClock();

        setInterval(
            updateClock,
            1000
        );

        setInterval(
            refreshQueue,
            15000
        );

    }
);


// ==========================================================
// PRESSURE
// ==========================================================

function updatePressure() {

    const bar =
        document.getElementById(
            "pressureFill"
        );


    const text =
        document.getElementById(
            "queuePressureText"
        );


    const status =
        document.getElementById(
            "pressureStatus"
        );


    if (!bar) {
        return;
    }


    let pressure =
        parseFloat(
            bar.dataset.pressure
        );


    if (isNaN(pressure)) {

        pressure = 0;

    }


    pressure =
        Math.max(
            0,
            Math.min(
                100,
                pressure
            )
        );


    bar.style.width =
        pressure + "%";


    if (text) {

        text.textContent =
            pressure.toFixed(1) + "%";

    }


    if (status) {

        if (pressure >= 75) {

            status.textContent =
                "🔴 Critical";

        }
        else if (pressure >= 50) {

            status.textContent =
                "🟠 High";

        }
        else if (pressure >= 25) {

            status.textContent =
                "🟡 Moderate";

        }
        else {

            status.textContent =
                "🟢 Low";

        }

    }

}


// ==========================================================
// CLOCK
// ==========================================================

function updateClock() {

    const clock =
        document.getElementById(
            "liveClock"
        );


    if (!clock) {
        return;
    }


    clock.textContent =
        new Date().toLocaleString();

}


// ==========================================================
// LIVE QUEUE
// ==========================================================

async function refreshQueue() {

    try {

        const response =
            await fetch(
                "/api/queue",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Queue API error"
            );

        }


        const data =
            await response.json();


        if (!data.success) {
            return;
        }


        setText(
            "totalPatients",
            data.total_patients
        );


        setText(
            "emergencyPatients",
            data.emergency_patients
        );


        setText(
            "doctorsAvailable",
            data.doctors_available
        );


        const bar =
            document.getElementById(
                "pressureFill"
            );


        if (bar) {

            bar.dataset.pressure =
                data.queue_pressure_percentage;

        }


        updatePressure();

    }
    catch (error) {

        console.error(
            "Queue error:",
            error
        );

    }

}


// ==========================================================
// SET TEXT
// ==========================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (element) {

        element.textContent =
            value;

    }

}


// ==========================================================
// HOSPITAL SEARCH
// ==========================================================

async function searchHospitals() {

    const input =
        document.getElementById(
            "hospitalSearch"
        );


    const results =
        document.getElementById(
            "hospitalResults"
        );


    if (!input || !results) {
        return;
    }


    const query =
        input.value.trim();


    results.innerHTML =
        "<div>🔎 Searching...</div>";


    try {

        const response =
            await fetch(
                "/api/hospital/search?q=" +
                encodeURIComponent(query)
            );


        const data =
            await response.json();


        results.innerHTML = "";


        if (
            !data.hospitals ||
            data.hospitals.length === 0
        ) {

            results.innerHTML =
                "<div>No hospitals found.</div>";

            return;

        }


        data.hospitals.forEach(
            function (hospital) {

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "hospital-result";


                card.innerHTML = `

                    <strong>
                        🏥 ${escapeHTML(
                            hospital.name
                        )}
                    </strong>

                    <span>

                        📍 ${escapeHTML(
                            hospital.city || ""
                        )}

                        <br>

                        👨‍⚕️ Doctors:
                        ${hospital.doctors || 0}

                        <br>

                        🏥
                        ${escapeHTML(
                            hospital.departments || ""
                        )}

                    </span>

                `;


                results.appendChild(
                    card
                );

            }
        );

    }
    catch (error) {

        console.error(
            "Hospital search error:",
            error
        );


        results.innerHTML =
            "<div>Unable to search hospitals.</div>";

    }

}


// ==========================================================
// SECURITY
// ==========================================================

function escapeHTML(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}