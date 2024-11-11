document.addEventListener("DOMContentLoaded", () => {
    const signupForm = document.getElementById("signupForm");
    const loginForm = document.getElementById("loginForm");

    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(signupForm);
            const data = {
                name: formData.get("name"),
                email: formData.get("email"),
                role: formData.get("role"),
                contact: formData.get("contact"),
                password: formData.get("password"),
                confirmPassword: formData.get("confirmPassword")
            };
            const response = await fetch("/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            alert(result.message || result.error);
        });
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const formData = new FormData(loginForm);
            const data = {
                email: formData.get("email"),
                password: formData.get("password"),
                role: formData.get("role"),
            };
            const response = await fetch("/admin/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            const result = await response.json();
            alert(result.message || result.error);
            if (response.ok) {
                window.location.href = "/admin";
            }
        });
    }
});
