/**
 * Module 6: AI Health & Medicine Chatbot Interface
 * Handles conversational queries, quick prompt pills, and markdown formatting.
 */

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const promptPills = document.querySelectorAll('.suggestion-pill');

    if (!chatForm || !chatInput || !chatMessages) return;

    // Scroll to bottom on load
    scrollToBottom();

    // Handle form submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        appendMessage('user', text, new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
        showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            hideTypingIndicator();

            if (data.success) {
                appendMessage('assistant', data.reply, data.timestamp);
            } else {
                appendMessage('assistant', "I apologize, but I encountered an error processing your query. Please try again.", "Now");
            }
        } catch (err) {
            hideTypingIndicator();
            appendMessage('assistant', `Connection error: ${err.message}. Please check local server status.`, "Now");
        }
    });

    // Prompt suggestion pills
    promptPills.forEach(pill => {
        pill.addEventListener('click', () => {
            const query = pill.getAttribute('data-query');
            if (query) {
                chatInput.value = query;
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    function appendMessage(role, content, timeStr) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;

        const formattedContent = parseMarkdownToHtml(content);

        bubble.innerHTML = `
            <div class="bubble-content">
                ${formattedContent}
                <span class="bubble-time">${timeStr}</span>
            </div>
        `;

        chatMessages.appendChild(bubble);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const typingEl = document.createElement('div');
        typingEl.id = 'chatTypingIndicator';
        typingEl.className = 'chat-bubble assistant';
        typingEl.innerHTML = `
            <div class="bubble-content">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(typingEl);
        scrollToBottom();
    }

    function hideTypingIndicator() {
        const el = document.getElementById('chatTypingIndicator');
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Converts basic markdown to clean HTML tags safely
     */
    function parseMarkdownToHtml(text) {
        if (!text) return '';
        let escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Headings
        escaped = escaped.replace(/^### (.*$)/gim, '<h6 class="fw-bold mt-2 mb-1 text-primary">$1</h6>');
        escaped = escaped.replace(/^#### (.*$)/gim, '<strong class="d-block text-secondary mt-2 mb-1">$1</strong>');
        
        // Bold & Italic
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Lists
        escaped = escaped.replace(/^\- (.*$)/gim, '• $1<br>');
        escaped = escaped.replace(/^\d+\. (.*$)/gim, '<span class="fw-semibold text-secondary">$1</span><br>');

        // Paragraph breaks
        escaped = escaped.replace(/\n\n/g, '<div class="my-2"></div>');
        escaped = escaped.replace(/\n/g, '<br>');

        return escaped;
    }
});
