document.addEventListener('DOMContentLoaded', function () {
    const emailInput = document.getElementById('email');
    const emailError = document.getElementById('emailError');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordError = document.getElementById('passwordError');
    const registerBtn = document.getElementById('registerBtn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // ─── Fungsi Shake ───────────────────────────────────────────
    function triggerShake(element) {
        element.classList.remove('shake');
        void element.offsetWidth; // reset animasi biar bisa dipicu ulang
        element.classList.add('shake');
        setTimeout(function () {
            element.classList.remove('shake');
        }, 400);
    }

    // ─── Handle Submit Form Login ────────────────────────────────
    if (loginForm) {
        loginForm.addEventListener('submit', function (e) {
            const inputs = loginForm.querySelectorAll('input[required]');
            let hasEmpty = false;

            inputs.forEach(function (input) {
                if (!input.value.trim()) {
                    triggerShake(input);
                    hasEmpty = true;
                }
            });

            if (hasEmpty) {
                e.preventDefault();
            }
        });
    }

    // ─── Handle Submit Form Register ────────────────────────────
    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            const inputs = registerForm.querySelectorAll('input[required]');
            let hasEmpty = false;

            inputs.forEach(function (input) {
                if (!input.value.trim()) {
                    triggerShake(input);
                    hasEmpty = true;
                }
            });

            if (hasEmpty) {
                e.preventDefault();
            }
        });
    }

    // ─── Validasi Email Real-time ────────────────────────────────
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

    // ─── Validasi Password Real-time ─────────────────────────────
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
        if (registerBtn && passwordInput && confirmPasswordInput) {
            if (passwordInput.value !== confirmPasswordInput.value) {
                registerBtn.disabled = true;
            } else {
                registerBtn.disabled = false;
            }
        }
    }

    // ─── Ubah pesan validasi bawaan browser ke Bahasa Indonesia ───
    document.querySelectorAll('input[required]').forEach(function (input) {
        input.addEventListener('invalid', function () {
            if (input.value.trim() === '') {
                input.setCustomValidity('Mohon isi kolom ini.');
            } else {
                input.setCustomValidity('');
            }
        });

        input.addEventListener('input', function () {
            input.setCustomValidity('');
        });
    });
});