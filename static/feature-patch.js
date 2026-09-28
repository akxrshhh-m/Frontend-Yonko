/*
 * GRAN TESORO — FRONTEND FEATURE PATCH
 * -------------------------------------
 * Adds: Guest Status / Log Pose lookup
 *
 * This patch does NOT replace index.html.
 * It uses the existing frontend API helpers/state:
 *   S, API, call(), esc(), loadEvents()
 *
 * No new backend route is required.
 */

(function () {
  "use strict";

  // Prevent accidental double-loading.
  if (window.GTFeaturePatchLoaded) return;
  window.GTFeaturePatchLoaded = true;

  const patchState = {
    modal: null,
    busy: false
  };

  function q(selector, root = document) {
    return root.querySelector(selector);
  }

  function createLookupUI() {
    // Don't create it twice.
    if (q("#gt-status-btn")) return;

    /*
     * Add the button beside the existing voyage filter.
     *
     * If your current frontend doesn't have #filter,
     * the floating fallback button below will be used.
     */
    const filter = q("#filter");

    if (filter && filter.parentElement) {
      const button = document.createElement("button");

      button.id = "gt-status-btn";
      button.className = "btn sm ghost gt-patch-status-btn";
      button.type = "button";
      button.innerHTML = "🧭 Check Guest Status";

      filter.parentElement.appendChild(button);

      button.addEventListener("click", openLookup);
    } else {
      // Safe fallback if #filter doesn't exist.
      const button = document.createElement("button");

      button.id = "gt-status-btn";
      button.className = "gt-patch-status-btn gt-patch-floating-button";
      button.type = "button";
      button.innerHTML = "🧭 Check Guest Status";

      document.body.appendChild(button);

      button.addEventListener("click", openLookup);
    }

    /*
     * Modal is created dynamically.
     * Therefore we don't have to modify your existing HTML.
     */
    const modal = document.createElement("div");

    modal.id = "gt-status-modal";
    modal.className = "gt-patch-modal";

    modal.innerHTML = `
      <div
        class="gt-patch-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gt-status-title"
      >

        <button
          type="button"
          class="gt-patch-close"
          id="gt-status-close"
          aria-label="Close"
        >
          ×
        </button>

        <p class="eyebrow">Log Pose</p>

        <h2 id="gt-status-title" class="goldtext">
          Check Guest Status
        </h2>

        <p class="sub">
          Enter the email used for the invitation.
          The current event manifest will be checked for
          confirmed seats, waiting-list positions and active
          Golden Tickets.
        </p>

        <form id="gt-status-form" class="gt-patch-form">

          <label for="gt-status-email">
            Den Den Mushi address
          </label>

          <div class="gt-patch-input-row">

            <input
              id="gt-status-email"
              class="field"
              type="email"
              required
              autocomplete="email"
              placeholder="guest@example.com"
            >

            <button
              class="btn"
              type="submit"
            >
              Search
            </button>

          </div>

        </form>

        <div
          id="gt-status-results"
          class="gt-patch-results"
          aria-live="polite"
        ></div>

      </div>
    `;

    document.body.appendChild(modal);

    patchState.modal = modal;

    /*
     * Close button.
     */
    q("#gt-status-close").addEventListener(
      "click",
      closeLookup
    );

    /*
     * Clicking the dark background closes the modal.
     */
    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        closeLookup();
      }
    });

    /*
     * Search form.
     */
    q("#gt-status-form").addEventListener(
      "submit",
      async function (event) {

        event.preventDefault();

        const input = q("#gt-status-email");

        const email = input.value
          .trim()
          .toLowerCase();

        if (!email) return;

        await lookupGuest(email);
      }
    );

    /*
     * ESC closes modal.
     */
    document.addEventListener(
      "keydown",
      function (event) {

        if (
          event.key === "Escape" &&
          patchState.modal?.classList.contains("open")
        ) {
          closeLookup();
        }

      }
    );
  }


  /*
   * Open lookup modal.
   */
  function openLookup() {

    if (!patchState.modal) {
      createLookupUI();
    }

    patchState.modal.classList.add("open");

    document.body.classList.add(
      "gt-patch-lock"
    );

    const input =
      q("#gt-status-email");

    const results =
      q("#gt-status-results");

    results.innerHTML = `
      <div class="gt-patch-empty">

        Enter the email address used
        during registration.

      </div>
    `;

    setTimeout(function () {

      if (input) {
        input.focus();
      }

    }, 50);
  }


  /*
   * Close lookup modal.
   */
  function closeLookup() {

    if (patchState.modal) {

      patchState.modal.classList.remove(
        "open"
      );

    }

    document.body.classList.remove(
      "gt-patch-lock"
    );
  }


  /*
   * Loading state.
   */
  function renderLoading() {

    const results =
      q("#gt-status-results");

    if (!results) return;

    results.innerHTML = `
      <div class="gt-patch-loading">

        <span class="gt-patch-spinner"></span>

        Consulting the Log Pose…

      </div>
    `;
  }


  /*
   * Nothing found.
   */
  function renderEmpty(email) {

    const results =
      q("#gt-status-results");

    if (!results) return;

    results.innerHTML = `
      <div class="gt-patch-empty">

        <strong>
          No active record found.
        </strong>

        <span>
          No confirmed seat, waiting-list entry,
          or pending Golden Ticket was found for
          <b>${esc(email)}</b>.
        </span>

      </div>
    `;
  }


  /*
   * Render one status card.
   */
  function statusCard(item) {

    const event =
      item.event || {};

    const eventName =
      esc(event.name || "Unnamed voyage");

    const venue =
      esc(
        event.venue ||
        "Venue unavailable"
      );

    const date =
      esc(
        event.date ||
        event.event_date ||
        "Date unavailable"
      );


    /*
     * CONFIRMED
     */
    if (item.type === "confirmed") {

      const guest =
        item.guest || {};

      const seat =
        esc(
          guest.seat ??
          guest.seat_number ??
          guest.registration_number ??
          "Confirmed"
        );

      return `
        <article
          class="gt-status-card gt-status-confirmed"
        >

          <div class="gt-status-icon">
            🎫
          </div>

          <div class="gt-status-main">

            <div class="gt-status-label">
              BOARDING CONFIRMED
            </div>

            <h3>
              ${eventName}
            </h3>

            <p>
              ${venue} · ${date}
            </p>

            <span class="gt-status-chip">
              Seat ${seat}
            </span>

          </div>

        </article>
      `;
    }


    /*
     * WAITLIST
     */
    if (item.type === "waitlisted") {

      const position =
        esc(
          item.position ?? "?"
        );

      return `
        <article
          class="gt-status-card gt-status-waiting"
        >

          <div class="gt-status-icon">
            🚢
          </div>

          <div class="gt-status-main">

            <div class="gt-status-label">
              WAITING DECK
            </div>

            <h3>
              ${eventName}
            </h3>

            <p>
              ${venue} · ${date}
            </p>

            <span class="gt-status-chip">
              Position #${position}
            </span>

          </div>

        </article>
      `;
    }


    /*
     * GOLDEN TICKET
     */
    if (item.type === "offer") {

      const offer =
        item.offer || {};

      const expiry =
        offer.expiresAt ||
        offer.expires_at;

      const remaining =
        expiry
          ? Math.max(
              0,
              new Date(expiry).getTime()
              - Date.now()
            )
          : 0;

      return `
        <article
          class="gt-status-card gt-status-offer"
        >

          <div class="gt-status-icon">
            📞
          </div>

          <div class="gt-status-main">

            <div class="gt-status-label">
              GOLDEN TICKET
            </div>

            <h3>
              ${eventName}
            </h3>

            <p>
              A seat has opened.
              Your invitation is awaiting a response.
            </p>

            <div
              class="gt-status-countdown"
              data-gt-expiry="${esc(
                expiry || ""
              )}"
            >
              ${
                remaining > 0
                  ? formatCountdown(remaining)
                  : "EXPIRED"
              }
            </div>

          </div>

        </article>
      `;
    }


    return "";
  }


  /*
   * Convert milliseconds to MM:SS.
   */
  function formatCountdown(ms) {

    const totalSeconds =
      Math.max(
        0,
        Math.floor(ms / 1000)
      );

    const minutes =
      String(
        Math.floor(
          totalSeconds / 60
        )
      ).padStart(2, "0");

    const seconds =
      String(
        totalSeconds % 60
      ).padStart(2, "0");

    return `${minutes}:${seconds}`;
  }


  /*
   * Get one event's current summary.
   */
  async function getEventSummary(event) {

    try {

      const response =
        await call(
          "summary",
          event.id
        );

      if (!response.ok) {
        return null;
      }

      const data =
        response.data || {};

      const confirmed =
        (
          API.read.confirmed(data)
          || []
        );

      const waitlist =
        (
          API.read.waitlist(data)
          || []
        );

      const offers =
        (
          API.read.offers(data)
          || []
        );

      return {
        event,
        confirmed,
        waitlist,
        offers
      };

    } catch (error) {

      console.warn(
        "[GT Feature Patch] Summary lookup failed:",
        error
      );

      return null;
    }
  }


  /*
   * Safely get email from backend objects.
   */
  function guestEmail(record) {

    return String(

      record?.email ??

      record?.guest?.email ??

      record?.registration?.email ??

      ""

    )
      .trim()
      .toLowerCase();
  }


  /*
   * Search all current events.
   */
  async function lookupGuest(email) {

    if (patchState.busy) {
      return;
    }

    patchState.busy = true;

    renderLoading();

    try {

      /*
       * Refresh event list first.
       */
      await loadEvents();

      const events =
        Array.isArray(S.events)
          ? S.events
          : [];

      if (!events.length) {

        renderEmpty(email);

        return;
      }


      /*
       * Request summaries for all events.
       */
      const summaries =
        await Promise.all(
          events.map(
            getEventSummary
          )
        );


      const results = [];


      for (const summary of summaries) {

        if (!summary) {
          continue;
        }

        const {
          event,
          confirmed,
          waitlist,
          offers
        } = summary;


        /*
         * Confirmed guest.
         */
        const confirmedGuest =
          confirmed.find(
            guest =>
              guestEmail(guest) === email
          );


        if (confirmedGuest) {

          results.push({
            type: "confirmed",
            event,
            guest: confirmedGuest
          });

        }


        /*
         * Waiting-list guest.
         */
        const waitIndex =
          waitlist.findIndex(
            entry =>
              guestEmail(entry) === email
          );


        if (waitIndex !== -1) {

          const entry =
            waitlist[waitIndex];

          results.push({

            type: "waitlisted",

            event,

            guest: entry,

            position:
              entry?.position ??
              entry?.pos ??
              waitIndex + 1

          });

        }


        /*
         * Pending Golden Ticket.
         */
        const pendingOffer =
          offers.find(function (offer) {

            const status =
              String(
                offer.status || ""
              ).toUpperCase();

            return (
              status === "PENDING" &&
              guestEmail(offer) === email
            );

          });


        if (pendingOffer) {

          results.push({

            type: "offer",

            event,

            offer: pendingOffer

          });

        }

      }


      renderResults(
        email,
        results
      );

    } finally {

      patchState.busy = false;

    }
  }


  /*
   * Render search results.
   */
  function renderResults(
    email,
    results
  ) {

    const box =
      q("#gt-status-results");

    if (!box) {
      return;
    }


    if (!results.length) {

      renderEmpty(email);

      return;
    }


    box.innerHTML = `

      <div class="gt-patch-result-heading">

        <span>
          Current records for
        </span>

        <strong>
          ${esc(email)}
        </strong>

      </div>

      ${results
        .map(statusCard)
        .join("")}

      <p class="gt-patch-note">

        Status is read from the
        current event summaries.
        Refresh the search after
        accepting, declining, or
        cancelling a seat.

      </p>

    `;


    startPatchCountdowns();
  }


  /*
   * Golden Ticket countdown.
   */
  function startPatchCountdowns() {

    const update =
      function () {

        document
          .querySelectorAll(
            "[data-gt-expiry]"
          )
          .forEach(
            function (element) {

              const expiry =
                element.dataset.gtExpiry;

              if (!expiry) {
                return;
              }

              const remaining =
                new Date(expiry).getTime()
                - Date.now();


              if (remaining <= 0) {

                element.textContent =
                  "EXPIRED";

                element.classList.add(
                  "expired"
                );

              } else {

                element.textContent =
                  formatCountdown(
                    remaining
                  );

              }

            }
          );
      };


    update();


    clearInterval(
      window.GTStatusPatchTimer
    );


    window.GTStatusPatchTimer =
      setInterval(
        update,
        1000
      );
  }


  /*
   * Wait until the existing frontend
   * application has initialized.
   */
  function boot() {

    if (
      typeof S === "undefined" ||
      typeof API === "undefined" ||
      typeof call !== "function" ||
      typeof loadEvents !== "function"
    ) {

      setTimeout(
        boot,
        100
      );

      return;
    }


    createLookupUI();
  }


  boot();

})();