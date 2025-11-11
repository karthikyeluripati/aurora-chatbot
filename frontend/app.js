// Configuration
const API_URL = 'http://localhost:8000';

// State
let chatHistory = [];
let isLoading = false;

// Suggested questions by category
const questionTemplates = {
    general: [
        "What are {member}'s travel preferences?",
        "Which restaurants has {member} visited?",
        "What are {member}'s recent bookings?",
        "Tell me about {member}'s preferences",
        "What cities has {member} traveled to?"
    ],
    travel: [
        "When is {member} planning their next trip?",
        "What are {member}'s flight seating preferences?",
        "Which hotels does {member} prefer?",
        "What destinations has {member} visited?"
    ],
    dining: [
        "Which restaurants has {member} made reservations at?",
        "What are {member}'s dining preferences?",
        "What cuisine does {member} prefer?",
        "What are {member}'s favorite restaurants?"
    ],
    preferences: [
        "What are {member}'s room preferences?",
        "What are {member}'s travel preferences?",
        "Does {member} have any specific requirements?",
        "What amenities does {member} prefer?"
    ],
    bookings: [
        "What recent bookings has {member} made?",
        "What events has {member} attended?",
        "What services has {member} requested?",
        "What tickets has {member} purchased?"
    ]
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    updateSuggestedQuestions();
});

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();

        document.getElementById('memberCount').textContent = data.unique_users || 'N/A';
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('memberCount').textContent = 'Offline';
    }
}

// Update suggested questions based on selected member
function updateSuggestedQuestions() {
    const member = document.getElementById('memberSelect').value;
    const container = document.getElementById('suggestedQuestions');

    let questions;
    if (member) {
        // Member-specific questions
        questions = questionTemplates.general.map(q => q.replace('{member}', member)).slice(0, 5);
    } else {
        // General questions
        questions = [
            "Who has traveled to London recently?",
            "What are the most popular destinations?",
            "Which members prefer aisle seats?",
            "Show me recent restaurant reservations",
            "What are common member preferences?"
        ];
    }

    container.innerHTML = questions.map((q, i) => `
        <button
            onclick="askSuggested('${q.replace(/'/g, "\\'")}')"
            class="w-full text-left px-4 py-3 bg-gray-50 hover:bg-purple-50 text-gray-700 hover:text-purple-700 rounded-lg transition hover-lift text-sm border border-gray-200 hover:border-purple-300"
        >
            <i class="fas fa-comment-dots mr-2 text-xs"></i>
            ${q}
        </button>
    `).join('');
}

// Quick ask by category
function quickAsk(category) {
    const member = document.getElementById('memberSelect').value;
    const questions = questionTemplates[category] || questionTemplates.general;

    let question;
    if (member) {
        question = questions[0].replace('{member}', member);
    } else {
        // Generic question for the category
        const categoryQuestions = {
            'travel': "What are the recent travel plans?",
            'dining': "What are the popular dining destinations?",
            'preferences': "What are common member preferences?",
            'bookings': "What are the recent bookings?"
        };
        question = categoryQuestions[category] || "Tell me about member activities";
    }

    document.getElementById('questionInput').value = question;
}

// Ask suggested question
function askSuggested(question) {
    document.getElementById('questionInput').value = question;
    document.getElementById('questionForm').dispatchEvent(new Event('submit'));
}

// Ask question
async function askQuestion(event) {
    event.preventDefault();

    if (isLoading) return;

    const input = document.getElementById('questionInput');
    const question = input.value.trim();

    if (!question) return;

    // Clear input
    input.value = '';

    // Add user message
    addMessage('user', question);

    // Add loading indicator
    const loadingId = addLoadingMessage();

    isLoading = true;
    document.getElementById('askButton').disabled = true;

    try {
        const startTime = Date.now();

        const response = await fetch(`${API_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question })
        });

        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get answer');
        }

        const data = await response.json();

        // Remove loading indicator
        removeMessage(loadingId);

        // Add AI response
        addMessage('ai', data.answer, elapsed);

    } catch (error) {
        console.error('Error:', error);
        removeMessage(loadingId);
        addMessage('error', `Error: ${error.message}. Make sure the server is running on ${API_URL}`);
    } finally {
        isLoading = false;
        document.getElementById('askButton').disabled = false;
    }
}

// Add message to chat
function addMessage(type, content, elapsed = null) {
    const container = document.getElementById('chatMessages');

    // Remove welcome message if exists
    if (container.querySelector('.text-center')) {
        container.innerHTML = '';
    }

    const messageId = `msg-${Date.now()}`;

    let html = '';

    if (type === 'user') {
        html = `
            <div id="${messageId}" class="message-fade-in mb-4 flex justify-end">
                <div class="max-w-2xl">
                    <div class="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-2xl rounded-tr-sm shadow-lg">
                        <p class="text-sm leading-relaxed">${escapeHtml(content)}</p>
                    </div>
                    <p class="text-xs text-gray-500 mt-1 text-right">Just now</p>
                </div>
            </div>
        `;
    } else if (type === 'ai') {
        html = `
            <div id="${messageId}" class="message-fade-in mb-4 flex justify-start">
                <div class="max-w-2xl">
                    <div class="flex items-start gap-3">
                        <div class="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                            <i class="fas fa-robot text-white text-sm"></i>
                        </div>
                        <div>
                            <div class="bg-white border border-gray-200 px-6 py-3 rounded-2xl rounded-tl-sm shadow-lg">
                                <p class="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap">${escapeHtml(content)}</p>
                            </div>
                            <p class="text-xs text-gray-500 mt-1">
                                ${elapsed ? `Answered in ${elapsed}s` : 'Just now'}
                                ${content.toLowerCase().includes("don't have") ?
                                    '<span class="ml-2 text-amber-600"><i class="fas fa-exclamation-circle"></i> No information found</span>' :
                                    '<span class="ml-2 text-green-600"><i class="fas fa-check-circle"></i> Found</span>'
                                }
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else if (type === 'error') {
        html = `
            <div id="${messageId}" class="message-fade-in mb-4">
                <div class="bg-red-50 border border-red-200 px-6 py-3 rounded-lg">
                    <p class="text-sm text-red-700"><i class="fas fa-exclamation-triangle mr-2"></i>${escapeHtml(content)}</p>
                </div>
            </div>
        `;
    }

    container.insertAdjacentHTML('beforeend', html);
    container.scrollTop = container.scrollHeight;

    return messageId;
}

// Add loading message
function addLoadingMessage() {
    const container = document.getElementById('chatMessages');
    const messageId = `msg-${Date.now()}`;

    const html = `
        <div id="${messageId}" class="message-fade-in mb-4 flex justify-start">
            <div class="max-w-2xl">
                <div class="flex items-start gap-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                        <i class="fas fa-robot text-white text-sm"></i>
                    </div>
                    <div>
                        <div class="bg-white border border-gray-200 px-6 py-3 rounded-2xl rounded-tl-sm shadow-lg">
                            <div class="typing-indicator flex gap-1">
                                <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                                <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                                <span class="w-2 h-2 bg-gray-400 rounded-full"></span>
                            </div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">Thinking...</p>
                    </div>
                </div>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', html);
    container.scrollTop = container.scrollHeight;

    return messageId;
}

// Remove message
function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// Show stats modal
async function showStats() {
    const modal = document.getElementById('statsModal');
    const content = document.getElementById('statsContent');

    modal.classList.remove('hidden');
    content.innerHTML = '<div class="text-center py-8"><i class="fas fa-spinner fa-spin text-3xl text-purple-500"></i></div>';

    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();

        let html = `
            <div class="grid grid-cols-2 gap-4 mb-6">
                <div class="bg-purple-50 rounded-lg p-4">
                    <p class="text-sm text-purple-600 font-medium">Total Messages</p>
                    <p class="text-3xl font-bold text-purple-700">${data.total_messages.toLocaleString()}</p>
                </div>
                <div class="bg-blue-50 rounded-lg p-4">
                    <p class="text-sm text-blue-600 font-medium">Active Members</p>
                    <p class="text-3xl font-bold text-blue-700">${data.unique_users}</p>
                </div>
            </div>

            <h3 class="font-semibold text-gray-700 mb-3">Messages per Member</h3>
            <div class="space-y-2">
        `;

        const sortedUsers = Object.entries(data.users).sort((a, b) => b[1] - a[1]);

        sortedUsers.forEach(([user, count]) => {
            const percentage = (count / data.total_messages * 100).toFixed(1);
            html += `
                <div class="flex items-center gap-3">
                    <div class="flex-1">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-sm font-medium text-gray-700">${user}</span>
                            <span class="text-xs text-gray-500">${count} (${percentage}%)</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div class="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full" style="width: ${percentage}%"></div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';

        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = `
            <div class="text-center py-8 text-red-600">
                <i class="fas fa-exclamation-circle text-3xl mb-3"></i>
                <p>Failed to load statistics</p>
                <p class="text-sm mt-2">${error.message}</p>
            </div>
        `;
    }
}

// Hide stats modal
function hideStats(event) {
    if (!event || event.target.id === 'statsModal') {
        document.getElementById('statsModal').classList.add('hidden');
    }
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle Enter key
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('questionInput');
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            document.getElementById('questionForm').dispatchEvent(new Event('submit'));
        }
    });
});
