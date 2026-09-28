(function () {
    "use strict";

    /* =========================================================
       CAPTAIN'S DESK
       ========================================================= */

    if (window.GTCaptainDeskLoaded) return;
    window.GTCaptainDeskLoaded = true;

    const state = {
        events: [],
        selected: null,
        busy: false
    };


    /* =========================================================
       HELPERS
       ========================================================= */

    function $(id) {
        return document.getElementById(id);
    }


    function esc(value) {
        return String(value ?? "").replace(/[&<>"]/g, function (c) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;"
            }[c];
        });
    }


    /* =========================================================
       API
       IMPORTANT:
       Uses the SAME login token as the main website.
       ========================================================= */

    async function api(url, options = {}) {

        let token = null;

        try {
            token = localStorage.getItem("gt_token");
        } catch (error) {
            console.error(
                "Could not read gt_token:",
                error
            );
        }


        const headers = {
            "Content-Type": "application/json"
        };


        if (token) {
            headers["Authorization"] =
                "Bearer " + token;
        }


        console.log(
            "Captain's Desk request:",
            url
        );

        console.log(
            "Organizer token exists:",
            !!token
        );


        const response = await fetch(
            url,
            {
                ...options,

                headers: {
                    ...headers,
                    ...(options.headers || {})
                }
            }
        );


        let data = {};

        try {
            data = await response.json();
        } catch (error) {
            console.error(
                "Could not parse API response:",
                error
            );
        }


        console.log(
            "API status:",
            response.status
        );

        console.log(
            "API response:",
            data
        );


        return {
            ok:
                response.ok &&
                data.success !== false,

            status:
                response.status,

            data:
                data
        };
    }


    /* =========================================================
       CAPTAIN'S DESK BUTTON
       ========================================================= */

    function createLaunchButton() {

        if ($("gt-captain-launch")) {
            return;
        }


        const button =
            document.createElement("button");


        button.id =
            "gt-captain-launch";


        button.type =
            "button";


        button.className =
            "btn";


        button.innerHTML =
            "⚓ Captain's Desk";


        const existingButton =
            $("accBtn") ||
            $("newBtn");


        if (
            existingButton &&
            existingButton.parentElement
        ) {

            existingButton.parentElement.insertBefore(
                button,
                existingButton
            );

        } else {

            button.style.position =
                "fixed";

            button.style.bottom =
                "25px";

            button.style.right =
                "25px";

            button.style.zIndex =
                "9999";

            document.body.appendChild(
                button
            );
        }


        button.addEventListener(
            "click",
            openDesk
        );
    }


    /* =========================================================
       CREATE DESK
       ========================================================= */

    function createDesk() {

        if ($("gt-captain-overlay")) {
            return;
        }


        const overlay =
            document.createElement("div");


        overlay.id =
            "gt-captain-overlay";


        overlay.className =
            "gt-captain-overlay";


        overlay.innerHTML = `

            <section class="gt-captain-panel">

                <header class="gt-captain-header">

                    <div>

                        <p class="eyebrow">
                            COMMAND CENTRE
                        </p>

                        <h2 class="goldtext">
                            Captain's Desk
                        </h2>

                        <p class="sub">
                            Manage your Gran Tesoro events.
                        </p>

                    </div>


                    <button
                        id="gt-captain-close"
                        class="gt-captain-close"
                        type="button"
                    >
                        ×
                    </button>

                </header>


                <div class="gt-captain-body">


                    <!-- =====================================
                         CREATE EVENT
                         ===================================== -->

                    <section class="gt-captain-card">

                        <div class="gt-captain-card-head">

                            <div>

                                <span class="gt-captain-kicker">
                                    NEW VOYAGE
                                </span>

                                <h3>
                                    Chart a New Event
                                </h3>

                            </div>

                            <span>
                                🗺️
                            </span>

                        </div>


                        <form
                            id="gt-create-event-form"
                            class="gt-create-form"
                        >

                            <div class="gt-form-grid">


                                <label>

                                    Event name

                                    <input
                                        id="gt-create-name"
                                        type="text"
                                        required
                                        placeholder="Grand Golden Gala"
                                    >

                                </label>


                                <label>

                                    Category

                                    <select
                                        id="gt-create-category"
                                    >

                                        <option>
                                            VIP Gala
                                        </option>

                                        <option>
                                            Council Session
                                        </option>

                                        <option>
                                            Banquet
                                        </option>

                                        <option>
                                            Private Event
                                        </option>

                                    </select>

                                </label>


                                <label>

                                    Venue

                                    <input
                                        id="gt-create-venue"
                                        type="text"
                                        required
                                        placeholder="Gran Tesoro — Gold Room"
                                    >

                                </label>


                                <label>

                                    Date & Time

                                    <input
                                        id="gt-create-date"
                                        type="datetime-local"
                                        required
                                    >

                                </label>


                                <label>

                                    Capacity

                                    <input
                                        id="gt-create-capacity"
                                        type="number"
                                        min="1"
                                        value="50"
                                        required
                                    >

                                </label>


                            </div>


                            <label>

                                Description

                                <textarea
                                    id="gt-create-description"
                                    rows="3"
                                    placeholder="Event description..."
                                ></textarea>

                            </label>


                            <button
                                class="btn"
                                type="submit"
                            >
                                ⚓ Chart Event
                            </button>


                        </form>

                    </section>



                    <!-- =====================================
                         EVENTS
                         ===================================== -->

                    <section class="gt-captain-card">

                        <div class="gt-captain-card-head">

                            <div>

                                <span class="gt-captain-kicker">
                                    EVENT MANIFEST
                                </span>

                                <h3>
                                    Previous & Current Voyages
                                </h3>

                            </div>


                            <button
                                id="gt-captain-refresh"
                                class="gt-captain-small-btn"
                                type="button"
                            >
                                ↻ Refresh
                            </button>

                        </div>


                        <div id="gt-captain-events">

                            <div class="gt-captain-loading">
                                Loading events...
                            </div>

                        </div>

                    </section>



                    <!-- =====================================
                         EVENT DETAILS
                         ===================================== -->

                    <section
                        id="gt-captain-detail"
                        class="gt-captain-card gt-captain-detail-card"
                        hidden
                    ></section>


                </div>

            </section>

        `;


        document.body.appendChild(
            overlay
        );


        /* CLOSE */

        $("gt-captain-close")
            .addEventListener(
                "click",
                closeDesk
            );


        overlay.addEventListener(
            "click",
            function (event) {

                if (
                    event.target === overlay
                ) {

                    closeDesk();

                }

            }
        );


        /* REFRESH */

        $("gt-captain-refresh")
            .addEventListener(
                "click",
                loadCaptainEvents
            );


        /* =============================================
           ⭐ CHART EVENT BUTTON
           ============================================= */

        $("gt-create-event-form")
            .addEventListener(
                "submit",
                createEventFromDesk
            );


        loadCaptainEvents();
    }


    /* =========================================================
       OPEN DESK
       ========================================================= */

    function openDesk() {

        createDesk();


        const overlay =
            $("gt-captain-overlay");


        overlay.classList.add(
            "open"
        );


        document.body.classList.add(
            "gt-captain-lock"
        );


        loadCaptainEvents();
    }


    /* =========================================================
       CLOSE DESK
       ========================================================= */

    function closeDesk() {

        const overlay =
            $("gt-captain-overlay");


        if (overlay) {

            overlay.classList.remove(
                "open"
            );

        }


        document.body.classList.remove(
            "gt-captain-lock"
        );
    }


    /* =========================================================
       ⭐ CREATE EVENT
       ========================================================= */

    async function createEventFromDesk(event) {

        event.preventDefault();


        if (state.busy) {
            return;
        }


        const name =
            $("gt-create-name")
                .value
                .trim();


        const category =
            $("gt-create-category")
                .value;


        const venue =
            $("gt-create-venue")
                .value
                .trim();


        const date =
            $("gt-create-date")
                .value;


        const capacity =
            Number(
                $("gt-create-capacity")
                    .value
            );


        const description =
            $("gt-create-description")
                .value
                .trim();


        /* VALIDATION */

        if (
            !name ||
            !venue ||
            !date ||
            capacity < 1
        ) {

            alert(
                "Please fill Event Name, Venue, Date and Capacity."
            );

            return;
        }


        /* CHECK LOGIN */

        let token = null;

        try {
            token =
                localStorage.getItem(
                    "gt_token"
                );
        } catch (_) {}


        if (!token) {

            alert(
                "Please sign in as an organizer first."
            );

            return;
        }


        state.busy = true;


        try {

            console.log(
                "Creating event..."
            );


            const result =
                await api(
                    "/api/events",
                    {

                        method: "POST",

                        body:
                            JSON.stringify({

                                name:
                                    name,

                                description:
                                    description,

                                venue:
                                    venue,

                                capacity:
                                    capacity,

                                event_date:
                                    date,

                                category:
                                    category,

                                /*
                                 * Backend expects organizer.
                                 */
                                organizer:
                                    "Gild Tesoro's Golden Entertainment Division"

                            })

                    }
                );


            console.log(
                "Create event result:",
                result
            );


            if (!result.ok) {

                throw new Error(
                    result.data.error ||
                    result.data.message ||
                    "Event creation failed."
                );

            }


            /* SUCCESS */

            alert(
                "⚓ Event created successfully!"
            );


            /* RESET FORM */

            $("gt-create-event-form")
                .reset();


            $("gt-create-capacity")
                .value = 50;


            /* REFRESH CAPTAIN EVENTS */

            await loadCaptainEvents();


            /* REFRESH MAIN EVENT LIST */

            if (
                typeof loadEvents ===
                "function"
            ) {

                await loadEvents();

            }


        } catch (error) {

            console.error(
                "Create Event Error:",
                error
            );


            alert(
                "❌ Could not create event:\n\n" +
                error.message
            );


        } finally {

            state.busy = false;

        }

    }


    /* =========================================================
       LOAD EVENTS
       ========================================================= */

    async function loadCaptainEvents() {

        const box =
            $("gt-captain-events");


        if (!box) {
            return;
        }


        box.innerHTML = `

            <div class="gt-captain-loading">
                Loading events...
            </div>

        `;


        try {

            const result =
                await api(
                    "/api/events"
                );


            if (!result.ok) {

                throw new Error(
                    result.data.error ||
                    "Could not load events."
                );

            }


            const events =
                result.data.events ||
                result.data.data ||
                [];


            state.events =
                Array.isArray(events)
                    ? events
                    : [];


            renderCaptainEvents();


        } catch (error) {

            console.error(
                "Load events error:",
                error
            );


            box.innerHTML = `

                <div class="gt-captain-empty">

                    ❌ ${esc(
                        error.message
                    )}

                </div>

            `;
        }

    }


    /* =========================================================
       RENDER EVENTS
       ========================================================= */

    function renderCaptainEvents() {

        const box =
            $("gt-captain-events");


        if (!box) {
            return;
        }


        if (!state.events.length) {

            box.innerHTML = `

                <div class="gt-captain-empty">

                    <strong>
                        No events found.
                    </strong>

                    <span>
                        Create your first event above.
                    </span>

                </div>

            `;

            return;
        }


        box.innerHTML =
            state.events
                .map(function (event) {

                    const capacity =
                        Number(
                            event.capacity || 0
                        );


                    const confirmed =
                        Number(
                            event.confirmed ||
                            event.confirmed_count ||
                            0
                        );


                    const waiting =
                        Number(
                            event.waitlist_count ||
                            event.waiting ||
                            0
                        );


                    const free =
                        Math.max(
                            0,
                            capacity -
                            confirmed
                        );


                    return `

                        <article
                            class="gt-captain-event"
                        >

                            <div
                                class="gt-event-main"
                            >

                                <span>
                                    ${esc(
                                        event.status ||
                                        "OPEN"
                                    )}
                                </span>


                                <h4>
                                    ${esc(
                                        event.name ||
                                        "Unnamed Event"
                                    )}
                                </h4>


                                <p>
                                    ${esc(
                                        event.venue ||
                                        "No venue"
                                    )}
                                </p>


                                <p>
                                    ${esc(
                                        event.event_date ||
                                        event.date ||
                                        "No date"
                                    )}
                                </p>

                            </div>


                            <div
                                class="gt-event-stats"
                            >

                                <div>

                                    <strong>
                                        ${confirmed}
                                    </strong>

                                    <span>
                                        Guests
                                    </span>

                                </div>


                                <div>

                                    <strong>
                                        ${free}
                                    </strong>

                                    <span>
                                        Free
                                    </span>

                                </div>


                                <div>

                                    <strong>
                                        ${waiting}
                                    </strong>

                                    <span>
                                        Waiting
                                    </span>

                                </div>


                                <div>

                                    <strong>
                                        ${capacity}
                                    </strong>

                                    <span>
                                        Capacity
                                    </span>

                                </div>

                            </div>


                            <button
                                type="button"
                                class="gt-view-event"
                                data-event-id="${esc(
                                    event.id
                                )}"
                            >
                                Open Manifest →
                            </button>


                        </article>

                    `;

                })
                .join("");


        box
            .querySelectorAll(
                "[data-event-id]"
            )
            .forEach(
                function (button) {

                    button.addEventListener(
                        "click",
                        function () {

                            openCaptainEvent(
                                button.dataset.eventId
                            );

                        }
                    );

                }
            );
    }


    /* =========================================================
       OPEN EVENT MANIFEST
       ========================================================= */

    async function openCaptainEvent(id) {

        const box =
            $("gt-captain-detail");


        if (!box) {
            return;
        }


        box.hidden = false;


        box.innerHTML = `

            <div class="gt-captain-loading">
                Loading manifest...
            </div>

        `;


        try {

            /*
             * Get summary.
             */

            const summary =
                await api(
                    "/api/events/" +
                    encodeURIComponent(id) +
                    "/summary"
                );


            if (!summary.ok) {

                throw new Error(
                    summary.data.error ||
                    "Could not open event."
                );

            }


            /*
             * Also get registrations.
             * This gives us actual people.
             */

            const registrations =
                await api(
                    "/api/events/" +
                    encodeURIComponent(id) +
                    "/registrations"
                );


            /*
             * Get waiting list separately.
             */

            const waitlist =
                await api(
                    "/api/events/" +
                    encodeURIComponent(id) +
                    "/waitlist"
                );


            const combined = {

                summary:
                    summary.data,

                registrations:
                    registrations.ok
                        ? (
                            registrations.data.registrations ||
                            []
                        )
                        : [],

                waitlist:
                    waitlist.ok
                        ? (
                            waitlist.data.waitlist ||
                            waitlist.data.entries ||
                            []
                        )
                        : []

            };


            renderCaptainDetail(
                id,
                combined
            );


        } catch (error) {

            console.error(
                "Manifest error:",
                error
            );


            box.innerHTML = `

                <div class="gt-captain-empty">

                    ❌ ${esc(
                        error.message
                    )}

                </div>

            `;
        }

    }


    /* =========================================================
       RENDER EVENT DETAILS
       ========================================================= */

    function renderCaptainDetail(
        eventId,
        data
    ) {

        const box =
            $("gt-captain-detail");


        const summary =
            data.summary || {};


        const event =
            summary.event ||
            state.events.find(
                function (e) {

                    return String(e.id) ===
                        String(eventId);

                }
            ) ||
            {};


        /*
         * Actual registrations.
         */

        const registrations =
            data.registrations || [];


        /*
         * Waiting list.
         */

        const waitlist =
            data.waitlist || [];


        const capacity =
            Number(
                event.capacity || 0
            );


        box.innerHTML = `

            <div class="gt-detail-header">

                <div>

                    <span
                        class="gt-captain-kicker"
                    >
                        CAPTAIN'S MANIFEST
                    </span>


                    <h3>
                        ${esc(
                            event.name ||
                            "Event"
                        )}
                    </h3>

                </div>


                <button
                    type="button"
                    class="gt-captain-small-btn"
                    id="gt-close-manifest"
                >
                    Close
                </button>

            </div>



            <!-- CAPACITY -->

            <div class="gt-capacity-panel">

                <div>

                    <span
                        class="gt-captain-kicker"
                    >
                        CAPACITY
                    </span>


                    <strong>

                        ${registrations.length}

                        /

                        ${capacity}

                    </strong>

                </div>


                <div>

                    <input
                        id="gt-capacity-input"
                        type="number"
                        min="1"
                        value="${capacity}"
                    >


                    <button
                        id="gt-capacity-save"
                        class="btn sm"
                        type="button"
                    >
                        Update Capacity
                    </button>

                </div>

            </div>



            <!-- CONFIRMED GUESTS -->

            <div class="gt-manifest-section">

                <div
                    class="gt-section-heading"
                >

                    <h4>
                        Confirmed Guests
                        (${registrations.length})
                    </h4>

                </div>


                ${
                    registrations.length

                    ?

                    registrations
                        .map(
                            function (item) {

                                const person =
                                    item.participant ||
                                    item;


                                const registration =
                                    item.registration ||
                                    {};


                                return `

                                    <div
                                        class="guest"
                                    >

                                        <div
                                            class="g-av"
                                        >

                                            ${esc(
                                                (
                                                    person.name ||
                                                    "?"
                                                )[0]
                                            )}

                                        </div>


                                        <div
                                            class="g-main"
                                        >

                                            <div
                                                class="g-name"
                                            >
                                                ${esc(
                                                    person.name ||
                                                    "Unknown Guest"
                                                )}
                                            </div>


                                            <div
                                                class="g-sub"
                                            >
                                                ${esc(
                                                    person.email ||
                                                    ""
                                                )}
                                            </div>


                                            ${
                                                registration.status
                                                ?

                                                `
                                                <small>
                                                    ${esc(
                                                        registration.status
                                                    )}
                                                </small>
                                                `

                                                :

                                                ""
                                            }

                                        </div>

                                    </div>

                                `;

                            }
                        )
                        .join("")

                    :

                    `

                    <div
                        class="gt-captain-empty"
                    >
                        No confirmed guests.
                    </div>

                    `
                }

            </div>



            <!-- WAITING LIST -->

            <div class="gt-manifest-section">

                <div
                    class="gt-section-heading"
                >

                    <h4>
                        Waiting List
                        (${waitlist.length})
                    </h4>

                </div>


                ${
                    waitlist.length

                    ?

                    waitlist
                        .map(
                            function (
                                item,
                                index
                            ) {

                                const person =
                                    item.participant ||
                                    item;


                                return `

                                    <div
                                        class="pose"
                                    >

                                        <strong>
                                            #${index + 1}
                                        </strong>


                                        <div>

                                            ${esc(
                                                person.name ||
                                                "Unknown Guest"
                                            )}


                                            <small>

                                                ${esc(
                                                    person.email ||
                                                    ""
                                                )}

                                            </small>

                                        </div>

                                    </div>

                                `;

                            }
                        )
                        .join("")

                    :

                    `

                    <div
                        class="gt-captain-empty"
                    >
                        Waiting list is empty.
                    </div>

                    `
                }

            </div>

        `;


        /* CLOSE */

        $("gt-close-manifest")
            .addEventListener(
                "click",
                function () {

                    box.hidden = true;

                }
            );


        /* CAPACITY */

        $("gt-capacity-save")
            .addEventListener(
                "click",
                function () {

                    updateCapacity(
                        eventId,
                        $("gt-capacity-input")
                            .value
                    );

                }
            );

    }


    /* =========================================================
       UPDATE CAPACITY
       ========================================================= */

    async function updateCapacity(
        eventId,
        value
    ) {

        const capacity =
            Number(value);


        if (capacity < 1) {

            alert(
                "Capacity must be at least 1."
            );

            return;
        }


        try {

            const result =
                await api(
                    "/api/events/" +
                    encodeURIComponent(
                        eventId
                    ) +
                    "/capacity",
                    {

                        method: "PUT",

                        body:
                            JSON.stringify({
                                capacity:
                                    capacity
                            })

                    }
                );


            if (!result.ok) {

                throw new Error(
                    result.data.error ||
                    "Capacity update failed."
                );

            }


            alert(
                "Capacity updated successfully."
            );


            await loadCaptainEvents();


            await openCaptainEvent(
                eventId
            );


        } catch (error) {

            console.error(
                "Capacity error:",
                error
            );


            alert(
                "❌ " +
                error.message
            );

        }

    }


    /* =========================================================
       START
       ========================================================= */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            createLaunchButton
        );

    } else {

        createLaunchButton();

    }

})();