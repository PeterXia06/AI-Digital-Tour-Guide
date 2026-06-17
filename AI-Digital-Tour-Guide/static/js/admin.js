/**
 * 管理后台 JS
 * - 数据大屏（ECharts）
 * - 知识库 CRUD
 * - 数字人配置
 * - 情感报告
 *
 * 鉴权和视图切换逻辑在 index.html 中处理
 */

const API_BASE = '/api/admin';

function getAdminToken() {
    return sessionStorage.getItem('admin_token') || '';
}

async function adminFetch(url, options = {}) {
    const resp = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'X-Admin-Token': getAdminToken(),
            ...(options.headers || {}),
        },
    });
    if (resp.status === 403) {
        if (typeof switchToTourist === 'function') switchToTourist();
        throw new Error('Forbidden');
    }
    return resp;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ═══════════════════════════════════════════════
// 数据大屏
// ═══════════════════════════════════════════════
async function loadDashboard() {
    try {
        const resp = await adminFetch(`${API_BASE}/dashboard`);
        const data = await resp.json();
        document.getElementById('today-count').textContent = data.today?.service_count || 0;
        const weekTotal = (data.week_trend || []).reduce(function(s, d) { return s + d.service_count; }, 0);
        document.getElementById('week-count').textContent = weekTotal;
        const trend = data.emotion_trend || [];
        const posTotal = trend.reduce(function(s, d) { return s + (d.positive || 0); }, 0);
        const allTotal = trend.reduce(function(s, d) { return s + d.positive + d.neutral + d.negative; }, 0);
        document.getElementById('positive-rate').textContent = allTotal > 0 ? Math.round(posTotal / allTotal * 100) + '%' : '-';
        const tagTotal = (data.tag_distribution || []).reduce(function(s, d) { return s + d.value; }, 0);
        document.getElementById('knowledge-count').textContent = tagTotal || '-';
        renderWeekChart(data.week_trend || []);
        renderEmotionChart(data.emotion_trend || []);
        renderHotList(data.hot_questions || []);
        renderTagChart(data.tag_distribution || []);
    } catch (e) { console.error('Dashboard error:', e); }
}

function renderWeekChart(data) {
    var el = document.getElementById('chart-week');
    if (!el || !data.length) return;
    var chart = echarts.init(el);
    chart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 40, right: 20, top: 20, bottom: 30 },
        xAxis: { type: 'category', data: data.map(function(d) { return (d.date || '').slice(5); }), axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{ data: data.map(function(d) { return d.service_count; }), type: 'line', smooth: true, lineStyle: { color: '#BF8D3A', width: 2 }, areaStyle: { color: 'rgba(191,141,58,0.1)' }, itemStyle: { color: '#BF8D3A' } }],
    });
}

function renderEmotionChart(data) {
    var el = document.getElementById('chart-emotion');
    if (!el || !data.length) return;
    var chart = echarts.init(el);
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['正面', '中性', '负面'], top: 0, textStyle: { fontSize: 10 } },
        grid: { left: 40, right: 20, top: 35, bottom: 30 },
        xAxis: { type: 'category', data: data.map(function(d) { return (d.date || '').slice(5); }), axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
            { name: '正面', data: data.map(function(d) { return d.positive || 0; }), type: 'line', smooth: true, lineStyle: { color: '#5E7A4A' }, itemStyle: { color: '#5E7A4A' } },
            { name: '中性', data: data.map(function(d) { return d.neutral || 0; }), type: 'line', smooth: true, lineStyle: { color: '#8C7C6C' }, itemStyle: { color: '#8C7C6C' } },
            { name: '负面', data: data.map(function(d) { return d.negative || 0; }), type: 'line', smooth: true, lineStyle: { color: '#B85C4A' }, itemStyle: { color: '#B85C4A' } },
        ],
    });
}

function renderHotList(data) {
    var container = document.getElementById('hot-list');
    if (!data.length) { container.innerHTML = '<p class=\"text-gray-400 text-sm\">暂无数据</p>'; return; }
    container.innerHTML = data.map(function(item, i) {
        return '<div class=\"flex items-center gap-3 text-sm\"><span class=\"w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold\" style=\"background:#fdf8ef;color:#BF8D3A\">' + (i+1) + '</span><span class=\"flex-1 truncate\">' + escapeHtml(item.question) + '</span><span class=\"text-xs\" style=\"color:#8C7C6C\">' + item.count + '次</span></div>';
    }).join('');
}

function renderTagChart(data) {
    if (!data || !data.length) return;
    var el = document.getElementById('chart-tag');
    if (!el) return;
    var chart = echarts.init(el);
    chart.setOption({
        tooltip: { trigger: 'item' },
        series: [{ type: 'pie', radius: ['45%', '75%'], data: data.map(function(d) { return { name: d.name, value: d.value }; }), label: { fontSize: 10 }, itemStyle: { borderRadius: 3 } }],
    });
}

// ═══════════════════════════════════════════════
// 知识库 CRUD
// ═══════════════════════════════════════════════
var knowledgePage = 1;

async function loadKnowledge() {
    var search = document.getElementById('k-search') ? document.getElementById('k-search').value : '';
    var tag = document.getElementById('k-tag') ? document.getElementById('k-tag').value : '';
    var route = document.getElementById('k-route') ? document.getElementById('k-route').value : '';
    var params = new URLSearchParams({ page: knowledgePage });
    if (search) params.set('search', search);
    if (tag) params.set('tag', tag);
    if (route) params.set('route', route);
    try {
        var resp = await adminFetch(API_BASE + '/knowledge?' + params.toString());
        var data = await resp.json();
        var tbody = document.getElementById('knowledge-tbody');
        if (!data.items || !data.items.length) {
            tbody.innerHTML = '<tr><td colspan=\"5\" class=\"p-6 text-center text-gray-400\">暂无数据</td></tr>';
        } else {
            tbody.innerHTML = data.items.map(function(item) {
                return '<tr class=\"border-b\" style=\"border-color:#E8E0D0\"><td class=\"p-3 text-xs text-gray-500\">' + item.id + '</td><td class=\"p-3\"><p class=\"text-sm font-medium truncate\" style=\"max-width:280px\">' + escapeHtml(item.question) + '</p></td><td class=\"p-3\"><span class=\"px-2 py-0.5 rounded-full text-xs\" style=\"background:#fdf8ef;color:#BF8D3A\">' + escapeHtml(item.tag || '-') + '</span></td><td class=\"p-3 text-xs text-gray-500\">' + escapeHtml((item.route_name || '-').slice(0,8)) + '</td><td class=\"p-3\"><button onclick=\"deleteKnowledge(' + item.id + ')\" class=\"text-red-500 hover:text-red-700 text-xs\">删除</button></td></tr>';
            }).join('');
        }
        document.getElementById('knowledge-pagination').innerHTML = '<span class=\"text-xs text-gray-400\">共 ' + data.total + ' 条，第 ' + data.page + '/' + data.total_pages + ' 页</span><div class=\"flex gap-1\"><button onclick=\"knowledgePage=Math.max(1,knowledgePage-1);loadKnowledge()\" class=\"px-3 py-1 bg-gray-100 rounded text-xs hover:bg-gray-200\">上一页</button><button onclick=\"knowledgePage=Math.min(' + data.total_pages + ',knowledgePage+1);loadKnowledge()\" class=\"px-3 py-1 bg-gray-100 rounded text-xs hover:bg-gray-200\">下一页</button></div>';
    } catch (e) { console.error('Knowledge error:', e); }
}

function showKnowledgeForm(item) {
    document.getElementById('knowledge-modal').classList.remove('view-hidden');
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

function closeKnowledgeForm() { document.getElementById('knowledge-modal').classList.add('view-hidden'); }

async function deleteKnowledge(id) {
    if (!confirm('确定删除这条知识条目吗？')) return;
    try { await adminFetch(API_BASE + '/knowledge/' + id, { method: 'DELETE' }); loadKnowledge(); }
    catch (e) { alert('删除失败'); }
}

async function importKnowledge(event) {
    var file = event.target.files[0];
    if (!file) return;
    try {
        var text = await file.text();
        var data = JSON.parse(text);
        await adminFetch(API_BASE + '/knowledge/import', { method: 'POST', body: JSON.stringify(data) });
        alert('导入成功');
        loadKnowledge();
    } catch (e) { alert('导入失败'); }
    event.target.value = '';
}

document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('knowledge-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            var id = document.getElementById('k-id').value;
            var data = {
                spot_id: document.getElementById('k-spot_id').value,
                question: document.getElementById('k-question').value,
                answer: document.getElementById('k-answer').value,
                tag: document.getElementById('k-tag-form').value,
                route_name: document.getElementById('k-route-form').value,
                source: document.getElementById('k-source').value,
            };
            try {
                if (id) {
                    await adminFetch(API_BASE + '/knowledge/' + id, { method: 'PUT', body: JSON.stringify(data) });
                } else {
                    await adminFetch(API_BASE + '/knowledge', { method: 'POST', body: JSON.stringify(data) });
                }
                closeKnowledgeForm();
                loadKnowledge();
            } catch (err) { alert('保存失败'); }
        });
    }
});

// ═══════════════════════════════════════════════
// 数字人配置
// ═══════════════════════════════════════════════
async function loadAvatarConfig() {
    try {
        var modelsResp = await adminFetch(API_BASE + '/models');
        var modelsData = await modelsResp.json();
        var modelSelect = document.getElementById('av-model');
        if (modelSelect) {
            modelSelect.innerHTML = '<option value=\"\">不使用 Live2D</option>' + modelsData.models.map(function(m) { return '<option value=\"' + m.url + '\">' + m.name + '</option>'; }).join('');
        }
        if (window.speechSynthesis) {
            var voices = speechSynthesis.getVoices();
            var zhVoices = voices.filter(function(v) { return v.lang.indexOf('zh') === 0; });
            var voiceSelect = document.getElementById('av-voice');
            if (voiceSelect && zhVoices.length) {
                voiceSelect.innerHTML = zhVoices.map(function(v) { return '<option value=\"' + v.name + '\">' + v.name + '</option>'; }).join('');
            }
        }
        var resp = await adminFetch(API_BASE + '/avatar');
        var config = await resp.json();
        if (document.getElementById('av-model')) document.getElementById('av-model').value = config.model_url || '';
        if (document.getElementById('av-voice')) document.getElementById('av-voice').value = config.voice_name || '';
        if (document.getElementById('av-scale')) document.getElementById('av-scale').value = config.scale || 1;
        if (document.getElementById('av-greeting')) document.getElementById('av-greeting').value = config.greeting || '';
        if (document.getElementById('av-active')) document.getElementById('av-active').checked = config.is_active || false;
    } catch (e) { console.error('Avatar error:', e); }
}

async function saveAvatar() {
    var data = {
        model_url: document.getElementById('av-model') ? document.getElementById('av-model').value : '',
        voice_name: document.getElementById('av-voice') ? document.getElementById('av-voice').value : '',
        scale: parseFloat(document.getElementById('av-scale') ? document.getElementById('av-scale').value : 1),
        greeting: document.getElementById('av-greeting') ? document.getElementById('av-greeting').value : '',
        is_active: document.getElementById('av-active') ? document.getElementById('av-active').checked : false,
    };
    try { await adminFetch(API_BASE + '/avatar', { method: 'PUT', body: JSON.stringify(data) }); alert('配置保存成功'); }
    catch (e) { alert('保存失败'); }
}

function testAvatar() {
    var greeting = document.getElementById('av-greeting') ? document.getElementById('av-greeting').value : '欢迎来到灵山胜境！';
    var utterance = new SpeechSynthesisUtterance(greeting);
    utterance.lang = 'zh-CN'; utterance.rate = 0.95;
    speechSynthesis.speak(utterance);
}

// ═══════════════════════════════════════════════
// 情感报告
// ═══════════════════════════════════════════════
function setDefaultDates() {
    var now = new Date();
    var weekAgo = new Date(now.getTime() - 7*24*60*60*1000);
    if (document.getElementById('r-end')) document.getElementById('r-end').value = now.toISOString().slice(0,10);
    if (document.getElementById('r-start')) document.getElementById('r-start').value = weekAgo.toISOString().slice(0,10);
}

async function loadReport() {
    var start = document.getElementById('r-start') ? document.getElementById('r-start').value : '';
    var end = document.getElementById('r-end') ? document.getElementById('r-end').value : '';
    var params = new URLSearchParams();
    if (start) params.set('start', start);
    if (end) params.set('end', end);
    try {
        var resp = await adminFetch(API_BASE + '/report?' + params.toString());
        var data = await resp.json();
        document.getElementById('r-positive').textContent = data.summary ? data.summary.positive || 0 : 0;
        document.getElementById('r-neutral').textContent = data.summary ? data.summary.neutral || 0 : 0;
        document.getElementById('r-negative').textContent = data.summary ? data.summary.negative || 0 : 0;
        renderSentimentBar(data.summary);
        renderSentimentTrend(data.trend || []);
        renderRecentConvs(data.recent_conversations || []);
    } catch (e) { console.error('Report error:', e); }
}

function renderSentimentBar(summary) {
    var el = document.getElementById('chart-sentiment');
    if (!el) return;
    var chart = echarts.init(el);
    chart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['正面', '中性', '负面'] },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{ type: 'bar', barWidth: 40, data: [
            { value: summary ? summary.positive || 0 : 0, itemStyle: { color: '#5E7A4A' } },
            { value: summary ? summary.neutral || 0 : 0, itemStyle: { color: '#8C7C6C' } },
            { value: summary ? summary.negative || 0 : 0, itemStyle: { color: '#B85C4A' } },
        ]}],
    });
}

function renderSentimentTrend(trend) {
    var el = document.getElementById('chart-sentiment-trend');
    if (!el || !trend.length) return;
    var chart = echarts.init(el);
    chart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['正面', '中性', '负面'], top: 0, textStyle: { fontSize: 10 } },
        grid: { left: 40, right: 20, top: 35, bottom: 30 },
        xAxis: { type: 'category', data: trend.map(function(d) { return (d.date || '').slice(5); }), axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', minInterval: 1 },
        series: [
            { name: '正面', data: trend.map(function(d) { return d.positive || 0; }), type: 'line', smooth: true, lineStyle: { color: '#5E7A4A' } },
            { name: '中性', data: trend.map(function(d) { return d.neutral || 0; }), type: 'line', smooth: true, lineStyle: { color: '#8C7C6C' } },
            { name: '负面', data: trend.map(function(d) { return d.negative || 0; }), type: 'line', smooth: true, lineStyle: { color: '#B85C4A' } },
        ],
    });
}

function renderRecentConvs(convs) {
    var container = document.getElementById('recent-convs');
    if (!convs || !convs.length) { container.innerHTML = '<p class=\"text-gray-400 text-sm\">暂无对话记录</p>'; return; }
    var emojiMap = { positive: '😊', negative: '😟', neutral: '😐' };
    container.innerHTML = convs.map(function(c) {
        return '<div class=\"border rounded-lg p-3 text-sm\" style=\"border-color:#E8E0D0\"><div class=\"flex items-center justify-between mb-1\"><span class=\"text-xs text-gray-400\">' + (c.create_time || '').slice(0,16) + '</span><span>' + (emojiMap[c.emotion] || '😐') + '</span></div><p class=\"font-medium\">👤 ' + escapeHtml(c.user_input || '') + '</p><p class=\"text-gray-500 mt-1 text-xs\">🤖 ' + escapeHtml((c.bot_answer || '').slice(0,100)) + '...</p></div>';
    }).join('');
}

// ═══════════════════════════════════════════════
// 图表 resize
// ═══════════════════════════════════════════════
window.addEventListener('resize', function() {
    ['chart-week', 'chart-emotion', 'chart-tag', 'chart-sentiment', 'chart-sentiment-trend'].forEach(function(id) {
        var el = document.getElementById(id);
        if (el && !el.closest('.view-hidden')) {
            var instance = echarts.getInstanceByDom(el);
            if (instance) instance.resize();
        }
    });
});
