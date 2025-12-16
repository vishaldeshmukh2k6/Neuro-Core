// Enhanced DOM element selection
const messages = document.getElementById('chatMessages'); // Corrected to point to the inner wrapper
const promptEl = document.getElementById('prompt');
const streamBtn = document.getElementById('streamBtn');
const stopBtn = document.getElementById('stopBtn');
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
let currentStreamController = null;
let activeChatId = null;
let userChats = [];

// Performance monitoring
const performanceMetrics = {
  messageCount: 0,
  averageResponseTime: 0,
  totalResponseTime: 0
};

console.log('🚀 Neuro-Core AI Assistant initialized with advanced features');

// Chat management functions
function loadUserChats() {
  fetch('/chats')
    .then(response => response.json())
    .then(data => {
      console.log('Loaded chats:', data);
      if (data.success) {
        userChats = data.chats;
        updateChatSidebar();
      }
    })
    .catch(error => {
      console.error('Error loading chats:', error);
    });
}

async function createNewChat() {
  console.log('Resetting to new chat state...');

  // Reset state
  activeChatId = null;
  currentChatId = null;

  // Call backend to clear active chat session
  try {
    await fetch('/new-chat', { method: 'POST' });
  } catch (error) {
    console.error('Error clearing active chat:', error);
  }

  // Reset UI
  const welcomeScreen = document.getElementById('welcomeScreen');
  const chatMessages = document.getElementById('chatMessages');
  const chatbotComingSoon = document.getElementById('chatbotComingSoon');

  // Show welcome screen
  if (welcomeScreen) {
    welcomeScreen.style.display = 'block';
    welcomeScreen.classList.remove('hidden');
    welcomeScreen.style.opacity = '1';
  }

  // Hide other views
  if (chatMessages) {
    chatMessages.classList.add('hidden');
    // Clear messages content so old messages don't reappear
    chatMessages.innerHTML = '';
  }

  // Clean up any stray messages that might have been appended to the parent container due to previous bug
  if (messagesContainer) {
    const strayMessages = messagesContainer.querySelectorAll('.message-container');
    strayMessages.forEach(msg => msg.remove());
  }

  if (chatbotComingSoon) chatbotComingSoon.classList.add('hidden');

  // Reset input
  if (promptEl) {
    promptEl.value = '';
    promptEl.focus();
  }

  // Update URL without reload
  window.history.pushState({}, '', '/chat');

  // Refresh sidebar to remove active state
  updateChatSidebar();
}



function switchToChat(chatId) {
  activeChatId = chatId;
  loadChatHistory(chatId);
  loadUserChats();

  // Update URL
  window.history.pushState({}, '', `/chat?id=${chatId}`);
}

function deleteChat(chatId) {
  showConfirmModal('Are you sure you want to delete this chat?', () => {
    fetch(`/chat/${chatId}`, { method: 'DELETE' })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          if (chatId === activeChatId) {
            activeChatId = null;
            if (messages) messages.innerHTML = '';
            showWelcomeScreen();
            window.history.pushState({}, '', '/');
          }
          loadUserChats();
          showNotification('🗑️ Chat deleted', 'success', 1500);
        }
      })
      .catch(error => {
        console.error('Error deleting chat:', error);
        showNotification('❌ Failed to delete chat', 'error', 2000);
      });
  });
}

function loadChatHistory(chatId) {
  fetch(`/chat/${chatId}/history`)
    .then(response => response.json())
    .then(data => {
      if (data.success && messages) {
        messages.innerHTML = '';

        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatMessages = document.getElementById('chatMessages');

        if (data.history && data.history.length > 0) {
          if (welcomeScreen) welcomeScreen.style.display = 'none';
          if (chatMessages) chatMessages.classList.remove('hidden');

          data.history.forEach(msg => {
            if (msg.role === 'user') {
              addUserMessage(msg.content, msg.image_url);
            } else {
              addAssistantMessage(msg.content);
            }
          });
        } else {
          if (welcomeScreen) {
            welcomeScreen.style.display = 'block';
            welcomeScreen.style.opacity = '1';
          }
          if (chatMessages) chatMessages.classList.add('hidden');
        }

        scrollToBottom();
      }
    })
    .catch(error => {
      console.error('Error loading chat history:', error);
    });
}

function formatRelativeDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return 'Today';
  } else if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString();
  }
}

function updateChatSidebar() {
  if (!sidebarHistory) return;

  console.log('Updating sidebar with chats:', userChats);

  sidebarHistory.innerHTML = '';

  userChats.forEach(chat => {
    const isActive = chat.id === activeChatId;
    // Clean up title for display
    let displayTitle = chat.name.replace(/['"]+/g, '').trim();
    // No JS truncation needed, CSS will handle it

    const dateDisplay = formatRelativeDate(chat.updated || chat.created_at || Date.now());

    sidebarHistory.innerHTML += `
      <div class="group relative p-3 rounded-lg mb-2 flex justify-between items-center transition-all duration-200 ${isActive ? 'bg-blue-50 dark:bg-blue-900/40 border border-blue-200 dark:border-blue-800' : 'hover:bg-gray-100 dark:hover:bg-gray-800 border border-transparent'}">
        <div onclick="switchToChat('${chat.id}')" class="flex-1 cursor-pointer min-w-0 pr-2">
          <div class="font-medium text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white transition-colors line-clamp-2 leading-snug" title="${chat.name}">
            ${displayTitle}
          </div>
          <div class="text-xs text-gray-400 dark:text-gray-500 truncate mt-0.5">
            ${dateDisplay}
          </div>
        </div>
        
        <!-- Chat Options Menu -->
        <div class="relative">
          <button onclick="toggleChatMenu(event, '${chat.id}')" class="opacity-0 group-hover:opacity-100 p-1.5 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-200 text-gray-500 dark:text-gray-400">
            <i class="fas fa-ellipsis-v text-xs"></i>
          </button>
          
          <!-- Dropdown -->
          <div id="chat-menu-${chat.id}" class="hidden absolute right-0 top-full mt-1 w-32 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden">
            <button onclick="renameChat('${chat.id}', '${chat.name.replace(/'/g, "\\'")}')" class="w-full text-left px-3 py-2 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
              <i class="fas fa-edit"></i> Rename
            </button>
            <button onclick="shareChat('${chat.id}')" class="w-full text-left px-3 py-2 text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2">
              <i class="fas fa-share-alt"></i> Share
            </button>
            <div class="h-px bg-gray-200 dark:bg-gray-700 my-1"></div>
            <button onclick="deleteChat('${chat.id}')" class="w-full text-left px-3 py-2 text-xs text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-2">
              <i class="fas fa-trash-alt"></i> Delete
            </button>
          </div>
        </div>
      </div>
    `;
  });
}

// Chat Menu Functions
function toggleChatMenu(event, chatId) {
  event.stopPropagation();
  // Close all other menus
  document.querySelectorAll('[id^="chat-menu-"]').forEach(menu => {
    if (menu.id !== `chat-menu-${chatId}`) {
      menu.classList.add('hidden');
    }
  });

  const menu = document.getElementById(`chat-menu-${chatId}`);
  if (menu) {
    menu.classList.toggle('hidden');
  }
}

// Close menus when clicking outside
document.addEventListener('click', () => {
  document.querySelectorAll('[id^="chat-menu-"]').forEach(menu => {
    menu.classList.add('hidden');
  });
});

function shareChat(chatId) {
  const url = `${window.location.origin}/chat?id=${chatId}`;
  navigator.clipboard.writeText(url).then(() => {
    showNotification('🔗 Link copied to clipboard', 'success', 2000);
  }).catch(() => {
    showNotification('❌ Failed to copy link', 'error', 2000);
  });
}

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
  if (!isTyping) {
    isTyping = true;
  }
}

function hideTypingIndicator() {
  if (isTyping) {
    isTyping = false;
  }
}

// Enhanced event listeners
if (themeToggle) {
  themeToggle.addEventListener('click', toggleTheme);
}

if (headerThemeToggle) {
  headerThemeToggle.addEventListener('click', toggleTheme);
}

// Settings modal controls
if (layoutBtn) {
  layoutBtn.addEventListener('click', () => {
    document.getElementById('settingsModal')?.classList.remove('hidden');
  });
}

const closeSettingsBtn = document.getElementById('closeSettingsBtn');
const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
const modalOverlay = document.getElementById('modalOverlay');
const saveSettingsBtn = document.getElementById('saveSettingsBtn');

function closeSettingsModal() {
  document.getElementById('settingsModal')?.classList.add('hidden');
}

closeSettingsBtn?.addEventListener('click', closeSettingsModal);
cancelSettingsBtn?.addEventListener('click', closeSettingsModal);
modalOverlay?.addEventListener('click', closeSettingsModal);

// Settings tab navigation
document.querySelectorAll('.settings-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    const tabName = tab.dataset.tab;

    // Update active tab
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');

    // Update content
    document.querySelectorAll('.settings-content').forEach(content => content.classList.add('hidden'));
    document.getElementById(`${tabName}-tab`)?.classList.remove('hidden');

    // Update title
    const titles = {
      general: 'General Settings',
      profile: 'Profile Settings',
      llm: 'AI Models',
      interface: 'Interface Settings',
      advanced: 'Advanced Settings'
    };
    document.getElementById('settingsTitle').textContent = titles[tabName] || 'Settings';
  });
});

saveSettingsBtn?.addEventListener('click', () => {
  // Save all settings
  const settings = {
    openaiKey: document.getElementById('openaiKey')?.value,
    geminiKey: document.getElementById('geminiKey')?.value,
    ollamaModel: document.getElementById('ollamaModel')?.value,
    autoSave: document.getElementById('autoSave')?.checked,
    soundNotif: document.getElementById('soundNotif')?.checked
  };

  // Save to localStorage
  Object.entries(settings).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      localStorage.setItem(key, value);
    }
  });

  showNotification('⚙️ Settings saved successfully!', 'success');
  closeSettingsModal();
});

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




mobileMenuBtn?.addEventListener('click', () => {
  const overlay = document.getElementById('mobileOverlay');
  
  if (sidebar) {
    const isHidden = sidebar.classList.contains('hidden');
    
    if (isHidden) {
      // Show sidebar
      sidebar.classList.remove('hidden');
      sidebar.classList.add('flex');
      sidebar.classList.remove('-translate-x-full');
      overlay?.classList.remove('hidden');
    } else {
      // Hide sidebar
      sidebar.classList.add('-translate-x-full');
      overlay?.classList.add('hidden');
      setTimeout(() => {
        sidebar.classList.add('hidden');
        sidebar.classList.remove('flex');
      }, 300);
    }
  }
});

// Close sidebar when clicking overlay
document.getElementById('mobileOverlay')?.addEventListener('click', () => {
  const overlay = document.getElementById('mobileOverlay');
  if (sidebar && !sidebar.classList.contains('hidden')) {
    sidebar.classList.add('-translate-x-full');
    overlay?.classList.add('hidden');
    setTimeout(() => {
      sidebar.classList.add('hidden');
      sidebar.classList.remove('flex');
    }, 300);
  }
});

// Close sidebar when clicking close button
document.getElementById('closeSidebarBtn')?.addEventListener('click', () => {
  const overlay = document.getElementById('mobileOverlay');
  if (sidebar && !sidebar.classList.contains('hidden')) {
    sidebar.classList.add('-translate-x-full');
    overlay?.classList.add('hidden');
    setTimeout(() => {
      sidebar.classList.add('hidden');
      sidebar.classList.remove('flex');
    }, 300);
  }
});

// Enhanced logout with confirmation
// Enhanced logout with confirmation
logoutBtn?.addEventListener('click', () => {
  showConfirmModal(
    'Are you sure you want to logout?',
    async () => {
      try {
        showNotification('👋 Logging out...', 'info');
        await fetch('/auth/logout', { method: 'POST' });
        window.location.href = '/';
      } catch (error) {
        console.error('Logout failed:', error);
        showNotification('❌ Logout failed. Please try again.', 'error');
      }
    },
    {
      title: 'Confirm Logout',
      confirmText: 'Logout',
      icon: 'fas fa-sign-out-alt',
      confirmColor: 'red'
    }
  );
});

signupBtn?.addEventListener('click', () => {
  window.location.href = '/auth';
});

// Login button handler
const loginBtn = document.getElementById('loginBtn');
loginBtn?.addEventListener('click', () => {
  window.location.href = '/auth';
});

// Load saved settings and user data on page load
document.addEventListener('DOMContentLoaded', async () => {
  const settingsToLoad = [
    'openaiKey', 'geminiKey', 'ollamaModel', 'autoSave', 'soundNotif'
  ];

  settingsToLoad.forEach(setting => {
    const element = document.getElementById(setting);
    const saved = localStorage.getItem(setting);

    if (element && saved) {
      if (element.type === 'checkbox') {
        element.checked = saved === 'true';
      } else {
        element.value = saved;
      }
    }
  });

  // Load user profile data
  try {
    const response = await fetch('/user-status');
    const data = await response.json();
    
    if (data.user && !data.user.is_guest) {
      const profileName = document.getElementById('profileName');
      const profileEmail = document.getElementById('profileEmail');
      const profileMobile = document.getElementById('profileMobile');
      
      if (profileName) profileName.value = data.user.name || '';
      if (profileEmail) profileEmail.value = data.user.email || '';
      if (profileMobile) profileMobile.value = data.user.mobile || '';
    }
  } catch (error) {
    console.error('Failed to load user profile data:', error);
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

  // Ctrl/Cmd + Shift + S to open settings
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'S') {
    e.preventDefault();
    document.getElementById('settingsModal')?.classList.remove('hidden');
  }

  // Escape to close settings modal
  if (e.key === 'Escape') {
    closeSettingsModal();
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
  wrapper.querySelectorAll('pre').forEach((pre) => {
    pre.classList.add('overflow-x-auto', 'max-w-full', 'whitespace-pre-wrap', 'break-words');
    pre.style.maxWidth = 'calc(100vw - 2rem)';
  });
  wrapper.querySelectorAll('code').forEach((code) => {
    code.classList.add('break-words', 'whitespace-pre-wrap');
    if (code.parentElement.tagName === 'PRE') {
      code.style.maxWidth = '100%';
      code.style.wordBreak = 'break-all';
    }
  });
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
  messageContainer.className = 'flex gap-2 sm:gap-4 justify-end animate-slide-up message-container mt-6';

  const messageGroup = document.createElement('div');
  messageGroup.className = 'max-w-[85%] sm:max-w-[75%] group';

  const bubble = document.createElement('div');
  const bubbleClass = layoutSettings.messageStyle === 'card'
    ? 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100'
    : layoutSettings.messageStyle === 'minimal'
      ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
      : 'bg-gradient-to-r from-gemini-blue to-blue-600 text-white';

  bubble.className = `${bubbleClass} rounded-2xl rounded-tr-md px-4 sm:px-6 py-3 sm:py-4 shadow-lg hover:shadow-xl transition-all duration-200 message-content`;
  bubble.innerHTML = `<div class="whitespace-pre-line text-sm leading-relaxed">${text}</div>`;

  const timestamp = document.createElement('div');
  timestamp.className = 'text-xs text-gray-500 dark:text-gray-400 mt-2 text-right opacity-0 group-hover:opacity-100 transition-opacity';
  timestamp.innerHTML = `<i class="fas fa-clock mr-1"></i>${new Date().toLocaleTimeString()}`;

  messageGroup.append(bubble, timestamp);

  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-r from-gemini-blue to-blue-600 flex items-center justify-center shadow-lg flex-shrink-0 text-white font-bold text-xs sm:text-sm';
  
  // Get user initials
  fetch('/user-status')
    .then(response => response.json())
    .then(data => {
      if (data.user && data.user.name) {
        const nameParts = data.user.name.split(' ');
        const initials = nameParts.length > 1 
          ? nameParts[0][0].toUpperCase() + nameParts[nameParts.length - 1][0].toUpperCase()
          : data.user.name[0].toUpperCase();
        avatar.textContent = initials;
      } else {
        avatar.textContent = 'U';
      }
    })
    .catch(() => {
      avatar.textContent = 'U';
    });

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
  messageContainer.className = 'flex gap-2 sm:gap-4 animate-slide-up message-container';

  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-r from-gemini-blue to-gemini-green flex items-center justify-center shadow-lg flex-shrink-0 sparkle';
  avatar.innerHTML = '<i class="fas fa-brain text-white text-xs sm:text-sm"></i>';

  const messageGroup = document.createElement('div');
  messageGroup.className = 'flex-1 group';

  const bubble = document.createElement('div');
  bubble.className = 'bg-white dark:bg-gray-800 rounded-2xl rounded-tl-md px-4 sm:px-6 py-3 sm:py-4 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-200 message-bubble-advanced';

  const body = renderMarkdown(md);
  body.className = 'prose dark:prose-invert max-w-none markdown text-sm leading-relaxed';
  bubble.appendChild(body);

  const actions = document.createElement('div');
  actions.className = 'flex items-center gap-3 mt-3 opacity-0 group-hover:opacity-100 transition-opacity';
  actions.innerHTML = `
    <button class="feedback-btn text-xs text-gray-500 hover:text-green-600 transition-colors flex items-center gap-1" data-feedback="positive">
      <i class="fas fa-thumbs-up"></i>Helpful
    </button>
    <button class="feedback-btn text-xs text-gray-500 hover:text-red-600 transition-colors flex items-center gap-1" data-feedback="negative">
      <i class="fas fa-thumbs-down"></i>Not Helpful
    </button>
    <button class="text-xs text-gray-500 hover:text-gemini-blue transition-colors flex items-center gap-1 micro-interaction" onclick="copyMessage(this)">
      <i class="fas fa-copy"></i>Copy
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
  messageContainer.className = 'flex gap-2 sm:gap-4 animate-slide-up message-container';

  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-r from-gemini-blue to-gemini-green flex items-center justify-center shadow-lg flex-shrink-0 sparkle';
  avatar.innerHTML = '<i class="fas fa-brain text-white text-xs sm:text-sm"></i>';

  const messageGroup = document.createElement('div');
  messageGroup.className = 'flex-1 group';

  const bubble = document.createElement('div');
  bubble.className = 'bg-white dark:bg-gray-800 rounded-2xl rounded-tl-md px-4 sm:px-6 py-3 sm:py-4 shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-200 message-bubble-advanced';

  const body = document.createElement('div');
  body.className = 'prose dark:prose-invert max-w-none markdown relative text-sm leading-relaxed';
  body.innerHTML = `
    <div class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
      <div class="flex space-x-1">
        <div class="w-2 h-2 bg-gemini-blue rounded-full animate-bounce" style="animation-delay: 0ms"></div>
        <div class="w-2 h-2 bg-gemini-green rounded-full animate-bounce" style="animation-delay: 150ms"></div>
        <div class="w-2 h-2 bg-gemini-yellow rounded-full animate-bounce" style="animation-delay: 300ms"></div>
      </div>
      <span>AI is thinking...</span>
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

  // Hide welcome screen and show chat messages
  const welcomeScreen = document.getElementById('welcomeScreen');
  const chatMessages = document.getElementById('chatMessages');
  if (welcomeScreen) welcomeScreen.style.display = 'none';
  if (chatMessages) chatMessages.classList.remove('hidden');

  // Disable input during processing
  promptEl.disabled = true;
  streamBtn.disabled = true;

  // Show stop button during streaming
  if (useStream) {
    streamBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
  }

  // Create new chat if this is the first message and no active chat
  if (!activeChatId && text) {
    try {
      const response = await fetch('/start_chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      if (data.success) {
        activeChatId = data.chat_id;
        // Update URL with new chat ID
        window.history.pushState({}, '', `/chat?id=${data.chat_id}`);
      }
    } catch (error) {
      console.error('Error creating new chat:', error);
      showNotification('❌ Failed to create new chat', 'error', 2000);
      return;
    }
  }

  // Always add user message to UI first
  addUserMessage(text || '(image only)', lastImageUrl);

  // Save user message to backend
  if (activeChatId) {
    await fetch(`/chat/${activeChatId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        role: 'user',
        content: text || '(image only)',
        image_url: lastImageUrl
      })
    });
  }

  preview?.classList.add('hidden');
  if (preview) preview.innerHTML = '';

  promptEl.value = '';
  showTypingIndicator();

  // Simple context - just send the current message
  let contextualMessage = text;
  if (currentChatbot) {
    contextualMessage = `${currentChatbot.instructions}\n\nKnowledge: ${currentChatbot.trainingData}\n\nQuestion: ${text}`;
  }

  if (useStream) {
    const container = addAssistantStreamContainer();
    if (!container) return;

    try {
      const abortController = new AbortController();
      currentStreamController = abortController;

      const res = await fetch('/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: contextualMessage,
          image_url: lastImageUrl,
          chatbot_id: currentChatbot?.id
        }),
        signal: abortController.signal
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
            } catch (e) { }
          }
        }
      }

      // Save AI response and update chat title
      if (activeChatId && fullResponse) {
        await fetch(`/chat/${activeChatId}/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            role: 'assistant',
            content: fullResponse
          })
        });
        updateChatTitle(activeChatId, text, fullResponse);
      }

      // Track performance
      const responseTime = Date.now() - startTime;
      performanceMetrics.totalResponseTime += responseTime;
      performanceMetrics.averageResponseTime = performanceMetrics.totalResponseTime / performanceMetrics.messageCount;

    } catch (error) {
      hideTypingIndicator();
      if (error.name === 'AbortError') {
        container.innerHTML = renderMarkdown('⏹️ **Stopped**: Response generation was stopped by user.').innerHTML;
        showNotification('⏹️ Response stopped', 'info');
      } else {
        container.innerHTML = renderMarkdown('❌ **Error**: Could not stream response. Please try again.').innerHTML;
        showNotification('❌ Connection error. Please check your internet.', 'error');
      }
    } finally {
      currentStreamController = null;
    }
  } else {
    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: contextualMessage,
          image_url: lastImageUrl,
          chatbot_id: currentChatbot?.id
        })
      });

      hideTypingIndicator();

      const data = await res.json();
      const aiResponse = data.reply || 'No response received';
      addAssistantMessage(aiResponse);

      // Save AI response and update chat title
      if (activeChatId) {
        await fetch(`/chat/${activeChatId}/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            role: 'assistant',
            content: aiResponse
          })
        });
        updateChatTitle(activeChatId, text, aiResponse);
      }

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

  // Re-enable input and reset buttons
  promptEl.disabled = false;
  streamBtn.disabled = false;
  streamBtn.classList.remove('hidden');
  stopBtn.classList.add('hidden');
  promptEl.focus();

  lastImageUrl = null;
  scrollToBottom();

  // Refresh sidebar to show updated chat
  loadUserChats();
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

// Feedback system
document.addEventListener('click', (e) => {
  if (e.target.closest('.feedback-btn')) {
    const btn = e.target.closest('.feedback-btn');
    const feedbackType = btn.dataset.feedback;
    const messageContainer = btn.closest('.message-container');
    const aiResponse = messageContainer.querySelector('.markdown').textContent;

    const prevMessage = messageContainer.previousElementSibling;
    const userInput = prevMessage ? prevMessage.querySelector('.message-content')?.textContent || '' : '';

    submitFeedback(Date.now().toString(), feedbackType, userInput, aiResponse);

    btn.style.color = feedbackType === 'positive' ? '#10b981' : '#ef4444';
    showNotification(feedbackType === 'positive' ? '👍 Thanks for feedback!' : '👎 Feedback recorded', 'success', 1500);
  }
});

function submitFeedback(messageId, type, userInput, aiResponse) {
  fetch('/api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message_id: messageId,
      type: type,
      user_input: userInput,
      ai_response: aiResponse
    })
  }).catch(error => console.error('Feedback error:', error));
}





// Enhanced sidebar with better history management
// This function is replaced by updateChatSidebar()

// Remove this function since we're using backend storage

// Remove this function since we're not using local chat storage anymore

// Unused loadChat function removed

// Unused generateChatTitle function removed

async function updateChatTitle(chatId, userMessage, aiResponse) {
  try {
    // Only generate title if it's a new chat or has very few messages
    // We let the backend decide based on history length or just force it for now
    // But to avoid spamming, let's only do it if the current title is "New Chat" 
    // or if we want to refresh it.

    // For now, let's call the generator. The backend will use the history.
    // We can optimize by checking if we really need to update.

    const response = await fetch(`/chat/${chatId}/generate_title`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        loadUserChats(); // Refresh sidebar
      }
    }
  } catch (error) {
    console.error('Error updating chat title:', error);
  }
}



// Duplicate createNewChat function removed

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

// refreshSidebar(); // Will be called after chats are initialized

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

// Example prompts functionality
document.querySelectorAll('.example-prompt').forEach(button => {
  button.addEventListener('click', () => {
    const promptText = button.querySelector('span').textContent;
    if (promptEl) {
      promptEl.value = promptText;
      promptEl.focus();
      showNotification('💡 Example prompt loaded', 'success', 1500);
    }
  });
});

// AI Model selection functionality
const aiModelSelect = document.getElementById('aiModelSelect');
const currentModelDisplay = document.getElementById('currentModel');

if (aiModelSelect) {
  // Load saved model preference
  const savedModel = localStorage.getItem('selectedAIModel') || 'ollama';
  aiModelSelect.value = savedModel;
  updateCurrentModelDisplay(savedModel);

  aiModelSelect.addEventListener('change', async (e) => {
    const selectedModel = e.target.value;

    try {
      // Send model selection to backend
      const response = await fetch('/set-ai-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });

      if (response.ok) {
        localStorage.setItem('selectedAIModel', selectedModel);
        updateCurrentModelDisplay(selectedModel);
        showNotification(`🤖 Switched to ${getModelDisplayName(selectedModel)}`, 'success');
      } else {
        const data = await response.json();
        showNotification(`❌ ${data.error || 'Failed to switch model'}`, 'error');
        // Revert selection
        aiModelSelect.value = localStorage.getItem('selectedAIModel') || 'ollama';
      }
    } catch (error) {
      console.error('Error switching model:', error);
      showNotification('❌ Connection error while switching model', 'error');
      // Revert selection
      aiModelSelect.value = localStorage.getItem('selectedAIModel') || 'ollama';
    }
  });
}

function updateCurrentModelDisplay(model) {
  if (currentModelDisplay) {
    currentModelDisplay.textContent = getModelDisplayName(model);
  }
}

function getModelDisplayName(model) {
  const modelNames = {
    'ollama': 'Ollama',
    'openai': 'ChatGPT',
    'gemini': 'Gemini'
  };
  return modelNames[model] || 'Unknown';
}

// Check available AI models on page load
async function checkAvailableModels() {
  try {
    const response = await fetch('/available-models');
    const data = await response.json();

    if (aiModelSelect && data.models) {
      // Update select options based on available models
      const options = aiModelSelect.querySelectorAll('option');
      options.forEach(option => {
        const model = option.value;
        if (!data.models.includes(model)) {
          option.disabled = true;
          option.textContent += ' (Not Available)';
        }
      });

      // If current selection is not available, switch to first available
      const currentModel = localStorage.getItem('selectedAIModel') || 'ollama';
      if (!data.models.includes(currentModel) && data.models.length > 0) {
        const firstAvailable = data.models[0];
        aiModelSelect.value = firstAvailable;
        localStorage.setItem('selectedAIModel', firstAvailable);
        updateCurrentModelDisplay(firstAvailable);
        showNotification(`🔄 Switched to ${getModelDisplayName(firstAvailable)} (only available model)`, 'info');
      }
    }
  } catch (error) {
    console.error('Error checking available models:', error);
  }
}

// Initialize model checking
checkAvailableModels();

// Ollama model management
function loadOllamaModels() {
  fetch('/ollama/models')
    .then(response => response.json())
    .then(data => {
      const container = document.getElementById('installedModels');
      if (data.success && data.models) {
        container.innerHTML = data.models.map(model => `
          <div class="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border">
            <div class="flex-1">
              <div class="font-medium text-sm text-gray-900 dark:text-white">${model.name}</div>
              <div class="text-xs text-gray-500">${model.size} • Modified ${model.modified}</div>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="updateModel('${model.name}')" class="p-1 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded" title="Update">
                <i class="fas fa-sync text-xs"></i>
              </button>
              <button onclick="removeModel('${model.name}')" class="p-1 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded" title="Remove">
                <i class="fas fa-trash text-xs"></i>
              </button>
            </div>
          </div>
        `).join('');
      } else {
        container.innerHTML = '<div class="text-sm text-gray-500 text-center py-4">No models found</div>';
      }
    })
    .catch(() => {
      document.getElementById('installedModels').innerHTML = '<div class="text-sm text-red-500 text-center py-4">Failed to load models</div>';
    });
}

function loadSystemInfo() {
  fetch('/ollama/info')
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        document.getElementById('usedStorage').textContent = data.used || '--';
        document.getElementById('freeStorage').textContent = data.free || '--';
        document.getElementById('totalRAM').textContent = data.ram || '--';
        
        // Update storage bar
        if (data.usagePercent) {
          document.getElementById('storageBar').style.width = data.usagePercent + '%';
          document.getElementById('storageText').textContent = data.usagePercent + '% used';
        }
      }
    })
    .catch(() => {});
}

function pullModel(modelName) {
  if (!modelName.trim()) return;
  
  const btn = document.getElementById('pullModelBtn');
  const originalText = btn.innerHTML;
  btn.innerHTML = '<i class="fas fa-spinner animate-spin mr-1"></i>Pulling...';
  btn.disabled = true;
  
  fetch('/ollama/pull', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model: modelName })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showNotification(`✅ ${modelName} pulled successfully`, 'success');
      document.getElementById('pullModelName').value = '';
      loadOllamaModels();
    } else {
      showNotification(`❌ Failed to pull ${modelName}: ${data.error}`, 'error');
    }
  })
  .catch(() => {
    showNotification(`❌ Failed to pull ${modelName}`, 'error');
  })
  .finally(() => {
    btn.innerHTML = originalText;
    btn.disabled = false;
  });
}

function updateModel(modelName) {
  showConfirmModal(`Update ${modelName}?`, () => {
    fetch('/ollama/pull', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: modelName })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showNotification(`✅ ${modelName} updated`, 'success');
        loadOllamaModels();
      } else {
        showNotification(`❌ Update failed: ${data.error}`, 'error');
      }
    });
  });
}

function removeModel(modelName) {
  showConfirmModal(`Remove ${modelName}?`, () => {
    fetch('/ollama/remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: modelName })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showNotification(`🗑️ ${modelName} removed`, 'success');
        loadOllamaModels();
      } else {
        showNotification(`❌ Remove failed: ${data.error}`, 'error');
      }
    });
  });
}

// Event listeners
document.getElementById('refreshModels')?.addEventListener('click', () => {
  loadOllamaModels();
  loadSystemInfo();
});

document.getElementById('pullModelBtn')?.addEventListener('click', () => {
  const dropdown = document.getElementById('modelDropdown');
  const custom = document.getElementById('customModelName');
  const modelName = dropdown?.value || custom?.value;
  if (modelName) {
    pullModel(modelName);
    dropdown.value = '';
    custom.value = '';
  }
});

document.getElementById('customModelName')?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    pullModel(e.target.value);
    e.target.value = '';
  }
});

// Load on settings open
document.querySelectorAll('.settings-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    if (tab.dataset.tab === 'llm') {
      setTimeout(() => {
        loadOllamaModels();
        loadSystemInfo();
      }, 100);
    }
  });
});

// Model selection functionality
const modelSelect = document.getElementById('modelSelect');
if (modelSelect) {
  // Load saved model
  const savedModel = localStorage.getItem('selectedModel') || 'llama3.2:3b';
  modelSelect.value = savedModel;
  
  modelSelect.addEventListener('change', async (e) => {
    const selectedModel = e.target.value;
    
    // Check if API key is required
    if (selectedModel.startsWith('gpt-') || selectedModel.startsWith('gemini-')) {
      const provider = selectedModel.startsWith('gpt-') ? 'openai' : 'gemini';
      const keyName = provider === 'openai' ? 'openaiKey' : 'geminiKey';
      const apiKey = localStorage.getItem(keyName);
      
      if (!apiKey) {
        showNotification(`❌ ${provider.toUpperCase()} API key required. Please add it in Settings.`, 'error', 4000);
        // Revert to previous selection
        modelSelect.value = localStorage.getItem('selectedModel') || 'llama3.2:3b';
        return;
      }
    }
    
    localStorage.setItem('selectedModel', selectedModel);
    const modelName = selectedModel.includes(':') ? selectedModel.split(':')[0] : selectedModel;
    showNotification(`🤖 Switched to ${modelName}`, 'success', 2000);
  });
}

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

// Chatbot management
let chatbots = JSON.parse(localStorage.getItem('chatbots') || '[]');
let currentChatbot = null;

// Chat management
let chats = [];
let currentChatId = null;

// This function is replaced by loadUserChats()

// These functions are now handled by the session manager backend

// New chat button
document.getElementById('newChatBtn')?.addEventListener('click', () => {
  createNewChat();
});

// New chatbot modal
const newChatbotBtn = document.getElementById('newChatbotBtn');
const newChatbotModal = document.getElementById('newChatbotModal');
const chatbotModalOverlay = document.getElementById('chatbotModalOverlay');
const cancelChatbotBtn = document.getElementById('cancelChatbotBtn');
const createChatbotBtn = document.getElementById('createChatbotBtn');

function closeChatbotModal() {
  newChatbotModal?.classList.add('hidden');
  document.getElementById('chatbotName').value = '';
  document.getElementById('chatbotKnowledge').value = '';
  document.getElementById('chatbotFiles').value = '';
}

newChatbotBtn?.addEventListener('click', () => {
  // Hide other views
  document.getElementById('welcomeScreen')?.classList.add('hidden');
  document.getElementById('chatMessages')?.classList.add('hidden');

  // Show coming soon
  const comingSoon = document.getElementById('chatbotComingSoon');
  if (comingSoon) {
    comingSoon.classList.remove('hidden');
  }

  // Update URL to reflect state
  history.pushState({ page: 'chatbot-coming-soon' }, '', '#chatbot-coming-soon');
});

// Handle back button to restore view
window.addEventListener('popstate', (event) => {
  if (!event.state) {
    window.location.reload();
  }
});

chatbotModalOverlay?.addEventListener('click', closeChatbotModal);
cancelChatbotBtn?.addEventListener('click', closeChatbotModal);

// Enhanced file handling
let uploadedFiles = [];

document.getElementById('chatbotFiles')?.addEventListener('change', (e) => {
  const files = Array.from(e.target.files);
  files.forEach(file => {
    if (!uploadedFiles.find(f => f.name === file.name)) {
      uploadedFiles.push({
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        content: null
      });
    }
  });
  updateFilesList();
});

function updateFilesList() {
  const filesList = document.getElementById('uploadedFilesList');
  const fileCount = document.getElementById('fileCount');

  if (!filesList || !fileCount) return;

  fileCount.textContent = `${uploadedFiles.length} files`;

  if (uploadedFiles.length === 0) {
    filesList.innerHTML = `
      <div class="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
        <i class="fas fa-folder-open text-2xl mb-2"></i>
        <p>No files uploaded yet</p>
      </div>
    `;
    return;
  }

  filesList.innerHTML = uploadedFiles.map((fileObj, index) => `
    <div class="flex items-center justify-between p-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600">
      <div class="flex items-center gap-2 flex-1 min-w-0">
        <i class="fas fa-file-alt text-gemini-blue text-sm"></i>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">${fileObj.name}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">${(fileObj.size / 1024).toFixed(1)} KB</p>
        </div>
      </div>
      <button onclick="removeFile(${index})" class="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors">
        <i class="fas fa-times text-red-500 text-xs"></i>
      </button>
    </div>
  `).join('');
}

function removeFile(index) {
  uploadedFiles.splice(index, 1);
  updateFilesList();
}

createChatbotBtn?.addEventListener('click', async () => {
  const name = document.getElementById('chatbotName')?.value.trim();
  const description = document.getElementById('chatbotDescription')?.value.trim();
  const instructions = document.getElementById('chatbotInstructions')?.value.trim();

  if (!name) {
    showNotification('❌ Please enter a chatbot name', 'error');
    return;
  }

  if (!instructions) {
    showNotification('❌ Please provide base instructions', 'error');
    return;
  }

  // Show training progress
  const createBtn = document.getElementById('createChatbotBtn');
  const originalText = createBtn.innerHTML;
  createBtn.innerHTML = '<i class="fas fa-spinner animate-spin"></i> Training...';
  createBtn.disabled = true;

  let trainingData = '';

  // Process uploaded files
  if (uploadedFiles.length > 0) {
    showNotification('📚 Processing training files...', 'info', 2000);

    for (let fileObj of uploadedFiles) {
      try {
        const text = await fileObj.file.text();
        trainingData += `\n\n=== ${fileObj.name} ===\n${text}`;
      } catch (error) {
        console.error('Error reading file:', error);
        showNotification(`❌ Error reading ${fileObj.name}`, 'error');
      }
    }
  }

  const newChatbot = {
    id: Date.now().toString(),
    name,
    description: description || 'Personal AI Assistant',
    instructions,
    trainingData,
    fileCount: uploadedFiles.length,
    created: new Date().toISOString(),
    lastTrained: new Date().toISOString()
  };

  // Simulate training process
  setTimeout(() => {
    chatbots.push(newChatbot);
    localStorage.setItem('chatbots', JSON.stringify(chatbots));

    renderChatbots();
    closeChatbotModal();

    // Reset form
    uploadedFiles = [];
    document.getElementById('chatbotName').value = '';
    document.getElementById('chatbotDescription').value = '';
    document.getElementById('chatbotInstructions').value = '';
    updateFilesList();

    createBtn.innerHTML = originalText;
    createBtn.disabled = false;

    showNotification(`🎉 Personal AI "${name}" trained successfully with ${newChatbot.fileCount} files!`, 'success', 4000);
  }, 2000);
});

function showConfirmModal(message, onConfirm, options = {}) {
  const modal = document.getElementById('confirmModal');
  const messageEl = document.getElementById('confirmMessage');
  const titleEl = document.getElementById('confirmTitle');
  const btnTextEl = document.getElementById('confirmBtnText');
  const btnIconEl = document.getElementById('confirmBtnIcon');
  const cancelBtn = document.getElementById('confirmCancel');
  const deleteBtn = document.getElementById('confirmDelete'); // This is the confirm button

  messageEl.textContent = message;
  titleEl.textContent = options.title || 'Confirm Action';
  btnTextEl.textContent = options.confirmText || 'Delete';

  if (options.icon) {
    btnIconEl.innerHTML = `<i class="${options.icon} mr-2"></i>`;
  } else {
    btnIconEl.innerHTML = '<i class="fas fa-trash mr-2"></i>';
  }

  // Update button color if needed (default is red)
  if (options.confirmColor === 'blue') {
    deleteBtn.className = 'px-6 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl';
  } else {
    // Reset to red
    deleteBtn.className = 'px-6 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-xl';
  }

  modal.classList.remove('hidden');

  const handleCancel = () => {
    modal.classList.add('hidden');
    cancelBtn.removeEventListener('click', handleCancel);
    deleteBtn.removeEventListener('click', handleConfirm);
  };

  const handleConfirm = () => {
    modal.classList.add('hidden');
    onConfirm();
    cancelBtn.removeEventListener('click', handleCancel);
    deleteBtn.removeEventListener('click', handleConfirm);
  };

  cancelBtn.addEventListener('click', handleCancel);
  deleteBtn.addEventListener('click', handleConfirm);
}



function renderChatbots() {
  const chatbotsList = document.getElementById('chatbotsList');
  if (!chatbotsList) return;

  chatbotsList.innerHTML = chatbots.map(bot => `
    <div class="chatbot-item p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors group" data-id="${bot.id}">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <i class="fas fa-robot text-gemini-blue text-sm"></i>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300">${bot.name}</span>
        </div>
        <button class="delete-bot opacity-0 group-hover:opacity-100 w-7 h-7 rounded-lg bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg hover:shadow-xl transform hover:scale-110 transition-all duration-200 flex items-center justify-center" data-id="${bot.id}" title="Delete bot">
          <i class="fas fa-trash text-xs"></i>
        </button>
      </div>
      <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">${new Date(bot.created).toLocaleDateString()}</div>
    </div>
  `).join('');

  // Add click handlers
  document.querySelectorAll('.chatbot-item').forEach(item => {
    item.addEventListener('click', (e) => {
      if (!e.target.closest('.delete-bot')) {
        const botId = item.dataset.id;
        const bot = chatbots.find(b => b.id === botId);
        if (bot) {
          currentChatbot = bot;
          if (messages) messages.innerHTML = '';
          showNotification(`🤖 Switched to ${bot.name}`, 'success', 1500);
        }
      }
    });
  });

  // Add delete handlers
  document.querySelectorAll('.delete-bot').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const botId = btn.dataset.id;
      deleteChatbot(botId);
    });
  });
}

function deleteChatbot(botId) {
  const bot = chatbots.find(b => b.id === botId);
  showConfirmModal(`Are you sure you want to delete "${bot?.name}" chatbot?`, () => {
    chatbots = chatbots.filter(b => b.id !== botId);
    localStorage.setItem('chatbots', JSON.stringify(chatbots));
    renderChatbots();
    showNotification('🗑️ Chatbot deleted', 'success', 1500);
  });
}

// Welcome Screen Management
function hideWelcomeScreen() {
  const welcomeScreen = document.getElementById('welcomeScreen');
  if (welcomeScreen && !welcomeScreen.style.display.includes('none')) {
    welcomeScreen.style.opacity = '0';
    welcomeScreen.style.transform = 'translateY(-20px)';
    welcomeScreen.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';

    setTimeout(() => {
      welcomeScreen.style.display = 'none';
    }, 500);
  }
}

function showWelcomeScreen() {
  const welcomeScreen = document.getElementById('welcomeScreen');
  if (welcomeScreen) {
    welcomeScreen.style.display = 'block';
    welcomeScreen.style.opacity = '0';
    welcomeScreen.style.transform = 'translateY(20px)';

    setTimeout(() => {
      welcomeScreen.style.opacity = '1';
      welcomeScreen.style.transform = 'translateY(0)';
    }, 10);
  }
}

function shouldShowWelcomeScreen() {
  // Check if there are any message containers (excluding welcome screen)
  const messageContainers = document.querySelectorAll('#messagesContainer .message-container');
  return messageContainers.length === 0;
}

// Enhanced send function with welcome screen handling
function enhancedSend(useStream = false) {
  // Hide welcome screen and show chat messages when first message is sent
  const welcomeScreen = document.getElementById('welcomeScreen');
  const chatMessages = document.getElementById('chatMessages');

  if (welcomeScreen && !welcomeScreen.style.display.includes('none')) {
    hideWelcomeScreen();

    if (chatMessages) {
      chatMessages.classList.remove('hidden');
    }

    setTimeout(() => {

    }, 300);
  } else if (chatMessages && chatMessages.classList.contains('hidden')) {
    // Ensure chat messages are visible even if welcome screen was already hidden
    chatMessages.classList.remove('hidden');
  }

  // Call the original send function
  send(useStream);
}

// Welcome screen feature demonstrations
function initializeWelcomeFeatures() {
  // Feature card hover effects with sound (optional)
  document.querySelectorAll('.feature-card').forEach((card, index) => {
    card.addEventListener('mouseenter', () => {
      // Add subtle animation delay based on index
      card.style.animationDelay = `${index * 0.1}s`;
      card.classList.add('animate-pulse');

      setTimeout(() => {
        card.classList.remove('animate-pulse');
      }, 600);
    });
  });

  // Quick action buttons
  const uploadAction = document.querySelector('.quick-action[data-action="upload"]');
  const voiceAction = document.querySelector('.quick-action[data-action="voice"]');

  if (uploadAction) {
    uploadAction.addEventListener('click', () => {
      document.getElementById('fileInput')?.click();
      showNotification('📁 File upload dialog opened', 'info', 2000);
    });
  }

  if (voiceAction) {
    voiceAction.addEventListener('click', () => {
      document.getElementById('voiceBtn')?.click();
      showNotification('🎤 Voice input activated', 'info', 2000);
    });
  }

  // Keyboard shortcuts demonstration
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      promptEl?.focus();
      showNotification('⌨️ Input focused via keyboard shortcut', 'success', 2000);
    }
  });
}

// Animated counter for features
function animateFeatureNumbers() {
  const features = [
    { element: '.feature-count-1', target: 6, suffix: '+' },
    { element: '.feature-count-2', target: 100, suffix: '%' },
    { element: '.feature-count-3', target: 24, suffix: '/7' }
  ];

  features.forEach(feature => {
    const element = document.querySelector(feature.element);
    if (element) {
      let current = 0;
      const increment = feature.target / 30;
      const timer = setInterval(() => {
        current += increment;
        if (current >= feature.target) {
          current = feature.target;
          clearInterval(timer);
        }
        element.textContent = Math.floor(current) + feature.suffix;
      }, 50);
    }
  });
}

// Welcome screen tutorial mode
function startWelcomeTutorial() {
  const steps = [
    {
      element: '#prompt',
      message: 'Type your message here or click an example below',
      position: 'top'
    },
    {
      element: '#fileInput',
      message: 'Upload files for analysis (PDFs, images, text)',
      position: 'bottom'
    },
    {
      element: '#voiceBtn',
      message: 'Use voice input for hands-free interaction',
      position: 'bottom'
    },
    {
      element: '#aiModelSelect',
      message: 'Choose your preferred AI model',
      position: 'top'
    }
  ];

  let currentStep = 0;

  function showStep(step) {
    const element = document.querySelector(step.element);
    if (element) {
      // Highlight element
      element.style.boxShadow = '0 0 0 3px rgba(66, 133, 244, 0.5)';
      element.style.transition = 'box-shadow 0.3s ease';

      // Show tooltip
      showNotification(step.message, 'info', 3000);

      // Remove highlight after delay
      setTimeout(() => {
        element.style.boxShadow = '';
      }, 3000);
    }
  }

  // Start tutorial
  const tutorialInterval = setInterval(() => {
    if (currentStep < steps.length) {
      showStep(steps[currentStep]);
      currentStep++;
    } else {
      clearInterval(tutorialInterval);
      showNotification('✨ Tutorial complete! Start chatting to explore more features.', 'success', 4000);
    }
  }, 4000);
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  console.log('DOM loaded, initializing...');

  initializeRevealAnimations();
  renderChatbots();
  initializeWelcomeFeatures();

  // Clear sidebar first
  if (sidebarHistory) {
    sidebarHistory.innerHTML = '';
  }

  // Load user chats
  loadUserChats();

  // Load chat from URL if present
  const urlParams = new URLSearchParams(window.location.search);
  const chatId = urlParams.get('id');

  if (chatId) {
    switchToChat(chatId);
  } else {
    // Always show welcome screen by default
    showWelcomeScreen();


  }

  console.log('🎨 Advanced Gemini-style UI initialized successfully!');

  // Initialize example prompts after DOM is loaded
  setTimeout(() => {
    document.querySelectorAll('.example-prompt').forEach((button, index) => {
      // Add staggered animation
      button.style.animationDelay = `${index * 0.1}s`;
      button.classList.add('welcome-slide-in');

      button.addEventListener('click', () => {
        const promptText = button.querySelector('span').textContent;
        if (promptEl) {
          promptEl.value = promptText;
          promptEl.focus();
          showNotification('💡 Example prompt loaded', 'success', 1500);

          // Auto-hide welcome screen after loading prompt
          setTimeout(() => {
            hideWelcomeScreen();
          }, 1000);
        }
      });
    });

    // Animate feature numbers
    animateFeatureNumbers();
  }, 100);

  // Set up send button and enter key handlers
  if (streamBtn) {
    streamBtn.addEventListener('click', () => enhancedSend(true));
  }

  if (promptEl) {
    // Auto-resize textarea
    promptEl.addEventListener('input', () => {
      promptEl.style.height = 'auto';
      promptEl.style.height = Math.min(promptEl.scrollHeight, 120) + 'px';
    });
    
    promptEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        enhancedSend(true);
      }
    });
  }

  // Stop button functionality
  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      if (currentStreamController) {
        currentStreamController.abort();
        showNotification('⏹️ Stopping response...', 'info', 1500);
      }
    });
  }
});

// User Menu Dropdown
const userMenuBtn = document.getElementById('userMenuBtn');
const userDropdown = document.getElementById('userDropdown');

if (userMenuBtn && userDropdown) {
  userMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    userDropdown.classList.toggle('hidden');
  });

  document.addEventListener('click', (e) => {
    if (!userMenuBtn.contains(e.target) && !userDropdown.contains(e.target)) {
      userDropdown.classList.add('hidden');
    }
  });
}
// Rename Chat Modal Logic
let currentRenameChatId = null;

function openRenameModal(chatId, currentName) {
  currentRenameChatId = chatId;
  const modal = document.getElementById('renameChatModal');
  const input = document.getElementById('renameChatInput');

  if (modal && input) {
    input.value = currentName;
    modal.classList.remove('hidden');
    input.focus();
  }
}

function closeRenameModal() {
  const modal = document.getElementById('renameChatModal');
  if (modal) {
    modal.classList.add('hidden');
  }
  currentRenameChatId = null;
}

function confirmRenameChat() {
  const input = document.getElementById('renameChatInput');
  if (!input || !currentRenameChatId) return;

  const newName = input.value.trim();
  if (newName !== '') {
    fetch(`/chat/${currentRenameChatId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          loadUserChats();
          showNotification('✏️ Chat renamed', 'success', 2000);
          closeRenameModal();
        }
      })
      .catch(error => {
        console.error('Error renaming chat:', error);
        showNotification('❌ Failed to rename chat', 'error', 2000);
      });
  }
}

// Update renameChat to use modal
function renameChat(chatId, currentName) {
  openRenameModal(chatId, currentName);
}
