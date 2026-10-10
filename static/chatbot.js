
/* ==========================================
   SANJIVNI CHATBOT
   Handles the chat window and user messages
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    // ----------------------------------------
    // 1. Get the HTML elements we need
    // ----------------------------------------

    const chatToggle = document.getElementById("sanjivni-chat-toggle");
    const chatWindow = document.getElementById("sanjivni-chat-window");
    const minimizeButton = document.getElementById("sanjivni-chat-minimize");
    const closeButton = document.getElementById("sanjivni-chat-close");

    const chatForm = document.getElementById("sanjivni-chat-form");
    const messageInput = document.getElementById("sanjivni-chat-input");
    const sendButton = document.getElementById("sanjivni-chat-send");

    const messagesContainer = document.getElementById("sanjivni-chat-messages");
    const suggestionsContainer = document.getElementById(
        "sanjivni-chat-suggestions"
    );

    // Stop safely if the chatbot HTML is not present on this page.
    if (
        !chatToggle ||
        !chatWindow ||
        !chatForm ||
        !messageInput ||
        !messagesContainer
    ) {
        console.warn("Sanjivni chatbot HTML was not found on this page.");
        return;
    }

    // ----------------------------------------
    // 2. Chat settings
    // ----------------------------------------

    /*
     * This is a placeholder endpoint.
     * We will set it to the actual new backend URL
     * after confirming the chat API route.
     *
     * Do not put your Groq API key in this file.
     */
    const CHAT_API_URL = "/api/chat/message";
    
const AUTH_API = "/auth";

const authPanel = document.getElementById("sanjivni-auth-panel");
const authStatus = document.getElementById("sanjivni-auth-status");
const authActions = document.getElementById("sanjivni-auth-actions");
const loginForm = document.getElementById("sanjivni-login-form");
const registerForm = document.getElementById("sanjivni-register-form");
const authError = document.getElementById("sanjivni-auth-error");
const logoutButton = document.getElementById("sanjivni-logout");

const messagesArea = document.getElementById("sanjivni-chat-messages");
const suggestionsArea = document.getElementById("sanjivni-chat-suggestions");
const messageForm = document.getElementById("sanjivni-chat-form");

let authenticatedUser = null;

function showAuthError(message) {
    authError.textContent = message || "";
}

function showAuthView(view) {
    loginForm.hidden = view !== "login";
    registerForm.hidden = view !== "register";
    authActions.hidden = view !== "choices";
    showAuthError("");
}

function updateAuthUI(user) {
    authenticatedUser = user;
    const loggedIn = Boolean(user);

    authStatus.textContent = loggedIn
        ? `Logged in as ${user.name || "Patient"}`
        : "Please log in or create an account to use the assistant.";

    authActions.hidden = loggedIn;
    logoutButton.hidden = !loggedIn;

    loginForm.hidden = true;
    registerForm.hidden = true;

    messagesArea.hidden = !loggedIn;
    suggestionsArea.hidden = !loggedIn;
    messageForm.hidden = !loggedIn;

    if (!loggedIn) {
        showAuthView("choices");
    }
}

async function authRequest(path, method = "GET", body = null) {
    const options = {
        method,
        credentials: "same-origin",
        headers: {}
    };

    if (body !== null) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${AUTH_API}${path}`, options);
    const result = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(result.detail || result.message || "Request failed.");
    }

    return result;
}

document.getElementById("sanjivni-show-login")
    .addEventListener("click", () => showAuthView("login"));

document.getElementById("sanjivni-show-register")
    .addEventListener("click", () => showAuthView("register"));

document.getElementById("sanjivni-login-cancel")
    .addEventListener("click", () => showAuthView("choices"));

document.getElementById("sanjivni-register-cancel")
    .addEventListener("click", () => showAuthView("choices"));

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showAuthError("");

    const identifier =
        document.getElementById("sanjivni-login-identifier").value.trim();
    const password =
        document.getElementById("sanjivni-login-password").value;

    try {
        const result = await authRequest("/login", "POST", {
            identifier,
            password
        });

        loginForm.reset();
        updateAuthUI(result.user);
    } catch (error) {
        showAuthError(error.message);
    }
});

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showAuthError("");

    const formData = new FormData(registerForm);
    const data = Object.fromEntries(formData.entries());

    try {
        await authRequest("/register", "POST", data);

        registerForm.reset();
        showAuthView("login");
        authStatus.textContent =
            "Registration successful. Please log in with your new account.";
    } catch (error) {
        showAuthError(error.message);
    }
});

logoutButton.addEventListener("click", async () => {
    try {
        await authRequest("/logout", "POST");
        updateAuthUI(null);
        messagesArea.replaceChildren();
    } catch (error) {
        showAuthError(error.message);
    }
});

async function checkLoginStatus() {
    try {
        const result = await authRequest("/me");
        updateAuthUI(result.user);
    } catch {
        updateAuthUI(null);
    }
}

checkLoginStatus();


    // Prevent multiple messages from being sent at once.
    let isSendingMessage = false;


    // ----------------------------------------
    // 3. Open the chat window
    // ----------------------------------------

    function openChat() {
        chatWindow.hidden = false;
        chatWindow.setAttribute("aria-hidden", "false");

        chatToggle.setAttribute("aria-expanded", "true");
        chatToggle.setAttribute("aria-label", "Close Sanjivni AI Assistant");

        // Hide the notification dot after opening the chat.
        const notificationDot = chatToggle.querySelector(
            ".chat-notification-dot"
        );

        if (notificationDot) {
            notificationDot.hidden = true;
        }

        // Put the cursor in the message box.
        messageInput.focus();
    }


    // ----------------------------------------
    // 4. Close the chat window
    // ----------------------------------------

    function closeChat() {
        chatWindow.hidden = true;
        chatWindow.setAttribute("aria-hidden", "true");

        chatToggle.setAttribute("aria-expanded", "false");
        chatToggle.setAttribute("aria-label", "Open Sanjivni AI Assistant");

        chatToggle.focus();
    }


    // Clicking the floating icon opens or closes the window.
    chatToggle.addEventListener("click", () => {
        if (chatWindow.hidden) {
            openChat();
        } else {
            closeChat();
        }
    });

    // Both header buttons close/minimize the window for now.
    minimizeButton?.addEventListener("click", closeChat);
    closeButton?.addEventListener("click", closeChat);


    // ----------------------------------------
    // 5. Add a message to the chat safely
    // ----------------------------------------

    function addMessage(text, sender = "assistant") {

        // Create the outer message container.
        const messageRow = document.createElement("div");
        messageRow.classList.add("chat-message");

        // Apply different styling to user and assistant messages.
        if (sender === "user") {
            messageRow.classList.add("user-message");
        } else {
            messageRow.classList.add("assistant-message");
        }

        // Create the avatar.
        const avatar = document.createElement("div");
        avatar.classList.add("message-avatar");
        avatar.setAttribute("aria-hidden", "true");
        avatar.textContent = sender === "user" ? "Y" : "S";

        // Create the content area.
        const content = document.createElement("div");
        content.classList.add("message-content");

        // Create the sender label.
        const senderName = document.createElement("p");
        senderName.classList.add("message-sender");
        senderName.textContent =
            sender === "user" ? "You" : "Sanjivni Assistant";

        // Use textContent to prevent HTML/script injection.
        const bubble = document.createElement("div");
        bubble.classList.add("message-bubble");

        const paragraph = document.createElement("p");
        paragraph.textContent = text;

        bubble.appendChild(paragraph);

        // Add a simple timestamp.
        const time = document.createElement("span");
        time.classList.add("message-time");
        time.textContent = new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
        });

        // Assemble the complete message.
        content.appendChild(senderName);
        content.appendChild(bubble);
        content.appendChild(time);

        messageRow.appendChild(avatar);
        messageRow.appendChild(content);

        messagesContainer.appendChild(messageRow);

        // Scroll down so the latest message is visible.
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }


    // ----------------------------------------
    // 6. Show or remove the typing indicator
    // ----------------------------------------

    function showTypingIndicator() {
        // Avoid showing multiple indicators.
        if (document.getElementById("sanjivni-typing-indicator")) {
            return;
        }

        const typingRow = document.createElement("div");
        typingRow.id = "sanjivni-typing-indicator";
        typingRow.className = "chat-message assistant-message";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "S";
        avatar.setAttribute("aria-hidden", "true");

        const dots = document.createElement("div");
        dots.className = "message-bubble chat-typing";
        dots.setAttribute("aria-label", "Assistant is typing");

        // The three dots are animated by chatbot.css.
        for (let i = 0; i < 3; i++) {
            dots.appendChild(document.createElement("span"));
        }

        typingRow.appendChild(avatar);
        typingRow.appendChild(dots);

        messagesContainer.appendChild(typingRow);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function hideTypingIndicator() {
        const typingIndicator = document.getElementById(
            "sanjivni-typing-indicator"
        );

        typingIndicator?.remove();
    }


    // ----------------------------------------
    // 7. Send a message to the backend
    // ----------------------------------------

    async function sendMessage(message) {

        // Remove spaces from the beginning and end.
        const cleanMessage = message.trim();

        // Do not send an empty message.
        if (!cleanMessage || isSendingMessage) {
            return;
        }

        // Show the user's message immediately.
        addMessage(cleanMessage, "user");

        // Clear the input box.
        messageInput.value = "";
        messageInput.style.height = "auto";

        // Hide suggested questions after the first message.
        if (suggestionsContainer) {
            suggestionsContainer.hidden = true;
        }

        // Lock the send button while waiting for the reply.
        isSendingMessage = true;

        if (sendButton) {
            sendButton.disabled = true;
        }

        showTypingIndicator();

        try {
            /*
             * Send the message to the backend.
             * The endpoint must accept JSON with a "message" field.
             */
            const response = await fetch(CHAT_API_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin",
                body: JSON.stringify({
                    message: cleanMessage
                })
            });

            // Read the server's JSON response.
            const result = await response.json();

            // Display a safe, understandable error for failed requests.
            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error(
                        "Please log in to use the healthcare assistant."
                    );
                }

                throw new Error(
                    result.detail || "The message could not be sent."
                );
            }

            /*
             * Our current chat API returns:
             * { "success": true, "reply": "..." }
             *
             * We will adjust this if the new backend uses a
             * different response format.
             */
            const reply = result.reply;

            if (typeof reply !== "string" || !reply.trim()) {
                throw new Error("The assistant returned an empty response.");
            }

            addMessage(reply, "assistant");

        } catch (error) {
            console.error("Sanjivni chat request failed:", error);

            // Display a user-friendly message instead of a blank chat.
            addMessage(
                error.message ||
                "Sorry, the assistant is temporarily unavailable. Please try again.",
                "assistant"
            );

        } finally {
            // Always remove the typing indicator and unlock the button.
            hideTypingIndicator();

            isSendingMessage = false;

            if (sendButton) {
                sendButton.disabled = false;
            }

            messageInput.focus();
        }
    }


    // ----------------------------------------
    // 8. Handle the message form
    // ----------------------------------------

    chatForm.addEventListener("submit", (event) => {
        event.preventDefault();

        sendMessage(messageInput.value);
    });


    // ----------------------------------------
    // 9. Automatically grow the text box
    // ----------------------------------------

    messageInput.addEventListener("input", () => {
        messageInput.style.height = "auto";

        // Keep the text box within the maximum height from CSS.
        messageInput.style.height =
            Math.min(messageInput.scrollHeight, 110) + "px";
    });


    // ----------------------------------------
    // 10. Handle suggested questions
    // ----------------------------------------

    if (suggestionsContainer) {
        suggestionsContainer.addEventListener("click", (event) => {

            // Find the suggestion button that was clicked.
            const button = event.target.closest("button[data-message]");

            if (!button || isSendingMessage) {
                return;
            }

            // Use the suggestion as a normal chat message.
            const suggestedMessage = button.dataset.message;

            openChat();
            sendMessage(suggestedMessage);
        });
    }


    // ----------------------------------------
    // 11. Support the Escape key
    // ----------------------------------------

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !chatWindow.hidden) {
            closeChat();
        }
    });


    // ----------------------------------------
    // 12. Initialization complete
    // ----------------------------------------

    console.info("Sanjivni chatbot frontend initialized.");

});
