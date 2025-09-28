window.onbeforeunload = function() {
    const userInput = document.getElementById("userInput").value.trim();
    const hasMessages = document.getElementById("messages").children.length > 0;
    if (userInput !== "" || hasMessages) {
        console.log("Page is about to refresh");
        saveChatHistory();
        return "Do you want to leave this page? Your chat history may be lost.";
    }
    return null;
};

document.addEventListener("DOMContentLoaded", function () {
    const sendButton = document.getElementById("sendButton");
    const userInput = document.getElementById("userInput");
    const messages = document.getElementById("messages");

    const modeSelectButton = document.getElementById("modeSelectButton");
    const modeOptions = document.getElementById("modeOptions");
    const selectedModeText = document.getElementById("selectedModeText");

    if (!sendButton || !userInput || !messages || !modeSelectButton || !modeOptions) {
        console.error("Required elements not found!");
        return;
    }

    // Set default mode
    let selectedMode = "hybrid";

    // auto adjust height of textarea
    userInput.addEventListener("input", function () {
        if (this.value.trim() !== "") { // Only adjust when there is content
            this.style.height = "auto";
            this.style.height = this.scrollHeight + "px";
        }
    });

    // Toggle dropdown menu
    modeSelectButton.addEventListener("click", function () {
        modeOptions.classList.toggle("show");
    });

    // Select mode
    modeOptions.addEventListener("click", function (e) {
        const target = e.target.closest(".mode-option");
        if (!target) return;

        selectedMode = target.dataset.value;
        selectedModeText.textContent = target.textContent;

        // Highlight selected mode
        document.querySelectorAll(".mode-option").forEach(option => {
            option.classList.remove("selected");
        });
        target.classList.add("selected");

        // Hide dropdown
        modeOptions.classList.remove("show");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (e) {
        if (!modeSelectButton.contains(e.target) && !modeOptions.contains(e.target)) {
            modeOptions.classList.remove("show");
        }
    });

    loadChatHistory();

    sendButton.addEventListener("click", function (e) {
        e.preventDefault();
        sendMessage();
    });

    userInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.keyCode === 13) {
            e.preventDefault();
            sendMessage();
        }
    });

    if (!document.querySelector(".new-chat-button")) {
        const newChatButton = document.createElement("button");
        newChatButton.className = "new-chat-button";
        newChatButton.innerHTML = `
            <svg class="new-chat-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" stroke="white" stroke-width="2">
                <path d="M10 4V4C8.13623 4 7.20435 4 6.46927 4.30448C5.48915 4.71046 4.71046 5.48915 4.30448 6.46927C4 7.20435 4 8.13623 4 10V13.6C4 15.8402 4 16.9603 4.43597 17.816C4.81947 18.5686 5.43139 19.1805 6.18404 19.564C7.03968 20 8.15979 20 10.4 20H14C15.8638 20 16.7956 20 17.5307 19.6955C18.5108 19.2895 19.2895 18.5108 19.6955 17.5307C20 16.7956 20 15.8638 20 14V14" stroke="currentColor" stroke-linecap="square"></path>
                <path d="M12.4393 14.5607L19.5 7.5C20.3284 6.67157 20.3284 5.32843 19.5 4.5C18.6716 3.67157 17.3284 3.67157 16.5 4.5L9.43934 11.5607C9.15804 11.842 9 12.2235 9 12.6213V15H11.3787C11.7765 15 12.158 14.842 12.4393 14.5607Z" stroke="currentColor" stroke-linecap="square"></path>
            </svg>
            <span class="new-chat-text">New Chat</span>`;
        newChatButton.addEventListener("click", clearChat);
        document.querySelector(".chat-container").prepend(newChatButton);
    }

    async function sendMessage() {
        const messageText = userInput.value.trim();
        if (messageText === "") return;
    
        userInput.value = "";
    
        appendMessage(messageText, "message user-message");
        const botPlaceholder = appendMessage("Waiting...", "message bot-message");

        // Disable send button while processing
        sendButton.disabled = true;
        sendButton.classList.add("disabled");
    
        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");
        myHeaders.append("ngrok-skip-browser-warning", "bypass");
        myHeaders.append("User-Agent", "LibraAI/1.0");

        // Collect conversation history
        const conversationHistory = Array.from(messages.children).map(msg => {
            const role = msg.classList.contains("user-message") ? "user" : "assistant";
            return { role, content: msg.textContent.trim() };
        });
    
        const raw = JSON.stringify({
            query: messageText,
            conversation_history: conversationHistory,
            mode: selectedMode
            // model: selectedModel,
        });
    
        const requestOptions = {
            method: "POST",
            headers: myHeaders,
            body: raw,
            redirect: "follow"
        };
    
        console.log("Sending request with mode:", selectedMode);
        console.log("Request body:", raw);

        try {
            const startTime = performance.now();
    
            const response = await fetch("http://localhost:8000/query", requestOptions);
            const result = await response.json();
    
            const endTime = performance.now();
            const responseTime = ((endTime - startTime) / 1000).toFixed(2);
    
            if (response.ok) {
                botPlaceholder.innerHTML = marked.parse(result.response);
                const timeElement = document.createElement("small");
                timeElement.style.display = "block";
                timeElement.style.fontSize = "12px";
                timeElement.style.color = "#a0a0a0";
                timeElement.textContent = `Response time: ${responseTime}s`;
                botPlaceholder.appendChild(timeElement);
            } else {
                botPlaceholder.textContent = `Error: ${result.detail?.[0]?.msg || "Unable to get response from API"}`;
            }
        } catch (error) {
            botPlaceholder.textContent = "Error connecting to API!";
            console.error(error);
        } finally {
            // Re-enable send button after processing
            sendButton.disabled = false;
            sendButton.classList.remove("disabled");
            
            userInput.style.height = "auto";
            userInput.style.height = userInput.scrollHeight + "px";
        }
    
        saveChatHistory();
    }

    function appendMessage(text, className) {
        const messageDiv = document.createElement("div");
        className.split(" ").forEach(cls => messageDiv.classList.add(cls));
        messageDiv.innerHTML = marked.parse(text);

        // Check for list items with icons at the beginning and add .has-icon class
        const listItems = messageDiv.querySelectorAll("ul li");
        listItems.forEach(item => {
            // Get the first child node (text node or element)
            const firstChild = item.childNodes[0];
            if (firstChild && firstChild.nodeType === 3) { // Text node
                const textContent = firstChild.textContent.trim();
                const iconPattern = /^(✅|✔|➤|➜|→|★|✦|•|◦|□|■|📚|⭐|💡|🏦|💬|🔗)/;
                if (iconPattern.test(textContent)) {
                    item.classList.add("has-icon");
                }
            } else if (firstChild && firstChild.nodeType === 1) { // Element node (e.g., <strong>)
                const textContent = item.textContent.trim();
                const iconPattern = /^(✅|✔|➤|➜|→|★|✦|•|◦|□|■|📚|⭐|💡|🏦|💬|🔗)/;
                if (iconPattern.test(textContent)) {
                    item.classList.add("has-icon");
                }
            }
        });

        messages.appendChild(messageDiv);
    
        if (messages.scrollHeight > 958) {
            messageDiv.scrollIntoView({ behavior: "smooth", block: "end" });
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: "smooth"
            });
        }

        return messageDiv; 
    }
    
    function saveChatHistory() {
        try {
            const chatMessages = Array.from(messages.children).map(msg => ({
                text: msg.innerHTML,
                class: msg.className
            }));
            localStorage.setItem("chatHistory", JSON.stringify(chatMessages));
        } catch (error) {
            console.error("Error saving chat history:", error);
        }
    }

    function loadChatHistory() {
        try {
            const savedMessages = localStorage.getItem("chatHistory");
            if (savedMessages) {
                const chatMessages = JSON.parse(savedMessages);
                chatMessages.forEach(msg => {
                    const messageDiv = document.createElement("div");
                    msg.class.split(" ").forEach(cls => messageDiv.classList.add(cls));
                    messageDiv.innerHTML = msg.text;
                    messages.appendChild(messageDiv);
                });
            }
        } catch (error) {
            console.error("Error loading chat history:", error);
            localStorage.removeItem("chatHistory");
        }
    }

    function clearChat(e) {
        if (e) e.preventDefault();
        localStorage.removeItem("chatHistory");
        messages.innerHTML = "";
        console.log("Chat history cleared");
    }
});