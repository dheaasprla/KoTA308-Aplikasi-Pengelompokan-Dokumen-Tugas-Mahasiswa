document.addEventListener('DOMContentLoaded', function () {
    const emailInput = document.getElementById('email');
    const emailError = document.getElementById('emailError');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordError = document.getElementById('passwordError');
    const registerBtn = document.getElementById('registerBtn');

    // Email Validation (Real-time)
    if (emailInput && emailError) {
        emailInput.addEventListener('input', function () {
            const emailValue = emailInput.value;
            if (emailValue.length > 0 && !emailValue.includes('@')) {
                emailError.style.display = 'block';
                emailInput.style.borderColor = '#EF4444';
            } else {
                emailError.style.display = 'none';
                emailInput.style.borderColor = '#CBD5E1';
            }
            checkFormValidity();
        });
    }

    // Password Validation (Real-time)
    function validatePassword() {
        if (!passwordInput || !confirmPasswordInput || !passwordError || !registerBtn) return;

        const passwordValue = passwordInput.value;
        const confirmPasswordValue = confirmPasswordInput.value;

        if (confirmPasswordValue.length > 0 && passwordValue !== confirmPasswordValue) {
            passwordError.style.display = 'block';
            confirmPasswordInput.style.borderColor = '#EF4444';
            registerBtn.disabled = true;
        } else {
            passwordError.style.display = 'none';
            confirmPasswordInput.style.borderColor = '#CBD5E1';
            registerBtn.disabled = false;
        }
    }

    if (passwordInput && confirmPasswordInput) {
        passwordInput.addEventListener('input', validatePassword);
        confirmPasswordInput.addEventListener('input', validatePassword);
    }

    function checkFormValidity() {
        // Additional form level checks if needed before enabling the button
        if (registerBtn && passwordInput && confirmPasswordInput) {
            if (passwordInput.value !== confirmPasswordInput.value) {
                registerBtn.disabled = true;
            } else {
                registerBtn.disabled = false;
            }
        }
    }
});
