(() => {
    const storageKey = "biblioteca-admin-theme";

    function addThemeToggle() {
        const target = document.querySelector("#user-tools") || document.querySelector("#branding");
        if (!target) {
            return;
        }

        const button = document.createElement("button");
        button.className = "admin-glass-toggle";
        button.type = "button";
        button.setAttribute("aria-pressed", String(document.documentElement.dataset.adminTheme === "glass"));

        function updateButton() {
            const isGlass = document.documentElement.dataset.adminTheme === "glass";
            button.textContent = isGlass ? "Tema padrão" : "Tema iOS";
            button.setAttribute("aria-pressed", String(isGlass));
        }

        button.addEventListener("click", () => {
            const isGlass = document.documentElement.dataset.adminTheme === "glass";
            if (isGlass) {
                delete document.documentElement.dataset.adminTheme;
                localStorage.removeItem(storageKey);
            } else {
                document.documentElement.dataset.adminTheme = "glass";
                localStorage.setItem(storageKey, "glass");
            }
            updateButton();
        });

        updateButton();
        target.append(button);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", addThemeToggle, { once: true });
    } else {
        addThemeToggle();
    }
})();
