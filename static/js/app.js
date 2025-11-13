// Enhanced DOM element selection
const messages = document.getElementById('messagesContainer');
const promptEl = document.getElementById('prompt');
const streamBtn = document.getElementById('streamBtn');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const clearBtn = document.getElementById('clearBtn');
const sidebarHistory = document.getElementById('sidebarHistory');
const themeToggle = document.getElementById('themeToggle');
const headerThemeToggle = document.getElementById('headerThemeToggle');
const logoutBtn = document.getElementById('logoutBtn');
const signupBtn = document.getElementById('signupBtn');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const sidebar = document.getElementById('sidebar');
const layoutBtn = document.getElementById('layoutBtn');
const layoutPanel = document.getElementById('layoutPanel');
const closePanelBtn = document.getElementById('closePanelBtn');
const chatWidth = document.getElementById('chatWidth');
const messageStyle = document.getElementById('messageStyle');
const toggleSidebar = document.getElementById('toggleSidebar');
const typingIndicator = document.getElementById('typingIndicator');
const messagesContainer = document.getElementById('messagesContainer');
const headerContainer = document.getElementById('headerContainer');
const inputContainer = document.getElementById('inputContainer');

// Enhanced state management
let questionLimit = null;
let currentTheme = 'light';
let layoutSettings = {
  chatWidth: 'max-w-4xl',
  messageStyle: 'bubble',
  sidebarVisible: true
};
let isTyping = false;
let messageQueue = [];
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

// Performance monitoring
const performanceMetrics = {
  messageCount: 0,
  averageResponseTime: 0,
  totalResponseTime: 0
};

console.log('🚀 Neuro-Core AI Assistant initialized with advanced features');

// Enhanced theme initialization
const savedTheme = localStorage.getItem('theme');
const savedLayout = JSON.parse(localStorage.getItem('layoutSettings') || '{}');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const initialTheme = savedTheme || (systemDark ? 'dark' : 'light');

// Apply saved layout settings
layoutSettings = { ...layoutSettings, ...savedLayout };
currentTheme = initialTheme;

if (initialTheme === 'dark') {
  document.documentElement.classList.add('dark');
}

// Apply layout settings
applyLayoutSettings();

// Enhanced theme toggle with smooth transitions
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.classList.contains('dark');
  
  // Add transition class for smooth theme change
  html.style.transition = 'background-color 0.5s ease, color 0.5s ease';
  
  if (isDark) {
    html.classList.remove('dark');
    localStorage.setItem('theme', 'light');
    currentTheme = 'light';
    showNotification('☀️ Light theme activated', 'success');
  } else {
    html.classList.add('dark');
    localStorage.setItem('theme', 'dark');
    currentTheme = 'dark';
    showNotification('🌙 Dark theme activated', 'success');
  }
  
  // Remove transition after animation
  setTimeout(() => {
    html.style.transition = '';
  }, 500);
}

// Layout settings functions
function applyLayoutSettings() {
  if (messages) {
    messages.className = messages.className.replace(/max-w-\w+/, layoutSettings.chatWidth);
  }
  if (headerContainer) {
    headerContainer.className = headerContainer.className.replace(/max-w-\w+/, layoutSettings.chatWidth);
  }
  if (inputContainer) {
    inputContainer.className = inputContainer.className.replace(/max-w-\w+/, layoutSettings.chatWidth);
  }
  
  // Apply sidebar visibility
  if (sidebar) {
    if (layoutSettings.sidebarVisible) {
      sidebar.classList.remove('hidden');
      sidebar.classList.add('flex');
    } else {
      sidebar.classList.add('hidden');
      sidebar.classList.remove('flex');
    }
  }
  
  // Update form controls
  if (chatWidth) chatWidth.value = layoutSettings.chatWidth;
  if (messageStyle) messageStyle.value = layoutSettings.messageStyle;
}

function saveLayoutSettings() {
  localStorage.setItem('layoutSettings', JSON.stringify(layoutSettings));
}

// Notification system
function showNotification(message, type = 'info', duration = 3000) {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <div class="flex items-center gap-2">
      <span>${message}</span>
      <button onclick="this.parentElement.parentElement.remove()" class="ml-2 opacity-70 hover:opacity-100">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `;
  
  document.body.appendChild(notification);
  
  // Show notification
  setTimeout(() => notification.classList.add('show'), 100);
  
  // Auto remove
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, duration);
}

// Typing indicator functions
function showTypingIndicator() {
  if (typingIndicator && !isTyping) {
    isTyping = true;
    typingIndicator.classList.remove('hidden');
    scrollToBottom();
  }
}

function hideTypingIndicator() {
  if (typingIndicator && isTyping) {
    isTyping = false;
    typingIndicator.classList.add('hidden');
  }
}

// Enhanced event listeners
if (themeToggle) {
  themeToggle.addEventListener('click', toggleTheme);
}

if (headerThemeToggle) {
  headerThemeToggle.addEventListener('click', toggleTheme);
}

// Layout panel controls
if (layoutBtn) {
  layoutBtn.addEventListener('click', () => {
    layoutPanel?.classList.toggle('show');
  });
}

if (closePanelBtn) {
  closePanelBtn.addEventListener('click', () => {
    layoutPanel?.classList.remove('show');
  });
}

if (chatWidth) {
  chatWidth.addEventListener('change', (e) => {
    layoutSettings.chatWidth = e.target.value;
    applyLayoutSettings();
    saveLayoutSettings();
    showNotification('💬 Chat width updated', 'success');
  });
}

if (messageStyle) {
  messageStyle.addEventListener('change', (e) => {
    layoutSettings.messageStyle = e.target.value;
    saveLayoutSettings();
    showNotification('🎨 Message style updated', 'success');
  });
}

if (toggleSidebar) {
  toggleSidebar.addEventListener('click', () => {
    layoutSettings.sidebarVisible = !layoutSettings.sidebarVisible;
    applyLayoutSettings();
    saveLayoutSettings();
    showNotification(
      layoutSettings.sidebarVisible ? '📋 Sidebar shown' : '📋 Sidebar hidden', 
      'success'
    );
  });
}

// Mobile menu with enhanced animation
mobileMenuBtn?.addEventListener('click', () => {
  if (sidebar) {
    sidebar.classList.toggle('hidden');
    sidebar.classList.toggle('flex');
    
    // Add slide animation for mobile
    if (!sidebar.classList.contains('hidden')) {
      sidebar.style.transform = 'translateX(-100%)';
      setTimeout(() => {
        sidebar.style.transform = 'translateX(0)';
      }, 10);
    }
  }
});

// Enhanced logout with confirmation
logoutBtn?.addEventListener('click', async () => {
  if (confirm('Are you sure you want to logout?')) {
    try {
      showNotification('👋 Logging out...', 'info');
      await fetch('/auth/logout', { method: 'POST' });
      window.location.href = '/auth';
    } catch (error) {
      console.error('Logout failed:', error);
      showNotification('❌ Logout failed. Please try again.', 'error');
    }
  }
});

signupBtn?.addEventListener('click', () => {
  window.location.href = '/auth';
});

// Login button handler
const loginBtn = document.getElementById('loginBtn');
loginBtn?.addEventListener('click', () => {
  window.location.href = '/auth';
});

// Close layout panel when clicking outside
document.addEventListener('click', (e) => {
  if (layoutPanel && !layoutPanel.contains(e.target) && !layoutBtn?.contains(e.target)) {
    layoutPanel.classList.remove('show');
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + K to focus search
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    promptEl?.focus();
  }
  
  // Ctrl/Cmd + / to toggle sidebar
  if ((e.ctrlKey || e.metaKey) && e.key === '/') {
    e.preventDefault();
    layoutSettings.sidebarVisible = !layoutSettings.sidebarVisible;
    applyLayoutSettings();
    saveLayoutSettings();
  }
  
  // Ctrl/Cmd + Shift + L to toggle layout panel
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'L') {
    e.preventDefault();
    layoutPanel?.classList.toggle('show');
  }
});

// Check if user is logged in
let isLoggedIn = false;

async function checkUserStatus() {
  try {
    const res = await fetch('/user-status');
    const data = await res.json();
    isLoggedIn = data.is_authenticated;
  } catch (error) {
    console.error('Failed to check user status:', error);
  }
}



let lastImageUrl = null;

fileInput?.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  if (!isLoggedIn) {
    showNotification('❌ File upload requires login. Please sign up or login.', 'error');
    e.target.value = '';
    return;
  }
  
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/upload', { method: 'POST', body: fd });
  const data = await res.json();
  
  if (data.error) {
    showNotification(`❌ ${data.error}`, 'error');
    return;
  }
  
  if (data.url) {
    lastImageUrl = window.location.origin + data.url;
    preview?.classList.remove('hidden');
    const isImage = file.type.startsWith('image/');
    if (preview) {
      if (isImage) {
        preview.innerHTML = `<div class="text-xs text-gray-500 mb-1">Attached image</div><img src="${data.url}" class="max-h-32 rounded-xl border">`;
      } else {
        preview.innerHTML = `<div class="text-xs text-gray-500 mb-1">Attached file: ${file.name}</div><div class="text-xs bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">${file.type || 'Unknown type'}</div>`;
      }
    }
  }
});

function scrollToBottom() {
  requestAnimationFrame(() => {
    const chat = document.getElementById('chat');
    if (chat) chat.scrollTop = chat.scrollHeight;
  });
}

function renderMarkdown(md) {
  const html = marked.parse(md);
  const wrapper = document.createElement('div');
  wrapper.className = 'prose dark:prose-invert max-w-none markdown relative';
  wrapper.innerHTML = html;
  wrapper.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(block.innerText);
      btn.textContent = 'Copied!';
      setTimeout(() => (btn.textContent = 'Copy'), 1200);
    });
    block.parentElement.style.position = 'relative';
    block.parentElement.appendChild(btn);
  });
  return wrapper;
}

// Enhanced message rendering with animations
function addUserMessage(text, imageUrl) {
  if (!messages) return;
  
  const messageContainer = document.createElement('div');
  messageContainer.className = 'flex gap-4 justify-end animate-slide-up message-container';
  
  const messageGroup = document.createElement('div');
  messageGroup.className = 'max-w-[75%] group';
  
  const bubble = document.createElement('div');
  const bubbleClass = layoutSettings.messageStyle === 'card' 
    ? 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100'
    : layoutSettings.messageStyle === 'minimal'
    ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
    : 'bg-gradient-to-r from-gemini-blue to-blue-600 text-white';
  
  bubble.className = `${bubbleClass} rounded-2xl rounded-tr-md px-6 py-4 shadow-lg hover:shadow-xl transition-all duration-200 message-content`;
  bubble.innerHTML = `<div class="whitespace-pre-line text-sm leading-relaxed">${text}</div>`;
  
  const timestamp = document.createElement('div');
  timestamp.className = 'text-xs text-gray-500 dark:text-gray-400 mt-2 text-right opacity-0 group-hover:opacity-100 transition-opacity';
  timestamp.innerHTML = `<i class="fas fa-clock mr-1"></i>${new Date().toLocaleTimeString()}`;
  
  messageGroup.append(bubble, timestamp);
  
  const avatar = document.createElement('div');
  avatar.className = 'w-10 h-10 rounded-full bg-gradient-to-r from-gemini-blue to-blue-600 flex items-center justify-center shadow-lg flex-shrink-0';
  avatar.innerHTML = '<i class="fas fa-user text-white text-sm"></i>';
  
  messageContainer.append(messageGroup, avatar);
  messages.appendChild(messageContainer);

  if (imageUrl) {
    const imgContainer = document.createElement('div');
    imgContainer.className = 'flex justify-end pr-14 animate-fade-in';
    imgContainer.innerHTML = `
      <div class="rounded-2xl overflow-hidden shadow-lg border border-gray-200 dark:border-gray-700 max-w-sm">
        <img src="${imageUrl}" class="w-full h-auto" loading="lazy">
      </div>
    `;
    messages.appendChild(imgContainer);
  }
  
  performanceMetrics.messageCount++;
  scrollToBottom();
}

function addAssistantMessage(md) {
  if (!messages) return;
  
  const messageContainer = document.createElement('div');
  messageContainer.className = 'flex gap-4 animate-slide-up message-container';
  
  const avatar = document.createElement('div');
  avatar.className = 'w-10 h-10 rounded-full bg-gradient-to-r from-gemini-green to-green-600 flex items-center justify-center shadow-lg flex-shrink-0 sparkle';
  avatar.innerHTML = '<i class="fas fa-sparkles text-white text-sm"></i>';
  
  const messageGroup = document.createElement('div');
  messageGroup.className = 'flex-1 group';
  
  const bubble = document.createElement('div');
  bubble.className = 'bg-white dark:bg-gray-800 rounded-2xl rounded-tl-md px-6 py-4 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-200 message-bubble-advanced';
  
  const body = renderMarkdown(md);
  body.className = 'prose dark:prose-invert max-w-none markdown text-sm leading-relaxed';
  bubble.appendChild(body);
  
  const actions = document.createElement('div');
  actions.className = 'flex items-center gap-3 mt-3 opacity-0 group-hover:opacity-100 transition-opacity';
  actions.innerHTML = `
    <button class="text-xs text-gray-500 hover:text-gemini-blue transition-colors flex items-center gap-1 micro-interaction" onclick="likeMessage(this)">
      <i class="fas fa-thumbs-up"></i>Helpful
    </button>
    <button class="text-xs text-gray-500 hover:text-gemini-blue transition-colors flex items-center gap-1 micro-interaction" onclick="copyMessage(this)">
      <i class="fas fa-copy"></i>Copy
    </button>
    <button class="text-xs text-gray-500 hover:text-gemini-blue transition-colors flex items-center gap-1 micro-interaction" onclick="regenerateMessage(this)">
      <i class="fas fa-redo"></i>Regenerate
    </button>
    <span class="text-xs text-gray-400">
      <i class="fas fa-clock mr-1"></i>${new Date().toLocaleTimeString()}
    </span>
  `;
  
  messageGroup.append(bubble, actions);
  messageContainer.append(avatar, messageGroup);
  messages.appendChild(messageContainer);
  
  // Add completion indicator
  setTimeout(() => {
    bubble.classList.add('completion-indicator', 'complete');
  }, 500);
  
  scrollToBottom();
}

function addAssistantStreamContainer() {
  if (!messages) return null;
  
  const messageContainer = document.createElement('div');
  messageContainer.className = 'flex gap-4 animate-slide-up message-container';
  
  const avatar = document.createElement('div');
  avatar.className = 'w-10 h-10 rounded-full bg-gradient-to-r from-gemini-green to-green-600 flex items-center justify-center shadow-lg flex-shrink-0 sparkle';
  avatar.innerHTML = '<i class="fas fa-sparkles text-white text-sm animate-pulse"></i>';
  
  const messageGroup = document.createElement('div');
  messageGroup.className = 'flex-1 group';
  
  const bubble = document.createElement('div');
  bubble.className = 'bg-white dark:bg-gray-800 rounded-2xl rounded-tl-md px-6 py-4 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-200 message-bubble-advanced';
  
  const body = document.createElement('div');
  body.className = 'prose dark:prose-invert max-w-none markdown relative text-sm leading-relaxed';
  body.innerHTML = `
    <div class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <em>AI is thinking...</em>
    </div>
  `;
  
  bubble.appendChild(body);
  messageGroup.appendChild(bubble);
  messageContainer.append(avatar, messageGroup);
  messages.appendChild(messageContainer);
  
  scrollToBottom();
  return body;
}

// Enhanced send function with performance tracking
async function send(useStream = false) {
  if (!promptEl) return;
  
  const text = promptEl.value.trim();
  if (!text && !lastImageUrl) return;
  
  const startTime = Date.now();
  
  // Disable input during processing
  promptEl.disabled = true;
  streamBtn.disabled = true;
  
  addUserMessage(text || '(image only)', lastImageUrl);
  
  preview?.classList.add('hidden');
  if (preview) preview.innerHTML = '';
  
  promptEl.value = '';
  showTypingIndicator();

  if (useStream) {
    const container = addAssistantStreamContainer();
    if (!container) return;
    
    try {
      const res = await fetch('/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, image_url: lastImageUrl })
      });
      

      
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let isFirstChunk = true;
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.delta) {
                if (isFirstChunk) {
                  hideTypingIndicator();
                  isFirstChunk = false;
                }
                fullResponse += data.delta;
                const rendered = renderMarkdown(fullResponse);
                container.innerHTML = '';
                container.appendChild(rendered);
                scrollToBottom();
              }
              if (data.done) break;
            } catch (e) {}
          }
        }
      }
      
      // Track performance
      const responseTime = Date.now() - startTime;
      performanceMetrics.totalResponseTime += responseTime;
      performanceMetrics.averageResponseTime = performanceMetrics.totalResponseTime / performanceMetrics.messageCount;
      
    } catch (error) {
      hideTypingIndicator();
      container.innerHTML = renderMarkdown('❌ **Error**: Could not stream response. Please try again.').innerHTML;
      showNotification('❌ Connection error. Please check your internet.', 'error');
    }
  } else {
    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, image_url: lastImageUrl })
      });
      
      hideTypingIndicator();
      

      
      const data = await res.json();
      addAssistantMessage(data.reply || 'No response received');
      
      // Track performance
      const responseTime = Date.now() - startTime;
      performanceMetrics.totalResponseTime += responseTime;
      performanceMetrics.averageResponseTime = performanceMetrics.totalResponseTime / performanceMetrics.messageCount;
      
    } catch (error) {
      hideTypingIndicator();
      addAssistantMessage('❌ **Error**: Could not send message. Please try again.');
      showNotification('❌ Connection error. Please check your internet.', 'error');
    }
  }
  
  // Re-enable input
  promptEl.disabled = false;
  streamBtn.disabled = false;
  promptEl.focus();
  
  lastImageUrl = null;
  scrollToBottom();
  refreshSidebar();
  

}

// Message action functions
function likeMessage(button) {
  const icon = button.querySelector('i');
  if (icon.classList.contains('fas')) {
    icon.classList.remove('fas');
    icon.classList.add('far');
    showNotification('👍 Feedback removed', 'info', 1500);
  } else {
    icon.classList.remove('far');
    icon.classList.add('fas');
    showNotification('👍 Thanks for your feedback!', 'success', 1500);
  }
}

function copyMessage(button) {
  const messageContent = button.closest('.group').querySelector('.markdown');
  if (messageContent) {
    navigator.clipboard.writeText(messageContent.textContent);
    showNotification('📋 Message copied to clipboard', 'success', 1500);
  }
}

function regenerateMessage(button) {
  showNotification('🔄 Regenerating response...', 'info', 1500);
  // Implementation would depend on backend support
}

streamBtn?.addEventListener('click', () => send(true));

promptEl?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send(true);
  }
});

clearBtn?.addEventListener('click', async () => {
  try {
    await fetch('/clear', { method: 'POST' });
  } catch (error) {
    console.error('Failed to clear chat:', error);
  }
  
  if (messages) messages.innerHTML = '<div class="text-sm text-gray-500">Start a conversation below…</div>';
  if (sidebarHistory) sidebarHistory.innerHTML = '';
  preview?.classList.add('hidden');
  if (preview) preview.innerHTML = '';
  if (promptEl) promptEl.value = '';
  lastImageUrl = null;
});

// Enhanced sidebar with better history management
function refreshSidebar() {
  if (!sidebarHistory) return;
  
  const messageElements = Array.from(document.querySelectorAll('#messagesContainer .message-container'));
  const recentMessages = messageElements.slice(-10);
  
  const items = recentMessages.map((el, index) => {
    const isUser = el.querySelector('.fa-user');
    const text = el.innerText.slice(0, 60).replace(/\s+/g, ' ').trim();
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    return `
      <div class="history-item px-4 py-3 rounded-xl text-xs cursor-pointer hover-lift micro-interaction" onclick="scrollToMessage(${messageElements.indexOf(el)})">
        <div class="flex items-center gap-2 mb-1">
          <i class="fas ${isUser ? 'fa-user text-gemini-blue' : 'fa-sparkles text-gemini-green'}"></i>
          <span class="text-gray-500 dark:text-gray-400">${time}</span>
        </div>
        <div class="text-gray-700 dark:text-gray-300 line-clamp-2">${text}</div>
      </div>
    `;
  }).join('');
  
  sidebarHistory.innerHTML = items || '<div class="text-center text-gray-500 dark:text-gray-400 text-xs py-8">No conversations yet</div>';
}

function scrollToMessage(index) {
  const messageElements = document.querySelectorAll('#messagesContainer .message-container');
  if (messageElements[index]) {
    messageElements[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
    messageElements[index].style.background = 'rgba(66, 133, 244, 0.1)';
    setTimeout(() => {
      messageElements[index].style.background = '';
    }, 2000);
  }
}

document.querySelectorAll('.markdown').forEach((node) => {
  node.innerHTML = marked.parse(node.textContent);
  node.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
});

refreshSidebar();

// Enhanced loading screen with realistic progress
const loadingMessages = [
  'Initializing neural networks...',
  'Loading language models...',
  'Setting up memory systems...',
  'Configuring file processors...',
  'Establishing secure connections...',
  'Optimizing performance...',
  'Calibrating AI responses...',
  'Ready to assist! 🚀'
];

let currentMessageIndex = 0;
let progress = 0;

function updateLoadingProgress() {
  const statusEl = document.getElementById('loadingStatus');
  const progressBar = document.getElementById('progressBar');
  
  if (statusEl && currentMessageIndex < loadingMessages.length) {
    statusEl.textContent = loadingMessages[currentMessageIndex];
    statusEl.style.opacity = '0';
    setTimeout(() => {
      statusEl.style.opacity = '1';
    }, 100);
    currentMessageIndex++;
  }
  
  // More realistic progress increments
  const increment = currentMessageIndex < 3 ? Math.random() * 15 + 10 : Math.random() * 25 + 15;
  progress += increment;
  if (progress > 100) progress = 100;
  
  if (progressBar) {
    progressBar.style.width = progress + '%';
  }
  
  if (progress < 100 && currentMessageIndex < loadingMessages.length) {
    setTimeout(updateLoadingProgress, 600 + Math.random() * 400);
  } else if (progress >= 100) {
    setTimeout(() => {
      if (statusEl) statusEl.textContent = loadingMessages[loadingMessages.length - 1];
    }, 300);
  }
}

// Start loading animation with delay
setTimeout(updateLoadingProgress, 800);

// Voice recording functionality
const voiceBtn = document.getElementById('voiceBtn');

async function startRecording() {
  if (!recognition) {
    recognition = initSpeechRecognition();
  }
  
  if (!recognition) {
    showNotification('❌ Speech recognition not supported', 'error');
    return;
  }
  
  try {
    isRecording = true;
    
    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      if (promptEl) {
        promptEl.value = transcript;
      }
    };
    
    recognition.onerror = (event) => {
      console.error('Speech error:', event.error);
      stopRecording();
    };
    
    recognition.onend = () => {
      if (isRecording) {
        stopRecording();
      }
    };
    
    recognition.start();
    
    // Update UI
    const icon = voiceBtn.querySelector('i');
    icon.className = 'fas fa-stop text-red-500 animate-pulse';
    voiceBtn.title = 'Stop recording';
    showNotification('🎤 Speak now...', 'info');
    
  } catch (error) {
    console.error('Error starting recognition:', error);
    showNotification('❌ Could not start voice input', 'error');
    isRecording = false;
  }
}

function stopRecording() {
  if (recognition && isRecording) {
    recognition.stop();
    isRecording = false;
    
    // Update UI
    const icon = voiceBtn.querySelector('i');
    icon.className = 'fas fa-microphone text-gray-400';
    voiceBtn.title = 'Voice input';
    showNotification('🎤 Voice input complete', 'success');
  }
}

let recognition = null;

function initSpeechRecognition() {
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    return null;
  }
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';
  
  return recognition;
}

async function processAudio(audioBlob) {
  if (promptEl) {
    promptEl.focus();
    showNotification('✅ Ready to type or speak again', 'success');
  }
}

// Voice button event listener
voiceBtn?.addEventListener('click', () => {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

// Initialize user status check
checkUserStatus();

// Enhanced loading screen completion
window.addEventListener('load', () => {
  // Ensure all resources are loaded
  setTimeout(() => {
    progress = 100;
    const progressBar = document.getElementById('progressBar');
    const statusEl = document.getElementById('loadingStatus');
    
    if (progressBar) {
      progressBar.style.width = '100%';
      progressBar.style.background = 'linear-gradient(90deg, var(--gemini-green), var(--gemini-blue))';
    }
    if (statusEl) statusEl.textContent = 'Ready to assist! 🚀';
    
    // Add completion sound effect (optional)
    // playNotificationSound();
    
    setTimeout(() => {
      const loadingScreen = document.getElementById('loadingScreen');
      if (loadingScreen) {
        loadingScreen.style.opacity = '0';
        loadingScreen.style.transform = 'scale(1.1)';
        loadingScreen.style.transition = 'opacity 1s ease, transform 1s ease';
        
        setTimeout(() => {
          loadingScreen.style.display = 'none';
          // Show welcome notification
          showNotification('🎉 Welcome to Neuro-Core AI! Ready to help you.', 'success', 4000);
          
          // Focus on input
          if (promptEl) {
            promptEl.focus();
          }
        }, 1000);
      }
    }, 1200);
  }, 2000);
});

// Performance monitoring
setInterval(() => {
  if (performanceMetrics.messageCount > 0) {
    console.log('📊 Performance Metrics:', {
      messages: performanceMetrics.messageCount,
      avgResponseTime: `${performanceMetrics.averageResponseTime.toFixed(0)}ms`,
      theme: currentTheme,
      layout: layoutSettings
    });
  }
}, 30000); // Log every 30 seconds

// Initialize reveal animations for existing content
function initializeRevealAnimations() {
  const elements = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  });
  
  elements.forEach(el => observer.observe(el));
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  initializeRevealAnimations();
  console.log('🎨 Advanced Gemini-style UI initialized successfully!');
});

