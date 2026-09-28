let currentSessionId = null;


/* =========================
   DOM ELEMENTS
========================= */

const messagesContainer =
    document.getElementById("messagesContainer");

const messageInput =
    document.getElementById("messageInput");

const sendBtn =
    document.getElementById("sendBtn");

const newChatBtn =
    document.getElementById("newChatBtn");

const todayChats =
    document.getElementById("todayChats");

const yesterdayChats =
    document.getElementById("yesterdayChats");

const olderChats =
    document.getElementById("olderChats");

const menuBtn =
    document.getElementById("menuBtn");

const sidebar =
    document.getElementById("sidebar");

const closeSidebarBtn =
    document.getElementById("closeSidebarBtn");

const welcomeScreen =
    document.getElementById("welcomeScreen");


/* =========================
   INITIALIZATION
========================= */

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        await loadChatHistory();

        setupSuggestions();
        setupTextarea();
    }
);


/* =========================
   HISTORY
========================= */

async function loadChatHistory() {

    try {

        const response = await fetch(
            "/chatbot/history",
            {
                credentials: "include"
            }
        );

        if (!response.ok) {

            if (response.status === 401) {
                window.location.href = "/";
                return;
            }

            throw new Error(
                "Unable to load chat history."
            );
        }

        const data = await response.json();

        renderChatHistory(data.sessions || []);

    } catch (error) {

        console.error(
            "History loading error:",
            error
        );
    }
}


function renderChatHistory(sessions) {

    todayChats.innerHTML = "";
    yesterdayChats.innerHTML = "";
    olderChats.innerHTML = "";

    if (!sessions.length) {

        todayChats.innerHTML =
            `<div class="empty-history">
                No conversations yet
             </div>`;

        return;
    }

    sessions.forEach(session => {

        const date =
            new Date(session.started_at);

        const category =
            getDateCategory(date);

        const item =
            createChatItem(session);

        if (category === "today") {
            todayChats.appendChild(item);
        }

        else if (category === "yesterday") {
            yesterdayChats.appendChild(item);
        }

        else {
            olderChats.appendChild(item);
        }
    });
}


function getDateCategory(date) {

    const now = new Date();

    const today = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate()
    );

    const yesterday = new Date(today);

    yesterday.setDate(
        yesterday.getDate() - 1
    );

    const target = new Date(
        date.getFullYear(),
        date.getMonth(),
        date.getDate()
    );

    if (
        target.getTime() ===
        today.getTime()
    ) {
        return "today";
    }

    if (
        target.getTime() ===
        yesterday.getTime()
    ) {
        return "yesterday";
    }

    return "older";
}


/* =========================
   CHAT ITEM
========================= */

function createChatItem(session) {

    const item =
        document.createElement("div");

    item.className = "chat-item";

    item.dataset.sessionId =
        session.id;

    const title =
        document.createElement("div");

    title.className = "chat-title";

    title.textContent =
        `Conversation ${session.id}`;

    const deleteBtn =
        document.createElement("button");

    deleteBtn.className =
        "delete-chat-btn";

    deleteBtn.textContent = "🗑";

    deleteBtn.title =
        "Delete conversation";

    deleteBtn.addEventListener(
        "click",
        async (event) => {

            event.stopPropagation();

            await deleteChat(
                session.id
            );
        }
    );

    item.appendChild(title);
    item.appendChild(deleteBtn);

    item.addEventListener(
        "click",
        async () => {

            await openChat(
                session.id
            );
        }
    );

    return item;
}


/* =========================
   OPEN CHAT
========================= */

async function openChat(sessionId) {

    try {

        const response =
            await fetch(
                `/chatbot/history/${sessionId}`,
                {
                    credentials: "include"
                }
            );

        if (!response.ok) {
            throw new Error(
                "Unable to open conversation."
            );
        }

        const data =
            await response.json();

        currentSessionId =
            sessionId;

        clearMessages();

        (data.messages || []).forEach(
            message => {

                addMessageToUI(
                    message.role,
                    message.message
                );
            }
        );

        document
            .querySelectorAll(".chat-item")
            .forEach(item => {

                item.classList.toggle(
                    "active",
                    Number(
                        item.dataset.sessionId
                    ) === sessionId
                );
            });

        closeMobileSidebar();

    } catch (error) {

        console.error(
            "Open chat error:",
            error
        );
    }
}


/* =========================
   NEW CHAT
========================= */

newChatBtn.addEventListener(
    "click",
    async () => {

        try {

            const response =
                await fetch(
                    "/chatbot/history/new",
                    {
                        method: "POST",
                        credentials: "include"
                    }
                );

            if (!response.ok) {
                throw new Error(
                    "Unable to create new chat."
                );
            }

            const data =
                await response.json();

            currentSessionId =
                data.session_id;

            clearMessages();

            await loadChatHistory();

        } catch (error) {

            console.error(
                "New chat error:",
                error
            );
        }
    }
);


/* =========================
   DELETE CHAT
========================= */

async function deleteChat(sessionId) {

    const confirmed =
        confirm(
            "Delete this conversation?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(
                `/chatbot/history/${sessionId}`,
                {
                    method: "DELETE",
                    credentials: "include"
                }
            );

        if (!response.ok) {
            throw new Error(
                "Unable to delete chat."
            );
        }

        if (
            currentSessionId ===
            sessionId
        ) {

            currentSessionId = null;

            clearMessages();
        }

        await loadChatHistory();

    } catch (error) {

        console.error(
            "Delete chat error:",
            error
        );
    }
}


/* =========================
   SEND MESSAGE
========================= */

async function sendMessage() {

    const message =
        messageInput.value.trim();

    if (!message) {
        return;
    }

    addMessageToUI(
        "user",
        message
    );

    messageInput.value = "";

    autoResizeTextarea();

    showTypingIndicator();

    try {

        const response =
            await fetch(
                "/chatbot/message",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    credentials: "include",

                    body: JSON.stringify({
                        message: message
                    })
                }
            );

        if (!response.ok) {

            if (
                response.status === 401
            ) {
                window.location.href =
                    "/";
                return;
            }

            throw new Error(
                "Unable to send message."
            );
        }

        const data =
            await response.json();

        removeTypingIndicator();

        if (data.session_id) {

            currentSessionId =
                data.session_id;
        }

        addMessageToUI(
            "assistant",
            data.message ||
            "I was unable to generate a response."
        );

        await loadChatHistory();

    } catch (error) {

        removeTypingIndicator();

        console.error(
            "Send message error:",
            error
        );

        addMessageToUI(
            "assistant",
            "Sorry, something went wrong. Please try again."
        );
    }
}


/* =========================
   MESSAGE UI
========================= */

function addMessageToUI(
    role,
    message
) {

    if (welcomeScreen) {
        welcomeScreen.style.display =
            "none";
    }

    const row =
        document.createElement("div");

    row.className =
        `message-row ${role}`;

    const bubble =
        document.createElement("div");

    bubble.className =
        "message-bubble";

    bubble.textContent =
        message;

    row.appendChild(bubble);

    messagesContainer.appendChild(row);

    scrollToBottom();
}


function clearMessages() {

    messagesContainer.innerHTML = "";

    const welcome =
        document.createElement("div");

    welcome.className =
        "welcome-screen";

    welcome.id =
        "welcomeScreen";

    welcome.innerHTML = `
        <div class="welcome-icon">🏥</div>

        <h1>
            Welcome to Sanjivni Clinic
        </h1>

        <p>
            Tell me about your health concern,
            and I can help you find the relevant
            department and doctor.
        </p>

        <div class="suggestion-container">

            <button class="suggestion">
                I have a skin problem
            </button>

            <button class="suggestion">
                I have chest pain
            </button>

            <button class="suggestion">
                I need an orthopedic doctor
            </button>

        </div>
    `;

    messagesContainer.appendChild(
        welcome
    );

    setupSuggestions();
}


/* =========================
   TYPING INDICATOR
========================= */

function showTypingIndicator() {

    const row =
        document.createElement("div");

    row.className =
        "message-row assistant";

    row.id =
        "typingIndicator";

    const bubble =
        document.createElement("div");

    bubble.className =
        "message-bubble";

    bubble.textContent =
        "Sanjivni AI is typing...";

    row.appendChild(bubble);

    messagesContainer.appendChild(row);

    scrollToBottom();
}


function removeTypingIndicator() {

    const indicator =
        document.getElementById(
            "typingIndicator"
        );

    if (indicator) {
        indicator.remove();
    }
}


/* =========================
   SUGGESTIONS
========================= */

function setupSuggestions() {

    document
        .querySelectorAll(".suggestion")
        .forEach(button => {

            button.onclick = () => {

                messageInput.value =
                    button.textContent.trim();

                sendMessage();
            };
        });
}


/* =========================
   TEXTAREA
========================= */

function setupTextarea() {

    messageInput.addEventListener(
        "input",
        autoResizeTextarea
    );

    messageInput.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendMessage();
            }
        }
    );
}


function autoResizeTextarea() {

    messageInput.style.height =
        "auto";

    messageInput.style.height =
        Math.min(
            messageInput.scrollHeight,
            120
        ) + "px";
}


/* =========================
   MOBILE SIDEBAR
========================= */

menuBtn.addEventListener(
    "click",
    () => {

        sidebar.classList.add(
            "open"
        );
    }
);


closeSidebarBtn.addEventListener(
    "click",
    closeMobileSidebar
);


function closeMobileSidebar() {

    sidebar.classList.remove(
        "open"
    );
}


/* =========================
   SEND BUTTON
========================= */

sendBtn.addEventListener(
    "click",
    sendMessage
);


/* =========================
   SCROLL
========================= */

function scrollToBottom() {

    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;
}