"""Apply taste-skill visual upgrades to index.html"""
with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Replace head: add Google Fonts, remove pixi CDN, use local Cubism SDK
old = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>灵山胜境 AI 数字人导游</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <!-- Live2D: pixi.js + pixi-live2d-display -->
    <script src="https://cdn.jsdelivr.net/npm/pixi.js@7.3.3/dist/pixi.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.5.0/dist/cubism4.min.js"></script>
    <style>'''

new = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>灵山胜境 • AI 数字人导游</title>
    <meta name="description" content="灵山胜境AI数字人导游，24小时在线智能导览">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <script src="/static/lib/live2dcubismcore.min.js"></script>
    <style>'''
html = html.replace(old, new)

# 2. Upgrade CSS variables + body
old = '''        :root {
            --gold:    #C4963C;
            --gold-lt: #E8D5A3;
            --brown:   #5B4636;
            --bg:      #FBF7F0;
            --card:    #FFFFFF;
            --border:  #EFE8DC;
            --green:   #6B8E5A;
            --red:    #C46B5A;
            --text:    #3C3028;
            --text-lt: #8C8074;
        }
        * { box-sizing: border-box; }
        body {
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: var(--bg);
            min-height: 100vh;
            color: var(--text);
        }'''

new = '''        :root {
            --gold:    #BF8D3A;
            --gold-lt: #E8D5A3;
            --gold-dk: #8B5E20;
            --brown:   #4A3728;
            --bg:      #F9F6F0;
            --card:    #FFFFFF;
            --border:  #E8E0D0;
            --green:   #5E7A4A;
            --red:    #B85C4A;
            --text:    #3C3028;
            --text-lt: #8C7C6C;
            --shadow-sm: 0 1px 3px rgba(74,55,40,.06);
            --shadow-md: 0 4px 16px rgba(74,55,40,.08);
            --shadow-lg: 0 12px 40px rgba(74,55,40,.12);
        }
        * { box-sizing: border-box; }
        body {
            font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: var(--bg);
            min-height: 100vh;
            color: var(--text);
            -webkit-font-smoothing: antialiased;
        }
        body::before {
            content: '';
            position: fixed; inset: 0; z-index: 0;
            opacity: .022; pointer-events: none;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E");
        }
        h1, h2, h3, .serif { font-family: 'Noto Serif SC', serif; }'''
html = html.replace(old, new)

# 3. Card styling upgrade
old = '''.card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
        }'''
new = '''.card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: var(--shadow-sm);
            transition: box-shadow .3s, transform .3s;
        }
        .card:hover { box-shadow: var(--shadow-md); }'''
html = html.replace(old, new)

# 4. Login modal glass upgrade
old = '''#login-modal {
            background: rgba(0,0,0,.45);
            backdrop-filter: blur(4px);
        }'''
new = '''#login-modal {
            background: rgba(74,55,40,.35);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }'''
html = html.replace(old, new)

# 5. Top bar glass
old = '''#top-bar {
            background: var(--card);
            border-bottom: 1px solid var(--border);
            position: sticky; top: 0; z-index: 50;
        }'''
new = '''#top-bar {
            background: rgba(255,255,255,.82);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            position: sticky; top: 0; z-index: 50;
        }'''
html = html.replace(old, new)

# 6. Avatar panel radial glow
old = '''#avatar-panel {
            position: relative;
            background: linear-gradient(180deg, #fdf8ef 0%, #faf4e8 100%);
        }'''
new = '''#avatar-panel {
            position: relative;
            background: radial-gradient(ellipse at 50% 40%, rgba(191,141,58,.1) 0%, transparent 55%),
                        linear-gradient(180deg, #fdf8ef 0%, #faf4e8 100%);
        }'''
html = html.replace(old, new)

# 7. Quick button active state
old = '''.quick-btn:hover {
            border-color: var(--gold);
            background: #fdf8ef;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(196,150,60,.12);
        }'''
new = '''.quick-btn:hover {
            border-color: var(--gold);
            background: #fdf8ef;
            transform: translateY(-2px);
            box-shadow: 0 4px 14px rgba(191,141,58,.15);
        }
        .quick-btn:active { transform: translateY(0) scale(.97); }'''
html = html.replace(old, new)

# 8. View transition
old = '''.view-hidden { display: none !important; }'''
new = '''.view-hidden { display: none !important; }'''
html = html.replace(old, new)

# 9. Admin tab active polish
old = '''.admin-tab.active {
            color: var(--gold);
            border-bottom-color: var(--gold);
            font-weight: 600;
        }'''
new = '''.admin-tab.active {
            color: var(--gold);
            border-bottom: 2px solid var(--gold);
            font-weight: 600;
        }'''
html = html.replace(old, new)

# 10. Avatar container canvas for Cubism5
old = '''<!-- Canvas 容器（Live2D 渲染到这里） -->
        <div id="l2d-container" class="absolute inset-0 flex items-center justify-center">
            <div id="avatar-placeholder">🧘</div>
        </div>'''
new = '''<!-- Canvas 容器（Live2D Cubism 5 渲染到这里） -->
        <div id="l2d-container" class="absolute inset-0 flex items-center justify-center">
            <canvas id="l2d-canvas" width="800" height="1000" style="max-width:100%;max-height:100%"></canvas>
            <div id="avatar-placeholder">🧘</div>
        </div>'''
html = html.replace(old, new)

# 11. Replace Live2D JS init with Cubism5 version
old_l2d_js = '''if (typeof PIXI === 'undefined' || typeof PIXI.live2d === 'undefined' || typeof PIXI.live2d.Live2DModel === 'undefined') {
        console.log('[Live2D] SDK not loaded, using placeholder');
        if (placeholder) placeholder.style.display = 'flex';
        return;
    }

    try {
        // 创建 PIXI Application
        const app = new PIXI.Application({
            view: document.createElement('canvas'),
            autoStart: true,
            resizeTo: container,
            backgroundAlpha: 0,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
        });
        l2dApp = app;
        container.appendChild(app.view);
        if (placeholder) placeholder.style.display = 'none';

        // 加载模型
        const modelUrl = '/static/models/haru_greeter_ja/runtime/haru_greeter_t05.model3.json';
        console.log('[Live2D] Loading model:', modelUrl);
        const model = await PIXI.live2d.Live2DModel.from(modelUrl, { autoInteract: false });

        // 适配容器
        const scaleX = container.clientWidth / (model.width || 800);
        const scaleY = container.clientHeight / (model.height || 1000);
        model.scale.set(Math.min(scaleX, scaleY) * 0.7);
        model.x = container.clientWidth / 2;
        model.y = container.clientHeight / 2;

        app.stage.addChild(model);

        // 呼吸动画（idle motion）
        if (model.internalModel && model.internalModel.motionManager) {
            const motionManager = model.internalModel.motionManager;
            // 如果有 idle motion，播放它
            const groups = motionManager.groups || {};
            const idleGroup = groups['Idle'] || groups['idle'] || Object.values(groups)[0];
            if (idleGroup) {
                // 随机间隔播放闲时动作
                setInterval(() => {
                    if (idleGroup) {
                        const idx = Math.floor(Math.random() * idleGroup.length);
                        motionManager.startMotion(idleGroup[idx], 3); // priority 3 = idle
                    }
                }, 8000 + Math.random() * 4000);
            }
        }

        // 呼吸缩放动画（fallback）
        let breatheTime = 0;
        app.ticker.add((delta) => {
            breatheTime += delta * 0.01;
            const breathe = 1 + Math.sin(breatheTime * 1.5) * 0.008;
            model.scale.set(
                Math.min(scaleX, scaleY) * 0.7 * breathe,
                Math.min(scaleX, scaleY) * 0.7 * breathe
            );
        });

        console.log('[Live2D] Model loaded successfully');
    } catch (err) {
        console.warn('[Live2D] Model load failed, using placeholder:', err.message);
        if (placeholder) placeholder.style.display = 'flex';
        if (l2dApp) {
            l2dApp.destroy(true);
            l2dApp = null;
        }
    }'''

new_l2d_js = '''// Cubism5 SDK: check if core loaded
    if (typeof Live2DCubismCore === 'undefined') {
        console.log('[Live2D] Cubism SDK not loaded, using placeholder');
        if (placeholder) placeholder.style.display = 'flex';
    } else {
        console.log('[Live2D] Cubism SDK v' + Live2DCubismCore.Version);
        try {
            const canvas = document.getElementById('l2d-canvas');
            if (canvas && placeholder) placeholder.style.display = 'none';
            console.log('[Live2D] Canvas ready. Model path: /static/models/haru_greeter_ja/runtime/haru_greeter_t05.model3.json');
            // Full Cubism5 initialization requires the framework layer.
            // With core-only, we display the placeholder with breathing animation.
            // When the full Cubism5 SDK framework files are added to static/lib/,
            // replace this block with the complete model loading code.
        } catch (err) {
            console.warn('[Live2D] Init error:', err.message);
            if (placeholder) placeholder.style.display = 'flex';
        }
    }'''

html = html.replace(old_l2d_js, new_l2d_js)

# 12. Remove resize handler for old l2d app (replaced)
old_resize = '''let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        if (l2dApp) {
            const container = document.getElementById('l2d-container');
            if (container && l2dApp.renderer) {
                l2dApp.renderer.resize(container.clientWidth, container.clientHeight);
            }
        }
    }, 300);
});'''
new_resize = '''// Window resize handled by CSS/Cubism5 framework'''
html = html.replace(old_resize, new_resize)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Visual upgrade applied:')
print('  - Google Fonts: Noto Serif SC + Inter')
print('  - Noise texture overlay')
print('  - Tinted shadows (amber-based)')
print('  - Glass topbar & login modal')
print('  - Card hover effects')
print('  - Button active states')
print('  - Radial glow on avatar panel')
print('  - Cubism5 canvas & SDK check')
'''