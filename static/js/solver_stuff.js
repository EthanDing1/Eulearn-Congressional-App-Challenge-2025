let currentConversation = [];
let problemHistory = [];
let currentSolverMode = null;
let isPracticeMode = false;
let currentPracticeTypeMessage = null;
let currentPracticeDifficultyMessage = null;
let selectedPracticeType = null;
let selectedPracticeDifficulty = null;

const authManager = {
    userData: null,
    
    getToken: function() {
        return '';
    },
    
    getUser: function() {
        return this.userData || { 
            firstName: 'User', 
            lastName: 'Name' 
        };
    },
    
    setUser: function(userData) {
        this.userData = userData;
    },
    
    isLoggedIn: function() {
        return true;
    }
};

function renderLatex(element) {
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(element, {
            delimiters: [
                {left: "$$", right: "$$", display: true},
                {left: "$", right: "$", display: false}
            ],
            throwOnError: false,
            errorColor: "#cc0000"
        });
    }
}

function initializePageLatex() {
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
            delimiters: [
                {left: "$$", right: "$$", display: true},
                {left: "$", right: "$", display: false}
            ],
            throwOnError: false,
            errorColor: "#cc0000"
        });
    }
}

function setupInputHandlers() {
    const input = document.getElementById('main-input');
    const sendBtn = document.getElementById('send-btn');
    const dropdown = document.getElementById('solver-dropdown');

    if (!input || !sendBtn) {
        console.error('Required input elements not found');
        return;
    }

    input.addEventListener('input', function() {
        this.style.height = '24px';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        
        if (this.value.trim()) {
            hideDropdown();
        }
        if (isPracticeMode) {
            validatePracticeInput();
        } else {
            validateMainInput();
        }
    });

    input.addEventListener('focus', function() {
        if (!isPracticeMode) {
            showDropdown();
        }
    });

    input.addEventListener('blur', function() {
        if (!isPracticeMode) {
            setTimeout(() => {
                hideDropdown();
            }, 150);
        }
    });

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (isPracticeMode) {
                if (this.value.trim() && window.currentPracticeType && window.currentPracticeDifficulty) {
                    handlePracticeSubmission();
                }
            } else if (this.value.trim() && currentSolverMode) {
                solveIntegral();
            }
        }
        
        if (e.key === 'Escape') {
            hideDropdown();
            this.blur();
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!isPracticeMode && dropdown && !input.contains(e.target) && !dropdown.contains(e.target)) {
            hideDropdown();
        }
    });
    
    if (isPracticeMode) {
        validatePracticeInput();
    } else {
        validateMainInput();
    }
}

function validatePracticeInput() {
    const input = document.getElementById('main-input');
    const sendBtn = document.getElementById('send-btn');
    
    if (!input || !sendBtn) return;
    
    const hasContent = input.value.trim();
    
    clearRegularInputError();
    
    let isValid = true;
    let errorMessage = '';
    
    if (hasContent && !window.currentPracticeType) {
        isValid = false;
        errorMessage = 'Please select a problem type (Regular, Parametric, or Polar) first';
        showRegularInputError(errorMessage);
    }
    else if (hasContent && window.currentPracticeType && !window.currentPracticeDifficulty) {
        isValid = false;
        errorMessage = 'Please select a difficulty level (1-4) first';
        showRegularInputError(errorMessage);
    }
    
    
    const shouldEnable = hasContent && window.currentPracticeType && window.currentPracticeDifficulty && isValid;
    sendBtn.disabled = !shouldEnable;
    
    if (shouldEnable) {
        sendBtn.style.background = '#00A1FF';
        sendBtn.style.cursor = 'pointer';
        sendBtn.style.opacity = '1';
        sendBtn.classList.add('has-input');
    } else {
        sendBtn.style.background = 'gainsboro';
        sendBtn.style.cursor = 'not-allowed';
        sendBtn.style.opacity = '0.8';
        sendBtn.classList.remove('has-input');
    }
}


function validateMainInput() {
    const input = document.getElementById('main-input');
    const sendBtn = document.getElementById('send-btn');
    const inputContainer = document.querySelector('.input-container');
    
    if (!input || !sendBtn || !inputContainer) return;
    
    const hasContent = input.value.trim();
    const hasSolverMode = currentSolverMode !== null;
    
    clearRegularInputError();
    
    let isValid = true;
    let errorMessage = '';
    
    if (hasContent && !hasSolverMode && !isPracticeMode) {
        isValid = false;
        errorMessage = 'Please select a solver type (Regular, Parametric, or Polar)';
        showRegularInputError(errorMessage);
    }
    
    const shouldEnable = hasContent && hasSolverMode && isValid;
    sendBtn.disabled = !shouldEnable;
    
    if (shouldEnable) {
        sendBtn.style.background = '#00A1FF';
        sendBtn.style.cursor = 'pointer';
        sendBtn.style.opacity = '1';
        sendBtn.classList.add('has-input');
    } else {
        sendBtn.style.background = 'gainsboro';
        sendBtn.style.cursor = 'not-allowed';
        sendBtn.style.opacity = '0.8';
        sendBtn.classList.remove('has-input');
    }
}

function showDropdown() {
    const dropdown = document.getElementById('solver-dropdown');
    const input = document.getElementById('main-input');
    
    if (!dropdown || !input) return;
    
    dropdown.innerHTML = `
        <div class="example-prompt" onclick="selectSolverType('integral')">
            <h4>Regular</h4>
            <p>ex. ∫ x² dx </p>
        </div>
        <div class="example-prompt" onclick="selectSolverType('parametric')">
            <h4>Parametric</h4>
            <p>ex. x(t)=t, y(t)=t²</p>
        </div>
        <div class="example-prompt" onclick="selectSolverType('polar')">
            <h4>Polar</h4>
            <p>ex. r1(θ) = 2 + sin(θ), r2(θ) = 5cos(θ)</p>
        </div>
    `;
    
    dropdown.style.display = 'grid';
    input.classList.add('dropdown-active');
    
    setTimeout(() => {
        dropdown.classList.add('show');
    }, 10);
}

function hideDropdown() {
    const dropdown = document.getElementById('solver-dropdown');
    const input = document.getElementById('main-input');
    
    if (dropdown && input) {
        dropdown.classList.remove('show');
        input.classList.remove('dropdown-active');
        
        setTimeout(() => {
            if (!dropdown.classList.contains('show')) {
                dropdown.style.display = 'none';
            }
        }, 300);
    }

    const parametricDropdown = document.getElementById('parametric-solver-dropdown');
    const parametricInputs = document.querySelectorAll('.parametric-input');
    
    if (parametricDropdown) {
        parametricDropdown.classList.remove('show');
        parametricInputs.forEach(input => input.classList.remove('dropdown-active'));
        
        setTimeout(() => {
            if (!parametricDropdown.classList.contains('show')) {
                parametricDropdown.style.display = 'none';
            }
        }, 300);
    }
}

function selectSolverType(type) {
    currentSolverMode = type;
    
    if (type === 'parametric') {
        switchToParametricInput();
    } else if (type === 'polar') {
        switchToPolarInput();
    } else {
        switchToSingleInput();
        
        const input = document.getElementById('main-input');
        if (input) {
            input.placeholder = 'Enter your regular integral';
        }
        
        validateMainInput();
    }
    
    hideDropdown();
    
    console.log(`Selected solver mode: ${type}`);
}

function switchToSingleInput() {
    const singleContainer = document.querySelector('.input-container');
    if (singleContainer) {
        singleContainer.classList.remove('parametric-mode');
    }
    
    const splitContainer = document.querySelector('.split-input-container');
    if (splitContainer) {
        splitContainer.remove();
    }
    
    const input = document.getElementById('main-input');
    if (input) {
        input.focus();
        setupInputHandlers();
    }
}

function switchToParametricInput() {
    const singleContainer = document.querySelector('.input-container');
    if (singleContainer) {
        singleContainer.classList.add('parametric-mode');
    }
    
    const existingSplit = document.querySelector('.split-input-container');
    if (existingSplit) {
        existingSplit.remove();
    }
    
    const splitContainer = document.createElement('div');
    splitContainer.className = 'split-input-container';
    splitContainer.style.position = 'relative';
    
    splitContainer.innerHTML = `
        <div class="left-input-wrapper">
            <label class="input-label" for="x-param-input">x(t) =</label>
            <textarea 
                id="x-param-input" 
                class="parametric-input clickable-input"
                placeholder="Enter x(t)"
                rows="1"
            ></textarea>
            <span class="parametric-error-msg" id="x-param-error"></span>
        </div>
        <div class="right-input-wrapper">
            <label class="input-label" for="y-param-input">y(t) =</label>
            <div class="input-with-button">
                <textarea 
                    id="y-param-input" 
                    class="parametric-input clickable-input"
                    placeholder="Enter y(t)"
                    rows="1"
                ></textarea>
                <button class="send-btn" id="param-send-btn" onclick="solveIntegral()">
                    <img src="/static/images/arrow.png" alt="Send" id="arrow">
                </button>
            </div>
            <span class="parametric-error-msg" id="y-param-error"></span>
        </div>
    `;
    
    if (singleContainer && singleContainer.parentNode) {
        singleContainer.parentNode.insertBefore(splitContainer, singleContainer.nextSibling);
    }
    
    setTimeout(() => {
        splitContainer.classList.add('active');
    }, 10);
    
    setupParametricValidation();
    setupParametricClickHandlers();
}

function switchToPolarInput() {
    const singleContainer = document.querySelector('.input-container');
    if (singleContainer) {
        singleContainer.classList.add('parametric-mode');
    }
    
    const existingSplit = document.querySelector('.split-input-container');
    if (existingSplit) {
        existingSplit.remove();
    }
    
    const splitContainer = document.createElement('div');
    splitContainer.className = 'split-input-container';
    splitContainer.style.position = 'relative';
    
    splitContainer.innerHTML = `
        <div class="left-input-wrapper">
            <label class="input-label" for="inner-polar-input">Inner function =</label>
            <textarea 
                id="inner-polar-input" 
                class="parametric-input clickable-input"
                placeholder="Enter inner function"
                rows="1"
            ></textarea>
            <span class="parametric-error-msg" id="inner-polar-error"></span>
        </div>
        <div class="right-input-wrapper">
            <label class="input-label" for="outer-polar-input">Outer function =</label>
            <div class="input-with-button">
                <textarea 
                    id="outer-polar-input" 
                    class="parametric-input clickable-input"
                    placeholder="Enter outer function"
                    rows="1"
                ></textarea>
                <button class="send-btn" id="polar-send-btn" onclick="solveIntegral()">
                    <img src="/static/images/arrow.png" alt="Send" id="arrow">
                </button>
            </div>
            <span class="parametric-error-msg" id="outer-polar-error"></span>
        </div>
    `;
    
    if (singleContainer && singleContainer.parentNode) {
        singleContainer.parentNode.insertBefore(splitContainer, singleContainer.nextSibling);
    }
    
    setTimeout(() => {
        splitContainer.classList.add('active');
    }, 10);
    
    setupPolarValidation();
    setupPolarClickHandlers();
}

function setupParametricValidation() {
    const xInput = document.getElementById('x-param-input');
    const yInput = document.getElementById('y-param-input');
    const sendBtn = document.getElementById('param-send-btn');
    
    if (!xInput || !yInput || !sendBtn) return;
    
    [xInput, yInput].forEach(input => {
        input.addEventListener('input', function() {
            this.style.height = '24px';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';

            if (this.value.trim()) {
                hideDropdown();
            }
            validateParametricInputs();
        });

        
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
        
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const xValue = xInput.value.trim();
                const yValue = yInput.value.trim();
                if (xValue && yValue) {
                    solveIntegral();
                }
            }
        });
    });
    
    sendBtn.disabled = true;
    sendBtn.style.opacity = '0.6';
    
    validateParametricInputs();
}

function setupPolarValidation() {
    const innerInput = document.getElementById('inner-polar-input');
    const outerInput = document.getElementById('outer-polar-input');
    const sendBtn = document.getElementById('polar-send-btn');
    
    if (!innerInput || !outerInput || !sendBtn) return;
    
    [innerInput, outerInput].forEach(input => {
        input.addEventListener('input', function() {
            this.style.height = '24px';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';

            if (this.value.trim()) {
                hideDropdown();
            }
            validatePolarInputs();
        });
        
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
        
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const innerValue = innerInput.value.trim();
                const outerValue = outerInput.value.trim();
                if (innerValue &&outerValue) {
                    solveIntegral();
                }
            }
        });
    });
    
    sendBtn.disabled = true;
    sendBtn.style.opacity = '0.6';
    
    validatePolarInputs();
}

function validateParametricInputs() {
    const xInput = document.getElementById('x-param-input');
    const yInput = document.getElementById('y-param-input');
    const sendBtn = document.getElementById('param-send-btn');
    
    if (!xInput || !yInput || !sendBtn) return;
    
    const xValue = xInput.value.trim();
    const yValue = yInput.value.trim();
    
    const bothHaveContent = xValue !== '' && yValue !== '';
    
    sendBtn.disabled = !bothHaveContent;
    if (bothHaveContent) {
        sendBtn.style.opacity = '1';
        sendBtn.classList.add('has-input');
    } else {
        sendBtn.style.opacity = '0.6';
        sendBtn.classList.remove('has-input');
    }
}

function validatePolarInputs() {
    const innerInput = document.getElementById('inner-polar-input');
    const outerInput = document.getElementById('outer-polar-input');
    const sendBtn = document.getElementById('polar-send-btn');
    
    if (!innerInput || !outerInput || !sendBtn) return;
    
    const innerValue = innerInput.value.trim();
    const outerValue = outerInput.value.trim();
    
    const bothHaveContent = innerValue !== '' && outerValue !== '';
    
    sendBtn.disabled = !bothHaveContent;
    if (bothHaveContent) {
        sendBtn.style.opacity = '1';
        sendBtn.classList.add('has-input');
    } else {
        sendBtn.style.opacity = '0.6';
        sendBtn.classList.remove('has-input');
    }
}

function setupParametricClickHandlers() {
    const xInput = document.getElementById('x-param-input');
    const yInput = document.getElementById('y-param-input');
    
    if (xInput && yInput) {
        [xInput, yInput].forEach(input => {
            input.addEventListener('click', function(e) {
                if (e.target === this && this.selectionStart === this.selectionEnd) {
                    showParametricDropdown(this);
                }
            });
        });
    }
}

function setupPolarClickHandlers() {
    const innerInput = document.getElementById('inner-polar-input');
    const outerInput = document.getElementById('outer-polar-input');
    
    if (innerInput && outerInput) {
        [innerInput, outerInput].forEach(input => {
            input.addEventListener('click', function(e) {
                if (e.target === this && this.selectionStart === this.selectionEnd) {
                    showParametricDropdown(this);
                }
            });
        });
    }
}

function showParametricDropdown(clickedInput) {
    let dropdown = document.getElementById('parametric-solver-dropdown');
    
    if (!dropdown) {
        dropdown = createParametricDropdown();
    }
    
    dropdown.style.position = 'absolute';
    dropdown.style.bottom = '100%';
    dropdown.style.left = '0';
    dropdown.style.right = '0';
    dropdown.style.marginBottom = '8px';
    dropdown.style.display = 'grid';
    
    clickedInput.classList.add('dropdown-active');
    
    setTimeout(() => {
        dropdown.classList.add('show');
    }, 10);
}

function createParametricDropdown() {
    const dropdown = document.createElement('div');
    dropdown.id = 'parametric-solver-dropdown';
    dropdown.className = 'solver-type-dropdown';
    
    dropdown.innerHTML = `
        <div class="example-prompt" onclick="switchSolverType('integral')">
            <h4>Regular</h4>
            <p>ex. ∫ x² dx</p>
        </div>
        <div class="example-prompt" onclick="switchSolverType('parametric')">
            <h4>Parametric</h4>
            <p>ex. x(t)=t, y(t)=t²</p>
        </div>
        <div class="example-prompt" onclick="switchSolverType('polar')">
            <h4>Polar</h4>
            <p>ex. r1(θ) = 2 + sin(θ), r2(θ) = 5cos(θ)</p>
        </div>
    `;
    
    const splitContainer = document.querySelector('.split-input-container');
    if (splitContainer) {
        splitContainer.style.position = 'relative';
        splitContainer.appendChild(dropdown);
    }
    
    return dropdown;
}

function createPolarDesmos(containerId, innerFunction, outerFunction) {
    console.log(`Creating Desmos graph for: ${containerId}`);
    console.log('Original functions - Inner:', innerFunction, 'Outer:', outerFunction);
    
    if (typeof Desmos === 'undefined') {
        console.error('Desmos API not loaded');
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<p style="color: red; text-align: center; padding: 20px;">Desmos API not loaded. Please refresh the page.</p>';
        }
        return null;
    }
    
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with id ${containerId} not found`);
        return null;
    }
    
    try {
        const calculator = Desmos.GraphingCalculator(container, {
            keypad: false,
            graphpaper: true,
            expressions: true,
            settingsMenu: false,
            zoomButtons: true,
            expressionsTopbar: false
        });
        
        calculator.setMathBounds({
            left: -10,
            right: 10,
            bottom: -10,
            top: 10
        });

        const outerLatex = convertToDesmosFormat(outerFunction);
        console.log('Converted outer function for Desmos:', outerLatex);

        calculator.setExpression({
            id: 'outer',
            latex: `r\\le${outerLatex}\\left\\{0\\le\\theta\\le2\\pi\\right\\}`,
            color: Desmos.Colors.BLUE,
            lineWidth: 2
        });

        if (innerFunction && innerFunction.trim()) {
            const innerLatex = convertToDesmosFormat(innerFunction);
            console.log('Converted inner function for Desmos:', innerLatex);
            
            calculator.setExpression({
                id: 'inner',
                latex: `r\\ge${innerLatex}\\left\\{0\\le\\theta\\le2\\pi\\right\\}`,
                color: Desmos.Colors.RED,
                lineWidth: 2
            });
        }

        
        console.log('Desmos graph created successfully');
        return calculator;
        
    } catch (error) {
        console.error('Error creating Desmos graph:', error);
        container.innerHTML = `<p style="color: red; text-align: center; padding: 20px;">Error creating graph: ${error.message}</p>`;
        return null;
    }
}

function convertToDesmosFormat(expression) {
    if (!expression || expression.trim() === '') return '0';
    
    console.log('Converting expression:', expression);
    
    let result = expression
        .replace(/\bsin\b/g, '\\sin')
        .replace(/\bcos\b/g, '\\cos')
        .replace(/\btan\b/g, '\\tan')
        .replace(/\bpi\b/g, '\\pi')
        .replace(/\btheta\b/gi, '\\theta')
        .replace(/\b[tx]\b/g, '\\theta')
        .replace(/\*/g, '');
    
    console.log('Converted to Desmos format:', result);
    return result;
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json'
    };
}

function hideWelcomeScreen() {
    const welcomeScreen = document.getElementById('welcome-screen');
    const messagesContainer = document.getElementById('messages-container');
    const conversationArea = document.getElementById('conversation-area');
    
    if (welcomeScreen) welcomeScreen.style.display = 'none';
    if (messagesContainer) messagesContainer.style.display = 'block';
    if (conversationArea) conversationArea.classList.add('has-messages');
}

function addMessage(content, isUser = false, isLoading = false) {
    hideWelcomeScreen();
    
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) {
        console.error('Messages container not found');
        return null;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper';

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isUser ? (authManager.getUser().firstName[0] || 'U') : 'E';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    if (isLoading) {
        messageContent.innerHTML = `
            <div class="loading">
                <span>Solving</span>
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        `;
    } else {
        messageContent.innerHTML = content;
    }

    if (isUser) {
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(avatar);
    } else {
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
    }

    wrapper.appendChild(messageDiv);
    messagesContainer.appendChild(wrapper);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    if (!isLoading) {
        renderLatex(messageDiv);
    }

    return messageDiv;
}

function scrollToMessage(messageElement) {
    const conversationArea = document.getElementById('conversation-area');
    const messagesContainer = document.getElementById('messages-container');
    
    if (!conversationArea || !messageElement) return;
    
    const messageTop = messageElement.offsetTop;
    const containerTop = messagesContainer.offsetTop;
    
    conversationArea.scrollTo({
        top: messageTop - containerTop,
        behavior: 'smooth'
    });
}

async function solveIntegral() {
    let integral = '';
    let inputsToClear = [];
    let polarInnerValue = '';
    let polarOuterValue = '';
    
    if (currentSolverMode === 'parametric') {
        const xInput = document.getElementById('x-param-input');
        const yInput = document.getElementById('y-param-input');
        
        if (!xInput || !yInput) return;
        
        const xValue = xInput.value.trim();
        const yValue = yInput.value.trim();
        
        if (!xValue || !yValue) {
            addMessage('⚠️ Please enter both x(t) and y(t) expressions', false);
            return;
        }
        
        integral = `x(t) = ${xValue}, y(t) = ${yValue}`;
        inputsToClear = [xInput, yInput];
        
    } else if (currentSolverMode === 'polar') {
        const innerInput = document.getElementById('inner-polar-input');
        const outerInput = document.getElementById('outer-polar-input');
        
        if (!innerInput || !outerInput) return;
        
        const innerValue = innerInput.value.trim();
        const outerValue = outerInput.value.trim();
        
        polarInnerValue = innerValue;
        polarOuterValue = outerValue;
        
        if (!innerValue || !outerValue) {
            addMessage('⚠️ Please enter both inner and outer functions', false);
            return;
        }
        integral=`${innerValue}, ${outerValue}`;
        inputsToClear = [innerInput, outerInput];
        
    } else {
        const input = document.getElementById('main-input');
        if (!input) return;
        
        integral = input.value.trim();
        inputsToClear = [input];
        
        if (!integral) return;
        
        if (!currentSolverMode) {
            return;
        }
    }

    let userDisplayText = integral;

    if (currentSolverMode === 'parametric') {
        userDisplayText = integral;
    } else if (currentSolverMode === 'polar') {
        if (integral.includes(',')) {
            const parts = integral.split(',');
            const innerFunc = parts[0].trim();
            const outerFunc = parts[1].trim();
            userDisplayText = `\\text{Inner: } r_1(\\theta) = ${innerFunc}, \\quad \\text{Outer: } r_2(\\theta) = ${outerFunc}`;
        } else {
            userDisplayText = `r(\\theta) = ${integral}`;
        }
    } else {
        userDisplayText = `∫ ${integral} dx`;
    }

    userDisplayText = userDisplayText.replace(/(?<!\\)theta/gi, '\\theta');

    const userMessageContent = `<div class="latex-input">$$${userDisplayText}$$</div>`;
    const userMessage = addMessage(userMessageContent, true);

    setTimeout(() => {
        scrollToMessage(userMessage);
    }, 100);
    
    inputsToClear.forEach(inputElement => {
        inputElement.value = '';
        inputElement.style.height = '24px';
        inputElement.dispatchEvent(new Event('input'));
    });

    const loadingMessage = addMessage('', false, true);

    try {
        const response = await fetch('/api/solver/solve', {
            method: 'POST',
            headers: getAuthHeaders(),
            credentials: 'include',
            body: JSON.stringify({ 
                integral: integral,
                solverType: currentSolverMode
            })
        });

        const result = await response.json();

        if (loadingMessage) {
            loadingMessage.remove();
        }

        if (response.ok) {
            const graphId = `desmos-graph-${Date.now()}`;
            
            const solutionHTML = `
                <div class="solution-display">
                    <div class="solution-header">
                        <span>📊</span>
                        ${currentSolverMode.charAt(0).toUpperCase() + currentSolverMode.slice(1)} Solution
                    </div>
                    <div class="solution-content">
                        <p><strong>Problem:</strong></p>
                        <div class="math-content">${result.input_latex || result.input}</div>
                        
                        <p><strong>Solution:</strong></p>
                        <div class="latex-output">${currentSolverMode === 'polar' ? 
                            `<div class="plain-output">${result.solution}</div>` : 
                            `<div class="latex-output">${result.solution_latex || result.solution}</div>`
                        }</div>
                    </div>
                    ${currentSolverMode === 'polar' ? `
                        <div class="desmos-container" id="${graphId}" style="width: 100%; height: 400px; margin: 16px 0; border: 1px solid #ddd; border-radius: 8px;"></div>
                    ` : ''}
                    ${result.steps && result.steps.length > 0 ? `
                        <div class="solution-steps">
                            <h4>Step-by-step Solution:</h4>
                            <ol>
                                ${result.steps.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        </div>
                    ` : ''}
                </div>
            `;
            
            addMessage(solutionHTML, false);
            
            if (currentSolverMode === 'polar') {
                setTimeout(() => {
                    console.log('Attempting to create Desmos graph...');
                    console.log('Graph container ID:', graphId);
                    console.log('Polar values - Inner:', polarInnerValue, 'Outer:', polarOuterValue);
                    
                    setTimeout(() => {
                        const container = document.getElementById(graphId);
                        if (!container) {
                            console.error(`Cannot find Desmos container with ID: ${graphId}`);
                            return;
                        }
                        
                        if (typeof Desmos === 'undefined') {
                            console.error('Desmos API is not loaded. Make sure you have the Desmos script tag in your HTML.');
                            container.innerHTML = '<p style="color: red; text-align: center; padding: 20px;">Desmos API not loaded. Please check your internet connection and refresh the page.</p>';
                            return;
                        }
                        
                        try {
                            createPolarDesmos(graphId, polarInnerValue, polarOuterValue);
                        } catch (error) {
                            console.error('Error creating Desmos graph:', error);
                            container.innerHTML = '<p style="color: red; text-align: center; padding: 20px;">Error loading graph. Please try again.</p>';
                        }
                    }, 200);
                }, 300);
            }
            
            window.currentProblem = result;
            
            currentConversation.push({
                input: integral,
                result: result,
                solverType: currentSolverMode,
                timestamp: new Date()
            });

        } else {
            addMessage(`⚠️ Error: ${result.error}`, false);
        }
    } catch (error) {
        if (loadingMessage) {
            loadingMessage.remove();
        }
        addMessage('⌘ Network error. Please try again.', false);
        console.error('Solver error:', error);
    }
}

function startPractice() {
    isPracticeMode = true;
    
    currentSolverMode = null;
    currentConversation = [];
    window.currentPracticeType = null;
    window.currentPracticeDifficulty = null;
    currentPracticeTypeMessage = null;
    currentPracticeDifficultyMessage = null;
    selectedPracticeType = null;
    selectedPracticeDifficulty = null;
    
    const splitContainer = document.querySelector('.split-input-container');
    if (splitContainer) {
        splitContainer.remove();
    }
    
    switchToSingleInput();
    
    const messagesContainer = document.getElementById('messages-container');
    const welcomeScreen = document.getElementById('welcome-screen');
    const conversationArea = document.getElementById('conversation-area');
    
    if (messagesContainer) messagesContainer.innerHTML = '';
    if (welcomeScreen) welcomeScreen.style.display = 'none';
    if (messagesContainer) messagesContainer.style.display = 'block';
    if (conversationArea) conversationArea.classList.add('has-messages');
    
    const input = document.getElementById('main-input');
    if (input) {
        input.value = '';
        input.placeholder = 'Enter your answer or [give up]';
        input.style.height = '24px';
    }
    
    if (conversationArea) {
        conversationArea.scrollTop = 0;
    }
    
    const practiceMessageHTML = `
        <div class="practice-setup">
            <div class="practice-header">
                <span>📚</span>
                Practice Mode
            </div>
            <div class="practice-content">
                <p>Select a problem type to get started:</p>
            </div>
            <div class="practice-dropdown" id="practice-type-dropdown">
                <div class="example-prompt" onclick="selectPracticeType('integral')">
                    <h4>Regular</h4>
                    <p>Standard integration problems</p>
                </div>
                <div class="example-prompt" onclick="selectPracticeType('parametric')">
                    <h4>Parametric</h4>
                    <p>Parametric equation problems</p>
                </div>
                <div class="example-prompt" onclick="selectPracticeType('polar')">
                    <h4>Polar</h4>
                    <p>Polar coordinate problems</p>
                </div>
            </div>
        </div>
    `;
    
    addMessage(practiceMessageHTML, false);
    setTimeout(() => {
        validatePracticeInput();
    }, 100);
}

function selectPracticeType(type) {
    window.currentPracticeType = type;
    selectedPracticeType = type;
    const input = document.getElementById('main-input');
    if (input) {
        input.placeholder = 'Enter your answer or [give up]';
    }
    
    const typeDropdown = document.getElementById('practice-type-dropdown');
    if (typeDropdown) {
        const allOptions = typeDropdown.querySelectorAll('.example-prompt');
        allOptions.forEach(option => option.classList.remove('selected'));
        
        const selectedOption = Array.from(allOptions).find(option => {
            const h4 = option.querySelector('h4');
            return h4 && h4.textContent === (type === 'integral' ? 'Regular' : type === 'parametric' ? 'Parametric' : 'Polar');
        });
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
    }
    
    
    
    if (currentPracticeDifficultyMessage) {
        currentPracticeDifficultyMessage.remove();
        currentPracticeDifficultyMessage = null;
    }
    
    const difficultyMessageHTML = `
        <div class="practice-setup">
            <div class="practice-header">
                <span>⚡</span>
                Select Difficulty
            </div>
            <div class="practice-content">
                <p>Choose your difficulty level:</p>
            </div>
            <div class="practice-dropdown" id="practice-difficulty-dropdown">
                <div class="example-prompt" onclick="selectPracticeDifficulty(1)">
                    <h4>Level 1</h4>
                    <p>Easiest</p>
                </div>
                <div class="example-prompt" onclick="selectPracticeDifficulty(2)">
                    <h4>Level 2</h4>
                    <p>Easy</p>
                </div>
                <div class="example-prompt" onclick="selectPracticeDifficulty(3)">
                    <h4>Level 3</h4>
                    <p>Medium</p>
                </div>
                <div class="example-prompt" onclick="selectPracticeDifficulty(4)">
                    <h4>Level 4</h4>
                    <p>Hardest</p>
                </div>
            </div>
        </div>
    `;
    
    currentPracticeDifficultyMessage = addMessage(difficultyMessageHTML, false);
    
    setTimeout(() => {
        scrollToMessage(currentPracticeDifficultyMessage);
        validatePracticeInput();
    }, 100);
}

function selectPracticeDifficulty(level) {
    window.currentPracticeDifficulty = level;
    selectedPracticeDifficulty = level;
    
    const difficultyDropdown = document.getElementById('practice-difficulty-dropdown');
    if (difficultyDropdown) {
        const allOptions = difficultyDropdown.querySelectorAll('.example-prompt');
        allOptions.forEach(option => {
            option.classList.remove('selected');
            option.classList.add('disabled');
            option.style.cursor = 'not-allowed';
            option.onclick = null;
        });
        
        const selectedOption = Array.from(allOptions).find(option => {
            const h4 = option.querySelector('h4');
            return h4 && h4.textContent === `Level ${level}`;
        });
        if (selectedOption) {
            selectedOption.classList.add('selected');
        }
    }
    
    const typeDropdown = document.getElementById('practice-type-dropdown');
    if (typeDropdown) {
        const allTypeOptions = typeDropdown.querySelectorAll('.example-prompt');
        allTypeOptions.forEach(option => {
            option.classList.add('disabled');
            option.style.cursor = 'not-allowed';
            option.onclick = null;
        });
    }
    
    const input = document.getElementById('main-input');
    if (input) {
        input.placeholder = 'Enter your answer or [give up]';
    }
    
    generatePracticeProblem(window.currentPracticeType, level);
    setTimeout(() => {
        validatePracticeInput();
    }, 100);
}

async function generatePracticeProblem(type, difficulty) {
    let endpoint;
    if (type === 'parametric') endpoint = `/api/practice/parametric/problems/${difficulty}`;
    else if (type === 'polar') endpoint = `/api/practice/polar/problems/${difficulty}`;
    else endpoint = `/api/practice/problems/${difficulty}`;
    
    try {
        const response = await fetch(endpoint, { headers: getAuthHeaders() });
        if (!response.ok) {
            addMessage(`Error: ${(await response.json()).error || 'Failed to get practice problem'}`, false);
            return;
        }
        
        const result = await response.json();
        window.currentPracticeProblem = result.problem;
        
        let practiceHTML;
        if (type === 'parametric') {
            practiceHTML = `
                <div class="practice-problem">
                    <div class="practice-content">
                        <p><strong>Given:</strong></p>
                        <div class="latex-output">$$x(t) = ${result.problem.x_t_latex.replace(/\$\$/g, '')}$$</div>
                        <div class="latex-output">$$y(t) = ${result.problem.y_t_latex.replace(/\$\$/g, '')}$$</div>
                        <p><strong>Find:</strong> $$\\int y \\, dx$$</p>
                        <p style="font-size: 0.9em; color: #666; margin-top: 8px;"><em>Express your answer in terms of t</em></p>
                    </div>
                </div>
            `;
        } else if (type === 'polar') {
            practiceHTML = `
                <div class="practice-problem">
                    <div class="practice-content">
                        <p><strong>Given polar functions:</strong></p>
                        <div class="latex-output">$$\\text{Inner: } r_1(\\theta) = ${result.problem.inner_function_latex.replace(/\$\$/g, '')}$$</div>
                        <div class="latex-output">$$\\text{Outer: } r_2(\\theta) = ${result.problem.outer_function_latex.replace(/\$\$/g, '')}$$</div>
                        <p>Bounds: $$\\theta \\in [${result.problem.lower_bound_display || result.problem.lower_bound}, ${result.problem.upper_bound_display || result.problem.upper_bound}]$$</p>
                        <p><strong>Find:</strong> Area of the region between the inner and outer curves</p>
                        <p style="font-size: 0.9em; color: #666; margin-top: 8px;"><em>Enter your answer as a decimal rounded to three decimal places</em></p>
                    </div>
                </div>
            `;
        } else {
            practiceHTML = `
                <div class="practice-problem">
                    <div class="practice-content">
                        <p><strong>Solve:</strong></p>
                        <div class="latex-output">${result.problem.problem_latex}</div>
                    </div>
                </div>
            `;
        }
        
        const problemMessage = addMessage(practiceHTML, false);
        setTimeout(() => {
            scrollToMessage(problemMessage);
        }, 150);
        
        const input = document.getElementById('main-input');
        if (input) {
            input.placeholder = 'Enter your answer or [give up]';
            input.focus();
        }
    } catch (error) {
        console.error('Practice problem error:', error);
        addMessage('Network error. Please try again.', false);
    }
}

async function handlePracticeSubmission() {
    const input = document.getElementById('main-input');
    const userAnswer = input.value.trim();
    if (!userAnswer) return;
    
    if (userAnswer.toLowerCase() !== 'give up') addMessage(userAnswer, true);
    input.value = '';
    input.style.height = '24px';
    
    if (userAnswer.toLowerCase() === 'give up') {
        const loadingMessage = addMessage('', false, true);
        try {
            const response = await fetch('/api/practice/give-up', {
                method: 'POST', 
                headers: getAuthHeaders(),
                credentials: 'include',
                body: JSON.stringify({ 
                    problem_id: window.currentPracticeProblem.id, 
                    problem_type: window.currentPracticeType 
                })
            });
            const result = await response.json();
            loadingMessage.remove();
            
            if (response.ok) {
                let solutionDisplay;
                if (window.currentPracticeType === 'polar') {
                    solutionDisplay = `<p><strong>Solution:</strong> ${result.correct_answer}</p>`;
                } else {
                    solutionDisplay = `<p><strong>Solution:</strong></p><div class="latex-output">${result.correct_answer_latex}</div>`;
                }
                
                const solutionMessage = addMessage(`
                    <div class="practice-response">
                        <div class="practice-header"><span>💡</span>Solution</div>
                        <div class="practice-content">${solutionDisplay}</div>
                    </div>
                `, false);
                setTimeout(() => scrollToMessage(solutionMessage), 100);
                
                if (['integral', 'parametric', 'polar'].includes(window.currentPracticeType)) showNextProblemButton();
                clearPracticeState();
            } else {
                addMessage(`Error: ${result.error}`, false);
            }
        } catch (error) {
            loadingMessage.remove();
            addMessage('Network error. Please try again.', false);
        }
        return;
    }
    
    const loadingMessage = addMessage('', false, true);
    let endpoint;
    if (window.currentPracticeType === 'parametric') endpoint = '/api/practice/parametric/submit-answer';
    else if (window.currentPracticeType === 'polar') endpoint = '/api/practice/polar/submit-answer';
    else endpoint = '/api/practice/submit-answer';
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST', 
            headers: getAuthHeaders(),
            credentials: 'include',
            body: JSON.stringify({ 
                problem_id: window.currentPracticeProblem.id, 
                answer: userAnswer 
            })
        });
        const result = await response.json();
        loadingMessage.remove();
        
        if (response.ok) {
            if (result.correct) {
                const correctMessage = addMessage(`
                    <div class="practice-response correct">
                        <div class="practice-header"><span>✅</span>Correct!</div>
                    </div>
                `, false);
                setTimeout(() => scrollToMessage(correctMessage), 100);
                if (['integral', 'parametric', 'polar'].includes(window.currentPracticeType)) showNextProblemButton();
                clearPracticeState();
            } else {
                const incorrectMessage = addMessage(`
                    <div class="practice-response incorrect">
                        <div class="practice-header"><span>❌</span>Incorrect</div>
                        <div class="practice-content"><p>Try again or type "give up" to see the solution.</p></div>
                    </div>
                `, false);
                setTimeout(() => scrollToMessage(incorrectMessage), 100);
                const inp = document.getElementById('main-input');
                if (inp) inp.focus();
            }
        } else {
            addMessage(`Error: ${result.error}`, false);
        }
    } catch (error) {
        loadingMessage.remove();
        addMessage('Network error. Please try again.', false);
    }
}

async function saveProblem(input, solution, steps, solverType) {
    try {
        const response = await fetch('/api/solver/save', {
            method: 'POST',
            headers: getAuthHeaders(),
            credentials: 'include',
            body: JSON.stringify({
                input: input,
                solution: solution,
                steps: steps,
                solverType: solverType || 'integral'
            })
        });

        const result = await response.json();

        if (response.ok) {
            addMessage('✅ Problem saved to your history!', false);
            loadHistory();
        } else {
            addMessage(`⌘ Failed to save: ${result.error}`, false);
        }
    } catch (error) {
        addMessage('⌘ Failed to save problem', false);
        console.error('Save error:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/api/solver/history', {
            headers: getAuthHeaders(),
            credentials: 'include'
        });

        if (response.ok) {
            const result = await response.json();
            displayHistory(result.problems);
        }
    } catch (error) {
        console.error('History load error:', error);
    }
}

function displayHistory(problems) {
    const problemList = document.getElementById('recent-problems');
    if (!problemList) return;
    
    if (!problems || problems.length === 0) {
        problemList.innerHTML = `
            <div class="problem-item">
                <div class="problem-preview">No recent problems</div>
                <div class="problem-date">Start solving to see history</div>
            </div>
        `;
        return;
    }

    problemList.innerHTML = problems.slice(0, 10).map(problem => {
        let displayText = problem.input_latex || problem.input;
        
        let solutionForLoad = problem.solver_type === 'polar' ? 
            encodeURIComponent(problem.solution) : 
            encodeURIComponent(problem.solution_latex || problem.solution);
        
        return `
            <div class="problem-item" 
                onclick="loadProblem('${encodeURIComponent(problem.input)}', '${encodeURIComponent(problem.solution)}', '${encodeURIComponent(problem.input_latex || '')}', '${solutionForLoad}', '${problem.solver_type || 'integral'}')">
                <div class="problem-preview">${displayText}</div>
                <div class="problem-date">${new Date(problem.created_at).toLocaleDateString()}</div>
            </div>
        `;
    }).join('');
    
    if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(problemList, {
            delimiters: [
                {left: "$$", right: "$$", display: true},
                {left: "$", right: "$", display: false}
            ],
            throwOnError: false
        });
    }
}

function loadProblem(input, solution, inputLatex, solutionLatex, solverType = 'integral') {
    isPracticeMode = false;
    
    input = decodeURIComponent(input);
    solution = decodeURIComponent(solution);
    inputLatex = decodeURIComponent(inputLatex);
    solutionLatex = decodeURIComponent(solutionLatex);

    const messagesContainer = document.getElementById('messages-container');
    if (messagesContainer) {
        messagesContainer.innerHTML = '';
    }
    hideWelcomeScreen();
    
    const inputElement = document.getElementById('main-input');
    if (inputElement) {
        inputElement.placeholder = 'Select integral option';
    }
    
    let displayInput = input;
    if (solverType === 'parametric') {
        displayInput = input;
    } else if (solverType === 'polar') {
        displayInput = input;
    } else {
        displayInput = `∫ ${input} dx`;
    }

    displayInput = displayInput.replace(/theta/gi, '\\theta');

    const userMessageContent = `<div class="latex-input">$$${displayInput}$$</div>`;
    const userMsgElement = addMessage(userMessageContent, true);
    if (userMsgElement) {
        renderLatex(userMsgElement);
    }
    
    const solutionHTML = `
        <div class="solution-display">
            <div class="solution-header">
                <span>📊</span>
                ${solverType.charAt(0).toUpperCase() + solverType.slice(1)} Solution
            </div>
            <div class="solution-content">
                <p><strong>Problem:</strong></p>
                <div class="math-content">${inputLatex || displayInput}</div>
                
                <p><strong>Solution:</strong></p>
                ${solverType === 'polar' ? 
                    `<div class="latex-output">${solution}</div>` : 
                    `<div class="latex-output">${solutionLatex || solution}</div>`
                }
            </div>
        </div>
    `;
    const solutionMsgElement = addMessage(solutionHTML, false);
    if (solutionMsgElement) {
        renderLatex(solutionMsgElement);
    }
}

function startNewProblem() {
    isPracticeMode = false;
    
    currentSolverMode = null;
    currentConversation = [];
    window.currentPracticeType = null;
    window.currentPracticeDifficulty = null;
    currentPracticeTypeMessage = null;
    currentPracticeDifficultyMessage = null;
    selectedPracticeType = null;
    selectedPracticeDifficulty = null;
    
    const splitContainer = document.querySelector('.split-input-container');
    if (splitContainer) {
        splitContainer.remove();
    }
    
    switchToSingleInput();
    
    const messagesContainer = document.getElementById('messages-container');
    const welcomeScreen = document.getElementById('welcome-screen');
    const conversationArea = document.getElementById('conversation-area');
    
    if (messagesContainer) messagesContainer.innerHTML = '';
    if (welcomeScreen) welcomeScreen.style.display = 'flex';
    if (messagesContainer) messagesContainer.style.display = 'none';
    if (conversationArea) conversationArea.classList.remove('has-messages');
    
    const input = document.getElementById('main-input');
    if (input) {
        input.placeholder = 'Select integral option';
        input.value = '';
        input.style.height = '24px';
    }
    
    if (conversationArea) {
        conversationArea.scrollTop = 0;
    }
    
    setTimeout(() => {
        const input = document.getElementById('main-input');
        if (input) {
            input.placeholder = 'Select integral option';
        }
        validateMainInput();
    }, 150);
}

function useExample(example) {
    const input = document.getElementById('main-input');
    const sendBtn = document.getElementById('send-btn');
    
    if (input && sendBtn) {
        input.value = example;
        sendBtn.disabled = false;
        sendBtn.style.background = '#00A1FF';
        sendBtn.style.opacity = '1';
        input.focus();
    }
}

function switchSolverType(newType) {
    if (currentSolverMode === newType) {
        hideDropdown();
        return;
    }
    
    console.log(`Switching solver mode from ${currentSolverMode} to ${newType}`);
    
    const mainInput = document.getElementById('main-input');
    const xInput = document.getElementById('x-param-input');
    const yInput = document.getElementById('y-param-input');
    const innerInput = document.getElementById('inner-polar-input');
    const outerInput = document.getElementById('outer-polar-input');
    
    if (mainInput) {
        mainInput.value = '';
        mainInput.style.height = '24px';
    }
    if (xInput) {
        xInput.value = '';
        xInput.style.height = '24px';
    }
    if (yInput) {
        yInput.value = '';
        yInput.style.height = '24px';
    }
    if (innerInput) {
        innerInput.value = '';
        innerInput.style.height = '24px';
    }
    if (outerInput) {
        outerInput.value = '';
        outerInput.style.height = '24px';
    }
    
    clearAllValidationErrors();
    
    currentSolverMode = newType;
    
    if (newType === 'parametric') {
        switchToParametricInput();
    } else if (newType === 'polar') {
        switchToPolarInput();
    } else {
        switchToSingleInput();
        
        const input = document.getElementById('main-input');
        if (input) {
            const placeholders = {
                'integral': 'Enter your regular integral'
            };
            input.placeholder = placeholders[newType] || 'Enter your problem';
            
            setTimeout(() => {
                input.focus();
            }, 100);
        }
    }
    
    hideDropdown();
    
    if (newType === 'parametric') {
        setTimeout(() => {
            validateParametricInputs();
        }, 100);
    } else if (newType === 'polar') {
        setTimeout(() => {
            validatePolarInputs();
        }, 100);
    } else {
        setTimeout(() => {
            validateMainInput();
        }, 100);
    }
}

function clearAllValidationErrors() {
    const mainInput = document.getElementById('main-input');
    const inputContainer = document.querySelector('.input-container');
    
    if (mainInput) {
        mainInput.classList.remove('validation-error');
    }
    if (inputContainer) {
        inputContainer.classList.remove('validation-error');
        const existingError = inputContainer.querySelector('.input-error-msg');
        if (existingError) {
            existingError.remove();
        }
    }
}

function showRegularInputError(message) {
    const input = document.getElementById('main-input');
    const inputContainer = document.querySelector('.input-container');
    
    if (!input || !inputContainer) return;
    
    input.classList.add('validation-error');
    inputContainer.classList.add('validation-error');
    
    const existingError = inputContainer.querySelector('.input-error-msg');
    if (existingError) {
        existingError.remove();
    }
    
    const errorSpan = document.createElement('span');
    errorSpan.className = 'input-error-msg';
    errorSpan.textContent = message;
    inputContainer.appendChild(errorSpan);
}

function clearRegularInputError() {
    const input = document.getElementById('main-input');
    const inputContainer = document.querySelector('.input-container');
    
    if (!input || !inputContainer) return;
    
    input.classList.remove('validation-error');
    inputContainer.classList.remove('validation-error');
    
    const existingError = inputContainer.querySelector('.input-error-msg');
    if (existingError) {
        existingError.remove();
    }
}
function clearPracticeState() {
    window.currentPracticeProblem = null;
    window.currentPracticeType = null;
    window.currentPracticeDifficulty = null;
}

function showNextProblemButton() {
    if (!['integral', 'parametric', 'polar'].includes(window.currentPracticeType)) return;
    addMessage(`
        <div style="margin-top: 16px; text-align: center;">
            <button class="button next-problem-btn" onclick="startNextProblem()" style="background: #00A1FF; border-color: #00A1FF; padding: 12px 24px; font-size: 16px;">
                Next Problem
            </button>
        </div>
    `, false);
}

function startNextProblem() {
    document.getElementById('messages-container').innerHTML = '';
    window.currentPracticeProblem = null;
    window.currentPracticeType = null;
    window.currentPracticeDifficulty = null;
    currentPracticeTypeMessage = null;
    currentPracticeDifficultyMessage = null;
    selectedPracticeType = null;
    selectedPracticeDifficulty = null;
    
    const input = document.getElementById('main-input');
    if (input) {
        input.value = '';
        input.placeholder = 'Enter your answer or [give up]';
        input.style.height = '24px';
    }
    document.getElementById('conversation-area').scrollTop = 0;
    
    addMessage(`
        <div class="practice-setup">
            <div class="practice-header"><span>📚</span>Practice Mode</div>
            <div class="practice-content"><p>Select a problem type to get started:</p></div>
            <div class="practice-dropdown" id="practice-type-dropdown">
                <div class="example-prompt" onclick="selectPracticeType('integral')"><h4>Regular</h4><p>Standard integration problems</p></div>
                <div class="example-prompt" onclick="selectPracticeType('parametric')"><h4>Parametric</h4><p>Parametric equation problems</p></div>
                <div class="example-prompt" onclick="selectPracticeType('polar')"><h4>Polar</h4><p>Polar coordinate problems</p></div>
            </div>
        </div>
    `, false);
}
function debugMissingElements() {
    const requiredElements = [
        'main-input',
        'send-btn', 
        'solver-dropdown',
        'welcome-screen',
        'messages-container',
        'conversation-area',
        'recent-problems'
    ];
    
    console.log('Checking for required elements:');
    requiredElements.forEach(id => {
        const element = document.getElementById(id);
        console.log(`${id}:`, element ? '✅ Found' : '❌ Missing');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing solver...');
    
    fetch('/api/auth/me', {
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        if (data.user) {
            authManager.setUser(data.user);
            console.log('✅ User data loaded:', data.user);
        }
    })
    .catch(error => {
        console.log('Could not fetch user data:', error);
    });
    
    initializePageLatex();
    
    debugMissingElements();
    
    const mainInput = document.getElementById('main-input');
    if (mainInput) {
        setupInputHandlers();
        console.log('✅ Input handlers initialized');
    } else {
        console.error('❌ Main input element not found!');
        return;
    }
    
    loadHistory().catch(error => {
        console.log('History load failed (normal if not logged in):', error);
    });
    
    console.log('✅ Solver initialization complete');
});

window.addEventListener('load', function() {
    if (!document.getElementById('main-input')) {
        console.warn('Main input still not found on window load');
    }
});

window.selectSolverType = selectSolverType;
window.switchSolverType = switchSolverType;
window.solveIntegral = solveIntegral;
window.saveProblem = saveProblem;
window.loadProblem = loadProblem;
window.startNewProblem = startNewProblem;
window.useExample = useExample;
window.startPractice = startPractice;
window.selectPracticeType = selectPracticeType;
window.selectPracticeDifficulty = selectPracticeDifficulty;
window.generatePracticeProblem = generatePracticeProblem;
window.handlePracticeSubmission = handlePracticeSubmission;
window.clearPracticeState = clearPracticeState;
window.showNextProblemButton = showNextProblemButton;
window.startNextProblem = startNextProblem;