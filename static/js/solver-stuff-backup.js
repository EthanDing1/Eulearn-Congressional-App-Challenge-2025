let currentConversation = [];
let problemHistory = [];
let currentSolverMode = null;

document.addEventListener('DOMContentLoaded', function() {
    const conversationArea = document.getElementById('conversation-area');
    conversationArea.scrollTop = 0;
    
    setTimeout(() => {
        if (!window.authManager || !authManager.isLoggedIn()) {
            window.location.href = 'login.html';
        } else {
            loadHistory();
            setupInputHandlers();
        }
    }, 1500);
});

function setupInputHandlers() {
    const input = document.getElementById('main-input');
    const sendBtn = document.getElementById('send-btn');
    const dropdown = document.getElementById('solver-dropdown');

    input.addEventListener('input', function() {
        this.style.height = '24px';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        
        validateMainInput();
    });

    input.addEventListener('focus', function() {
        showDropdown();
    });

    input.addEventListener('blur', function() {
        setTimeout(() => {
            hideDropdown();
        }, 150);
    });

    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim() && currentSolverMode) {
                solveIntegral();
            }
        }
        
        if (e.key === 'Escape') {
            hideDropdown();
            this.blur();
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            hideDropdown();
        }
    });
    
    validateMainInput();
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
    
    if (hasContent && !hasSolverMode) {
        isValid = false;
        errorMessage = 'Please select a solver type (Regular, Parametric, or Polar)';
        showRegularInputError(errorMessage);
    }
    else if (hasContent && hasSolverMode && currentSolverMode !== 'parametric') {
        if (!validateIntegralExpression(hasContent)) {
            isValid = false;
            errorMessage = 'Invalid characters. Use only numbers, x, and basic operators (+, -, *, /, ^, parentheses) or functions (sin, cos, tan, log, ln, exp, sqrt, abs)';
            showRegularInputError(errorMessage);
        }
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
function showParametricDropdown(clickedInput) {
    let dropdown = document.getElementById('parametric-solver-dropdown');
    
    if (!dropdown) {
        dropdown = createParametricDropdown();
    }
    
    const inputRect = clickedInput.getBoundingClientRect();
    const container = clickedInput.closest('.split-input-container');
    
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
function showDropdown() {
    const dropdown = document.getElementById('solver-dropdown');
    const input = document.getElementById('main-input');
    
    dropdown.style.display = 'grid';
    input.classList.add('dropdown-active');
    
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
            <p>ex. ∫ (x(t), y(t)) dt</p>
        </div>
        <div class="example-prompt" onclick="switchSolverType('polar')">
            <h4>Polar</h4>
            <p>ex. ∫ r(θ) dθ</p>
        </div>
    `;
    
    const splitContainer = document.querySelector('.split-input-container');
    if (splitContainer) {
        splitContainer.style.position = 'relative';
        splitContainer.appendChild(dropdown);
    }
    
    return dropdown;
}
function hideDropdown() {
    const dropdown = document.getElementById('solver-dropdown');
    const input = document.getElementById('main-input');
    
    dropdown.classList.remove('show');
    input.classList.remove('dropdown-active');
    
    setTimeout(() => {
        if (!dropdown.classList.contains('show')) {
            dropdown.style.display = 'none';
        }
    }, 300);
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
        input.placeholder = 'Enter your regular integral';
        
        validateMainInput();
    }
    
    hideDropdown();
    
    console.log(`Selected solver mode: ${type}`);
}
function switchToPolarInput() {
    const singleContainer = document.querySelector('.input-container');
    singleContainer.classList.add('parametric-mode');
    
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
                placeholder="Enter inner function (use x for θ, leave blank if only one function)"
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
                    placeholder="Enter outer function (use x for θ)"
                    rows="1"
                ></textarea>
                <button class="send-btn" id="polar-send-btn" onclick="solveIntegral()">
                    <img id="arrow" src="images/arrow.png" alt="Send">
                </button>
            </div>
            <span class="parametric-error-msg" id="outer-polar-error"></span>
        </div>
    `;
    
    singleContainer.parentNode.insertBefore(splitContainer, singleContainer.nextSibling);
    
    setTimeout(() => {
        splitContainer.classList.add('active');
    }, 10);
    
    setupPolarValidation();
    setupPolarClickHandlers();
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
                if (outerValue && validatePolarExpression(outerValue) && 
                    (innerValue === '' || validatePolarExpression(innerValue))) {
                    solveIntegral();
                }
            }
        });
    });
    
    sendBtn.disabled = true;
    sendBtn.style.opacity = '0.6';
    
    validatePolarInputs();
}

function validatePolarInputs() {
    const innerInput = document.getElementById('inner-polar-input');
    const outerInput = document.getElementById('outer-polar-input');
    const sendBtn = document.getElementById('polar-send-btn');
    
    if (!innerInput || !outerInput || !sendBtn) return;
    
    const innerValue = innerInput.value.trim();
    const outerValue = outerInput.value.trim();
    
    let innerValid = true;
    let outerValid = true;
    
    if (innerValue === '') {
        clearPolarError(innerInput);
    } else if (!validatePolarExpression(innerValue)) {
        showPolarError(innerInput, 'Invalid characters. Use only numbers, x (for θ), and basic operators (+, -, *, /, ^, parentheses)');
        innerValid = false;
    } else {
        clearPolarError(innerInput);
    }
    
    if (outerValue === '') {
        clearPolarError(outerInput);
        outerValid = false;
    } else if (!validatePolarExpression(outerValue)) {
        showPolarError(outerInput, 'Invalid characters. Use only numbers, x (for θ), and basic operators (+, -, *, /, ^, parentheses)');
        outerValid = false;
    } else {
        clearPolarError(outerInput);
    }
    
    const hasRequiredContent = outerValue !== '';
    const allValid = innerValid && outerValid;
    const shouldEnable = hasRequiredContent && allValid;
    
    sendBtn.disabled = !shouldEnable;
    if (shouldEnable) {
        sendBtn.style.opacity = '1';
        sendBtn.classList.add('has-input');
    } else {
        sendBtn.style.opacity = '0.6';
        sendBtn.classList.remove('has-input');
    }
}

function validatePolarExpression(expression) {
    if (!expression || expression.trim() === '') return true;
    
    const validPattern = /^[0-9x+\-*/^().\s]*$/;
    return validPattern.test(expression.trim());
}

function showPolarError(inputElement, message) {
    inputElement.classList.add('error');
    
    const errorId = inputElement.id.replace('-input', '-error');
    const errorSpan = document.getElementById(errorId);
    
    if (errorSpan) {
        errorSpan.textContent = message;
        errorSpan.style.display = 'block';
    }
}

function clearPolarError(inputElement) {
    inputElement.classList.remove('error');
    
    const errorId = inputElement.id.replace('-input', '-error');
    const errorSpan = document.getElementById(errorId);
    
    if (errorSpan) {
        errorSpan.textContent = '';
        errorSpan.style.display = 'none';
    }
}

function clearAllPolarErrors() {
    const innerInput = document.getElementById('inner-polar-input');
    const outerInput = document.getElementById('outer-polar-input');
    
    if (innerInput) clearPolarError(innerInput);
    if (outerInput) clearPolarError(outerInput);
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

function getAuthHeaders() {
    const token = authManager.getToken();
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

function hideWelcomeScreen() {
    document.getElementById('welcome-screen').style.display = 'none';
    document.getElementById('messages-container').style.display = 'block';

    document.getElementById('conversation-area').classList.add('has-messages');
}

function addMessage(content, isUser = false, isLoading = false) {
    hideWelcomeScreen();
    
    const messagesContainer = document.getElementById('messages-container');
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
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return messageDiv;
}

async function solveIntegral() {
    let integral = '';
    let inputsToClear = [];
    
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
        
        if (!validateParametricExpression(xValue) || !validateParametricExpression(yValue)) {
            addMessage('⚠️ Please fix the validation errors before solving', false);
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
        
        if (!outerValue) {
            addMessage('⚠️ Please enter at least the outer function', false);
            return;
        }
        
        if (!validatePolarExpression(outerValue) || 
            (innerValue && !validatePolarExpression(innerValue))) {
            addMessage('⚠️ Please fix the validation errors before solving', false);
            return;
        }
        
        if (innerValue) {
            integral = `Inner: ${innerValue}, Outer: ${outerValue}`;
        } else {
            integral = `Function: ${outerValue}`;
        }
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

    addMessage(integral, true);
    
    inputsToClear.forEach(inputElement => {
        inputElement.value = '';
        inputElement.style.height = '24px';
        inputElement.dispatchEvent(new Event('input'));
    });

    const loadingMessage = addMessage('', false, true);

    try {
        const response = await fetch('http://localhost:5000/api/solver/solve', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ 
                integral: integral,
                solverType: currentSolverMode
            })
        });

        const result = await response.json();

        loadingMessage.remove();

        if (response.ok) {
            const solutionHTML = `
                <div class="solution-display">
                    <div class="solution-header">
                        <span>📐</span>
                        ${currentSolverMode.charAt(0).toUpperCase() + currentSolverMode.slice(1)} Solution
                    </div>
                    <div class="solution-content">
                        <p><strong>Problem:</strong> ${result.input} (${currentSolverMode})</p>
                        <p><strong>Solution:</strong> ${result.solution}</p>
                    </div>
                    ${result.steps && result.steps.length > 0 ? `
                        <div class="solution-steps">
                            <h4>Step-by-step Solution:</h4>
                            <ol>
                                ${result.steps.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        </div>
                    ` : ''}
                </div>
                <div style="margin-top: 16px;">
                    <button class="button" onclick="saveProblem('${result.input}', '${result.solution}', ${JSON.stringify(result.steps || []).replace(/"/g, '&quot;')}, '${currentSolverMode}')" style="background: #10a37f; border-color: #10a37f;">
                        Save to History
                    </button>
                </div>
            `;
            
            addMessage(solutionHTML, false);
            
            window.currentProblem = result;
            
            currentConversation.push({
                input: integral,
                result: result,
                solverType: currentSolverMode,
                timestamp: new Date()
            });

        } else {
            addMessage(`❌ Error: ${result.error}`, false);
        }
    } catch (error) {
        loadingMessage.remove();
        addMessage('❌ Network error. Please try again.', false);
        console.error('Solver error:', error);
    }
}

async function saveProblem(input, solution, steps, solverType) {
    try {
        const response = await fetch('http://localhost:5000/api/solver/save', {
            method: 'POST',
            headers: getAuthHeaders(),
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
            addMessage(`❌ Failed to save: ${result.error}`, false);
        }
    } catch (error) {
        addMessage('❌ Failed to save problem', false);
        console.error('Save error:', error);
    }
}

async function loadHistory() {
    try {
        const response = await fetch('http://localhost:5000/api/solver/history', {
            headers: getAuthHeaders()
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
    
    if (!problems || problems.length === 0) {
        problemList.innerHTML = `
            <div class="problem-item">
                <div class="problem-preview">No recent problems</div>
                <div class="problem-date">Start solving to see history</div>
            </div>
        `;
        return;
    }

    problemList.innerHTML = problems.slice(0, 10).map(problem => `
        <div class="problem-item" onclick="loadProblem('${problem.input}', '${problem.solution}')">
            <div class="problem-preview">∫ ${problem.input} dx</div>
            <div class="problem-date">${new Date(problem.created_at).toLocaleDateString()}</div>
        </div>
    `).join('');
}

function loadProblem(input, solution) {
    document.getElementById('messages-container').innerHTML = '';
    hideWelcomeScreen();
    
    addMessage(input, true);
    addMessage(`
        <div class="solution-display">
            <div class="solution-header">
                <span>📐</span>
                Previous Solution
            </div>
            <div class="solution-content">
                <p><strong>Problem:</strong> ∫ ${input} dx</p>
                <p><strong>Solution:</strong> ${solution}</p>
            </div>
        </div>
    `, false);
}

function startNewProblem() {

    const splitContainer = document.querySelector('.split-input-container');
    if (splitContainer) {
        splitContainer.remove();
    }
    
    switchToSingleInput();
    
    currentSolverMode = null;
    currentConversation = [];
    
    document.getElementById('messages-container').innerHTML = '';
    document.getElementById('welcome-screen').style.display = 'flex';
    document.getElementById('messages-container').style.display = 'none';
    
    const input = document.getElementById('main-input');
    if (input) {
        input.placeholder = 'Select integral option';
    }

    document.getElementById('conversation-area').classList.remove('has-messages');
    
    const conversationArea = document.getElementById('conversation-area');
    conversationArea.scrollTop = 0;
}

function useExample(example) {
    const input = document.getElementById('main-input');
    const sendBtn = document.getElementById('send-btn');
    
    input.value = example;
    sendBtn.disabled = false;
    sendBtn.style.background = '#00A1FF';
    sendBtn.style.opacity = '1';
    input.focus();
}

function startPractice() {
    const practiceProblems = [
        'x^3 + 2x',
        'cos(x)',
        '2x + 1',
        'x*sin(x)',
        'sqrt(x)'
    ];
    
    const randomProblem = practiceProblems[Math.floor(Math.random() * practiceProblems.length)];
    
    addMessage(`Here's a practice problem for you: ∫ ${randomProblem} dx`, false);
    
    const input = document.getElementById('main-input');
    const sendBtn = document.getElementById('send-btn');
    
    input.value = randomProblem;
    sendBtn.disabled = false;
    sendBtn.style.background = '#00A1FF';
    sendBtn.style.opacity = '1';
    input.focus();
}
function switchToParametricInput() {
    const singleContainer = document.querySelector('.input-container');
    singleContainer.classList.add('parametric-mode');
    
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
                    <img id="arrow" src="images/arrow.png" alt="Send">
                </button>
            </div>
            <span class="parametric-error-msg" id="y-param-error"></span>
        </div>
    `;
    
    singleContainer.parentNode.insertBefore(splitContainer, singleContainer.nextSibling);
    
    setTimeout(() => {
        splitContainer.classList.add('active');
    }, 10);
    
    setupParametricValidation();
    setupParametricClickHandlers();
}
function switchToSingleInput() {
    const singleContainer = document.querySelector('.input-container');
    singleContainer.classList.remove('parametric-mode');
    
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

function setupParametricValidation() {
    const xInput = document.getElementById('x-param-input');
    const yInput = document.getElementById('y-param-input');
    const sendBtn = document.getElementById('param-send-btn');
    
    if (!xInput || !yInput || !sendBtn) return;
    
    [xInput, yInput].forEach(input => {
        input.addEventListener('input', function() {
            this.style.height = '24px';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
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
                if (xValue && yValue && validateParametricExpression(xValue) && validateParametricExpression(yValue)) {
                    solveIntegral();
                }
            }
        });
    });
    
    sendBtn.disabled = true;
    sendBtn.style.opacity = '0.6';
    
    validateParametricInputs();
}

function validateParametricInputs() {
    const xInput = document.getElementById('x-param-input');
    const yInput = document.getElementById('y-param-input');
    const sendBtn = document.getElementById('param-send-btn');
    
    if (!xInput || !yInput || !sendBtn) return;
    
    const xValue = xInput.value.trim();
    const yValue = yInput.value.trim();
    
    let xValid = true;
    let yValid = true;
    
    if (xValue === '') {
        clearParametricError(xInput);
    } else if (!validateParametricExpression(xValue)) {
        showParametricError(xInput, 'Invalid characters. Use only numbers, t, and basic operators (+, -, *, /, ^, parentheses)');
        xValid = false;
    } else {
        clearParametricError(xInput);
    }
    
    if (yValue === '') {
        clearParametricError(yInput);
    } else if (!validateParametricExpression(yValue)) {
        showParametricError(yInput, 'Invalid characters. Use only numbers, t, and basic operators (+, -, *, /, ^, parentheses)');
        yValid = false;
    } else {
        clearParametricError(yInput);
    }
    
    const bothHaveContent = xValue !== '' && yValue !== '';
    const bothValid = xValid && yValid;
    const shouldEnable = bothHaveContent && bothValid;
    
    sendBtn.disabled = !shouldEnable;
    if (shouldEnable) {
        sendBtn.style.opacity = '1';
        sendBtn.classList.add('has-input');
    } else {
        sendBtn.style.opacity = '0.6';
        sendBtn.classList.remove('has-input');
    }
}

function validateParametricExpression(expression) {
    if (!expression || expression.trim() === '') return false;
    
    const validPattern = /^[0-9t+\-*/^().\s]*$/;
    return validPattern.test(expression.trim());
}

function showParametricError(inputElement, message) {
    inputElement.classList.add('error');
    
    const errorId = inputElement.id.replace('-input', '-error');
    const errorSpan = document.getElementById(errorId);
    
    if (errorSpan) {
        errorSpan.textContent = message;
        errorSpan.style.display = 'block';
    }
}

function clearParametricError(inputElement) {
    inputElement.classList.remove('error');
    
    const errorId = inputElement.id.replace('-input', '-error');
    const errorSpan = document.getElementById(errorId);
    
    if (errorSpan) {
        errorSpan.textContent = '';
        errorSpan.style.display = 'none';
    }
}

function clearAllParametricErrors() {
    const xInput = document.getElementById('x-param-input');
    const yInput = document.getElementById('y-param-input');
    
    if (xInput) clearParametricError(xInput);
    if (yInput) clearParametricError(yInput);
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
        mainInput.style.height = '';
        setTimeout(() => {
            mainInput.style.height = 'auto';
            mainInput.style.height = Math.max(mainInput.scrollHeight, 24) + 'px';
        }, 50);
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
    
    clearAllParametricErrors();
    
    clearAllPolarErrors();
}
function validateIntegralExpression(expression) {
    if (!expression || expression.trim() === '') return true;
    
    const validPattern = /^[0-9x+\-*/^().\s]*$|^[0-9x+\-*/^().\ssincotanlgexpqrtabs]*$/;
    
    const comprehensivePattern = /^[\d\sx+\-*/^().]*(?:sin|cos|tan|log|ln|exp|sqrt|abs)*[\d\sx+\-*/^().]*$/;
    
    return comprehensivePattern.test(expression.trim());
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