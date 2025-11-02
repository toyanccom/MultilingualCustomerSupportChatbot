(function () {
  var DEFAULT_STRINGS = {
    widgetTitle: 'Support Assistant',
    inputLabel: 'Ask a question',
    placeholder: 'Type your message…',
    sendButton: 'Send',
    resetButton: 'Clear chat',
    errorMessage: 'Sorry, something went wrong. Please try again.',
    missingConfig: 'Chat configuration is missing. Please verify the widget settings.'
  };

  function resolveConfig(root) {
    var dataset = (root && root.dataset) || {};
    var globalConfig = window.MCSChatbotConfig || {};
    var strings = Object.assign({}, DEFAULT_STRINGS, globalConfig.strings || {});

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

    var chatEndpoint = globalConfig.chatEndpoint || dataset.chatEndpoint || '';
    var sessionEndpoint = globalConfig.sessionEndpoint || dataset.sessionEndpoint || '';

    return {
      chatEndpoint: chatEndpoint,
      sessionEndpoint: sessionEndpoint,
      apiKey: globalConfig.apiKey || dataset.apiKey || '',
      strings: strings
    };
  }

  function appendMessage(container, role, text) {
    var node = document.createElement('div');
    node.className = 'mcs-chatbot-message mcs-chatbot-message--' + role;
    node.textContent = text;
    container.appendChild(node);
    container.scrollTop = container.scrollHeight;
  }

  function displayError(root, history, text) {
    if (history) {
      appendMessage(history, 'system', text);
    }
    root.classList.add('mcs-chatbot-widget--error');
    var form = root.querySelector('.mcs-chatbot-form');
    if (form) {
      Array.prototype.slice.call(form.elements).forEach(function (element) {
        element.disabled = true;
      });
    }
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

  function buildHeaders(config) {
    var headers = { 'Content-Type': 'application/json' };
    if (config.apiKey) {
      headers['X-API-Key'] = config.apiKey;
    }
    return headers;
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

    if (!config.chatEndpoint || !config.sessionEndpoint || !form || !textarea || !history) {
      displayError(root, history, config.strings.missingConfig);
      return;
    }

    if (title) {
      title.textContent = config.strings.widgetTitle;
    }
    if (srLabel) {
      srLabel.textContent = config.strings.inputLabel;
    }
    textarea.placeholder = config.strings.placeholder;
    if (sendButton) {
      sendButton.textContent = config.strings.sendButton;
    }
    if (resetButton) {
      resetButton.textContent = config.strings.resetButton;
    }

    var sessionId = null;
    root.classList.add('mcs-chatbot-widget--ready');

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
          displayError(root, history, config.strings.errorMessage);
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
          headers: buildHeaders(config)
        })
          .catch(function () {})
          .finally(function () {
            sessionId = null;
          });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.mcs-chatbot-widget').forEach(function (root) {
      var config = resolveConfig(root);
      initWidget(root, config);
    });
  });
})();
