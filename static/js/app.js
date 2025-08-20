
const messages = document.getElementById('messages');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('sendBtn');
const streamBtn = document.getElementById('streamBtn');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const clearBtn = document.getElementById('clearBtn');
const sidebarHistory = document.getElementById('sidebarHistory');
const themeToggle = document.getElementById('themeToggle');

(() => {
  const theme = localStorage.getItem('theme') || 'light';
  if (theme === 'dark') document.documentElement.classList.add('dark');
})();
themeToggle?.addEventListener('click', () => {
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
});

promptEl.addEventListener('input', () => {
  promptEl.style.height = 'auto';
  promptEl.style.height = Math.min(promptEl.scrollHeight, 200) + 'px';
});

let lastImageUrl = null;
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append('file', file);
  const res = await fetch('/upload', { method: 'POST', body: fd });
  const data = await res.json();
  if (data.url) {
    lastImageUrl = window.location.origin + data.url;
    preview.classList.remove('hidden');
    preview.innerHTML = `<div class="text-xs text-gray-500 mb-1">Attached image</div><img src="${data.url}" class="max-h-32 rounded-xl border">`;
  }
});

function scrollToBottom() {
  requestAnimationFrame(() => {
    const chat = document.getElementById('chat');
    chat.scrollTop = chat.scrollHeight;
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
  const row = document.createElement('div');
  row.className = 'flex gap-3 justify-end';
  const bubble = document.createElement('div');
  bubble.className = 'max-w-[80%] rounded-2xl px-4 py-3 bg-indigo-600 text-white whitespace-pre-line';
  bubble.textContent = text;
  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-full bg-indigo-600/80 flex items-center justify-center';
  avatar.textContent = 'U';
  row.appendChild(bubble);
  row.appendChild(avatar);
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
  const row = document.createElement('div');
  row.className = 'flex gap-3';
  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center';
  avatar.textContent = '🤖';
  const body = renderMarkdown(md);
  row.appendChild(avatar);
  row.appendChild(body);
  messages.appendChild(row);
  scrollToBottom();
}

function addAssistantStreamContainer() {
  const row = document.createElement('div');
  row.className = 'flex gap-3';
  const avatar = document.createElement('div');
  avatar.className = 'w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center';
  avatar.textContent = '🤖';
  const body = document.createElement('div');
  body.className = 'prose dark:prose-invert max-w-none markdown relative';
  body.innerHTML = '<em>Thinking…</em>';
  row.appendChild(avatar);
  row.appendChild(body);
  messages.appendChild(row);
  scrollToBottom();
  return body;
}

async function send(normal = true) {
  const text = promptEl.value.trim();
  if (!text && !lastImageUrl) return;
  addUserMessage(text || '(image only)', lastImageUrl);
  preview.classList.add('hidden');
  preview.innerHTML = '';
  promptEl.value = '';
  promptEl.style.height = 'auto';

  if (normal) {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, image_url: lastImageUrl })
    });
    const data = await res.json();
    addAssistantMessage(data.reply || '');
  } else {
    const container = addAssistantStreamContainer();
    const res = await fetch('/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, image_url: lastImageUrl })
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let md = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const obj = JSON.parse(line.slice(6));
            if (obj.delta) {
              md += obj.delta;
              container.innerHTML = renderMarkdown(md).innerHTML;
            }
          } catch {}
        }
      }
    }
  }
  lastImageUrl = null;
  scrollToBottom();
  refreshSidebar();
}

sendBtn.addEventListener('click', () => send(true));
streamBtn.addEventListener('click', () => send(false));
promptEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send(false);
  }
});

clearBtn?.addEventListener('click', async () => {
  await fetch('/clear', { method: 'POST' });
  location.reload();
});

function refreshSidebar() {
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
