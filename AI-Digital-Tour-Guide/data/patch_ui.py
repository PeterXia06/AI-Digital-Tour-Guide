"""Apply taste-skill visual upgrades via surgical line patches."""
import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

count = 0

# 1. Add Google Fonts after viewport meta
old = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>'
new = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <meta name="description" content="灵山胜境AI数字人导游">\n    <link rel="preconnect" href="https://fonts.googleapis.com">\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">\n    <title>'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 2. Remove pixi CDN, keep Cubism core
old = '    <script src="https://cdn.jsdelivr.net/npm/pixi.js@7.3.3/dist/pixi.min.js"></script>\n    <script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.5.0/dist/cubism4.min.js"></script>'
new = '    <script src="/static/lib/live2dcubismcore.min.js"></script>'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 3. Add CSS shadow variables
old = '            --text-lt: #8C8074;\n        }'
new = '            --text-lt: #8C8074;\n            --shadow-sm: 0 1px 3px rgba(74,55,40,.06);\n            --shadow-md: 0 4px 16px rgba(74,55,40,.08);\n            --shadow-lg: 0 12px 40px rgba(74,55,40,.12);\n        }'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 4. Upgrade body font
old = "font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;"
new = "font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;"
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 5. Add antialiasing after body color
old = '            color: var(--text);\n        }'
new = '            color: var(--text);\n            -webkit-font-smoothing: antialiased;\n        }'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 6. Add noise texture after body closing brace (right after antialiased block)
old = '            -webkit-font-smoothing: antialiased;\n        }\n\n        /* ── 顶栏 ── */'
new = '            -webkit-font-smoothing: antialiased;\n        }\n        body::before {\n            content: "";\n            position: fixed; inset: 0; z-index: 0;\n            opacity: .022; pointer-events: none;\n            background-image: url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\' opacity=\'0.5\'/%3E%3C/svg%3E");\n        }\n\n        /* ── 顶栏 ── */'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 7. Glass topbar
old = '        #top-bar {\n            background: var(--card);\n            border-bottom: 1px solid var(--border);\n            position: sticky; top: 0; z-index: 50;\n        }'
new = '        #top-bar {\n            background: rgba(255,255,255,.82);\n            backdrop-filter: blur(12px);\n            -webkit-backdrop-filter: blur(12px);\n            border-bottom: 1px solid var(--border);\n            position: sticky; top: 0; z-index: 50;\n        }'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 8. Card upgrade with shadow + hover
old = '        .card {\n            background: var(--card);\n            border: 1px solid var(--border);\n            border-radius: 12px;\n        }'
new = '        .card {\n            background: var(--card);\n            border: 1px solid var(--border);\n            border-radius: 14px;\n            box-shadow: var(--shadow-sm);\n            transition: box-shadow .3s, transform .3s;\n        }\n        .card:hover { box-shadow: var(--shadow-md); }'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 9. Login modal glass
old = '        #login-modal {\n            background: rgba(0,0,0,.45);\n            backdrop-filter: blur(4px);\n        }'
new = '        #login-modal {\n            background: rgba(74,55,40,.35);\n            backdrop-filter: blur(14px);\n            -webkit-backdrop-filter: blur(14px);\n        }'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 10. Quick button active state
old = '        .quick-btn:hover {\n            border-color: var(--gold);\n            background: #fdf8ef;\n            transform: translateY(-1px);\n            box-shadow: 0 2px 8px rgba(196,150,60,.12);\n        }'
new = '        .quick-btn:hover {\n            border-color: var(--gold);\n            background: #fdf8ef;\n            transform: translateY(-2px);\n            box-shadow: 0 4px 14px rgba(191,141,58,.15);\n        }\n        .quick-btn:active { transform: translateY(0) scale(.97); }'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 11. Add canvas for Cubism5
old = '        <div id="l2d-container" class="absolute inset-0 flex items-center justify-center">\n            <div id="avatar-placeholder">'
new = '        <div id="l2d-container" class="absolute inset-0 flex items-center justify-center">\n            <canvas id="l2d-canvas" width="800" height="1000" style="max-width:100%;max-height:100%"></canvas>\n            <div id="avatar-placeholder">'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 12. Serif font rule for headlines
old = '        /* ── 响应式 ── */'
new = '        h1, h2, h3, .serif { font-family: "Noto Serif SC", serif; }\n\n        /* ── 响应式 ── */'
if old in content:
    content = content.replace(old, new, 1)
    count += 1

# 13. Update Live2D init for Cubism5
old_l2d = '''// 检查 pixi-live2d-display 是否可用
    if (typeof PIXI === 'undefined' || typeof PIXI.live2d === 'undefined' || typeof PIXI.live2d.Live2DModel === 'undefined') {'''
new_l2d = '''// Check Cubism 5 SDK
    if (typeof Live2DCubismCore === 'undefined') {'''
if old_l2d in content:
    content = content.replace(old_l2d, new_l2d, 1)
    count += 1

old_l2d2 = '''        console.log('[Live2D] SDK not loaded, using placeholder');'''
new_l2d2 = '''        console.log('[Live2D] Cubism SDK not loaded, using placeholder');'''
if old_l2d2 in content:
    content = content.replace(old_l2d2, new_l2d2, 1)

old_l2d3 = '''    try {
        // 创建 PIXI Application
        const app = new PIXI.Application({'''
new_l2d3 = '''    try {
        const canvas = document.getElementById('l2d-canvas');
        console.log('[Live2D] Cubism Core v' + Live2DCubismCore.Version + ', canvas ready');
        // Full Cubism5 model loading requires the framework layer
        // Model path: /static/models/haru_greeter_ja/runtime/haru_greeter_t05.model3.json
        if (canvas && placeholder) { placeholder.style.display = 'none'; }
        // Placeholder PIXI code removed - using Cubism5
        const app = { view: canvas, renderer: null, stage: null, ticker: null }; // stub for compatibility'''
if old_l2d3 in content:
    content = content.replace(old_l2d3, new_l2d3, 1)
    count += 1

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Applied {count} visual upgrade patches')
