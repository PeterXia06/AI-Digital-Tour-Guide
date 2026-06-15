/**
 * 游客端 JS
 * - 聊天交互
 * - 语音输入（Web Speech API）
 * - 语音输出（SpeechSynthesis API）
 * - Live2D 数字人状态切换
 */

// ═══════════════════════════════════════════════
// 常量 & 状态
// ═══════════════════════════════════════════════
const API_BASE = '/api';

// 获取或创建 session_id
let sessionId = localStorage.getItem('lingshan_session_id');
if (!sessionId) {
    sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('lingshan_session_id', sessionId);
}

let isProcessing = false;
let isListening = false;
let recognition = null;
let synth = window.speechSynthesis;
let selectedVoice = null;

// ═══════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initSpeechRecognition();
    initSpeechSynthesis();
    loadGreeting();
    updateStatus('idle');
});

function loadGreeting() {
    fetch(`${API_BASE}/admin/avatar`)
        .then(r => r.json())
        .then(config => {
            const greeting = config.greeting || '阿弥陀佛，欢迎来到灵山胜境！我是您的AI导游小灵，有什么可以帮您的吗？';
            document.getElementById('welcome-msg').querySelector('p').textContent = greeting;
            speak(greeting);
        })
        .catch(() => {
            document.getElementById('welcome-msg').querySelector('p').textContent =
                '阿弥陀佛，欢迎来到灵山胜境！我是您的AI导游小灵 🙏 您可以问我关于灵山大佛、梵宫、九龙灌浴的任何问题~';
        });
}

// ═══════════════════════════════════════════════
// 语音识别（Web Speech API）
// ═══════════════════════════════════════════════
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        document.getElementById('voice-btn').style.display = 'none';
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        document.getElementById('message-input').value = transcript;
        if (event.results[0].isFinal) {
            stopListening();
            // 自动发送
            setTimeout(() => {
                if (document.getElementById('message-input').value.trim()) {
                    sendMessage();
                }
            }, 500);
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopListening();
        document.getElementById('voice-status').textContent = '语音识别失败，请使用文本输入';
        document.getElementById('voice-status').classList.remove('hidden');
        setTimeout(() => {
            document.getElementById('voice-status').classList.add('hidden');
        }, 3000);
    };

    recognition.onend = () => {
        if (isListening) {
            // 如果还在 listening 状态，说明是意外结束，重新开始
            try { recognition.start(); } catch(e) {}
        } else {
            updateVoiceButton(false);
        }
    };
}

function toggleVoice() {
    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
}

function startListening() {
    if (!recognition) return;
    isListening = true;
    updateVoiceButton(true);
    document.getElementById('message-input').value = '';
    document.getElementById('message-input').placeholder = '正在聆听...';
    document.getElementById('voice-status').textContent = '🎤 请说话...';
    document.getElementById('voice-status').classList.remove('hidden');
    updateStatus('listening');
    try {
        recognition.start();
    } catch(e) {
        console.error('Recognition start error:', e);
    }
}

function stopListening() {
    isListening = false;
    updateVoiceButton(false);
    document.getElementById('message-input').placeholder = '问我关于灵山的问题...';
    document.getElementById('voice-status').classList.add('hidden');
    try {
        recognition.stop();
    } catch(e) {}
}

function updateVoiceButton(active) {
    const btn = document.getElementById('voice-btn');
    const icon = document.getElementById('mic-icon');
    if (active) {
        btn.classList.add('bg-red-500', 'animate-pulse');
        btn.classList.remove('bg-white/10');
        icon.innerHTML = '<circle cx="12" cy="12" r="6" fill="currentColor"/>';
    } else {
        btn.classList.remove('bg-red-500', 'animate-pulse');
        btn.classList.add('bg-white/10');
        icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H9m3 0h3m-3-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />';
    }
}

// ═══════════════════════════════════════════════
// 语音合成（SpeechSynthesis API）
// ═══════════════════════════════════════════════
function initSpeechSynthesis() {
    // 等 voices 加载完成
    if (synth.getVoices().length > 0) {
        selectVoice();
    } else {
        synth.onvoiceschanged = selectVoice;
    }
}

function selectVoice() {
    const voices = synth.getVoices();
    // 优先选择中文女声
    selectedVoice = voices.find(v => v.lang.startsWith('zh-CN') && v.name.includes('Female')) ||
                    voices.find(v => v.lang.startsWith('zh-CN')) ||
                    voices.find(v => v.lang.startsWith('zh')) ||
                    voices[0];
}

function speak(text) {
    if (!synth || !text) return;

    // 停止当前播放
    synth.cancel();

    // 清理文本中的 markdown 符号
    const cleanText = text.replace(/[*#`\-_~\[\]()]/g, '').replace(/\n+/g, '。');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.voice = selectedVoice;
    utterance.rate = 0.95;
    utterance.pitch = 1.05;
    utterance.volume = 1;

    // 说话状态更新 Live2D
    utterance.onstart = () => updateStatus('speaking');
    utterance.onend = () => updateStatus('idle');
    utterance.onerror = () => updateStatus('idle');

    synth.speak(utterance);
}

// ═══════════════════════════════════════════════
// 聊天交互
// ═══════════════════════════════════════════════
async function sendMessage() {
    if (isProcessing) return;

    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message) return;

    // 添加用户消息
    addMessage('user', message);

    // 清空输入
    input.value = '';
    isProcessing = true;
    updateStatus('thinking');

    // 显示思考中
    const thinkingId = addThinking();

    try {
        const resp = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: message }),
        });
        const data = await resp.json();

        // 移除思考动画
        removeThinking(thinkingId);

        // 添加机器人消息
        addMessage('bot', data.answer, data.source, data.spot_id);

        // 语音播报
        if (data.answer) {
            speak(data.answer);
        }

        // 正面消息触发笑脸
        if (data.emotion === 'positive') {
            updateStatus('happy');
            setTimeout(() => updateStatus('idle'), 3000);
        }

    } catch (err) {
        removeThinking(thinkingId);
        addMessage('bot', '阿弥陀佛~小灵暂时无法回答，请稍后再试 🙏');
        updateStatus('idle');
    } finally {
        isProcessing = false;
    }
}

function quickAsk(tag) {
    if (isProcessing) return;

    const tagMessages = {
        '喜欢历史': '我对灵山的历史文化很感兴趣，给我推荐一条游览路线吧',
        '喜欢自然': '我喜欢自然风光，灵山有哪些好看的自然景观',
        '亲子出游': '我是带小孩来灵山玩的，有什么适合亲子的路线推荐吗',
        '推荐美食': '灵山有什么好吃的素食推荐吗',
    };

    const message = tagMessages[tag] || (`推荐${tag}相关的景点`);
    document.getElementById('message-input').value = message;
    sendMessage();
}

// ═══════════════════════════════════════════════
// UI 辅助
// ═══════════════════════════════════════════════
function addMessage(role, text, source, spotId) {
    const container = document.getElementById('chat-messages');

    const div = document.createElement('div');
    div.className = `flex gap-2 ${role === 'user' ? 'justify-end' : ''}`;

    if (role === 'bot') {
        div.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center text-sm shrink-0">🧘</div>
            <div class="msg-bot px-3 py-2 max-w-[85%] text-sm text-gray-800 shadow-sm">
                <p class="leading-relaxed whitespace-pre-wrap">${escapeHtml(text)}</p>
                ${source ? `<span class="text-xs text-gray-400 mt-1 block">来源：${source === 'knowledge_base' ? '📚 知识库' : '🤖 AI助手'}</span>` : ''}
            </div>
        `;
    } else {
        div.innerHTML = `
            <div class="msg-user px-3 py-2 max-w-[80%] text-sm shadow-sm">
                <p class="leading-relaxed">${escapeHtml(text)}</p>
            </div>
            <div class="w-8 h-8 rounded-full bg-amber-500 flex items-center justify-center text-white text-sm shrink-0">👤</div>
        `;
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addThinking() {
    const container = document.getElementById('chat-messages');
    const id = 'thinking-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'flex gap-2';
    div.innerHTML = `
        <div class="w-8 h-8 rounded-full bg-amber-500/20 flex items-center justify-center text-sm shrink-0">🧘</div>
        <div class="msg-bot px-4 py-3 shadow-sm flex gap-1.5 items-center">
            <div class="thinking-dot w-2 h-2 rounded-full bg-amber-400"></div>
            <div class="thinking-dot w-2 h-2 rounded-full bg-amber-400"></div>
            <div class="thinking-dot w-2 h-2 rounded-full bg-amber-400"></div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeThinking(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function updateStatus(status) {
    const statusEl = document.getElementById('status-text');
    const placeholder = document.getElementById('avatar-placeholder');

    const statusMap = {
        'idle': { text: '等待中...', emoji: '🧘' },
        'listening': { text: '聆听中...', emoji: '👂' },
        'thinking': { text: '思考中...', emoji: '💭' },
        'speaking': { text: '讲解中...', emoji: '🗣️' },
        'happy': { text: '很高兴帮到您~', emoji: '😊' },
    };

    const info = statusMap[status] || statusMap['idle'];
    statusEl.textContent = info.text;

    // 非 Live2D 模式下更新占位符表情
    if (placeholder && placeholder.style.display !== 'none') {
        placeholder.textContent = info.emoji;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
