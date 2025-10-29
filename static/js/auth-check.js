console.log("🔍 Auth-check.js (Flask OAuth version) loaded!");

class AuthManager {
    constructor() {
        this.user = null;
        this.dropdownOpen = false;
        this.dropdownAnimating = false;
        console.log("🔍 AuthManager created");
        this.checkAuthOnLoad();
        this.setupClickOutsideListener();
        this.setupOAuthListener();
    }

    setupOAuthListener() {
        window.addEventListener('message', (event) => {
            if (event.origin !== window.location.origin) return;
            
            if (event.data.type === 'OAUTH_SUCCESS') {
                window.location.reload();
            } else if (event.data.type === 'OAUTH_ERROR') {
                this.showError('Login failed: ' + event.data.error);
            }
        });
    }

    async checkAuthOnLoad() {
        console.log("🔍 Checking authentication...");
        
        this.checkForSignupMessage();
        
        try {
            const response = await fetch('/api/auth/me', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            console.log("🔍 Auth response status:", response.status);
            
            if (response.ok) {
                const result = await response.json();
                console.log("🔍 Auth result:", result);
                this.user = result.user;
                console.log("✅ User logged in:", this.user);
                this.updateWelcomeMessage();
            } else {
                console.log("❌ Not authenticated");
                this.user = null;
            }
            
        } catch (error) {
            console.log("❌ Auth check failed:", error);
            this.user = null;
        }
        
        this.updateNavigation();
    }

    async makeAuthenticatedRequest(url, options = {}) {
        return fetch(url, {
            ...options,
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
    }

    updateNavigation() {
        console.log("🔍 Updating navigation, user:", this.user);
        
        const navUl = document.querySelector('nav ul');
        const solverLink = document.querySelector('.navlink[href*="solver"]');
        
        if (!navUl) {
            console.log("❌ Navigation not found");
            return;
        }
        
        console.log("🔍 Found navigation elements");
        
        if (this.user) {
            console.log("✅ Updating navigation for logged-in user");
            this.createLoggedInNavigation(navUl);
            
            if (solverLink) {
                solverLink.href = '/solver';
                solverLink.onclick = null;
                solverLink.style.opacity = '1';
                solverLink.style.pointerEvents = 'auto';
                solverLink.style.cursor = 'pointer';
            }
            
        } else {
            console.log("✅ Updating navigation for guest user");
            this.createGuestNavigation(navUl);
            
            if (solverLink) {
                solverLink.href = '#';
                solverLink.onclick = (e) => {
                    e.preventDefault();
                    this.showSignupPrompt();
                    return false;
                };
                solverLink.style.opacity = '0.6';
                solverLink.style.pointerEvents = 'auto';
                solverLink.style.cursor = 'pointer';
            }
        }
    }

    updateWelcomeMessage() {
        const welcomeTitle = document.querySelector('.welcome-title-main');
        const welcomeSubtitle = document.getElementById('track-progress-message');
        const welcomeButton = document.getElementById('welcome-get-started-btn');   
        
        if (welcomeTitle) {
            if (this.user) {
                welcomeTitle.textContent = `Hi, ${this.user.firstName}`;
                if (welcomeSubtitle) {
                    welcomeSubtitle.textContent = '';
                }
                if (welcomeButton) {
                    welcomeButton.textContent = "Start solving";
                    welcomeButton.onclick = () => { window.location.href = '/solver'; };
                }
            } else {
                welcomeTitle.textContent = 'Welcome to Eulearn';
                if (welcomeSubtitle) {
                    welcomeSubtitle.textContent = 'to use the Integral Solver and track progress.';
                }
                if (welcomeButton) {
                    welcomeButton.textContent = "Get Started";
                    welcomeButton.onclick = () => { window.location.href = '/getstarted'; };
                }
            }
        }
    }

    createLoggedInNavigation(navUl) {
        console.log("🔍 Creating logged in navigation for:", this.user);
        
        const userInitials = (this.user.firstName.charAt(0) + this.user.lastName.charAt(0)).toUpperCase();
        
        navUl.innerHTML = `
            <li><a href="/solver" class="navlink">Integral Solver</a></li>
            <li><a href="/techniques" class="navlink">Techniques</a></li>
            <li><a href="/about" class="navlink">About</a></li>
            <li class="user-profile">
                <button class="profile-button" id="profile-btn">
                    ${userInitials}
                </button>
            </li>
        `;
        
        this.addNavigationStyles();
        
        this.attachProfileButtonHandler();
    }

    attachProfileButtonHandler() {
        const profileBtn = document.getElementById('profile-btn');
        if (profileBtn) {
            console.log("🔍 Attaching profile button click handler");
            
            profileBtn.replaceWith(profileBtn.cloneNode(true));
            const newProfileBtn = document.getElementById('profile-btn');
            
            newProfileBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log("🔍 Profile button clicked - redirecting to profile settings");
                window.location.href = '/profilesettings';
            });
            
            console.log("✅ Profile button handler attached successfully");
        } else {
            console.error("❌ Profile button not found");
            setTimeout(() => {
                this.attachProfileButtonHandler();
            }, 100);
        }
    }

    createGuestNavigation(navUl) {
        navUl.innerHTML = `
            <li><a href="#" class="navlink solver-link-guest">Integral Solver</a></li>
            <li><a href="/techniques" class="navlink">Techniques</a></li>
            <li><a href="/about" class="navlink">About</a></li>
            <li class="auth-buttons">
                <button class="button login-btn" onclick="window.location.href='/login'">Login</button>
                <button class="button get-started-btn" onclick="window.location.href='/getstarted'">Get Started</button>
            </li>
        `;
        
        this.addNavigationStyles();
        
        const loginBtn = document.querySelector('.login-btn');
        if (loginBtn) {
            loginBtn.style.backgroundColor = 'white';
            loginBtn.style.color = '#00A1FF';
            loginBtn.style.border = '3px solid #00A1FF';
        }

        const solverLink = document.querySelector('.solver-link-guest');
        if (solverLink) {
            solverLink.onclick = (e) => {
                e.preventDefault();
                console.log("Guest clicked solver link, redirecting to signup with message");
                window.location.href = '/getstarted?message=solver_signup_required';
            };
            solverLink.style.opacity = '0.8';
            solverLink.style.cursor = 'pointer';
        }
    }

    addNavigationStyles() {
        if (document.getElementById('auth-nav-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'auth-nav-styles';
        styles.textContent = `
            /* Navigation improvements */
            nav ul {
                display: flex;
                align-items: center;
                list-style: none;
                margin: 0;
                padding: 0;
                gap: 20px;
            }
            
            nav ul li {
                display: flex;
                align-items: center;
            }
            
            .auth-buttons {
                display: flex;
                gap: 12px;
                margin-left: auto;
            }
            
            .user-profile {
                margin-left: auto;
                position: relative;
            }
            
            // .profile-button {
            //     width: 50px;
            //     height: 50px;
            //     border-radius: 50%;
            //     background-color: white;
            //     border: 3px solid #00A1FF;
            //     color: #00A1FF;
            //     font-weight: 600;
            //     font-size: 16px;
            //     display: flex;
            //     align-items: center;
            //     justify-content: center;
            //     cursor: pointer;
            //     transition: all 0.3s ease;
            //     box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            //     pointer-events: auto;
            //     position: relative;
            //     z-index: 999;
            // }
            .profile-button {
                width: 50px;
                height: 50px;
                min-width: 50px;  /* Add this */
                min-height: 50px; /* Add this */
                max-width: 50px;  /* Add this */
                max-height: 50px; /* Add this */
                border-radius: 50%;
                background-color: white;
                border: 3px solid #00A1FF;
                color: #00A1FF;
                font-weight: 600;
                font-size: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                pointer-events: auto;
                position: relative;
                z-index: 999;
                padding: 0; /* Add this to remove any padding */
                box-sizing: border-box; /* Add this */
            }
            
            .profile-button:hover {
                background-color: #00A1FF;
                color: white;
                transform: scale(1.05);
            }
            
            .profile-button:focus {
                outline: none;
                box-shadow: 0 0 0 3px rgba(0, 161, 255, 0.2);
            }
            
            /* Ensure buttons maintain original styling */
            .auth-buttons .button {
                margin: 0;
            }
            
            /* Specific styling for login button to keep white background */
            .auth-buttons .login-btn {
                background-color: white !important;
                color: #00A1FF !important;
                border: 3px solid #00A1FF !important;
            }
            
            .auth-buttons .login-btn:hover {
                background-color: #00A1FF !important;
                color: white !important;
            }
            
            /* Get Started button styling */
            .auth-buttons .get-started-btn {
                background-color: #00A1FF;
                color: white;
                border: 3px solid #00A1FF;
            }
            
            .auth-buttons .get-started-btn:hover {
                background-color: white;
                color: #00A1FF;
                border: 3px solid #00A1FF;
            }
            
            /* Responsive adjustments */
            @media (max-width: 768px) {
                nav ul {
                    gap: 15px;
                }
                
                .auth-buttons {
                    gap: 8px;
                }
                
                .auth-buttons .button {
                    padding: 8px 16px;
                    font-size: 14px;
                }
                
                .profile-button {
                    width: 45px;
                    height: 45px;
                    font-size: 14px;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    setupClickOutsideListener() {
        document.addEventListener('click', (e) => {
        });
    }

    checkForSignupMessage() {
        const urlParams = new URLSearchParams(window.location.search);
        const message = urlParams.get('message');
        
        if (message === 'solver_signup_required') {
            this.showSignupPageMessage();
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    showSignupPageMessage() {
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
        notification.textContent = 'Please sign up to access the Integral Solver';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(-50%) translateY(0)';
        }, 100);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(-50%) translateY(-20px)';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 2000);
    }

    showSignupPrompt() {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            max-width: 400px;
            margin: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        `;
        
        modalContent.innerHTML = `
            <h3 style="color: #333; margin-bottom: 15px;">Sign Up Required</h3>
            <p style="color: #666; margin-bottom: 25px;">Please create an account to access the Integral Solver.</p>
            <div style="display: flex; gap: 15px; justify-content: center;">
                <button id="signup-modal-btn" style="
                    background: #00A1FF;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                ">Get Started</button>
                <button id="cancel-modal-btn" style="
                    background: #6c757d;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                ">Cancel</button>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        document.getElementById('signup-modal-btn').onclick = () => {
            window.location.href = '/getstarted';
        };
        
        document.getElementById('cancel-modal-btn').onclick = () => {
            modal.remove();
        };
        
        modal.onclick = (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        };
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dc3545;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1001;
            font-size: 14px;
            font-weight: 500;
        `;
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 3000);
    }

    async logout() {
        console.log("🔍 Logging out...");
        
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            console.log("🔍 Logout response status:", response.status);
        } catch (error) {
            console.error("🔍 Logout request failed:", error);
        }
        
        this.user = null;
        this.updateNavigation();
        this.updateWelcomeMessage();
        
        const logoutMessage = document.createElement('div');
        logoutMessage.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1001;
            font-size: 14px;
            font-weight: 500;
        `;
        logoutMessage.textContent = '✓ Logged out successfully!';
        document.body.appendChild(logoutMessage);
        
        setTimeout(() => {
            if (logoutMessage.parentNode) {
                logoutMessage.remove();
            }
        }, 1500);
        
        if (window.location.pathname.includes('/solver') || window.location.pathname.includes('/profile')) {
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    }

    setToken(token) {
        console.log("🔍 setToken called (not used in session auth)");
        this.checkAuthOnLoad();
    }

    isLoggedIn() {
        return this.user !== null;
    }

    getUser() {
        return this.user || { firstName: 'User', lastName: 'Name' };
    }

    getToken() {
        return '';
    }
}

function loginWithGoogle() {
    window.location.href = '/login/google';
}

function loginWithGitHub() {
    window.location.href = '/login/github';
}

document.addEventListener('DOMContentLoaded', function() {
    console.log("🔍 DOM loaded, creating AuthManager");
    window.authManager = new AuthManager();
});

console.log("🔍 Auth-check.js (Flask OAuth version) script finished loading");