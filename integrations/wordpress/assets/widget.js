(function () {
    const DEFAULT_STRINGS = {
        widgetTitle: 'Support Assistant',
        inputLabel: 'Ask a question',
        placeholder: 'Type your message…',
        sendButton: 'Send',
        resetButton: 'Clear chat',
        errorMessage: 'Sorry, something went wrong. Please try again.',
        missingConfig: 'Chat configuration is missing. Please verify the widget settings.',
    };

    function resolveConfig(widget) {
        const dataset = widget.dataset || {};
        const globalConfig = window.MCSChatbot || {};
        const strings = Object.assign(
            {},
            DEFAULT_STRINGS,
            globalConfig.strings || {},
        );

        if (dataset.widgetTitle) {
            strings.widgetTitle = dataset.widgetTitle;
        }
        if (dataset.inputLabel) {
            strings.inputLabel = dataset.inputLabel;
        }
        if (dataset.placeholder) {
            strings.placeholder = dataset.placeholder;
        }
        if (dataset.sendButton) {
            strings.sendButton = dataset.sendButton;
        }
        if (dataset.resetButton) {
            strings.resetButton = dataset.resetButton;
        }
        if (dataset.errorMessage) {
            strings.errorMessage = dataset.errorMessage;
        }

        return {
            chatEndpoint: globalConfig.chatEndpoint || dataset.chatEndpoint || '',
            sessionEndpoint: globalConfig.sessionEndpoint || dataset.sessionEndpoint || '',
            apiKey: globalConfig.apiKey || dataset.apiKey || '',
            csrfToken: globalConfig.csrfToken || dataset.csrfToken || '',
            strings: strings,
        };
    }

    function appendMessage(container, role, text) {
        const message = document.createElement('div');
        message.className = 'mcs-chatbot-message mcs-chatbot-message--' + role;
        message.textContent = text;
        container.appendChild(message);
        container.scrollTop = container.scrollHeight;
    }

    function displayError(widget, history, text) {
        if (history) {
            appendMessage(history, 'system', text);
        }
        widget.classList.add('mcs-chatbot-widget--error');
        const form = widget.querySelector('.mcs-chatbot-form');
        if (form) {
            Array.from(form.elements).forEach(function (element) {
                element.disabled = true;
            });
        }
    }

    function setLoading(form, isLoading) {
        const submit = form.querySelector('.mcs-chatbot-send');
        if (submit) {
            submit.disabled = isLoading;
        }
    }

    function buildHeaders(config) {
        const headers = { 'Content-Type': 'application/json' };
        if (config.apiKey) {
            headers['X-API-Key'] = config.apiKey;
        }
        if (config.csrfToken) {
            headers['X-CSRF-Token'] = config.csrfToken;
        }
        return headers;
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

        const config = resolveConfig(widget);

        if (!config.chatEndpoint || !config.sessionEndpoint) {
            displayError(widget, history, config.strings.missingConfig);
            return;
        }

        if (title) {
            title.textContent = config.strings.widgetTitle;
        }
        if (screenReaderLabel) {
            screenReaderLabel.textContent = config.strings.inputLabel;
        }
        if (sendButton) {
            sendButton.textContent = config.strings.sendButton;
        }
        if (resetButton) {
            resetButton.textContent = config.strings.resetButton;
        }
        textarea.placeholder = config.strings.placeholder;

        let sessionId = null;
        widget.classList.add('mcs-chatbot-widget--ready');

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

            fetch(config.chatEndpoint, {
                method: 'POST',
                headers: buildHeaders(config),
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
                    displayError(widget, history, config.strings.errorMessage);
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
                fetch(config.sessionEndpoint + encodeURIComponent(sessionId), {
                    method: 'DELETE',
                    headers: buildHeaders(config)
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
        document
            .querySelectorAll('.mcs-chatbot-widget')
            .forEach(function (widget) {
                initWidget(widget);
            });
    });
})();
