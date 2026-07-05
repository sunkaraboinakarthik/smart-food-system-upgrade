// ===== CHATBOT.JS – SmartFood AI Assistant =====
// Powered by Claude (Anthropic API)

(function () {
  // ---- Inject CSS ----
  const style = document.createElement('style');
  style.textContent = `
    /* ===== CHATBOT WIDGET ===== */
    #sf-chat-fab {
      position: fixed; bottom: 28px; right: 28px; z-index: 9998;
      width: 60px; height: 60px; border-radius: 50%;
      background: linear-gradient(135deg, #FC8019, #e6700a);
      color: white; border: none; cursor: pointer;
      box-shadow: 0 6px 24px rgba(252,128,25,0.5);
      font-size: 1.5rem; display: flex; align-items: center; justify-content: center;
      transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
      animation: chatPulse 2.5s ease-in-out infinite;
    }
    #sf-chat-fab:hover { transform: scale(1.12); box-shadow: 0 8px 32px rgba(252,128,25,0.65); }
    @keyframes chatPulse {
      0%,100% { box-shadow: 0 6px 24px rgba(252,128,25,0.5); }
      50% { box-shadow: 0 6px 32px rgba(252,128,25,0.75), 0 0 0 8px rgba(252,128,25,0.12); }
    }
    #sf-chat-fab .fab-badge {
      position: absolute; top: -4px; right: -4px; width: 18px; height: 18px;
      background: #e23744; border-radius: 50%; border: 2px solid white;
      font-size: 0.6rem; font-weight: 800; display: flex; align-items: center; justify-content: center;
    }
    #sf-chat-window {
      position: fixed; bottom: 102px; right: 28px; z-index: 9997;
      width: 380px; max-height: 580px;
      background: white; border-radius: 24px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.2);
      display: flex; flex-direction: column;
      font-family: 'Nunito', sans-serif;
      transform: scale(0.85) translateY(30px); opacity: 0; pointer-events: none;
      transition: all 0.35s cubic-bezier(0.34,1.56,0.64,1);
      overflow: hidden;
    }
    #sf-chat-window.open {
      transform: scale(1) translateY(0); opacity: 1; pointer-events: all;
    }
    .chat-header {
      background: linear-gradient(135deg, #1a1a2e, #0f3460);
      padding: 18px 20px; display: flex; align-items: center; gap: 14px; flex-shrink: 0;
    }
    .chat-avatar {
      width: 44px; height: 44px; border-radius: 50%;
      background: linear-gradient(135deg, #FC8019, #e6700a);
      display: flex; align-items: center; justify-content: center;
      font-size: 1.3rem; flex-shrink: 0; position: relative;
    }
    .chat-avatar::after {
      content: ''; position: absolute; bottom: 2px; right: 2px;
      width: 10px; height: 10px; background: #60b246; border-radius: 50%; border: 2px solid #1a1a2e;
    }
    .chat-header-info { flex: 1; }
    .chat-header-name { color: white; font-weight: 800; font-size: 0.95rem; }
    .chat-header-status { color: rgba(255,255,255,0.55); font-size: 0.75rem; margin-top: 1px; }
    .chat-close {
      background: rgba(255,255,255,0.1); border: none; color: rgba(255,255,255,0.7);
      width: 30px; height: 30px; border-radius: 50%; cursor: pointer; font-size: 0.9rem;
      display: flex; align-items: center; justify-content: center; transition: all 0.2s;
    }
    .chat-close:hover { background: rgba(255,255,255,0.2); color: white; }
    .chat-messages {
      flex: 1; overflow-y: auto; padding: 16px; display: flex;
      flex-direction: column; gap: 12px; scroll-behavior: smooth;
    }
    .chat-messages::-webkit-scrollbar { width: 4px; }
    .chat-messages::-webkit-scrollbar-track { background: transparent; }
    .chat-messages::-webkit-scrollbar-thumb { background: #e9e9eb; border-radius: 10px; }
    .chat-msg { display: flex; gap: 8px; align-items: flex-end; max-width: 92%; }
    .chat-msg.user { align-self: flex-end; flex-direction: row-reverse; }
    .msg-avatar {
      width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
      display: flex; align-items: center; justify-content: center; font-size: 0.85rem;
    }
    .msg-avatar.bot { background: linear-gradient(135deg, #FC8019, #e6700a); }
    .msg-avatar.user { background: #282c3f; color: white; font-weight: 800; font-size: 0.7rem; }
    .msg-bubble {
      padding: 10px 14px; border-radius: 18px; font-size: 0.88rem;
      line-height: 1.55; max-width: 100%;
    }
    .chat-msg.bot .msg-bubble {
      background: #f4f4f5; color: #282c3f; border-bottom-left-radius: 4px;
    }
    .chat-msg.user .msg-bubble {
      background: linear-gradient(135deg, #FC8019, #e6700a); color: white; border-bottom-right-radius: 4px;
    }
    .msg-time { font-size: 0.65rem; color: #93959f; margin-top: 4px; text-align: right; }
    .chat-msg.bot .msg-time { text-align: left; }

    /* Typing indicator */
    .typing-bubble {
      background: #f4f4f5; border-radius: 18px; border-bottom-left-radius: 4px;
      padding: 12px 16px; display: flex; gap: 4px; align-items: center;
    }
    .typing-dot {
      width: 7px; height: 7px; background: #93959f; border-radius: 50%;
      animation: typingBounce 1.2s ease-in-out infinite;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typingBounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

    /* Quick replies */
    .quick-replies {
      display: flex; flex-wrap: wrap; gap: 6px; padding: 0 16px 12px;
    }
    .quick-reply {
      background: #fff3e8; color: #FC8019; border: 1px solid rgba(252,128,25,0.3);
      padding: 6px 12px; border-radius: 50px; font-size: 0.78rem; font-weight: 700;
      cursor: pointer; transition: all 0.2s; font-family: 'Nunito', sans-serif;
    }
    .quick-reply:hover { background: #FC8019; color: white; }

    /* Input area */
    .chat-input-area {
      padding: 12px 16px; border-top: 1px solid #e9e9eb; display: flex; gap: 8px;
      align-items: flex-end; flex-shrink: 0;
    }
    #chatInput {
      flex: 1; border: 2px solid #e9e9eb; border-radius: 20px;
      padding: 10px 16px; font-family: 'Nunito', sans-serif; font-size: 0.88rem;
      outline: none; resize: none; max-height: 80px; overflow-y: auto;
      transition: border-color 0.2s; line-height: 1.4;
    }
    #chatInput:focus { border-color: #FC8019; }
    #chatSendBtn {
      width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #FC8019, #e6700a);
      color: white; border: none; cursor: pointer; display: flex; align-items: center;
      justify-content: center; flex-shrink: 0; transition: all 0.2s; font-size: 0.9rem;
    }
    #chatSendBtn:hover { transform: scale(1.1); }
    #chatSendBtn:disabled { background: #e9e9eb; cursor: not-allowed; transform: none; }

    @media (max-width: 480px) {
      #sf-chat-window { width: calc(100vw - 24px); right: 12px; bottom: 92px; }
      #sf-chat-fab { right: 16px; bottom: 16px; }
    }
  `;
  document.head.appendChild(style);

  // ---- Build HTML ----
  const widget = document.createElement('div');
  widget.innerHTML = `
    <button id="sf-chat-fab" title="Ask SmartFood AI">
      🤖
      <span class="fab-badge">AI</span>
    </button>
    <div id="sf-chat-window">
      <div class="chat-header">
        <div class="chat-avatar">🤖</div>
        <div class="chat-header-info">
          <div class="chat-header-name">SmartFood AI</div>
          <div class="chat-header-status">Your personal food assistant</div>
        </div>
        <button class="chat-close" id="chatClose"><i class="fas fa-times"></i></button>
      </div>
      <div class="chat-messages" id="chatMessages"></div>
      <div class="quick-replies" id="quickReplies"></div>
      <div class="chat-input-area">
        <textarea id="chatInput" placeholder="Ask me anything about food, offers…" rows="1"></textarea>
        <button id="chatSendBtn"><i class="fas fa-paper-plane"></i></button>
      </div>
    </div>
  `;
  document.body.appendChild(widget);

  // ---- State ----
  let isOpen = false;
  let isTyping = false;
  const chatHistory = []; // { role, content }

  const SYSTEM_PROMPT = `You are SmartFood AI, a friendly and enthusiastic food ordering assistant for SmartFood, a Swiggy-style food delivery app. You help users with:
- Finding restaurants and food recommendations
- Explaining menu items, ingredients, and prices
- Helping apply promo codes (available: SAVE50 for flat ₹50 off on orders above ₹300, WELCOME20 for 20% off on ₹200+, FIRSTORDER for ₹100 off on ₹500+, SMARTFOOD for 15% off on ₹150+)
- Answering questions about delivery, tracking, payment
- Suggesting popular dishes and restaurants
- Providing helpful ordering tips

Available restaurants: Pizza Hub (Italian), Burger House (American), Biryani Palace (Indian), Food Express (Fast Food), Dragon Noodles (Chinese), South Spice (South Indian).

Keep responses concise, warm, and helpful. Use food emojis occasionally. Never mention being Claude or Anthropic — you are SmartFood AI. If you don't know something specific, guide them to browse the app. Always end with a helpful follow-up question or suggestion.`;

  const QUICK_REPLIES_LIST = [
    "🍕 Best pizzas?", "💰 Any offers today?", "🚀 How fast is delivery?",
    "📦 Track my order", "🏷️ Promo codes", "🍛 Recommend biryani"
  ];

  // ---- Init ----
  function init() {
    const fab = document.getElementById('sf-chat-fab');
    const closeBtn = document.getElementById('chatClose');
    const sendBtn = document.getElementById('chatSendBtn');
    const input = document.getElementById('chatInput');

    fab.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', () => setOpen(false));
    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    });
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 80) + 'px';
    });

    // Welcome message
    setTimeout(() => {
      addBotMessage("👋 Hey there! I'm **SmartFood AI**, your personal food assistant!\n\nI can help you find great restaurants, discover deals, apply promo codes, or answer any food questions. What are you craving today? 🍔🍕🍛");
      showQuickReplies();
    }, 500);
  }

  function toggleChat() { setOpen(!isOpen); }

  function setOpen(val) {
    isOpen = val;
    const win = document.getElementById('sf-chat-window');
    win.classList.toggle('open', isOpen);
    if (isOpen) scrollToBottom();
  }

  function showQuickReplies() {
    const qr = document.getElementById('quickReplies');
    qr.innerHTML = '';
    QUICK_REPLIES_LIST.forEach(text => {
      const btn = document.createElement('button');
      btn.className = 'quick-reply';
      btn.textContent = text;
      btn.onclick = () => { qr.innerHTML = ''; sendMessage(text); };
      qr.appendChild(btn);
    });
  }

  async function handleSend() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text || isTyping) return;
    input.value = '';
    input.style.height = 'auto';
    document.getElementById('quickReplies').innerHTML = '';
    sendMessage(text);
  }

  async function sendMessage(text) {
    addUserMessage(text);
    chatHistory.push({ role: 'user', content: text });
    isTyping = true;
    document.getElementById('chatSendBtn').disabled = true;

    const typingId = showTyping();

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 400,
          system: SYSTEM_PROMPT,
          messages: chatHistory.slice(-10) // last 10 turns for context
        })
      });

      removeTyping(typingId);

      if (!response.ok) throw new Error('API error ' + response.status);
      const data = await response.json();
      const reply = data.content?.[0]?.text || "Sorry, I couldn't get a response. Please try again!";

      chatHistory.push({ role: 'assistant', content: reply });
      addBotMessage(reply);
      showQuickReplies();
    } catch (err) {
      removeTyping(typingId);
      addBotMessage("Oops! I'm having a moment. 😅 Try asking again, or browse the app for restaurants and deals!");
      console.error('Chatbot error:', err);
    }

    isTyping = false;
    document.getElementById('chatSendBtn').disabled = false;
    scrollToBottom();
  }

  function addBotMessage(text) {
    const msgs = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    const formatted = formatMarkdown(text);
    div.innerHTML = `
      <div class="msg-avatar bot">🤖</div>
      <div>
        <div class="msg-bubble">${formatted}</div>
        <div class="msg-time">${getTime()}</div>
      </div>`;
    msgs.appendChild(div);
    scrollToBottom();
  }

  function addUserMessage(text) {
    const msgs = document.getElementById('chatMessages');
    const user = AUTH?.getLoggedInUser?.();
    const initials = user ? user.name[0].toUpperCase() : '👤';
    const div = document.createElement('div');
    div.className = 'chat-msg user';
    div.innerHTML = `
      <div class="msg-avatar user">${initials}</div>
      <div>
        <div class="msg-bubble">${escapeHTML(text)}</div>
        <div class="msg-time">${getTime()}</div>
      </div>`;
    msgs.appendChild(div);
    scrollToBottom();
  }

  function showTyping() {
    const msgs = document.getElementById('chatMessages');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'chat-msg bot';
    div.id = id;
    div.innerHTML = `
      <div class="msg-avatar bot">🤖</div>
      <div class="typing-bubble">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>`;
    msgs.appendChild(div);
    scrollToBottom();
    return id;
  }

  function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function scrollToBottom() {
    const msgs = document.getElementById('chatMessages');
    if (msgs) msgs.scrollTop = msgs.scrollHeight;
  }

  function getTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function escapeHTML(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // Basic markdown: **bold**, *italic*, newlines, bullet lists
  function formatMarkdown(text) {
    return escapeHTML(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>')
      .replace(/^- (.+)/gm, '• $1');
  }

  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
