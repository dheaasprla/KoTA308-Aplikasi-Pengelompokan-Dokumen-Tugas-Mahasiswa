document.addEventListener('DOMContentLoaded', function () {
    const emailInput = document.getElementById('email');
    const emailError = document.getElementById('emailError');
    const emailRequiredError = document.getElementById('emailRequiredError');
    const passwordInput = document.getElementById('password');
    const passwordRequiredError = document.getElementById('passwordRequiredError');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const confirmRequiredError = document.getElementById('confirmRequiredError');
    const passwordError = document.getElementById('passwordError');
    const registerBtn = document.getElementById('registerBtn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    function triggerShake(element) {
        element.classList.remove('shake');
        void element.offsetWidth;
        element.classList.add('shake');
        setTimeout(function () {
            element.classList.remove('shake');
        }, 400);
    }

    function showFieldError(errorEl, inputEl) {
        if (errorEl) errorEl.style.display = 'block';
        if (inputEl) {
            inputEl.style.borderColor = '#EF4444';
            triggerShake(inputEl);
        }
    }

    function hideFieldError(errorEl, inputEl) {
        if (errorEl) errorEl.style.display = 'none';
        if (inputEl) inputEl.style.borderColor = '#CBD5E1';
    }

    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            let hasError = false;

            if (!emailInput.value.trim()) {
                showFieldError(emailRequiredError, emailInput);
                hasError = true;
            } else {
                hideFieldError(emailRequiredError, emailInput);
            }

            if (!passwordInput.value.trim()) {
                showFieldError(passwordRequiredError, passwordInput);
                hasError = true;
            } else {
                hideFieldError(passwordRequiredError, passwordInput);
            }

            if (hasError) {
                e.preventDefault();
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            let hasError = false;

            if (!emailInput.value.trim()) {
                showFieldError(emailRequiredError, emailInput);
                hasError = true;
            } else {
                hideFieldError(emailRequiredError, emailInput);
            }

            if (!passwordInput.value.trim()) {
                showFieldError(passwordRequiredError, passwordInput);
                hasError = true;
            } else {
                hideFieldError(passwordRequiredError, passwordInput);
            }

            if (!confirmPasswordInput.value.trim()) {
                showFieldError(confirmRequiredError, confirmPasswordInput);
                hasError = true;
            } else {
                hideFieldError(confirmRequiredError, confirmPasswordInput);
            }

            if (hasError) {
                e.preventDefault();
            }
        });
    }

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
            if (emailValue.trim()) hideFieldError(emailRequiredError, emailInput);
            checkFormValidity();
        });
    }

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

        if (passwordValue.trim()) hideFieldError(passwordRequiredError, passwordInput);
        if (confirmPasswordValue.trim()) hideFieldError(confirmRequiredError, confirmPasswordInput);
    }

    if (passwordInput && confirmPasswordInput) {
        passwordInput.addEventListener('input', validatePassword);
        confirmPasswordInput.addEventListener('input', validatePassword);
    }

    function checkFormValidity() {
        if (registerBtn && passwordInput && confirmPasswordInput) {
            if (passwordInput.value !== confirmPasswordInput.value) {
                registerBtn.disabled = true;
            } else {
                registerBtn.disabled = false;
            }
        }
    }
});