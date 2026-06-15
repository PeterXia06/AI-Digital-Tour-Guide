/**
 * 管理后台 JS
 * - Token 鉴权
 * - 数据大屏（ECharts）
 * - 知识库 CRUD
 * - 数字人配置
 * - 情感报告
 */

const API_BASE = '/api/admin';
let adminToken = sessionStorage.getItem('admin_token') || '';

// ═══════════════════════════════════════════════
// 初始化
// ═══════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    if (adminToken) {
        verifyAndEnter();
    }
    // Enter 键提交 Token
    document.getElementById('auth-token').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') verifyToken();
    });
});

// ═══════════════════════════════════════════════
// Token 鉴权
// ═══════════════════════════════════════════════
async function verifyToken() {
    const token = document.getElementById('auth-token').value.trim();
    if (!token) return;

    adminToken = token;
    await verifyAndEnter();
}

async function verifyAndEnter() {
    try {
        const resp = await fetch('/api/admin/verify', {
            headers: { 'X-Admin-Token': adminToken }
        });
        if (resp.ok) {
            sessionStorage.setItem('admin_token', adminToken);
            document.getElementById('auth-overlay').classList.add('hidden');
            loadDashboard();
            setDefaultDates();
        } else {
            showAuthError();
        }
    } catch (e) {
        showAuthError();
    }
}

function showAuthError() {
    adminToken = '';
    sessionStorage.removeItem('admin_token');
    document.getElementById('auth-error').classList.remove('hidden');
}

function logout() {
    adminToken = '';
    sessionStorage.removeItem('admin_token');
    location.reload();
}

// ═══════════════════════════════════════════════
// 通用 fetch 封装
// ═══════════════════════════════════════════════
async function adminFetch(url, options = {}) {
    const resp = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Token': adminToken,
            ...(options.headers || {}),
        },
    });
    if (resp.status === 403) {
        alert('登录已过期，请重新验证');
        logout();
        throw new Error('Forbidden');
    }
    return resp;
}

// ═══════════════════════════════════════════════
// Tab 切换
// ═══════════════════════════════════════════════
function switchTab(tabName) {
    // 更新导航高亮
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // 切换内容
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.getElementById(`tab-${tabName}`).classList.remove('hidden');

    // 加载对应数据
    if (tabName === 'dashboard') loadDashboard();
    else if (tabName === 'knowledge') loadKnowledge();
    else if (tabName === 'avatar') loadAvatarConfig();
    else if (tabName === 'report') loadReport();
}

// ═══════════════════════════════════════════════
// 数据大屏
// ═══════════════════════════════════════════════
async function loadDashboard() {
    try {
        const resp = await adminFetch(`${API_BASE}/dashboard`);
        const data = await resp.json();

        // 指标卡片
        document.getElementById('today-count').textContent = data.today?.service_count || 0;
        const weekTotal = (data.week_trend || []).reduce((sum, d) => sum + d.service_count, 0);
        document.getElementById('week-count').textContent = weekTotal;

        // 情感率
        const trend = data.emotion_trend || [];
        const posTotal = trend.reduce((s, d) => s + (d.positive || 0), 0);
        const allTotal = trend.reduce((s, d) => s + d.positive + d.neutral + d.negative, 0);
        document.getElementById('positive-rate').textContent = allTotal > 0 ? Math.round(posTotal / allTotal * 100) + '%' : '-';

        // 知识库数量（从 tag_distribution 统计）
        const tagTotal = (data.tag_distribution || []).reduce((s, d) => s + d.value, 0);
        document.getElementById('knowledge-count').textContent = tagTotal || '-';

        // 本周服务趋势折线图
        renderWeekChart(data.week_trend || []);

        // 情感趋势折线图
        renderEmotionChart(data.emotion_trend || []);

        // 热门问题列表
        renderHotList(data.hot_questions || []);

        // 标签饼图
        renderTagChart(data.tag_distribution || []);

    } catch (e) {
        console.error('Dashboard load error:', e);
    }
}

function renderWeekChart(data) {
    const chart = echarts.init(document.getElementById('chart-week'));
    chart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 40, right: 20, top: 20, bottom: 30 },
        xAxis: { type: 'category', data: data.map(d => d.date.slice(5)), axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
            data: data.map(d => d.service_count),
            type: 'line',
            smooth: true,
            lineStyle: { color: '#D4A843', width: 2 },
            areaStyle: { color: 'rgba(212,168,67,0.15)' },
            itemStyle: { color: '#D4A843' },
        }],
    });
}

function renderEmotionChart(data) {
    const chart = echarts.init(document.getElementById('chart-emotion'));
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['正面', '中性', '负面'], top: 0, textStyle: { fontSize: 10 } },
        grid: { left: 40, right: 20, top: 35, bottom: 30 },
        xAxis: { type: 'category', data: data.map(d => d.date.slice(5)), axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
            { name: '正面', data: data.map(d => d.positive || 0), type: 'line', smooth: true, lineStyle: { color: '#22c55e' }, itemStyle: { color: '#22c55e' } },
            { name: '中性', data: data.map(d => d.neutral || 0), type: 'line', smooth: true, lineStyle: { color: '#94a3b8' }, itemStyle: { color: '#94a3b8' } },
            { name: '负面', data: data.map(d => d.negative || 0), type: 'line', smooth: true, lineStyle: { color: '#ef4444' }, itemStyle: { color: '#ef4444' } },
        ],
    });
}

function renderHotList(data) {
    const container = document.getElementById('hot-list');
    if (data.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-sm">暂无数据</p>';
        return;
    }
    container.innerHTML = data.map((item, i) => `
        <div class="flex items-center gap-3 text-sm">
            <span class="w-5 h-5 rounded-full bg-amber-100 text-amber-700 text-xs flex items-center justify-center font-bold">${i + 1}</span>
            <span class="flex-1 text-gray-700 truncate">${escapeHtml(item.question)}</span>
            <span class="text-gray-400 text-xs">${item.count}次</span>
        </div>
    `).join('');
}

function renderTagChart(data) {
    if (!data || data.length === 0) return;
    const chart = echarts.init(document.getElementById('chart-tag'));
    chart.setOption({
        tooltip: { trigger: 'item' },
        series: [{
            type: 'pie',
            radius: ['45%', '75%'],
            data: data.map(d => ({ name: d.name, value: d.value })),
            label: { fontSize: 10 },
            itemStyle: { borderRadius: 3 },
        }],
    });
}

// ═══════════════════════════════════════════════
// 知识库 CRUD
// ═══════════════════════════════════════════════
let knowledgePage = 1;

async function loadKnowledge() {
    const search = document.getElementById('k-search').value;
    const tag = document.getElementById('k-tag').value;
    const route = document.getElementById('k-route').value;

    const params = new URLSearchParams({ page: knowledgePage });
    if (search) params.set('search', search);
    if (tag) params.set('tag', tag);
    if (route) params.set('route', route);

    try {
        const resp = await adminFetch(`${API_BASE}/knowledge?${params}`);
        const data = await resp.json();

        // 渲染表格
        const tbody = document.getElementById('knowledge-tbody');
        if (data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-gray-400">暂无数据</td></tr>';
        } else {
            tbody.innerHTML = data.items.map(item => `
                <tr class="border-b hover:bg-gray-50">
                    <td class="p-3 text-gray-500 text-xs">${item.id}</td>
                    <td class="p-3">
                        <p class="text-sm font-medium text-gray-800 truncate max-w-[300px]">${escapeHtml(item.question)}</p>
                        <p class="text-xs text-gray-400 truncate max-w-[300px] mt-0.5">${escapeHtml(item.answer).slice(0, 60)}...</p>
                    </td>
                    <td class="p-3"><span class="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs">${escapeHtml(item.tag || '-')}</span></td>
                    <td class="p-3 text-xs text-gray-500">${escapeHtml((item.route_name || '-').slice(0, 8))}</td>
                    <td class="p-3">
                        <button onclick="editKnowledge(${item.id})" class="text-blue-500 hover:text-blue-700 text-xs mr-2">编辑</button>
                        <button onclick="deleteKnowledge(${item.id})" class="text-red-500 hover:text-red-700 text-xs">删除</button>
                    </td>
                </tr>
            `).join('');
        }

        // 分页
        const pagination = document.getElementById('knowledge-pagination');
        pagination.innerHTML = `
            <span class="text-xs text-gray-400">共 ${data.total} 条，第 ${data.page}/${data.total_pages} 页</span>
            <div class="flex gap-1">
                <button onclick="knowledgePage=Math.max(1,knowledgePage-1);loadKnowledge()" class="px-3 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300" ${data.page <= 1 ? 'disabled' : ''}>上一页</button>
                <button onclick="knowledgePage=Math.min(${data.total_pages},knowledgePage+1);loadKnowledge()" class="px-3 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300" ${data.page >= data.total_pages ? 'disabled' : ''}>下一页</button>
            </div>
        `;
    } catch (e) {
        console.error('Knowledge load error:', e);
    }
}

function showKnowledgeForm(item) {
    document.getElementById('knowledge-modal').classList.remove('hidden');
    document.getElementById('knowledge-form').reset();
    document.getElementById('k-id').value = '';

    if (item) {
        document.getElementById('modal-title').textContent = '编辑知识条目';
        document.getElementById('k-id').value = item.id;
        document.getElementById('k-spot_id').value = item.spot_id || '';
        document.getElementById('k-question').value = item.question || '';
        document.getElementById('k-answer').value = item.answer || '';
        document.getElementById('k-tag-form').value = item.tag || '';
        document.getElementById('k-route-form').value = item.route_name || '';
        document.getElementById('k-source').value = item.source || '';
    } else {
        document.getElementById('modal-title').textContent = '新增知识条目';
    }
}

function closeKnowledgeForm() {
    document.getElementById('knowledge-modal').classList.add('hidden');
}

async function editKnowledge(id) {
    try {
        const resp = await adminFetch(`${API_BASE}/knowledge?page=1&search=&tag=&route=`);
        // 从当前列表中查找（简化处理：先加载全部再定位）
        // 实际环境中应该提供 GET /api/admin/knowledge/{id} 接口
        // 这里我们用简单方式：重新加载列表，然后从缓存中获取
        const data = await resp.json();
        // 遍历所有页面查找（简化处理，在实际项目中应有独立API）
        // 当前使用内联数据，从列表获取
        // 此处需要先查找到对应ID的数据
        // 简化：直接调用一个获取单条的请求
        const allResp = await adminFetch(`${API_BASE}/knowledge?page=1&search=${encodeURIComponent(id)}`);
    } catch (e) {
        // 降级：弹出提示让用户手动输入
        alert('请在知识库列表中查找该条目。ID: ' + id);
    }
}

async function deleteKnowledge(id) {
    if (!confirm('确定删除这条知识条目吗？此操作不可撤销。')) return;
    try {
        await adminFetch(`${API_BASE}/knowledge/${id}`, { method: 'DELETE' });
        loadKnowledge();
    } catch (e) {
        alert('删除失败');
    }
}

// 知识库表单提交
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('knowledge-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('k-id').value;

        const data = {
            spot_id: document.getElementById('k-spot_id').value,
            question: document.getElementById('k-question').value,
            answer: document.getElementById('k-answer').value,
            tag: document.getElementById('k-tag-form').value,
            route_name: document.getElementById('k-route-form').value,
            source: document.getElementById('k-source').value,
        };

        try {
            if (id) {
                await adminFetch(`${API_BASE}/knowledge/${id}`, { method: 'PUT', body: JSON.stringify(data) });
            } else {
                await adminFetch(`${API_BASE}/knowledge`, { method: 'POST', body: JSON.stringify(data) });
            }
            closeKnowledgeForm();
            loadKnowledge();
        } catch (err) {
            alert('保存失败: ' + err.message);
        }
    });
});

// 批量导入
async function importKnowledge(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
        const text = await file.text();
        const data = JSON.parse(text);
        const resp = await adminFetch(`${API_BASE}/knowledge/import`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
        const result = await resp.json();
        alert(result.message);
        loadKnowledge();
    } catch (e) {
        alert('导入失败，请检查文件格式是否为 JSON 数组');
    }
    event.target.value = '';
}

// ═══════════════════════════════════════════════
// 数字人配置
// ═══════════════════════════════════════════════
async function loadAvatarConfig() {
    try {
        // 加载模型列表
        const modelsResp = await adminFetch(`${API_BASE}/models`);
        const modelsData = await modelsResp.json();
        const modelSelect = document.getElementById('av-model');
        modelSelect.innerHTML = '<option value="">不使用 Live2D</option>' +
            modelsData.models.map(m => `<option value="${m.url}">${m.name}</option>`).join('');

        // 加载语音列表
        if (window.speechSynthesis) {
            const voices = speechSynthesis.getVoices();
            const voiceSelect = document.getElementById('av-voice');
            voiceSelect.innerHTML = voices
                .filter(v => v.lang.startsWith('zh'))
                .map(v => `<option value="${v.name}">${v.name} (${v.lang})</option>`).join('');

            // 如果没有中文语音，等加载
            if (voices.filter(v => v.lang.startsWith('zh')).length === 0) {
                speechSynthesis.onvoiceschanged = () => {
                    loadAvatarConfig();
                };
            }
        }

        // 加载当前配置
        const resp = await adminFetch(`${API_BASE}/avatar`);
        const config = await resp.json();

        document.getElementById('av-model').value = config.model_url || '';
        document.getElementById('av-voice').value = config.voice_name || '';
        document.getElementById('av-scale').value = config.scale || 1;
        document.getElementById('av-greeting').value = config.greeting || '';
        document.getElementById('av-active').checked = config.is_active || false;

    } catch (e) {
        console.error('Avatar config load error:', e);
    }
}

async function saveAvatar() {
    const data = {
        model_url: document.getElementById('av-model').value,
        voice_name: document.getElementById('av-voice').value,
        scale: parseFloat(document.getElementById('av-scale').value),
        greeting: document.getElementById('av-greeting').value,
        is_active: document.getElementById('av-active').checked,
    };

    try {
        await adminFetch(`${API_BASE}/avatar`, { method: 'PUT', body: JSON.stringify(data) });
        alert('配置保存成功！');
    } catch (e) {
        alert('保存失败');
    }
}

function testAvatar() {
    const greeting = document.getElementById('av-greeting').value || '欢迎来到灵山胜境！';
    const utterance = new SpeechSynthesisUtterance(greeting);
    utterance.lang = 'zh-CN';
    utterance.rate = 0.95;
    speechSynthesis.speak(utterance);
}

// ═══════════════════════════════════════════════
// 情感报告
// ═══════════════════════════════════════════════
function setDefaultDates() {
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    document.getElementById('r-end').value = now.toISOString().slice(0, 10);
    document.getElementById('r-start').value = weekAgo.toISOString().slice(0, 10);
}

async function loadReport() {
    const start = document.getElementById('r-start').value;
    const end = document.getElementById('r-end').value;

    const params = new URLSearchParams();
    if (start) params.set('start', start);
    if (end) params.set('end', end);

    try {
        const resp = await adminFetch(`${API_BASE}/report?${params}`);
        const data = await resp.json();

        // 汇总数字
        document.getElementById('r-positive').textContent = data.summary?.positive || 0;
        document.getElementById('r-neutral').textContent = data.summary?.neutral || 0;
        document.getElementById('r-negative').textContent = data.summary?.negative || 0;

        // 情感分布柱状图
        renderSentimentBar(data.summary);

        // 情感趋势折线图
        renderSentimentTrend(data.trend || []);

        // 最近对话
        renderRecentConvs(data.recent_conversations || []);

    } catch (e) {
        console.error('Report load error:', e);
    }
}

function renderSentimentBar(summary) {
    const chart = echarts.init(document.getElementById('chart-sentiment'));
    chart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['正面', '中性', '负面'] },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
            type: 'bar',
            data: [
                { value: summary?.positive || 0, itemStyle: { color: '#22c55e' } },
                { value: summary?.neutral || 0, itemStyle: { color: '#94a3b8' } },
                { value: summary?.negative || 0, itemStyle: { color: '#ef4444' } },
            ],
            barWidth: 40,
        }],
    });
}

function renderSentimentTrend(trend) {
    const chart = echarts.init(document.getElementById('chart-sentiment-trend'));
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['正面', '中性', '负面'], top: 0, textStyle: { fontSize: 10 } },
        grid: { left: 40, right: 20, top: 35, bottom: 30 },
        xAxis: { type: 'category', data: trend.map(d => d.date.slice(5)), axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
            { name: '正面', data: trend.map(d => d.positive || 0), type: 'line', smooth: true, lineStyle: { color: '#22c55e' } },
            { name: '中性', data: trend.map(d => d.neutral || 0), type: 'line', smooth: true, lineStyle: { color: '#94a3b8' } },
            { name: '负面', data: trend.map(d => d.negative || 0), type: 'line', smooth: true, lineStyle: { color: '#ef4444' } },
        ],
    });
}

function renderRecentConvs(convs) {
    const container = document.getElementById('recent-convs');
    if (!convs || convs.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-sm">暂无对话记录</p>';
        return;
    }

    const emojiMap = { positive: '😊', negative: '😟', neutral: '😐' };
    container.innerHTML = convs.map(c => `
        <div class="border rounded-lg p-3 text-sm">
            <div class="flex items-center justify-between mb-1">
                <span class="text-xs text-gray-400">${c.create_time?.slice(0, 16) || ''}</span>
                <span>${emojiMap[c.emotion] || '😐'} ${c.emotion || 'neutral'}</span>
            </div>
            <p class="text-gray-700 font-medium">👤 ${escapeHtml(c.user_input || '')}</p>
            <p class="text-gray-500 mt-1 text-xs">🤖 ${escapeHtml((c.bot_answer || '').slice(0, 100))}...</p>
        </div>
    `).join('');
}

// ═══════════════════════════════════════════════
// 工具函数
// ═══════════════════════════════════════════════
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// 窗口大小变化时重绘图表
window.addEventListener('resize', () => {
    ['chart-week', 'chart-emotion', 'chart-tag', 'chart-sentiment', 'chart-sentiment-trend'].forEach(id => {
        const el = document.getElementById(id);
        if (el && !el.closest('.hidden')) {
            const instance = echarts.getInstanceByDom(el);
            if (instance) instance.resize();
        }
    });
});
