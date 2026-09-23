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
    }

    const revealItems = document.querySelectorAll(".card, .team-card, .sponsor-card, .info-box, .content-text");

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