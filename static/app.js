(function () {
    "use strict";

    const deviceQuery = window.matchMedia("(max-width: 900px)");

    function updateDeviceMode() {
        const mode = deviceQuery.matches ? "mobile" : "desktop";
        document.documentElement.dataset.deviceMode = mode;
        document.documentElement.classList.toggle("is-mobile", mode === "mobile");
        document.documentElement.classList.toggle("is-desktop", mode === "desktop");
    }

    updateDeviceMode();
    deviceQuery.addEventListener("change", updateDeviceMode);

    const menuButton = document.querySelector(".menu-toggle");
    const navigation = document.querySelector("#site-navigation");

    if (menuButton && navigation) {
        menuButton.addEventListener("click", function () {
            const isOpen = menuButton.getAttribute("aria-expanded") === "true";
            menuButton.setAttribute("aria-expanded", String(!isOpen));
            navigation.classList.toggle("is-open", !isOpen);
            menuButton.querySelector(".sr-only").textContent = isOpen
                ? menuButton.dataset.openLabel
                : menuButton.dataset.closeLabel;
        });

        navigation.addEventListener("click", function (event) {
            if (event.target.matches("a")) {
                menuButton.setAttribute("aria-expanded", "false");
                navigation.classList.remove("is-open");
            }
        });

        navigation.querySelectorAll(".nav-more > button").forEach(function (moreButton) {
            moreButton.addEventListener("click", function () {
                const more = moreButton.parentElement;
                more.classList.toggle("is-open");
                moreButton.setAttribute("aria-expanded", String(more.classList.contains("is-open")));
            });
        });
    }

    const countdown = document.querySelector("[data-countdown-target]");

    if (countdown) {
        const target = new Date(countdown.dataset.countdownTarget).getTime();
        const days = countdown.querySelector("[data-countdown-days]");
        const hours = countdown.querySelector("[data-countdown-hours]");
        const minutes = countdown.querySelector("[data-countdown-minutes]");
        const seconds = countdown.querySelector("[data-countdown-seconds]");

        function updateCountdown() {
            const remaining = Math.max(0, target - Date.now());
            const totalSeconds = Math.floor(remaining / 1000);
            const dayValue = Math.floor(totalSeconds / 86400);
            const hourValue = Math.floor((totalSeconds % 86400) / 3600);
            const minuteValue = Math.floor((totalSeconds % 3600) / 60);
            const secondValue = totalSeconds % 60;

            days.textContent = String(dayValue).padStart(2, "0");
            hours.textContent = String(hourValue).padStart(2, "0");
            minutes.textContent = String(minuteValue).padStart(2, "0");
            seconds.textContent = String(secondValue).padStart(2, "0");
        }

        updateCountdown();
        window.setInterval(updateCountdown, 1000);
    }

    const revealItems = document.querySelectorAll(".card, .team-card, .sponsor-card, .info-box, .content-text, .metric-card, .timeline-card, .feature-card, .contact-person-card");

    if ("IntersectionObserver" in window && revealItems.length) {
        const revealObserver = new IntersectionObserver(function (entries, observer) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });

        revealItems.forEach(function (item) {
            item.classList.add("reveal-on-scroll");
            revealObserver.observe(item);
        });
    }

}());