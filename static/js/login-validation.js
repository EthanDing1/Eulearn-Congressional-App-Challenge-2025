document.querySelector("form").addEventListener("submit", function(e) {
    e.preventDefault();
    console.log("Login form submitted");
    
    const submitButton = document.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Signing In...';

    let isValid = true;
    let firstInvalid = null;

    document.querySelectorAll(".error-msg").forEach(span => {
        span.textContent = "";
        span.parentElement.classList.remove('error');
    });

    const existingError = document.querySelector('.submit-error-msg');
    if (existingError) existingError.remove();

    const emailInput = document.querySelector('input[placeholder="Email Address"]');
    const passwordInput = document.querySelector('input[placeholder="Password"]');
    
    const email = emailInput.value.trim();
    const password = passwordInput.value;

    console.log("Form data:", { email, passwordLength: password.length });

    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (email === "") {
        showFieldError(emailInput, "Email address is required");
        isValid = false;
        if (!firstInvalid) firstInvalid = emailInput;
    } else if (!emailPattern.test(email)) {
        showFieldError(emailInput, "Please enter a valid email address");
        isValid = false;
        if (!firstInvalid) firstInvalid = emailInput;
    }

    if (password === "") {
        showFieldError(passwordInput, "Password is required");
        isValid = false;
        if (!firstInvalid) firstInvalid = passwordInput;
    } else if (password.length < 8) {
        showFieldError(passwordInput, "Password must be at least 8 characters long");
        isValid = false;
        if (!firstInvalid) firstInvalid = passwordInput;
    }

    if (!isValid) {
        console.log("Form validation failed");
        submitButton.disabled = false;
        submitButton.textContent = originalText;
        
        if (firstInvalid) {
            firstInvalid.focus();
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return;
    }

    console.log("Form validation passed, sending to backend");
    sendLoginData(email, password)
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
    
    const form = document.querySelector('form');
    form.parentNode.insertBefore(errorDiv, form);
    
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 10000);
}

async function sendLoginData(email, password) {
    console.log("Sending login data to backend...");
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
            console.log("Request timed out");
        }, 10000);
        
        const response = await fetch('http://localhost:5000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            }),
            credentials: 'include',
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        console.log("Backend response status:", response.status);
        console.log("Response headers:", [...response.headers.entries()]);
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error("Non-JSON response received:", text);
            throw new Error(`Server returned ${response.status}. Expected JSON but got: ${text.substring(0, 100)}...`);
        }

        const result = await response.json();
        console.log("Backend response data:", result);

        if (response.ok) {
            console.log("Login successful, saving token...");
            
            if (result.token) {
                localStorage.setItem('authToken', result.token);
                console.log("Token stored in localStorage");
            }
            
            if (window.authManager && result.token) {
                console.log("AuthManager found, setting token");
                window.authManager.setToken(result.token);
            } else {
                console.log("AuthManager not found, token stored directly");
            }
            
            showSuccessMessage('Login successful! Redirecting to dashboard...');
            console.log("About to redirect to main page");
            
            setTimeout(() => {
                window.location.href = "/";
            }, 1500);

        } else {
            console.error("Login failed:", result);
            
            const errorMessage = result.error || 'Login failed. Please try again.';
            showSubmitError(errorMessage);
            
            if (errorMessage.toLowerCase().includes('email')) {
                document.querySelector('input[placeholder="Email Address"]').focus();
            } else if (errorMessage.toLowerCase().includes('password')) {
                document.querySelector('input[placeholder="Password"]').focus();
            }
        }
        
    } catch (error) {
        console.error("Network error details:", error);
        
        let errorMessage = 'Network error. Please check your connection and try again.';
        
        if (error.name === 'AbortError') {
            errorMessage = 'Request timed out. Please try again.';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Cannot connect to server. Please check if the server is running on http://localhost:5000';
        } else if (error.message.includes('NetworkError')) {
            errorMessage = 'Network connection failed. Please check your internet connection.';
        } else if (error.message.includes('CORS')) {
            errorMessage = 'Connection blocked by browser. Please ensure the server allows cross-origin requests.';
        } else if (error.message.includes('JSON')) {
            errorMessage = 'Server response error. Please try again or contact support.';
        }
        
        showSubmitError(errorMessage);
    }
}

function showSuccessMessage(message) {
    const existingError = document.querySelector('.submit-error-msg');
    const existingSuccess = document.querySelector('.submit-success-msg');
    if (existingError) existingError.remove();
    if (existingSuccess) existingSuccess.remove();
    
    const successDiv = document.createElement('div');
    successDiv.className = 'submit-success-msg';
    successDiv.style.color = '#155724';
    successDiv.style.textAlign = 'center';
    successDiv.style.marginTop = '10px';
    successDiv.style.padding = '10px';
    successDiv.style.backgroundColor = '#d4edda';
    successDiv.style.border = '1px solid #c3e6cb';
    successDiv.style.borderRadius = '4px';
    successDiv.textContent = message;
    
    const form = document.querySelector('form');
    form.parentNode.insertBefore(successDiv, form);
}

document.querySelectorAll("input").forEach(input => {
    input.addEventListener("input", () => {
        const errorSpan = input.nextElementSibling;
        if (errorSpan && errorSpan.classList.contains("error-msg")) {
            errorSpan.textContent = "";
            input.parentElement.classList.remove('error');
        }
        
        const submitError = document.querySelector(".submit-error-msg");
        if (submitError) submitError.remove();
    });
    
    input.addEventListener("focus", () => {
        input.parentElement.classList.add('focused');
    });
    
    input.addEventListener("blur", () => {
        input.parentElement.classList.remove('focused');
    });
});

const style = document.createElement('style');
style.textContent = `
    .input-box.error input {
        border-color: #dc3545 !important;
        box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
    }
    
    .input-box.focused input {
        border-color: #00A1FF !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 161, 255, 0.25) !important;
    }
    
    .error-msg {
        font-size: 0.875rem;
        margin-top: 0.25rem;
        display: block;
    }
`;
document.head.appendChild(style);

function testServerConnection() {
    fetch('http://localhost:5000/api/test')
        .then(response => {
            console.log("Server test response:", response.status);
            return response.json();
        })
        .then(data => console.log("Server test data:", data))
        .catch(error => console.error("Server test failed:", error));
}

