(function () {
    function appendMessage(container, role, text) {
        const message = document.createElement('div');
        message.className = 'mcs-chatbot-message mcs-chatbot-message--' + role;
        message.textContent = text;
        container.appendChild(message);
        container.scrollTop = container.scrollHeight;
    }

    function setLoading(form, isLoading) {
        const submit = form.querySelector('.mcs-chatbot-send');
        if (submit) {
            submit.disabled = isLoading;
        }
    }

    function initWidget(widget) {
        const history = widget.querySelector('.mcs-chatbot-history');
        const form = widget.querySelector('.mcs-chatbot-form');
        const textarea = widget.querySelector('.mcs-chatbot-input');
        const sendButton = widget.querySelector('.mcs-chatbot-send');
        const resetButton = widget.querySelector('.mcs-chatbot-reset');
        const title = widget.querySelector('.mcs-chatbot-title');
        const screenReaderLabel = widget.querySelector('.screen-reader-text');

        if (!history || !form || !textarea) {
            return;
        }

        if (title) {
            title.textContent = MCSChatbot.strings.widgetTitle;
        }
        if (screenReaderLabel) {
            screenReaderLabel.textContent = MCSChatbot.strings.inputLabel;
        }
        if (sendButton) {
            sendButton.textContent = MCSChatbot.strings.sendButton;
        }
        if (resetButton) {
            resetButton.textContent = MCSChatbot.strings.resetButton;
        }
        textarea.placeholder = MCSChatbot.strings.placeholder;

        let sessionId = null;

        form.addEventListener('submit', function (event) {
            event.preventDefault();
            const message = textarea.value.trim();
            if (!message) {
                return;
            }

            appendMessage(history, 'user', message);
            textarea.value = '';
            setLoading(form, true);

            const payload = { message: message };
            if (sessionId) {
                payload.session_id = sessionId;
            }

            fetch(MCSChatbot.chatEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
                .then(function (response) {
                    if (!response.ok) {
                        throw new Error('Request failed');
                    }
                    return response.json();
                })
                .then(function (data) {
                    sessionId = data.session_id;
                    appendMessage(history, 'bot', data.reply);
                })
                .catch(function () {
                    appendMessage(history, 'system', MCSChatbot.strings.errorMessage);
                })
                .finally(function () {
                    setLoading(form, false);
                });
        });

        if (resetButton) {
            resetButton.addEventListener('click', function () {
                history.innerHTML = '';
                if (!sessionId) {
                    return;
                }
                fetch(MCSChatbot.sessionEndpoint + encodeURIComponent(sessionId), {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                })
                    .catch(function () {
                        // Ignore errors when clearing the session
                    })
                    .finally(function () {
                        sessionId = null;
                    });
            });
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (!window.MCSChatbot) {
            return;
        }
        document
            .querySelectorAll('.mcs-chatbot-widget')
            .forEach(function (widget) {
                initWidget(widget);
            });
    });
})();
