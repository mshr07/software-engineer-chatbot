class ChatbotApp {
    constructor() {
        this.apiUrl = '/api';
        this.token = localStorage.getItem('token');
        this.currentUser = null;
        this.currentSessionId = null;
        this.availableTechStacks = [];
        this.selectedTechStacks = new Set();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
    }
    
    setupEventListeners() {
        // Authentication
        document.getElementById('login-btn').addEventListener('click', () => this.showLoginForm());
        document.getElementById('register-btn').addEventListener('click', () => this.showRegisterForm());
        document.getElementById('show-register').addEventListener('click', () => this.showRegisterForm());
        document.getElementById('show-login').addEventListener('click', () => this.showLoginForm());
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
        
        document.getElementById('login-form-element').addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('register-form-element').addEventListener('submit', (e) => this.handleRegister(e));
        
        // Chat
        document.getElementById('new-chat').addEventListener('click', () => this.createNewChat());
        document.getElementById('send-message').addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Tech Stack
        document.getElementById('update-tech-stack').addEventListener('click', () => this.updateTechStack());
        document.getElementById('tech-category-filter').addEventListener('change', (e) => this.filterTechStacks(e.target.value));
        
        // Interview Questions
        document.getElementById('generate-questions').addEventListener('click', () => this.showInterviewForm());
        document.getElementById('practice-interview').addEventListener('click', () => this.generatePracticeInterview());
        document.getElementById('close-interview-modal').addEventListener('click', () => this.hideInterviewModal());
    }
    
    async checkAuthStatus() {
        if (this.token) {
            try {
                const user = await this.makeRequest('/auth/me', 'GET');
                this.currentUser = user;
                this.showMainApp();
                await this.loadTechStacks();
                await this.createNewChat();
            } catch (error) {
                this.token = null;
                localStorage.removeItem('token');
                this.showAuthForms();
            }
        } else {
            this.showAuthForms();
        }
    }
    
    showAuthForms() {
        document.getElementById('auth-section').classList.remove('hidden');
        document.getElementById('main-app').classList.add('hidden');
        document.getElementById('nav-auth').classList.remove('hidden');
        document.getElementById('nav-user').classList.add('hidden');
        this.showLoginForm();
    }
    
    showMainApp() {
        document.getElementById('auth-section').classList.add('hidden');
        document.getElementById('main-app').classList.remove('hidden');
        document.getElementById('nav-auth').classList.add('hidden');
        document.getElementById('nav-user').classList.remove('hidden');
        document.getElementById('username-display').textContent = this.currentUser.username;
    }
    
    showLoginForm() {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    }
    
    showRegisterForm() {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    }
    
    async handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        
        try {
            this.showLoading();
            const response = await this.makeRequest('/auth/login', 'POST', { username, password });
            this.token = response.access_token;
            localStorage.setItem('token', this.token);
            await this.checkAuthStatus();
        } catch (error) {
            this.showError('Login failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        const userData = {
            username: document.getElementById('reg-username').value,
            email: document.getElementById('reg-email').value,
            full_name: document.getElementById('reg-fullname').value,
            years_of_experience: parseInt(document.getElementById('reg-experience').value),
            current_role: document.getElementById('reg-role').value,
            password: document.getElementById('reg-password').value
        };
        
        try {
            this.showLoading();
            await this.makeRequest('/auth/register', 'POST', userData);
            this.showSuccess('Registration successful! Please login.');
            this.showLoginForm();
        } catch (error) {
            this.showError('Registration failed: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    logout() {
        this.token = null;
        this.currentUser = null;
        this.currentSessionId = null;
        localStorage.removeItem('token');
        this.showAuthForms();
        document.getElementById('chat-messages').innerHTML = '';
    }
    
    async loadTechStacks() {
        try {
            // Load available tech stacks
            const available = await this.makeRequest('/techstack/available', 'GET');
            this.availableTechStacks = available;
            
            // Load categories
            const categories = await this.makeRequest('/techstack/categories', 'GET');
            this.populateCategories(categories.categories);
            
            // Load user's current tech stack
            await this.loadUserTechStack();
            this.renderTechStacks();
        } catch (error) {
            console.error('Error loading tech stacks:', error);
        }
    }
    
    async loadUserTechStack() {
        try {
            const userTechStack = await this.makeRequest('/techstack/my-stack', 'GET');
            this.selectedTechStacks = new Set(userTechStack.map(t => t.id));
            this.renderCurrentTechStack(userTechStack);
        } catch (error) {
            console.error('Error loading user tech stack:', error);
        }
    }
    
    populateCategories(categories) {
        const select = document.getElementById('tech-category-filter');
        select.innerHTML = '<option value=\"\">All Categories</option>';
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            select.appendChild(option);
        });
    }
    
    renderCurrentTechStack(techStacks) {
        const container = document.getElementById('current-tech-stack');
        container.innerHTML = '';
        
        techStacks.forEach(tech => {
            const element = document.createElement('div');
            element.className = 'flex justify-between items-center bg-blue-50 p-2 rounded';
            element.innerHTML = `
                <span class="text-sm">${tech.name}</span>
                <button onclick="app.removeTechStack(${tech.id})" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(element);
        });
    }
    
    filterTechStacks(category) {
        this.renderTechStacks(category);
    }
    
    renderTechStacks(filterCategory = '') {
        const container = document.getElementById('available-tech-stack');
        container.innerHTML = '';
        
        const filtered = this.availableTechStacks.filter(tech => 
            !filterCategory || tech.category === filterCategory
        );
        
        filtered.forEach(tech => {
            const isSelected = this.selectedTechStacks.has(tech.id);
            const element = document.createElement('label');
            element.className = 'flex items-center space-x-2 p-1 hover:bg-gray-50 cursor-pointer';
            element.innerHTML = `
                <input type="checkbox" ${isSelected ? 'checked' : ''} 
                       onchange="app.toggleTechStack(${tech.id}, this.checked)"
                       class="form-checkbox">
                <span class="text-sm">${tech.name}</span>
                <span class="text-xs text-gray-500">(${tech.category})</span>
            `;
            container.appendChild(element);
        });
    }
    
    toggleTechStack(techId, isSelected) {
        if (isSelected) {
            this.selectedTechStacks.add(techId);
        } else {
            this.selectedTechStacks.delete(techId);
        }
    }
    
    async removeTechStack(techId) {
        this.selectedTechStacks.delete(techId);
        await this.updateTechStack();
    }
    
    async updateTechStack() {
        try {
            this.showLoading();
            const techStackIds = Array.from(this.selectedTechStacks);
            await this.makeRequest('/techstack/my-stack', 'PUT', { tech_stack_ids: techStackIds });
            await this.loadUserTechStack();
            this.showSuccess('Tech stack updated successfully!');
        } catch (error) {
            this.showError('Error updating tech stack: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    async createNewChat() {
        try {
            const session = await this.makeRequest('/chat/session', 'POST', {});
            this.currentSessionId = session.session_id;
            this.clearChat();
        } catch (error) {
            console.error('Error creating new chat:', error);
        }
    }
    
    clearChat() {
        const container = document.getElementById('chat-messages');
        container.innerHTML = `
            <div class="message bg-blue-100 p-3 rounded-lg">
                <div class="flex items-start space-x-2">
                    <i class="fas fa-robot text-blue-600 mt-1"></i>
                    <div>
                        <p class="font-semibold text-blue-700">AI Assistant</p>
                        <p>Hello! I'm your AI assistant specialized in software engineering. I can help you with programming questions, technical problems, career advice, and more. What would you like to know?</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || !this.currentSessionId) return;
        
        // Add user message to chat
        this.addMessageToChat('user', message);
        input.value = '';
        
        try {
            this.showTypingIndicator();
            const response = await this.makeRequest('/chat/message', 'POST', {
                content: message,
                session_id: this.currentSessionId
            });
            
            this.removeTypingIndicator();
            this.addMessageToChat('assistant', response.message);
        } catch (error) {
            this.removeTypingIndicator();
            this.addMessageToChat('assistant', 'Sorry, I encountered an error. Please try again.');
            console.error('Error sending message:', error);
        }
    }
    
    addMessageToChat(type, content) {
        const container = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message mb-4 p-3 rounded-lg';
        
        if (type === 'user') {
            messageDiv.className += ' bg-gray-200 ml-8';
            messageDiv.innerHTML = `
                <div class="flex items-start space-x-2 justify-end">
                    <div class="text-right">
                        <p class="font-semibold text-gray-700">You</p>
                        <p>${this.formatMessage(content)}</p>
                    </div>
                    <i class="fas fa-user text-gray-600 mt-1"></i>
                </div>
            `;
        } else {
            messageDiv.className += ' bg-blue-100 mr-8';
            messageDiv.innerHTML = `
                <div class="flex items-start space-x-2">
                    <i class="fas fa-robot text-blue-600 mt-1"></i>
                    <div>
                        <p class="font-semibold text-blue-700">AI Assistant</p>
                        <p>${this.formatMessage(content)}</p>
                    </div>
                </div>
            `;
        }
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }
    
    formatMessage(content) {
        // Basic formatting for code blocks and line breaks
        return content
            .replace(/```([\\s\\S]*?)```/g, '<pre class="bg-gray-100 p-2 rounded mt-2 overflow-x-auto"><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
            .replace(/\\n/g, '<br>');
    }
    
    showTypingIndicator() {
        const container = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'message bg-blue-100 p-3 rounded-lg mr-8';
        typingDiv.innerHTML = `
            <div class="flex items-start space-x-2">
                <i class="fas fa-robot text-blue-600 mt-1"></i>
                <div>
                    <p class="font-semibold text-blue-700">AI Assistant</p>
                    <p><i class="fas fa-circle-notch fa-spin mr-1"></i>Thinking...</p>
                </div>
            </div>
        `;
        container.appendChild(typingDiv);
        container.scrollTop = container.scrollHeight;
    }
    
    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }
    
    showInterviewForm() {
        // Create a simple prompt for interview questions
        const targetRole = prompt('What role are you preparing for?', this.currentUser.current_role || 'Software Engineer');
        const yearsExp = prompt('Years of experience for the target role?', this.currentUser.years_of_experience || 3);
        
        if (targetRole && yearsExp) {
            this.generateInterviewQuestions(parseInt(yearsExp), targetRole);
        }
    }
    
    async generateInterviewQuestions(yearsExp, targetRole) {
        try {
            this.showLoading();
            const response = await this.makeRequest('/interview/generate', 'POST', {
                years_of_experience: yearsExp,
                target_role: targetRole,
                focus_areas: [],
                num_questions: 5
            });
            
            this.showInterviewModal(response.questions);
        } catch (error) {
            this.showError('Error generating interview questions: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    async generatePracticeInterview() {
        try {
            this.showLoading();
            const response = await this.makeRequest('/interview/practice-set', 'POST', {});
            this.showInterviewModal(response.questions);
        } catch (error) {
            this.showError('Error generating practice interview: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    showInterviewModal(questions) {
        const modal = document.getElementById('interview-modal');
        const content = document.getElementById('interview-questions-content');
        
        content.innerHTML = '';
        questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'mb-4 p-3 border rounded-lg';
            questionDiv.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold">Question ${index + 1}</h4>
                    <span class="text-xs bg-${this.getCategoryColor(question.category)}-100 text-${this.getCategoryColor(question.category)}-800 px-2 py-1 rounded">
                        ${question.category}
                    </span>
                </div>
                <p class="mb-2">${question.question}</p>
                <div class="text-sm text-gray-600">
                    <p><strong>Difficulty:</strong> ${question.difficulty_level}</p>
                    ${question.tech_stack ? `<p><strong>Tech:</strong> ${question.tech_stack}</p>` : ''}
                </div>
                <details class="mt-2">
                    <summary class="cursor-pointer text-blue-600">Expected Answer</summary>
                    <p class="mt-2 text-sm text-gray-700">${question.expected_answer || 'No expected answer provided.'}</p>
                </details>
            `;
            content.appendChild(questionDiv);
        });
        
        modal.classList.remove('hidden');
    }
    
    hideInterviewModal() {
        document.getElementById('interview-modal').classList.add('hidden');
    }
    
    getCategoryColor(category) {
        const colors = {
            'Technical': 'blue',
            'Behavioral': 'green',
            'System Design': 'purple',
            'Coding': 'orange',
            'Problem Solving': 'red'
        };
        return colors[category] || 'gray';
    }
    
    showLoading() {
        document.getElementById('loading').classList.remove('hidden');
    }
    
    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }
    
    showError(message) {
        // Simple alert for now - could be improved with toast notifications
        alert('Error: ' + message);
    }
    
    showSuccess(message) {
        // Simple alert for now - could be improved with toast notifications
        alert('Success: ' + message);
    }
    
    async makeRequest(endpoint, method, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        if (this.token) {
            options.headers.Authorization = `Bearer ${this.token}`;
        }
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(this.apiUrl + endpoint, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Request failed');
        }
        
        return await response.json();
    }
}

// Initialize the app when the page loads
const app = new ChatbotApp();

// Global functions for event handlers
window.app = app;