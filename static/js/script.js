// Client-side validation for every form with the "needs-validation" class.
document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll(".needs-validation");

    forms.forEach(function (form) {
        const password = form.querySelector("#password");
        const confirm = form.querySelector("#confirm_password");

        // Registration form only: make sure both passwords match.
        function checkMatch() {
            if (password && confirm) {
                confirm.setCustomValidity(
                    confirm.value === password.value ? "" : "Passwords do not match"
                );
            }
        }

        if (password && confirm) {
            password.addEventListener("input", checkMatch);
            confirm.addEventListener("input", checkMatch);
        }

        form.addEventListener("submit", function (event) {
            checkMatch();
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add("was-validated");
        });
    });
});
