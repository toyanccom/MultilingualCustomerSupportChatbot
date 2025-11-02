(function () {
  function selectConfig() {
    if (window.MCSChatbotConfig) {
      return window.MCSChatbotConfig;
    }
    var root = document.querySelector('[data-chat-endpoint][data-session-endpoint]');
    if (!root) {
      return null;
    }
    return {
      chatEndpoint: root.getAttribute('data-chat-endpoint'),
      sessionEndpoint: root.getAttribute('data-session-endpoint'),
      strings: {
        widgetTitle: 'Support Assistant',
        inputLabel: 'Ask a question',
        placeholder: 'Type your message…',
        sendButton: 'Send',
        resetButton: 'Clear chat',
        errorMessage: 'Sorry, something went wrong. Please try again.'
      }
    };
  }

  function appendMessage(container, role, text) {
    var node = document.createElement('div');
    node.className = 'mcs-chatbot-message mcs-chatbot-message--' + role;
    node.textContent = text;
    container.appendChild(node);
    container.scrollTop = container.scrollHeight;
  }

  function setLoading(button, loading) {
    if (!button) {
      return;
    }
    button.disabled = loading;
    if (loading) {
      button.setAttribute('aria-busy', 'true');
    } else {
      button.removeAttribute('aria-busy');
    }
  }

  function initWidget(root, config) {
    if (!root || !config) {
      return;
    }
    var history = root.querySelector('.mcs-chatbot-history');
    var form = root.querySelector('.mcs-chatbot-form');
    var textarea = root.querySelector('.mcs-chatbot-input');
    var sendButton = root.querySelector('.mcs-chatbot-send');
    var resetButton = root.querySelector('.mcs-chatbot-reset');
    var title = root.querySelector('.mcs-chatbot-title');
    var srLabel = root.querySelector('.mcs-chatbot-label .visually-hidden');

    if (title) {
      title.textContent = config.strings.widgetTitle;
    }
    if (srLabel) {
      srLabel.textContent = config.strings.inputLabel;
    }
    if (textarea) {
      textarea.placeholder = config.strings.placeholder;
    }
    if (sendButton) {
      sendButton.textContent = config.strings.sendButton;
    }
    if (resetButton) {
      resetButton.textContent = config.strings.resetButton;
    }

    var sessionId = null;

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var message = textarea.value.trim();
      if (!message) {
        return;
      }
      appendMessage(history, 'user', message);
      textarea.value = '';
      setLoading(sendButton, true);
      var payload = { message: message };
      if (sessionId) {
        payload.session_id = sessionId;
      }
      fetch(config.chatEndpoint, {
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
          appendMessage(history, 'system', config.strings.errorMessage);
        })
        .finally(function () {
          setLoading(sendButton, false);
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
          headers: { 'Content-Type': 'application/json' }
        })
          .catch(function () {})
          .finally(function () {
            sessionId = null;
          });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var config = selectConfig();
    if (!config) {
      return;
    }
    document.querySelectorAll('.mcs-chatbot-widget').forEach(function (root) {
      initWidget(root, config);
    });
  });
})();
