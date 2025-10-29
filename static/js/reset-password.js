document.addEventListener('DOMContentLoaded', function() {
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const resetForm = document.getElementById('reset-form');
    const successState = document.getElementById('success-state');
    const form = document.getElementById('password-reset-form');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const submitButton = form.querySelector('button[type="submit"]');

    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    console.log("🔍 Reset password page loaded");
    console.log("🔍 Token from URL:", token ? "Present" : "Missing");

    if (!token) {
        console.log("❌ No token in URL");
        showErrorState();
        return;
    }

    verifyToken(token);

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log("🔍 Password reset form submitted");
        
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Resetting...';

        let isValid = true;
        let firstInvalid = null;

        document.querySelectorAll(".error-msg").forEach(span => {
            span.textContent = "";
            span.parentElement.classList.remove('error');
        });

        const existingError = document.querySelector('.submit-error-msg');
        if (existingError) existingError.remove();

        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        console.log("🔍 Password lengths:", {
            newPassword: newPassword.length,
            confirmPassword: confirmPassword.length
        });

        if (newPassword === "") {
            showFieldError(newPasswordInput, "Password is required");
            isValid = false;
            if (!firstInvalid) firstInvalid = newPasswordInput;
        } else if (newPassword.length < 8) {
            showFieldError(newPasswordInput, "Password must be at least 8 characters long");
            isValid = false;
            if (!firstInvalid) firstInvalid = newPasswordInput;
        }

        if (confirmPassword === "") {
            showFieldError(confirmPasswordInput, "Please confirm your password");
            isValid = false;
            if (!firstInvalid) firstInvalid = confirmPasswordInput;
        } else if (newPassword !== confirmPassword) {
            showFieldError(confirmPasswordInput, "Passwords do not match");
            isValid = false;
            if (!firstInvalid) firstInvalid = confirmPasswordInput;
        }

        if (!isValid) {
            console.log("🔍 Form validation failed");
            submitButton.disabled = false;
            submitButton.textContent = originalText;
            
            if (firstInvalid) {
                firstInvalid.focus();
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }

        console.log("🔍 Form validation passed, sending to backend");
        resetPassword(token, newPassword)
            .finally(() => {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            });
    });

    [newPasswordInput, confirmPasswordInput].forEach(input => {
        input.addEventListener('input', function() {
            const errorSpan = input.nextElementSibling;
            if (errorSpan && errorSpan.classList.contains("error-msg")) {
                errorSpan.textContent = "";
                input.parentElement.classList.remove('error');
            }
            
            const submitError = document.querySelector(".submit-error-msg");
            if (submitError) submitError.remove();
        });

        input.addEventListener('focus', function() {
            input.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function() {
            input.parentElement.classList.remove('focused');
        });
    });

    function showFieldError(input, message) {
        const errorSpan = input.nextElementSibling;
        if (errorSpan && errorSpan.classList.contains("error-msg")) {
            errorSpan.textContent = message;
            input.parentElement.classList.add('error');
        }
    }

    function showSubmitError(message) {
        const existingError = document.querySelector('.submit-error-msg');
        if (existingError) existingError.remove();
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'submit-error-msg';
        errorDiv.style.color = '#dc3545';
        errorDiv.style.textAlign = 'center';
        errorDiv.style.marginTop = '10px';
        errorDiv.style.padding = '10px';
        errorDiv.style.backgroundColor = '#f8d7da';
        errorDiv.style.border = '1px solid #f5c6cb';
        errorDiv.style.borderRadius = '4px';
        errorDiv.textContent = message;
        
        form.parentNode.insertBefore(errorDiv, form);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 10000);
    }

    function showLoadingState() {
        loadingState.style.display = 'block';
        errorState.style.display = 'none';
        resetForm.style.display = 'none';
        successState.style.display = 'none';
    }

    function showErrorState() {
        loadingState.style.display = 'none';
        errorState.style.display = 'block';
        resetForm.style.display = 'none';
        successState.style.display = 'none';
    }

    function showResetForm() {
        loadingState.style.display = 'none';
        errorState.style.display = 'none';
        resetForm.style.display = 'block';
        successState.style.display = 'none';
    }

    function showSuccessState() {
        loadingState.style.display = 'none';
        errorState.style.display = 'none';
        resetForm.style.display = 'none';
        successState.style.display = 'block';
    }

    async function verifyToken(token) {
        console.log("🔍 Verifying token with backend...");
        showLoadingState();
        
        try {
            const response = await fetch('/api/auth/verify-reset-token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: token }),
                credentials: 'include',
                signal: AbortSignal.timeout(10000)
            });

            const result = await response.json();
            console.log("🔍 Token verification response:", result);

            if (response.ok && result.valid) {
                console.log("✅ Token is valid");
                showResetForm();
            } else {
                console.log("❌ Token is invalid or expired");
                showErrorState();
            }
        } catch (error) {
            console.error("❌ Token verification error:", error);
            showErrorState();
        }
    }

    async function resetPassword(token, newPassword) {
        console.log("🔍 Resetting password...");
        
        try {
            const response = await fetch('/api/auth/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: token,
                    newPassword: newPassword
                }),
                credentials: 'include',
                signal: AbortSignal.timeout(10000)
            });

            const result = await response.json();
            console.log("🔍 Reset password response:", result);

            if (response.ok) {
                console.log("✅ Password reset successful");
                showSuccessState();
            } else {
                console.error("❌ Password reset failed:", result);
                const errorMessage = result.error || 'Failed to reset password. Please try again.';
                showSubmitError(errorMessage);
            }
        } catch (error) {
            console.error("❌ Network error:", error);
            
            let errorMessage = 'Network error. Please check your connection and try again.';
            
            if (error.name === 'TimeoutError') {
                errorMessage = 'Request timed out. Please try again.';
            } else if (error.name === 'AbortError') {
                errorMessage = 'Request was cancelled. Please try again.';
            }
            
            showSubmitError(errorMessage);
        }
    }
});