document.addEventListener("DOMContentLoaded", () => {

    /* =========================================================
       STYLES
    ========================================================= */

    const style = document.createElement("style");

    style.textContent = `

        #chatbot-button {
            position: fixed;
            right: 25px;
            bottom: 25px;

            height: 72px;
            min-width: 72px;
            padding: 0 18px;

            border: none;
            border-radius: 40px;

            background: linear-gradient(135deg, #1f7a64, #17604f);
            color: white;

            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;

            cursor: pointer;

            box-shadow: 0 10px 30px rgba(31, 122, 100, 0.35);

            z-index: 9999;

            transition: 0.25s ease;
        }

        #chatbot-button:hover {
            transform: translateY(-3px) scale(1.03);
            box-shadow: 0 15px 38px rgba(31, 122, 100, 0.45);
        }

        .chatbot-icon {
            width: 44px;
            height: 44px;

            border-radius: 50%;

            background: rgba(255,255,255,0.16);

            display: flex;
            align-items: center;
            justify-content: center;

            font-size: 23px;
        }

        .chatbot-label {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }

        .chatbot-name {
            font-size: 14px;
            font-weight: 700;
        }

        .chatbot-status {
            margin-top: 4px;
            font-size: 11px;
        }

        .online-dot {
            display: inline-block;

            width: 7px;
            height: 7px;

            margin-right: 5px;

            border-radius: 50%;

            background: #8ff0b8;
        }


        /* CHAT WINDOW */

        #chatbot-box {
            position: fixed;

            right: 25px;
            bottom: 110px;

            width: 380px;
            height: 560px;

            background: white;

            border-radius: 20px;

            overflow: hidden;

            display: none;
            flex-direction: column;

            border: 1px solid #e3e8e6;

            box-shadow: 0 20px 60px rgba(0,0,0,0.22);

            z-index: 10000;

            font-family: Arial, Helvetica, sans-serif;
        }


        /* HEADER */

        #chatbot-header {
            min-height: 72px;

            padding: 0 18px;

            background: linear-gradient(135deg, #1f7a64, #17604f);

            color: white;

            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chatbot-header-left {
            display: flex;
            align-items: center;
            gap: 11px;
        }

        .chatbot-header-icon {
            width: 42px;
            height: 42px;

            border-radius: 50%;

            background: rgba(255,255,255,0.16);

            display: flex;
            align-items: center;
            justify-content: center;

            font-size: 21px;
        }

        .chatbot-header-title {
            font-size: 16px;
            font-weight: 700;
        }

        .chatbot-header-status {
            margin-top: 4px;
            font-size: 11px;
            opacity: 0.9;
        }

        #chatbot-close {
            width: 36px;
            height: 36px;

            border: none;
            border-radius: 50%;

            background: rgba(255,255,255,0.12);

            color: white;

            font-size: 25px;

            cursor: pointer;
        }


        /* CONTENT */

        #chatbot-messages {
            flex: 1;

            padding: 18px;

            overflow-y: auto;

            background: #f5f8f7;
        }


        /* LOGIN */

        .chatbot-login-card {
            background: white;

            border: 1px solid #e1e7e4;

            border-radius: 16px;

            padding: 20px;

            box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        }

        .chatbot-login-icon {
            width: 48px;
            height: 48px;

            margin-bottom: 12px;

            border-radius: 50%;

            background: #eaf5f1;

            display: flex;
            align-items: center;
            justify-content: center;

            font-size: 23px;
        }

        .chatbot-login-title {
            color: #174d40;

            font-size: 18px;
            font-weight: 700;

            margin-bottom: 6px;
        }

        .chatbot-login-text {
            color: #666;

            font-size: 13px;

            line-height: 1.5;

            margin-bottom: 18px;
        }

        .chatbot-login-field {
            margin-bottom: 12px;
        }

        .chatbot-login-field label {
            display: block;

            margin-bottom: 5px;

            font-size: 12px;

            color: #555;

            font-weight: 600;
        }

        .chatbot-login-field input {
            width: 100%;

            height: 42px;

            padding: 0 12px;

            border: 1px solid #d4ddda;

            border-radius: 10px;

            box-sizing: border-box;

            outline: none;

            font-size: 13px;
        }

        .chatbot-login-field input:focus {
            border-color: #1f7a64;

            box-shadow: 0 0 0 3px rgba(31,122,100,0.08);
        }

        #chatbot-login-button {
            width: 100%;

            height: 44px;

            border: none;

            border-radius: 10px;

            background: #1f7a64;

            color: white;

            font-size: 14px;

            font-weight: 600;

            cursor: pointer;
        }

        #chatbot-login-button:hover {
            background: #165b4c;
        }
        .chatbot-register-link {
            margin-top: 14px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }

        .chatbot-register-link button {
            border: none;
            background: transparent;
            color: #1f7a64;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
        }

        .chatbot-register-link button:hover {
            text-decoration: underline;
        }
                #chatbot-login-error {
            display: none;

            margin-top: 10px;

            padding: 9px;

            border-radius: 8px;

            background: #fff1f1;

            color: #b42318;

            font-size: 12px;
        }


        /* WELCOME */

        .chatbot-welcome {
            padding: 15px;

            background: white;

            border: 1px solid #e1e7e4;

            border-radius: 15px;
        }

        .chatbot-welcome-title {
            color: #174d40;

            font-size: 15px;

            font-weight: 700;

            margin-bottom: 7px;
        }

        .chatbot-welcome-text {
            color: #555;

            font-size: 13px;

            line-height: 1.5;
        }


        /* QUICK ACTIONS */

        .chatbot-quick-actions {
            display: flex;

            flex-wrap: wrap;

            gap: 7px;

            margin-top: 13px;
        }

        .chatbot-quick-btn {
            border: 1px solid #cfe0da;

            background: white;

            color: #17604f;

            padding: 8px 10px;

            border-radius: 20px;

            font-size: 11px;

            cursor: pointer;
        }

        .chatbot-quick-btn:hover {
            background: #eaf5f1;

            border-color: #1f7a64;
        }


        /* USER / BOT */

        .bot-message,
        .user-message {
            max-width: 82%;

            padding: 11px 14px;

            border-radius: 15px;

            font-size: 14px;

            line-height: 1.5;

            margin-bottom: 12px;

            white-space: pre-wrap;
        }

        .bot-message {
            background: white;

            color: #222;

            border: 1px solid #e1e7e4;

            border-bottom-left-radius: 5px;

            margin-right: auto;
        }

        .user-message {
            background: #1f7a64;

            color: white;

            border-bottom-right-radius: 5px;

            margin-left: auto;
        }


        /* TYPING */

        .typing-message {
            display: inline-flex;

            padding: 12px 15px;

            background: white;

            border: 1px solid #e1e7e4;

            border-radius: 15px;

            margin-bottom: 12px;
        }

        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dots span {
            width: 6px;
            height: 6px;

            border-radius: 50%;

            background: #1f7a64;

            animation: typing 1.2s infinite;
        }

        .typing-dots span:nth-child(2) {
            animation-delay: 0.15s;
        }

        .typing-dots span:nth-child(3) {
            animation-delay: 0.3s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                opacity: 0.3;
                transform: translateY(0);
            }

            30% {
                opacity: 1;
                transform: translateY(-3px);
            }
        }


        /* INPUT */

        #chatbot-input-area {
            display: flex;

            gap: 8px;

            padding: 12px;

            background: white;

            border-top: 1px solid #e5e9e7;
        }

        #chatbot-input {
            flex: 1;

            min-width: 0;

            height: 44px;

            padding: 0 13px;

            border: 1px solid #d4ddda;

            border-radius: 12px;

            outline: none;

            font-size: 14px;
        }

        #chatbot-input:focus {
            border-color: #1f7a64;
        }

        #chatbot-send {
            height: 44px;

            padding: 0 17px;

            border: none;

            border-radius: 12px;

            background: #1f7a64;

            color: white;

            font-weight: 600;

            cursor: pointer;
        }

        #chatbot-send:disabled {
            opacity: 0.6;
        }


        /* LOGOUT */

        .chatbot-logout {
            margin-top: 12px;

            text-align: center;
        }

        .chatbot-logout button {
            border: none;

            background: transparent;

            color: #777;

            font-size: 11px;

            cursor: pointer;

            text-decoration: underline;
        }


        /* MOBILE */

        @media (max-width: 600px) {

            #chatbot-button {
                right: 18px;
                bottom: 18px;

                width: 64px;
                min-width: 64px;

                height: 64px;

                padding: 0;
            }

            .chatbot-label {
                display: none;
            }

            #chatbot-box {
                left: 10px;
                right: 10px;

                bottom: 92px;

                width: auto;

                height: calc(100vh - 125px);

                max-height: 600px;
            }
        }
    `;

    document.head.appendChild(style);


    /* =========================================================
       FLOATING BUTTON
    ========================================================= */

    const chatButton = document.createElement("button");

    chatButton.id = "chatbot-button";

    chatButton.type = "button";

    chatButton.title = "Chat with Sanjeevani AI";

    chatButton.innerHTML = `
        <span class="chatbot-icon">🤖</span>

        <span class="chatbot-label">
            <span class="chatbot-name">
                Sanjeevani AI
            </span>

            <span class="chatbot-status">
                <span class="online-dot"></span>
                Online • Ask me
            </span>
        </span>
    `;


    /* =========================================================
       CHAT WINDOW
    ========================================================= */

    const chatBox = document.createElement("div");

    chatBox.id = "chatbot-box";

    chatBox.innerHTML = `

        <div id="chatbot-header">

            <div class="chatbot-header-left">

                <div class="chatbot-header-icon">
                    🤖
                </div>

                <div>

                    <div class="chatbot-header-title">
                        Sanjeevani AI
                    </div>

                    <div class="chatbot-header-status">
                        <span class="online-dot"></span>
                        Clinic Assistant
                    </div>

                </div>

            </div>

            <button
                id="chatbot-close"
                type="button"
            >
                ×
            </button>

        </div>


        <div id="chatbot-messages"></div>


        <div id="chatbot-input-area">

            <input
                id="chatbot-input"
                type="text"
                placeholder="Ask Sanjeevani AI..."
                autocomplete="off"
            />

            <button
                id="chatbot-send"
                type="button"
            >
                Send
            </button>

        </div>
    `;


    document.body.appendChild(chatButton);

    document.body.appendChild(chatBox);


    /* =========================================================
       ELEMENTS
    ========================================================= */

    const messages =
        document.getElementById("chatbot-messages");

    const input =
        document.getElementById("chatbot-input");

    const sendButton =
        document.getElementById("chatbot-send");


    /* =========================================================
       OPEN / CLOSE
    ========================================================= */

    chatButton.addEventListener("click", () => {

        if (chatBox.style.display === "flex") {

            chatBox.style.display = "none";

        } else {

            chatBox.style.display = "flex";

            input.focus();

            checkLoginStatus();
        }

    });


    document
        .getElementById("chatbot-close")
        .addEventListener("click", () => {

            chatBox.style.display = "none";

        });


    /* =========================================================
       CHECK LOGIN STATUS
    ========================================================= */

    async function checkLoginStatus() {

        try {

            const response =
                await fetch("/auth/me");

            const data =
                await response.json();

            if (
                data.authenticated === true &&
                data.user
            ) {

                showChatInterface(data.user);

            } else {

                showLoginInterface();

            }

        } catch (error) {

            console.error(
                "Login status check failed:",
                error
            );

            showLoginInterface();

        }

    }


    /* =========================================================
       SHOW LOGIN
    ========================================================= */

    function showLoginInterface() {

        messages.innerHTML = `

            <div class="chatbot-login-card">

                <div class="chatbot-login-icon">
                    🔐
                </div>

                <div class="chatbot-login-title">
                    Login to Sanjeevani AI
                </div>

                <div class="chatbot-login-text">
                    Please login with your registered
                    phone number or email to use the
                    clinic assistant.
                </div>


                <div class="chatbot-login-field">

                    <label>
                        Phone / Email
                    </label>

                    <input
                        id="chatbot-login-identifier"
                        type="text"
                        placeholder="Enter phone or email"
                        autocomplete="username"
                    />

                </div>


                <div class="chatbot-login-field">

                    <label>
                        Password
                    </label>

                    <input
                        id="chatbot-login-password"
                        type="password"
                        placeholder="Enter password"
                        autocomplete="current-password"
                    />

                </div>


                <button
                    id="chatbot-login-button"
                    type="button"
                >
                    Login to Continue
                </button>
                <div class="chatbot-register-link">
                    New patient?
                    <button
                        id="chatbot-register-button"
                        type="button"
                    >
                        Create Account
                    </button>
                </div>


                <div id="chatbot-login-error"></div>

            </div>
        `;


        document
            .getElementById("chatbot-login-button")
            .addEventListener(
                "click",
                loginPatient
            );


        document
            .getElementById("chatbot-login-password")
            .addEventListener(
                "keydown",
                (event) => {

                    if (event.key === "Enter") {
                        loginPatient();
                    }

                }
            );
        document
            .getElementById("chatbot-register-button")
            .addEventListener(
                "click",
                showRegisterInterface
            );
    }

    function showRegisterInterface() {

            messages.innerHTML = `

                <div class="chatbot-login-card">

                    <div class="chatbot-login-icon">
                        📝
                    </div>

                    <div class="chatbot-login-title">
                        Create Patient Account
                    </div>

                    <div class="chatbot-login-text">
                        Register your account to use Sanjeevani AI.
                    </div>

                    <div class="chatbot-login-field">
                        <label>Name *</label>
                        <input
                            id="chatbot-register-name"
                            type="text"
                            placeholder="Enter your full name"
                            autocomplete="name"
                        />
                    </div>

                    <div class="chatbot-login-field">
                        <label>Phone *</label>
                        <input
                            id="chatbot-register-phone"
                            type="tel"
                            placeholder="Enter phone number"
                            autocomplete="tel"
                        />
                    </div>

                    <div class="chatbot-login-field">
                        <label>Email</label>
                        <input
                            id="chatbot-register-email"
                            type="email"
                            placeholder="Enter email"
                            autocomplete="email"
                        />
                    </div>

                    <div class="chatbot-login-field">
                        <label>Password *</label>
                        <input
                            id="chatbot-register-password"
                            type="password"
                            placeholder="Create password"
                            autocomplete="new-password"
                        />
                    </div>

                    <div class="chatbot-login-field">
                        <label>Date of Birth</label>
                        <input
                            id="chatbot-register-dob"
                            type="date"
                        />
                    </div>

                    <div class="chatbot-login-field">
                        <label>Gender</label>
                        <input
                            id="chatbot-register-gender"
                            type="text"
                            placeholder="Male / Female / Other"
                        />
                    </div>

                    <div class="chatbot-login-field">
                        <label>Address</label>
                        <input
                            id="chatbot-register-address"
                            type="text"
                            placeholder="Enter address"
                        />
                    </div>

                    <button
                        id="chatbot-register-submit"
                        type="button"
                    >
                        Create Account
                    </button>

                    <div id="chatbot-register-error"></div>

                    <div class="chatbot-register-link">
                        Already have an account?
                        <button
                            id="chatbot-back-login"
                            type="button"
                        >
                            Login
                        </button>
                    </div>

                </div>
            `;

            document
                .getElementById("chatbot-register-submit")
                .addEventListener(
                    "click",
                    registerPatient
                );

            document
                .getElementById("chatbot-back-login")
                .addEventListener(
                    "click",
                    showLoginInterface
                );
        }    
    async function registerPatient() {

        const name = document
            .getElementById("chatbot-register-name")
            .value
            .trim();

        const phone = document
            .getElementById("chatbot-register-phone")
            .value
            .trim();

        const email = document
            .getElementById("chatbot-register-email")
            .value
            .trim();

        const password = document
            .getElementById("chatbot-register-password")
            .value;

        const dob = document
            .getElementById("chatbot-register-dob")
            .value;

        const gender = document
            .getElementById("chatbot-register-gender")
            .value
            .trim();

        const address = document
            .getElementById("chatbot-register-address")
            .value
            .trim();

        const registerButton =
            document.getElementById(
                "chatbot-register-submit"
            );

        const errorBox =
            document.getElementById(
                "chatbot-register-error"
            );

        if (!name || !phone || !password) {

            errorBox.textContent =
                "Name, phone aur password required hai.";

            errorBox.style.display = "block";

            return;
        }

        registerButton.disabled = true;
        registerButton.textContent = "Creating Account...";
        errorBox.style.display = "none";

        try {

            const response = await fetch(
                "/auth/register",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    credentials: "same-origin",

                    body: JSON.stringify({
                        name: name,
                        phone: phone,
                        email: email || null,
                        password: password,
                        dob: dob || null,
                        gender: gender || null,
                        address: address || null
                    })
                }
            );

            const data = await response.json();

            if (!response.ok || !data.success) {

                errorBox.textContent =
                    data.message ||
                    "Registration failed. Please try again.";

                errorBox.style.display = "block";

                registerButton.disabled = false;
                registerButton.textContent =
                    "Create Account";

                return;
            }

            /*
            * Registration successful
            * Now show login screen
            */

            showLoginInterface();

            const loginIdentifier =
                document.getElementById(
                    "chatbot-login-identifier"
                );

            loginIdentifier.value = phone;

            const loginError =
                document.getElementById(
                    "chatbot-login-error"
                );

            loginError.textContent =
                "Account created successfully. Please login.";

            loginError.style.display = "block";

            loginError.style.background = "#eaf5f1";
            loginError.style.color = "#17604f";

        } catch (error) {

            console.error(
                "Registration error:",
                error
            );

            errorBox.textContent =
                "Unable to connect to the server.";

            errorBox.style.display = "block";

            registerButton.disabled = false;
            registerButton.textContent =
                "Create Account";
        }
    }
    /* =========================================================
       PATIENT LOGIN
    ========================================================= */

    async function loginPatient() {

        const identifier =
            document
                .getElementById(
                    "chatbot-login-identifier"
                )
                .value
                .trim();


        const password =
            document
                .getElementById(
                    "chatbot-login-password"
                )
                .value;


        const loginButton =
            document.getElementById(
                "chatbot-login-button"
            );


        const errorBox =
            document.getElementById(
                "chatbot-login-error"
            );


        if (!identifier || !password) {

            errorBox.textContent =
                "Please enter phone/email and password.";

            errorBox.style.display = "block";

            return;
        }


        loginButton.disabled = true;

        loginButton.textContent =
            "Logging in...";

        errorBox.style.display = "none";


        try {

            const response =
                await fetch(
                    "/auth/login",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        credentials: "same-origin",

                        body: JSON.stringify({
                            identifier: identifier,
                            password: password
                        })
                    }
                );


            const data =
                await response.json();


            if (!response.ok || !data.success) {

                errorBox.textContent =
                    data.message ||
                    "Invalid phone/email or password.";

                errorBox.style.display = "block";

                loginButton.disabled = false;

                loginButton.textContent =
                    "Login to Continue";

                return;
            }


            /* Login successful */

            showChatInterface(
                data.user
            );


        } catch (error) {

            console.error(
                "Login error:",
                error
            );


            errorBox.textContent =
                "Unable to connect to the server.";

            errorBox.style.display = "block";


            loginButton.disabled = false;

            loginButton.textContent =
                "Login to Continue";
        }

    }


    /* =========================================================
       SHOW CHAT INTERFACE
    ========================================================= */

    function showChatInterface(user) {

        messages.innerHTML = `

            <div class="chatbot-welcome">

                <div class="chatbot-welcome-title">
                    👋 Namaste ${escapeHtml(user.name || "Patient")}!
                </div>

                <div class="chatbot-welcome-text">

                    Main Sanjeevani Clinic ka AI Assistant hoon.
                    Aap doctors, appointments, departments
                    aur clinic services ke baare mein pooch sakte hain.

                </div>


                <div class="chatbot-quick-actions">

                    <button
                        class="chatbot-quick-btn"
                        data-message="Mujhe doctors ke baare mein batao"
                    >
                        👨‍⚕️ Find Doctor
                    </button>

                    <button
                        class="chatbot-quick-btn"
                        data-message="Mujhe appointment book karni hai"
                    >
                        📅 Appointment
                    </button>

                    <button
                        class="chatbot-quick-btn"
                        data-message="Clinic ke departments batao"
                    >
                        🏥 Departments
                    </button>

                    <button
                        class="chatbot-quick-btn"
                        data-message="Meri appointments batao"
                    >
                        📋 My Appointments
                    </button>

                </div>


                <div class="chatbot-logout">

                    <button
                        id="chatbot-logout-button"
                        type="button"
                    >
                        Logout
                    </button>

                </div>

            </div>
        `;


        document
            .querySelectorAll(".chatbot-quick-btn")
            .forEach((button) => {

                button.addEventListener(
                    "click",
                    () => {

                        sendMessage(
                            button.getAttribute(
                                "data-message"
                            )
                        );

                    }
                );

            });


        document
            .getElementById(
                "chatbot-logout-button"
            )
            .addEventListener(
                "click",
                logoutPatient
            );

    }


    /* =========================================================
       LOGOUT
    ========================================================= */

    async function logoutPatient() {

        try {

            await fetch(
                "/auth/logout",
                {
                    method: "POST",
                    credentials: "same-origin"
                }
            );

            showLoginInterface();

        } catch (error) {

            console.error(
                "Logout error:",
                error
            );

        }

    }


    /* =========================================================
       SEND MESSAGE
    ========================================================= */

    sendButton.addEventListener(
        "click",
        () => sendMessage()
    );


    input.addEventListener(
        "keydown",
        (event) => {

            if (event.key === "Enter") {

                event.preventDefault();

                sendMessage();

            }

        }
    );


    async function sendMessage(customMessage = null) {

        const message =
            customMessage ||
            input.value.trim();


        if (!message) {
            return;
        }


        addMessage(
            message,
            "user-message"
        );


        input.value = "";


        sendButton.disabled = true;

        sendButton.textContent = "...";


        const typing =
            showTyping();


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

                        credentials:
                            "same-origin",

                        body: JSON.stringify({
                            message: message
                        })
                    }
                );


            const data =
                await response.json();


            typing.remove();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Something went wrong."
                );

            }


            const reply =
                data.response ||
                data.message ||
                data.reply ||
                "Sorry, mujhe response nahi mila.";


            addMessage(
                reply,
                "bot-message"
            );


        } catch (error) {

            console.error(
                "Chatbot error:",
                error
            );


            typing.remove();


            addMessage(
                error.message ||
                "Chatbot se connection nahi ho pa raha.",
                "bot-message"
            );

        }


        sendButton.disabled = false;

        sendButton.textContent = "Send";

        input.focus();

    }


    /* =========================================================
       ADD MESSAGE
    ========================================================= */

    function addMessage(
        message,
        className
    ) {

        const element =
            document.createElement("div");


        element.className =
            className;


        element.textContent =
            message;


        messages.appendChild(
            element
        );


        messages.scrollTop =
            messages.scrollHeight;

    }


    /* =========================================================
       TYPING
    ========================================================= */

    function showTyping() {

        const element =
            document.createElement("div");


        element.className =
            "typing-message";


        element.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;


        messages.appendChild(
            element
        );


        messages.scrollTop =
            messages.scrollHeight;


        return element;

    }


    /* =========================================================
       SAFE USER NAME
    ========================================================= */

    function escapeHtml(value) {

        const div =
            document.createElement("div");

        div.textContent =
            value;

        return div.innerHTML;

    }

});