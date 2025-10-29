console.log("Profile settings loaded");

class ProfileManager {
    constructor() {
        this.user = null;
        this.init();
    }

    async init() {
        console.log("Initializing profile manager");

        await this.loadUserData();
        this.setupEventListeners();
    }

    async loadUserData() {
        try {
            console.log("Loading user data...");
            
            const response = await fetch('http://localhost:5000/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const result = await response.json();
                this.user = result.user;
                this.populateForm();
                this.handlePasswordSectionVisibility();
                console.log("User data loaded:", this.user);
            } else {
                console.log("Failed to load user data, redirecting to login");
                localStorage.removeItem('authToken');
                window.location.href = "/login";
            }
        } catch (error) {
            console.error("Error loading user data:", error);
            this.showError('Failed to load user data');
        }
    }

    populateForm() {
        document.getElementById('firstName').value = this.user.firstName || '';
        document.getElementById('lastName').value = this.user.lastName || '';
        document.getElementById('email').value = this.user.email || '';
    }

    handlePasswordSectionVisibility() {
        const passwordSection = document.getElementById('password-form').closest('.form-element');
        const isOAuthUser = this.user.authProvider && this.user.authProvider !== 'local';
        
        if (isOAuthUser) {
            console.log(`OAuth user detected (${this.user.authProvider}), disabling password section`);
            
            passwordSection.style.display = 'none';
            
        } else {
            console.log("Local user detected, password section enabled");
        }
    }

    getProviderDisplayName(provider) {
        const providers = {
            'google': 'Google',
            'facebook': 'Facebook',
            'github': 'GitHub',
            'linkedin': 'LinkedIn',
            'twitter': 'Twitter'
        };
        return providers[provider] || provider;
    }

    setupEventListeners() {
        document.getElementById('personal-info-form').addEventListener('submit', (e) => {
            this.handlePersonalInfoUpdate(e);
        });

        const passwordForm = document.getElementById('password-form');
        if (passwordForm && (!this.user || !this.user.authProvider || this.user.authProvider === 'local')) {
            passwordForm.addEventListener('submit', (e) => {
                this.handlePasswordChange(e);
            });
        }

        document.getElementById('delete-account-btn').addEventListener('click', () => {
            this.showDeleteModal();
        });

        document.getElementById('confirm-delete-btn').addEventListener('click', () => {
            this.deleteAccount();
        });

        document.getElementById('cancel-delete-btn').addEventListener('click', () => {
            this.hideDeleteModal();
        });

        document.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => {
                this.clearFieldError(input);
            });

            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });

            input.addEventListener('blur', () => {
                input.parentElement.classList.remove('focused');
            });
        });

        if (!this.user || !this.user.authProvider || this.user.authProvider === 'local') {
            this.enablePasswordPaste();
        }
    }

    enablePasswordPaste() {
        const passwordFields = document.querySelectorAll('input[type="password"]');
        console.log(`Found ${passwordFields.length} password fields`);
        
        passwordFields.forEach((input, index) => {
            console.log(`Setting up paste for password field ${index + 1}`);
            
            input.onpaste = null;
            
            input.addEventListener('paste', (e) => {
                e.stopPropagation();
                console.log('Paste event triggered on password field');
                
                setTimeout(() => {
                    this.clearFieldError(input);
                }, 50);
            });

            input.addEventListener('contextmenu', (e) => {
                e.stopPropagation();
            });

            input.style.webkitUserSelect = 'text';
            input.style.mozUserSelect = 'text';
            input.style.msUserSelect = 'text';
            input.style.userSelect = 'text';

            input.setAttribute('autocomplete', 'new-password');
        });
    }

    async handlePersonalInfoUpdate(e) {
        e.preventDefault();
        console.log("Updating personal information");

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Updating...';

        this.clearAllErrors();

        const firstName = document.getElementById('firstName').value.trim();
        const lastName = document.getElementById('lastName').value.trim();
        const email = document.getElementById('email').value.trim();

        let isValid = true;
        if (!this.validateName(firstName)) {
            this.showFieldError(document.getElementById('firstName'), 'First name is required');
            isValid = false;
        }
        if (!this.validateName(lastName)) {
            this.showFieldError(document.getElementById('lastName'), 'Last name is required');
            isValid = false;
        }
        if (!this.validateEmail(email)) {
            this.showFieldError(document.getElementById('email'), 'Please enter a valid email address');
            isValid = false;
        }

        if (!isValid) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }

        try {
            const response = await fetch('/api/auth/update-profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    firstName,
                    lastName,
                    email
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.user = result.user;
                this.showSuccess('Personal information updated successfully!');
                console.log("Personal info updated");
            } else {
                this.showError(result.error || 'Failed to update personal information');
            }
        } catch (error) {
            console.error("Update error:", error);
            this.showError('Network error. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    async handlePasswordChange(e) {
        e.preventDefault();
        
        if (this.user.authProvider && this.user.authProvider !== 'local') {
            this.showError('Password changes are not available for OAuth users');
            return;
        }

        console.log("Changing password");

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Changing...';

        this.clearAllErrors();

        const currentPassword = document.getElementById('currentPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        console.log('Password lengths:', {
            current: currentPassword.length,
            new: newPassword.length,
            confirm: confirmPassword.length
        });

        let isValid = true;
        if (!currentPassword) {
            this.showFieldError(document.getElementById('currentPassword'), 'Current password is required');
            isValid = false;
        }
        if (newPassword.length < 8) {
            this.showFieldError(document.getElementById('newPassword'), 'New password must be at least 8 characters');
            isValid = false;
        }
        if (newPassword !== confirmPassword) {
            this.showFieldError(document.getElementById('confirmPassword'), 'Passwords do not match');
            isValid = false;
        }

        if (!isValid) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }

        try {
            const response = await fetch('/api/auth/change-password', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    currentPassword,
                    newPassword
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Password changed successfully!');
                document.getElementById('currentPassword').value = '';
                document.getElementById('newPassword').value = '';
                document.getElementById('confirmPassword').value = '';
                console.log("Password changed");
            } else {
                this.showError(result.error || 'Failed to change password');
            }
        } catch (error) {
            console.error("Password change error:", error);
            this.showError('Network error. Please try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    showDeleteModal() {
        document.getElementById('delete-modal').style.display = 'flex';
    }

    hideDeleteModal() {
        document.getElementById('delete-modal').style.display = 'none';
    }

    async deleteAccount() {
        console.log("Deleting account");

        const confirmBtn = document.getElementById('confirm-delete-btn');
        const originalText = confirmBtn.textContent;
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Deleting...';

        try {
            const response = await fetch('/api/auth/delete-account', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                console.log("Account deleted");
                localStorage.removeItem('authToken');
                
                this.showDeleteSuccessNotification();
                
                setTimeout(() => {
                    window.location.href = "/";
                }, 2000);
            } else {
                const result = await response.json();
                this.showError(result.error || 'Failed to delete account');
            }
        } catch (error) {
            console.error("Delete account error:", error);
            this.showError('Network error. Please try again.');
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.textContent = originalText;
            this.hideDeleteModal();
        }
    }

    showDeleteSuccessNotification() {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #00A1FF;
            color: white;
            padding: 16px 32px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1001;
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transform: translateX(-50%) translateY(-20px);
            transition: all 0.3s ease;
            text-align: center;
            max-width: 90%;
        `;
        notification.textContent = 'Account deleted successfully. Redirecting...';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(-50%) translateY(0)';
        }, 100);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    validateName(name) {
        return name.length >= 1 && name.length <= 100;
    }

    validateEmail(email) {
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return emailPattern.test(email);
    }

    showFieldError(input, message) {
        const errorSpan = input.nextElementSibling;
        if (errorSpan && errorSpan.classList.contains('error-msg')) {
            errorSpan.textContent = message;
            input.parentElement.classList.add('error');
        }
    }

    clearFieldError(input) {
        const errorSpan = input.nextElementSibling;
        if (errorSpan && errorSpan.classList.contains('error-msg')) {
            errorSpan.textContent = '';
            input.parentElement.classList.remove('error');
        }
        this.clearSubmitMessages();
    }

    clearAllErrors() {
        document.querySelectorAll('.error-msg').forEach(span => {
            span.textContent = '';
            span.parentElement.classList.remove('error');
        });
        this.clearSubmitMessages();
    }

    clearSubmitMessages() {
        const existingError = document.querySelector('.submit-error-msg');
        const existingSuccess = document.querySelector('.submit-success-msg');
        if (existingError) existingError.remove();
        if (existingSuccess) existingSuccess.remove();
    }

    showError(message) {
        this.clearSubmitMessages();
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'submit-error-msg';
        errorDiv.style.cssText = `
            color: #dc3545;
            text-align: center;
            margin: 15px 0;
            padding: 12px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 6px;
            font-size: 14px;
        `;
        errorDiv.textContent = message;
        
        const firstForm = document.querySelector('.form-element');
        firstForm.parentNode.insertBefore(errorDiv, firstForm);
        
        setTimeout(() => {
            if (errorDiv.parentNode) errorDiv.remove();
        }, 10000);
    }

    showSuccess(message) {
        this.clearSubmitMessages();
        
        const successDiv = document.createElement('div');
        successDiv.className = 'submit-success-msg';
        successDiv.style.cssText = `
            color: #155724;
            text-align: center;
            margin: 15px 0;
            padding: 12px;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 6px;
            font-size: 14px;
        `;
        successDiv.textContent = message;
        
        const firstForm = document.querySelector('.form-element');
        firstForm.parentNode.insertBefore(successDiv, firstForm);
        
        setTimeout(() => {
            if (successDiv.parentNode) successDiv.remove();
        }, 5000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM loaded, creating ProfileManager");
    window.profileManager = new ProfileManager();
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
        color: #dc3545;
    }
    
    /* Ensure password fields allow text selection and paste */
    input[type="password"] {
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -ms-user-select: text !important;
        user-select: text !important;
    }
    
    /* OAuth info message styling */
    .oauth-info-msg {
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

console.log("Profile settings script loaded");