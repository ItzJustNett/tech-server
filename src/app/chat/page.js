'use client';

import { useState, useEffect, useRef } from 'react';

// Set your server IP and port here
const SERVER_IP = "139.28.37.39"; // Replace with your actual server IP
const SERVER_PORT = 5000;
const SERVER_URL = `http://${SERVER_IP}:${SERVER_PORT}`;

export default function ChatPage() {
  // State for chat functionality
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [username, setUsername] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState('');
  const [users, setUsers] = useState([]);
  const [step, setStep] = useState('username'); // Skip server URL input, just ask for username
  
  // Refs
  const chatClientRef = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);
  
  // Load ChatClient script on component mount
  useEffect(() => {
    // Create a script element to load the ChatClient
    const script = document.createElement('script');
    script.innerHTML = `
      // ChatClient implementation
      class ChatClient {
        constructor(serverUrl) {
          this.serverUrl = serverUrl;
          this.socket = null;
          this.isConnected = false;
          this.username = null;
          
          // Event handlers
          this.onConnect = null;
          this.onDisconnect = null;
          this.onMessage = null;
          this.onUserTyping = null;
          this.onUserList = null;
        }
        
        // Load Socket.IO client library dynamically
        async loadSocketIO() {
          return new Promise((resolve, reject) => {
            // Check if Socket.IO is already loaded
            if (window.io) {
              resolve(window.io);
              return;
            }
            
            const script = document.createElement('script');
            script.src = 'https://cdn.socket.io/4.6.0/socket.io.min.js';
            script.async = true;
            
            script.onload = () => resolve(window.io);
            script.onerror = () => reject(new Error('Failed to load Socket.IO client'));
            
            document.head.appendChild(script);
          });
        }
        
        // Connect to the chat server
        async connect(username) {
          try {
            // Load Socket.IO if not already loaded
            await this.loadSocketIO();
            
            // Connect to the Socket.IO server
            this.socket = io(this.serverUrl);
            this.username = username || 'Anonymous';
            
            // Set up event listeners
            this.socket.on('connect', () => {
              this.isConnected = true;
              console.log('Connected to chat server');
              
              // Register username
              this.socket.emit('register', this.username);
              
              // Call onConnect callback if provided
              if (typeof this.onConnect === 'function') {
                this.onConnect();
              }
            });
            
            this.socket.on('disconnect', () => {
              this.isConnected = false;
              console.log('Disconnected from chat server');
              
              // Call onDisconnect callback if provided
              if (typeof this.onDisconnect === 'function') {
                this.onDisconnect();
              }
            });
            
            this.socket.on('message', (message) => {
              // Call onMessage callback if provided
              if (typeof this.onMessage === 'function') {
                this.onMessage(message);
              }
            });
            
            this.socket.on('message_history', (messages) => {
              // Process each message in history
              messages.forEach(message => {
                if (typeof this.onMessage === 'function') {
                  this.onMessage(message);
                }
              });
            });
            
            this.socket.on('users', (users) => {
              // Call onUserList callback if provided
              if (typeof this.onUserList === 'function') {
                this.onUserList(users);
              }
            });
            
            this.socket.on('user_typing', (data) => {
              // Call onUserTyping callback if provided
              if (typeof this.onUserTyping === 'function') {
                this.onUserTyping(data);
              }
            });
            
            return true;
          } catch (error) {
            console.error('Failed to connect to chat server:', error);
            return false;
          }
        }
        
        // Send a message
        sendMessage(text) {
          if (!this.isConnected || !this.socket) {
            throw new Error('Not connected to chat server');
          }
          
          this.socket.emit('message', text);
        }
        
        // Update typing status
        setTyping(isTyping) {
          if (!this.isConnected || !this.socket) {
            return;
          }
          
          this.socket.emit('typing', isTyping);
        }
        
        // Disconnect from the server
        disconnect() {
          if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.isConnected = false;
          }
        }
        
        // Get current connection status
        getStatus() {
          return {
            connected: this.isConnected,
            username: this.username
          };
        }
        
        // Fetch message history via REST API
        async fetchMessages() {
          try {
            const response = await fetch(\`\${this.serverUrl}/api/messages\`);
            return await response.json();
          } catch (error) {
            console.error('Failed to fetch messages:', error);
            return [];
          }
        }
        
        // Fetch user list via REST API
        async fetchUsers() {
          try {
            const response = await fetch(\`\${this.serverUrl}/api/users\`);
            return await response.json();
          } catch (error) {
            console.error('Failed to fetch users:', error);
            return [];
          }
        }
      }
      
      // Make available globally
      window.ChatClient = ChatClient;
    `;
    
    document.head.appendChild(script);
    
    // Cleanup on unmount
    return () => {
      document.head.removeChild(script);
      if (chatClientRef.current && chatClientRef.current.isConnected) {
        chatClientRef.current.disconnect();
      }
    };
  }, []);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Handle username submit
  const handleUsernameSubmit = async (e) => {
    e.preventDefault();
    if (!username) return;
    
    try {
      // Initialize chat client
      const ChatClient = window.ChatClient;
      if (!ChatClient) {
        alert('Chat client not loaded. Please try refreshing the page.');
        return;
      }
      
      chatClientRef.current = new ChatClient(SERVER_URL);
      
      // Set up event handlers
      chatClientRef.current.onConnect = () => {
        setIsConnected(true);
        setStep('chat');
      };
      
      chatClientRef.current.onDisconnect = () => {
        setIsConnected(false);
        setMessages(prev => [
          ...prev, 
          {
            id: Date.now(),
            type: 'system',
            text: 'Disconnected from server',
            timestamp: new Date().toISOString()
          }
        ]);
      };
      
      chatClientRef.current.onMessage = (message) => {
        setMessages(prev => {
          // Avoid duplicate messages
          if (prev.some(m => m.id === message.id)) return prev;
          return [...prev, message];
        });
      };
      
      chatClientRef.current.onUserTyping = (data) => {
        if (data.isTyping) {
          setTypingUsers(`${data.username} is typing...`);
        } else {
          setTypingUsers('');
        }
      };
      
      chatClientRef.current.onUserList = (userList) => {
        setUsers(userList);
      };
      
      // Connect to server
      const connected = await chatClientRef.current.connect(username);
      if (!connected) {
        alert(`Failed to connect to chat server at ${SERVER_URL}. Please try again later.`);
      }
    } catch (error) {
      console.error('Error connecting to chat server:', error);
      alert(`Error connecting to chat server: ${error.message}`);
    }
  };
  
  // Handle sending a message
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputText.trim() || !chatClientRef.current) return;
    
    try {
      chatClientRef.current.sendMessage(inputText);
      setInputText('');
      
      // Clear typing indicator
      clearTimeout(typingTimeoutRef.current);
      chatClientRef.current.setTyping(false);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          type: 'system',
          text: `Error sending message: ${error.message}`,
          timestamp: new Date().toISOString()
        }
      ]);
    }
  };
  
  // Handle typing indicator
  const handleTyping = (e) => {
    setInputText(e.target.value);
    
    if (!chatClientRef.current || !chatClientRef.current.isConnected) return;
    
    chatClientRef.current.setTyping(true);
    
    clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      chatClientRef.current.setTyping(false);
    }, 2000);
  };
  
  return (
    <div className="chat-page">
      <main className="chat-main">
        <h1 className="chat-title">Chat App</h1>
        
        {step === 'username' && (
          <div className="form-container">
            <h2>Enter Your Username</h2>
            <form onSubmit={handleUsernameSubmit} className="form">
              <div className="form-group">
                <label htmlFor="username">Username:</label>
                <input
                  type="text"
                  id="username"
                  placeholder="Your name"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="input"
                />
              </div>
              <div className="server-info">
                Connecting to: {SERVER_URL}
              </div>
              <button type="submit" className="button">Join Chat</button>
            </form>
          </div>
        )}
        
        {step === 'chat' && (
          <div className="chat-container">
            <div className="chat-header">
              <span className={isConnected ? "status-connected" : "status-disconnected"}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
              <span className="user-count">{users.length} users online</span>
            </div>
            
            <div className="message-container">
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className={`message ${
                    message.type === 'system' 
                      ? 'system-message' 
                      : message.username === username 
                        ? 'sent-message' 
                        : 'received-message'
                  }`}
                >
                  {message.type !== 'system' && message.username !== username && (
                    <div className="message-username">{message.username}</div>
                  )}
                  <div className="message-text">{message.text}</div>
                  {message.type !== 'system' && (
                    <div className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
            
            <div className="typing-indicator">{typingUsers}</div>
            
            <form onSubmit={handleSendMessage} className="input-form">
              <input
                type="text"
                value={inputText}
                onChange={handleTyping}
                placeholder="Type a message..."
                className="message-input"
              />
              <button type="submit" className="send-button">Send</button>
            </form>
          </div>
        )}
      </main>
      
      <style jsx>{`
        /* CSS styles for the chat page - DARK MODE */
        .chat-page {
          min-height: 100vh;
          padding: 0 1rem;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          background-color: #121212;
          color: #e0e0e0;
        }
        
        .chat-main {
          padding: 2rem 0;
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          width: 100%;
          max-width: 800px;
        }
        
        .chat-title {
          margin: 0 0 2rem;
          line-height: 1.15;
          font-size: 2.5rem;
          text-align: center;
          color: #7288d9;
        }
        
        .form-container {
          background-color: #1e1e1e;
          padding: 2rem;
          border-radius: 10px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
          width: 100%;
          max-width: 500px;
        }
        
        .form-container h2 {
          margin-top: 0;
          color: #7288d9;
          margin-bottom: 1.5rem;
        }
        
        .server-info {
          margin-top: 1rem;
          font-size: 0.9rem;
          color: #a0a0a0;
          text-align: center;
          padding: 0.5rem;
          background-color: #2a2a2a;
          border-radius: 5px;
        }
        
        .form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }
        
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        
        .form-group label {
          font-weight: 600;
          color: #c0c0c0;
        }
        
        .input {
          padding: 0.8rem 1rem;
          border: 1px solid #444;
          border-radius: 5px;
          font-size: 1rem;
          background-color: #2a2a2a;
          color: #e0e0e0;
        }
        
        .input:focus {
          border-color: #7288d9;
          outline: none;
        }
        
        .button {
          padding: 0.8rem 1.5rem;
          background-color: #7288d9;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
          font-size: 1rem;
          font-weight: 600;
          transition: background-color 0.2s;
        }
        
        .button:hover {
          background-color: #5a6fb3;
        }
        
        .chat-container {
          background-color: #1e1e1e;
          border-radius: 10px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
          width: 100%;
          height: 80vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        
        .chat-header {
          padding: 1rem;
          background-color: #292929;
          color: white;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid #444;
        }
        
        .status-connected {
          background-color: #10b981;
          color: #d1fae5;
          padding: 0.3rem 0.8rem;
          border-radius: 50px;
          font-size: 0.8rem;
          font-weight: 600;
        }
        
        .status-disconnected {
          background-color: #ef4444;
          color: #fee2e2;
          padding: 0.3rem 0.8rem;
          border-radius: 50px;
          font-size: 0.8rem;
          font-weight: 600;
        }
        
        .user-count {
          font-size: 0.9rem;
          opacity: 0.8;
        }
        
        .message-container {
          flex: 1;
          padding: 1rem;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 0.8rem;
          background-color: #1e1e1e;
        }
        
        .message-container::-webkit-scrollbar {
          width: 8px;
        }
        
        .message-container::-webkit-scrollbar-track {
          background: #292929;
        }
        
        .message-container::-webkit-scrollbar-thumb {
          background-color: #444;
          border-radius: 10px;
        }
        
        .message {
          padding: 0.8rem 1rem;
          border-radius: 8px;
          max-width: 80%;
          word-break: break-word;
        }
        
        .system-message {
          align-self: center;
          background-color: #2a2a2a;
          color: #a0a0a0;
          font-style: italic;
          font-size: 0.9rem;
          padding: 0.5rem 1rem;
        }
        
        .sent-message {
          align-self: flex-end;
          background-color: #7288d9;
          color: white;
        }
        
        .received-message {
          align-self: flex-start;
          background-color: #383838;
          color: #e0e0e0;
        }
        
        .message-username {
          font-weight: 600;
          font-size: 0.9rem;
          margin-bottom: 0.3rem;
          color: #a0a0a0;
        }
        
        .message-text {
          line-height: 1.4;
        }
        
        .message-time {
          font-size: 0.75rem;
          opacity: 0.7;
          margin-top: 0.3rem;
          text-align: right;
        }
        
        .typing-indicator {
          padding: 0.5rem 1rem;
          font-style: italic;
          color: #a0a0a0;
          font-size: 0.9rem;
          height: 1.8rem;
          background-color: #232323;
        }
        
        .input-form {
          display: flex;
          padding: 1rem;
          background-color: #292929;
          gap: 0.5rem;
        }
        
        .message-input {
          flex: 1;
          padding: 0.8rem 1rem;
          border: 1px solid #444;
          border-radius: 5px;
          font-size: 1rem;
          background-color: #2a2a2a;
          color: #e0e0e0;
        }
        
        .message-input:focus {
          border-color: #7288d9;
          outline: none;
        }
        
        .send-button {
          padding: 0.8rem 1.5rem;
          background-color: #7288d9;
          color: white;
          border: none;
          border-radius: 5px;
          cursor: pointer;
          font-weight: 600;
        }
        
        .send-button:hover {
          background-color: #5a6fb3;
        }
        
        @media (max-width: 600px) {
          .chat-main {
            padding: 1rem 0;
          }
          
          .chat-container {
            height: 85vh;
          }
          
          .message {
            max-width: 90%;
          }
        }
      `}</style>
    </div>
  );
}
