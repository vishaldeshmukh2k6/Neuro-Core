const messages = document.getElementById('messages');
const promptEl = document.getElementById('prompt');
const streamBtn = document.getElementById('streamBtn');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const clearBtn = document.getElementById('clearBtn');
const sidebarHistory = document.getElementById('sidebarHistory');
const themeToggle = document.getElementById('themeToggle');
const headerThemeToggle = document.getElementById('headerThemeToggle');
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const sidebar = document.querySelector('aside');

console.log('Theme toggle elements:', {
  themeToggle: !!themeToggle,
  headerThemeToggle: !!headerThemeToggle,
  sidebar: !!sidebar
});

// Initialize theme
const savedTheme = localStorage.getItem('theme');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const initialTheme = savedTheme || (systemDark ? 'dark' : 'light');

if (initialTheme === 'dark') {
  document.documentElement.classList.add('dark');
}

// Theme toggle function
function toggleTheme() {
  console.log('Theme toggle clicked');
  const html = document.documentElement;
  const isDark = html.classList.contains('dark');
  
  if (isDark) {
    html.classList.remove('dark');
    localStorage.setItem('theme', 'light');
    console.log('Switched to light theme');
  } else {
    html.classList.add('dark');
    localStorage.setItem('theme', 'dark');
    console.log('Switched to dark theme');
  }
}

// Add event listeners
if (themeToggle) {
  themeToggle.addEventListener('click', toggleTheme);
  console.log('Sidebar theme toggle attached');
}

if (headerThemeToggle) {
  headerThemeToggle.addEventListener('click', toggleTheme);
  console.log('Header theme toggle attached');
}

mobileMenuBtn?.addEventListener('click', () => {
  sidebar?.classList.toggle('hidden');
  sidebar?.classList.toggle('flex');
});



let lastImageUrl = null;

fileInput?.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/upload', { method: 'POST', body: fd });
  const data = await res.json();
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

function addUserMessage(text, imageUrl) {
  if (!messages) return;
  
  const row = document.createElement('div');
  row.className = 'flex gap-3 justify-end';
  const bubble = document.createElement('div');
  bubble.className = 'max-w-[80%] rounded-2xl px-4 py-3 bg-indigo-600 text-white whitespace-pre-line';
  bubble.textContent = text;
  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-full bg-indigo-600/80 flex items-center justify-center';
  avatar.textContent = '👤';
  row.append(bubble, avatar);
  messages.appendChild(row);

  if (imageUrl) {
    const imgRow = document.createElement('div');
    imgRow.className = 'flex justify-end pr-10';
    imgRow.innerHTML = `<img src="${imageUrl}" class="rounded-lg max-w-xs border">`;
    messages.appendChild(imgRow);
  }
  scrollToBottom();
}

function addAssistantMessage(md) {
  if (!messages) return;
  
  const row = document.createElement('div');
  row.className = 'flex gap-3';
  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center';
  avatar.textContent = '֎';
  const body = renderMarkdown(md);
  row.append(avatar, body);
  messages.appendChild(row);
  scrollToBottom();
}

function addAssistantStreamContainer() {
  if (!messages) return null;
  
  const row = document.createElement('div');
  row.className = 'flex gap-3';
  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center';
  avatar.textContent = '֎';
  const body = document.createElement('div');
  body.className = 'prose dark:prose-invert max-w-none markdown relative';
  body.innerHTML = '<em>Thinking…</em>';
  row.append(avatar, body);
  messages.appendChild(row);
  scrollToBottom();
  return body;
}

async function send(useStream = false) {
  if (!promptEl) return;
  
  const text = promptEl.value.trim();
  if (!text && !lastImageUrl) return;
  
  addUserMessage(text || '(image only)', lastImageUrl);
  
  preview?.classList.add('hidden');
  if (preview) preview.innerHTML = '';
  
  promptEl.value = '';

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
                fullResponse += data.delta;
                container.innerHTML = renderMarkdown(fullResponse).innerHTML;
                scrollToBottom();
              }
              if (data.done) break;
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      container.innerHTML = renderMarkdown('Error: Could not stream response.').innerHTML;
    }
  } else {
    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, image_url: lastImageUrl })
      });
      const data = await res.json();
      addAssistantMessage(data.reply || 'No response received');
    } catch (error) {
      addAssistantMessage('Error: Could not send message. Please try again.');
    }
  }
  
  lastImageUrl = null;
  scrollToBottom();
  refreshSidebar();
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

function refreshSidebar() {
  if (!sidebarHistory) return;
  
  const items = Array.from(document.querySelectorAll('#messages .flex'))
    .slice(-10)
    .map((el) => {
      const text = el.innerText.slice(0, 50).replace(/\s+/g, ' ');
      return `<div class="px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800 text-xs">${text}</div>`;
    })
    .join('');
  sidebarHistory.innerHTML = items;
}

document.querySelectorAll('.markdown').forEach((node) => {
  node.innerHTML = marked.parse(node.textContent);
  node.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
});

refreshSidebar();

