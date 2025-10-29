document.addEventListener('DOMContentLoaded', function() {
    const forgotPasswordLink = document.querySelector('.forgot-pass a');
    const modal = document.getElementById('forgot-password-modal');
    const closeBtn = document.querySelector('.close-modal');
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    const emailInput = document.getElementById('forgot-email');
    const errorMsg = emailInput.parentElement.querySelector('.error-msg');
    const submitButton = forgotPasswordForm.querySelector('button[type="submit"]');

    forgotPasswordLink.addEventListener('click', function(e) {
        e.preventDefault();
        modal.style.display = 'flex';
        emailInput.value = '';
        errorMsg.textContent = '';
        emailInput.parentElement.classList.remove('error');
        const existingMsg = modal.querySelector('.submit-error-msg, .submit-success-msg');
        if (existingMsg) existingMsg.remove();
    });

    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            modal.style.display = 'none';
        }
    });

    forgotPasswordForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log("🔍 Forgot password form submitted");
        
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Sending...';

        errorMsg.textContent = '';
        emailInput.parentElement.classList.remove('error');
        
        const existingMsg = modal.querySelector('.submit-error-msg, .submit-success-msg');
        if (existingMsg) existingMsg.remove();

        const email = emailInput.value.trim();
        let isValid = true;

        console.log("🔍 Email:", email);

        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        
        if (email === "") {
            showFieldError(emailInput, "Email address is required");
            isValid = false;
        } else if (!emailPattern.test(email)) {
            showFieldError(emailInput, "Please enter a valid email address");
            isValid = false;
        }

        if (!isValid) {
            console.log("🔍 Form validation failed");
            submitButton.disabled = false;
            submitButton.textContent = originalText;
            emailInput.focus();
            return;
        }

        console.log("🔍 Form validation passed, sending to backend");
        
        sendForgotPasswordRequest(email)
            .finally(() => {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            });
    });

    function showFieldError(input, message) {
        const errorSpan = input.nextElementSibling;
        if (errorSpan && errorSpan.classList.contains("error-msg")) {
            errorSpan.textContent = message;
            input.parentElement.classList.add('error');
        }
    }

    function showModalSuccess(message) {
        const existingMsg = modal.querySelector('.submit-error-msg, .submit-success-msg');
        if (existingMsg) existingMsg.remove();
        
        const successDiv = document.createElement('div');
        successDiv.className = 'submit-success-msg';
        successDiv.style.color = '#155724';
        successDiv.style.textAlign = 'center';
        successDiv.style.marginTop = '15px';
        successDiv.style.padding = '12px';
        successDiv.style.backgroundColor = '#d4edda';
        successDiv.style.border = '1px solid #c3e6cb';
        successDiv.style.borderRadius = '8px';
        successDiv.style.fontSize = '14px';
        successDiv.textContent = message;
        
        forgotPasswordForm.appendChild(successDiv);
    }

    function showModalError(message) {
        const existingMsg = modal.querySelector('.submit-error-msg, .submit-success-msg');
        if (existingMsg) existingMsg.remove();
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'submit-error-msg';
        errorDiv.style.color = '#dc3545';
        errorDiv.style.textAlign = 'center';
        errorDiv.style.marginTop = '15px';
        errorDiv.style.padding = '12px';
        errorDiv.style.backgroundColor = '#f8d7da';
        errorDiv.style.border = '1px solid #f5c6cb';
        errorDiv.style.borderRadius = '8px';
        errorDiv.style.fontSize = '14px';
        errorDiv.textContent = message;
        
        forgotPasswordForm.appendChild(errorDiv);
    }

    async function sendForgotPasswordRequest(email) {
        console.log("🔍 Sending forgot password request to backend...");
        
        try {
            const response = await fetch('http://localhost:5000/api/auth/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email }),
                signal: AbortSignal.timeout(10000)
            });

            console.log("🔍 Backend response status:", response.status);
            const result = await response.json();
            console.log("🔍 Backend response data:", result);

            if (response.ok) {
                console.log("✅ Request successful");
                
                showModalSuccess(result.message || 'If an account exists with this email, you will receive password reset instructions.');
                
                emailInput.value = '';
                
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 4000);

            } else {
                console.error("❌ Request failed:", result);
                const errorMessage = result.error || 'Failed to process request. Please try again.';
                    showModalError(errorMessage);
            }
        } catch (error) {
            console.error("❌ Network error:", error);
            
            let errorMessage = 'Network error. Please check your connection and try again.';
            
            if (error.name === 'TimeoutError') {
                errorMessage = 'Request timed out. Please try again.';
            } else if (error.name === 'AbortError') {
                errorMessage = 'Request was cancelled. Please try again.';
            }
            
            showModalError(errorMessage);
        }
    }

    

    emailInput.addEventListener('input', function() {
        if (errorMsg.textContent) {
            errorMsg.textContent = '';
            emailInput.parentElement.classList.remove('error');
        }
        
        const existingMsg = modal.querySelector('.submit-error-msg, .submit-success-msg');
        if (existingMsg) existingMsg.remove();
    });

    emailInput.addEventListener('focus', function() {
        emailInput.parentElement.classList.add('focused');
    });

    emailInput.addEventListener('blur', function() {
        emailInput.parentElement.classList.remove('focused');
    });
});