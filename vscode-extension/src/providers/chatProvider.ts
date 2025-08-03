import * as vscode from 'vscode';
import { CodingAgent } from '../core/agent';

export class ChatProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'aiCodingAgent.chat';
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly agent: CodingAgent
    ) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this.getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage':
                    await this.handleChatMessage(data.message);
                    break;
                case 'clearChat':
                    this.clearChat();
                    break;
            }
        });
    }

    private async handleChatMessage(message: string) {
        if (!this._view) {
            return;
        }

        // Show user message
        this._view.webview.postMessage({
            type: 'addMessage',
            message: {
                content: message,
                isUser: true,
                timestamp: new Date().toISOString()
            }
        });

        try {
            // Get AI response
            const response = await this.agent.chat(message);
            
            // Show AI response
            this._view.webview.postMessage({
                type: 'addMessage',
                message: {
                    content: response,
                    isUser: false,
                    timestamp: new Date().toISOString()
                }
            });
        } catch (error) {
            this._view.webview.postMessage({
                type: 'addMessage',
                message: {
                    content: `Error: ${error}`,
                    isUser: false,
                    isError: true,
                    timestamp: new Date().toISOString()
                }
            });
        }
    }

    private clearChat() {
        if (!this._view) {
            return;
        }

        this._view.webview.postMessage({
            type: 'clearMessages'
        });
    }

    private getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chat</title>
    <style>
        body {
            padding: 0;
            margin: 0;
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .message {
            max-width: 85%;
            padding: 8px 12px;
            border-radius: 8px;
            word-wrap: break-word;
        }

        .user-message {
            align-self: flex-end;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
        }

        .ai-message {
            align-self: flex-start;
            background-color: var(--vscode-input-background);
            border: 1px solid var(--vscode-input-border);
        }

        .error-message {
            background-color: var(--vscode-errorForeground);
            color: var(--vscode-editor-background);
        }

        .timestamp {
            font-size: 0.8em;
            opacity: 0.7;
            margin-top: 4px;
        }

        .input-container {
            padding: 10px;
            border-top: 1px solid var(--vscode-input-border);
            display: flex;
            gap: 8px;
        }

        .message-input {
            flex: 1;
            padding: 8px;
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            border-radius: 4px;
            outline: none;
        }

        .message-input:focus {
            border-color: var(--vscode-focusBorder);
        }

        .send-button, .clear-button {
            padding: 8px 12px;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        .send-button:hover, .clear-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        .clear-button {
            background-color: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }

        .clear-button:hover {
            background-color: var(--vscode-button-secondaryHoverBackground);
        }

        .empty-state {
            text-align: center;
            color: var(--vscode-descriptionForeground);
            margin-top: 50px;
        }

        pre {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 8px 0;
        }

        code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 4px;
            border-radius: 2px;
            font-family: var(--vscode-editor-font-family);
        }
    </style>
</head>
<body>
    <div class="chat-container" id="chatContainer">
        <div class="empty-state">
            <p>👋 Hello! I'm your AI coding assistant.</p>
            <p>Ask me anything about your code, request code generation, or get help with programming concepts.</p>
        </div>
    </div>
    <div class="input-container">
        <input type="text" class="message-input" id="messageInput" placeholder="Ask me about your code..." />
        <button class="send-button" id="sendButton">Send</button>
        <button class="clear-button" id="clearButton">Clear</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const clearButton = document.getElementById('clearButton');

        function addMessage(message) {
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${message.isUser ? 'user-message' : 'ai-message'}\${message.isError ? ' error-message' : ''}\`;
            
            const content = document.createElement('div');
            content.innerHTML = formatMessage(message.content);
            messageDiv.appendChild(content);

            const timestamp = document.createElement('div');
            timestamp.className = 'timestamp';
            timestamp.textContent = new Date(message.timestamp).toLocaleTimeString();
            messageDiv.appendChild(timestamp);

            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;

            // Remove empty state if it exists
            const emptyState = chatContainer.querySelector('.empty-state');
            if (emptyState) {
                emptyState.remove();
            }
        }

        function formatMessage(content) {
            // Basic markdown-like formatting
            content = content.replace(/\`\`\`([\\s\\S]*?)\`\`\`/g, '<pre><code>$1</code></pre>');
            content = content.replace(/\`([^\`]+)\`/g, '<code>$1</code>');
            content = content.replace(/\\*\\*([^\\*]+)\\*\\*/g, '<strong>$1</strong>');
            content = content.replace(/\\*([^\\*]+)\\*/g, '<em>$1</em>');
            content = content.replace(/\\n/g, '<br>');
            return content;
        }

        function sendMessage() {
            const message = messageInput.value.trim();
            if (message) {
                vscode.postMessage({
                    type: 'sendMessage',
                    message: message
                });
                messageInput.value = '';
            }
        }

        function clearChat() {
            vscode.postMessage({
                type: 'clearChat'
            });
        }

        function clearMessages() {
            chatContainer.innerHTML = '<div class="empty-state"><p>👋 Hello! I\\'m your AI coding assistant.</p><p>Ask me anything about your code, request code generation, or get help with programming concepts.</p></div>';
        }

        sendButton.addEventListener('click', sendMessage);
        clearButton.addEventListener('click', clearChat);

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Listen for messages from the extension
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.type) {
                case 'addMessage':
                    addMessage(message.message);
                    break;
                case 'clearMessages':
                    clearMessages();
                    break;
            }
        });
    </script>
</body>
</html>`;
    }
}