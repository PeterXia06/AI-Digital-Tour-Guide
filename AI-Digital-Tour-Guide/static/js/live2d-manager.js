/**
 * Live2DManager — PixiJS v7 + Cubism 4 + pixi-live2d-display v0.4.0
 * 音画同步升级版：beforeModelUpdate 钩子 + 2.5x 口型放大
 */
(function () {
    'use strict';

    var LOG_PREFIX = '[Live2D] ';

    function log(msg, level) {
        level = level || 'log';
        console[level](LOG_PREFIX + msg);
    }

    var Live2DManager = function (opts) {
        opts = opts || {};
        this._canvasId = opts.canvasId || 'l2d-canvas';
        this._placeholderId = opts.placeholderId || 'avatar-placeholder';
        this._width = opts.width || 800;
        this._height = opts.height || 1000;
        this._app = null;
        this._model = null;
        this._ready = false;
        this._initOk = false;
        this._idleTimer = null;
        this._idleInterval = opts.idleInterval || 8000;
        this._lipCallback = null;     // beforeModelUpdate 回调引用（用于 off）
        this._lipAudio = null;        // AudioManager 引用
        this._currentLip = 0;         // 当前平滑后的口型值
        this._currentModelUrl = null;
        this._loadId = 0;
        window.l2dManager = this;
    };

    Live2DManager.prototype.init = function () {
        try {
            var PIXI = window.PIXI;
            if (!PIXI) { log('✗ PixiJS 未加载', 'error'); this._showPlaceholder(); return Promise.resolve(false); }

            var live2d = PIXI.live2d;
            if (!live2d) { log('✗ PIXI.live2d 未加载', 'error'); this._showPlaceholder(); return Promise.resolve(false); }

            if (!window.Live2DCubismCore) {
                log('✗ Live2DCubismCore 未加载', 'error');
                this._showPlaceholder();
                return Promise.resolve(false);
            }

            // 开启日志（兼容不同版本的 config API）
            try {
                if (live2d.config) {
                    live2d.config.logLevel = live2d.config.LOG_LEVEL_VERBOSE || 3;
                }
            } catch (e) {}
            log('✓ Cubism 4 + PixiJS v7 + pixi-live2d-display v0.4.0');

            // PixiJS v7: 同步构造函数，传入已有 canvas
            var canvas = document.getElementById(this._canvasId);
            if (!canvas) { log('✗ Canvas 未找到', 'error'); this._showPlaceholder(); return Promise.resolve(false); }

            this._app = new PIXI.Application({
                view: canvas,
                width: this._width,
                height: this._height,
                backgroundAlpha: 0,
                antialias: true,
                resolution: window.devicePixelRatio || 1,
                autoDensity: true,
            });

            log('✓ PixiJS v7 就绪 ' + this._width + 'x' + this._height);

            // Canvas 居中样式
            canvas.style.maxWidth = '100%';
            canvas.style.maxHeight = '100%';
            canvas.style.position = 'absolute';
            canvas.style.top = '50%';
            canvas.style.left = '50%';
            canvas.style.transform = 'translate(-50%, -50%)';

            this._initOk = true;
            return Promise.resolve(true);
        } catch (e) {
            log('✗ 初始化失败: ' + e.message, 'error');
            console.error(e);
            this._showPlaceholder();
            return Promise.resolve(false);
        }
    };

    /**
     * 加载 Live2D 模型
     * @param {string} modelUrl - 模型 JSON 路径
     * @param {object} [profile]  - 角色配置（scale, y_offset, name 等）
     */
    Live2DManager.prototype.loadModel = function (modelUrl, profile) {
        if (!this._initOk) { log('✗ PixiJS 未就绪', 'error'); return; }

        var loadId = ++this._loadId;
        this.unloadModel();
        profile = profile || {};
        log('⏳ 加载模型: ' + modelUrl + (profile.name ? ' (' + profile.name + ')' : ''));

        var self = this;

        window.PIXI.live2d.Live2DModel.from(modelUrl).then(function (model) {
            if (loadId !== self._loadId) { model.destroy(); return; }

            self._model = model;
            self._currentModelUrl = modelUrl;

            // 读取画师原生物理尺寸
            var rawW = (model.internalModel && model.internalModel.width) || model.width || 0;
            var rawH = (model.internalModel && model.internalModel.height) || model.height || 0;
            log('📊 画师原生尺寸: W=' + rawW + ', H=' + rawH);

            // 除零防御
            if (rawW === 0 || rawH === 0) {
                log('⚠️ 尺寸为 0！启用 fallback...', 'warn');
                rawW = 1000;
                rawH = 2000;
            }

            // 自适应缩放：高度占画布 90%
            var targetScale = (self._app.screen.height * 0.9) / rawH;
            if (!isFinite(targetScale) || targetScale > 5) {
                log('⚠️ 缩放异常，强制降级为 ' + (profile.scale || 0.15), 'warn');
                targetScale = profile.scale || 0.15;
            }
            model.scale.set(targetScale);

            // X 轴居中，Y 轴居中 + 角色专属偏移
            var finalW = rawW * targetScale;
            var finalH = rawH * targetScale;
            model.x = (self._app.screen.width - finalW) / 2;
            model.y = (self._app.screen.height - finalH) / 2 + (profile.y_offset || 0);

            // 推上舞台
            self._app.stage.addChild(model);

            // 视线跟随（pixi-live2d-display v0.4.0 API: model.focus）
            self._app.stage.interactive = true;
            self._app.stage.hitArea = new PIXI.Rectangle(0, 0, self._app.screen.width, self._app.screen.height);
            self._app.stage.on('pointermove', function (ev) {
                if (self._model) {
                    self._model.focus(ev.data.global.x, ev.data.global.y);
                }
            });

            self._hidePlaceholder();
            self.startIdle(self._idleInterval);
            self._ready = true;

            log('✓ 模型就绪! scale=' + targetScale.toFixed(4) +
                ' pos=(' + model.x.toFixed(0) + ',' + model.y.toFixed(0) + ')' +
                ' raw=(' + rawW.toFixed(0) + 'x' + rawH.toFixed(0) + ')');
        }).catch(function (e) {
            log('✗ 加载失败: ' + e.message, 'error');
            console.error(e);
            self._showPlaceholder();
        });
    };

    Live2DManager.prototype.unloadModel = function () {
        this.stopIdle();
        this.disableLipSync();
        this._ready = false;
        if (this._model) {
            try {
                this._app.stage.removeChild(this._model);
                this._model.destroy();
            } catch (e) {}
            this._model = null;
        }
        this._currentModelUrl = null;
    };

    Live2DManager.prototype.switchModel = function (modelUrl, profile) {
        this.setLipSync(0);
        this.loadModel(modelUrl, profile);
    };

    /**
     * 🎭 多模态中枢：从后端 API 查询当前激活角色并加载对应模型
     * 异步方法，先问 API "我是谁"，再按需加载模型资产。
     */
    Live2DManager.prototype.fetchAndLoadCharacter = async function () {
        if (!this._initOk) { log('✗ PixiJS 未就绪，跳过角色加载', 'error'); return; }

        try {
            log('🎭 查询中枢系统当前角色...');
            var resp = await fetch('/api/admin/character');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var data = await resp.json();
            var profile = data.profile;
            var characterId = data.character_id;

            log('🎭 接收到中枢指令 → ' + profile.name + ' (ID: ' + characterId + ')');
            this.loadModel(profile.model_url, profile);

        } catch (e) {
            log('✗ 角色查询失败，降级加载默认 hiyori: ' + e.message, 'warn');
            this.loadModel('/static/models/hiyori/hiyori_free_t08.model3.json', {
                name: '小灵 (默认)',
                scale: 0.18,
                y_offset: 100,
            });
        }
    };

    Live2DManager.prototype.playMotion = function (group, index) {
        if (!this._model || !this._model.internalModel) return;
        try {
            this._model.motion(group, index);
        } catch (e) {
            log('⚠ 动作播放失败: ' + e.message, 'warn');
        }
    };

    Live2DManager.prototype.startIdle = function (intervalMs) {
        var self = this;
        this.stopIdle();
        this._idleInterval = intervalMs || 8000;
        this._idleTimer = setInterval(function () { self.playMotion('Idle'); }, this._idleInterval);
    };

    Live2DManager.prototype.stopIdle = function () {
        if (this._idleTimer) { clearInterval(this._idleTimer); this._idleTimer = null; }
    };

    Live2DManager.prototype.setLipSync = function (value) {
        if (this._model && this._model.internalModel) {
            try { this._model.setLipSyncValue(Math.max(0, Math.min(1, value))); } catch (e) {}
        }
    };

    /**
     * 启用唇形同步 — 使用 beforeModelUpdate 钩子避免与呼吸动画竞态
     * @param {AudioManager} audioManager
     */
    Live2DManager.prototype.enableLipSync = function (audioManager) {
        if (!this._app || !this._model || !this._model.internalModel) return;
        this.disableLipSync();

        this._lipAudio = audioManager;
        this._currentLip = 0;
        var self = this;

        // 🚨 偏差一修复：用 beforeModelUpdate 替代 app.ticker
        // 在引擎渲染前一刻强行注入口型，不会被 Live2D 内部呼吸动画覆盖
        this._lipCallback = function () {
            if (!self._lipAudio || !self._lipAudio.isPlaying()) return;

            // 🚨 偏差二修复：用 getSmoothedVolume（已含阈值过滤+黄金比例 lerp）
            var target = self._lipAudio.getSmoothedVolume
                ? self._lipAudio.getSmoothedVolume()
                : self._lipAudio.getVolume();

            // 人类肌肉反应级 lerp (0.4)
            self._currentLip += (target - self._currentLip) * 0.4;

            // 2.5x 放大系数 — 让嘴巴张开更明显
            var mouthOpen = Math.min(1.0, self._currentLip * 2.5);

            // 直接写入 Cubism 底层参数 ParamMouthOpenY
            try {
                self._model.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', mouthOpen);
            } catch (e) {
                // 降级：用 pixi-live2d-display 封装的 API
                self.setLipSync(mouthOpen);
            }
        };

        this._model.internalModel.on('beforeModelUpdate', this._lipCallback);
        log('🔊 唇形同步已启动 (beforeModelUpdate 钩子)');
    };

    Live2DManager.prototype.disableLipSync = function () {
        if (this._lipCallback && this._model && this._model.internalModel) {
            this._model.internalModel.off('beforeModelUpdate', this._lipCallback);
        }
        this._lipCallback = null;
        this._lipAudio = null;
        this._currentLip = 0;
        this.setLipSync(0);  // 嘴巴闭合
        log('🔇 唇形同步已停止');
    };

    Live2DManager.prototype.setStatus = function (status) {
        var el = document.getElementById('avatar-status');
        var map = {
            idle: '等待中', speaking: '讲解中...', listening: '倾听中...', thinking: '思考中...', happy: '😊'
        };
        if (el) el.textContent = map[status] || status;
        if (status === 'speaking' || status === 'happy') this.playMotion('Tap');
        else if (status === 'listening') this.playMotion('Idle');
    };

    Live2DManager.prototype._showPlaceholder = function () {
        var el = document.getElementById(this._placeholderId);
        if (el) el.style.display = 'flex';
    };

    Live2DManager.prototype._hidePlaceholder = function () {
        var el = document.getElementById(this._placeholderId);
        if (el) el.style.display = 'none';
    };

    Live2DManager.prototype.isReady = function () { return this._ready; };

    Live2DManager.prototype.destroy = function () {
        this.stopIdle();
        this.unloadModel();
        if (this._app) { try { this._app.destroy(true, { children: true }); } catch (e) {} this._app = null; }
        this._initOk = false;
        this._ready = false;
        if (window.l2dManager === this) delete window.l2dManager;
        this._showPlaceholder();
    };

    window.Live2DManager = Live2DManager;
})();
