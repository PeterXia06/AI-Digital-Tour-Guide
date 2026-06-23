/**
 * AudioManager — Web Audio API 播放 + 实时音量分析
 * 用于替代浏览器内置 SpeechSynthesis，驱动 Live2D 唇形同步
 */
(function () {
    'use strict';

    var LOG_PREFIX = '[Audio] ';

    function log(msg, level) {
        level = level || 'log';
        console[level](LOG_PREFIX + msg);
    }

    function AudioManager() {
        this._ctx = null;           // AudioContext
        this._analyser = null;      // AnalyserNode
        this._source = null;        // AudioBufferSourceNode
        this._playing = false;
        this._audioBuffer = null;   // 解码后的 AudioBuffer
        this._startTime = 0;        // 播放开始时间
        this._duration = 0;         // 音频时长（秒）
        this._onStartCb = null;
        this._onEndCb = null;
        this._gainNode = null;      // GainNode（音量控制）
        this._currentVolume = 0;    // 平滑后的当前音量（黄金比例 lerp）
    }

    AudioManager.prototype._ensureContext = function () {
        if (!this._ctx) {
            this._ctx = new (window.AudioContext || window.webkitAudioContext)();
            this._analyser = this._ctx.createAnalyser();
            this._analyser.fftSize = 256;
            this._analyser.smoothingTimeConstant = 0.4;
            this._gainNode = this._ctx.createGain();
            this._gainNode.connect(this._analyser);
            this._analyser.connect(this._ctx.destination);
            // 首次用户交互时自动恢复 AudioContext
            var self = this;
            var resume = function () {
                if (self._ctx && self._ctx.state === 'suspended') self._ctx.resume();
                document.removeEventListener('click', resume);
                document.removeEventListener('touchstart', resume);
                document.removeEventListener('keydown', resume);
            };
            document.addEventListener('click', resume);
            document.addEventListener('touchstart', resume);
            document.addEventListener('keydown', resume);
        }
        if (this._ctx.state === 'suspended') {
            this._ctx.resume();
        }
    };

    /**
     * 下载并播放 TTS 音频
     * @param {string} url - 音频 URL（如 /api/tts?text=...）
     */
    AudioManager.prototype.play = async function (url) {
        this.stop();
        this._ensureContext();

        // ── 击穿 Chrome 自动播放限制 ──
        if (this._ctx && this._ctx.state === 'suspended') {
            await this._ctx.resume();
            log('🔈 浏览器音频引擎已唤醒！');
        }

        try {
            log('⏳ 加载音频...');
            var resp = await fetch(url);
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            var arrayBuffer = await resp.arrayBuffer();
            this._audioBuffer = await this._ctx.decodeAudioData(arrayBuffer);
            this._duration = this._audioBuffer.duration;
            log('✓ 音频就绪 ' + this._duration.toFixed(1) + 's');

            this._start();
            return this._duration;
        } catch (e) {
            log('✗ 音频加载失败: ' + e.message, 'error');
            console.error(e);
            if (this._onEndCb) this._onEndCb();
            return 0;
        }
    };

    AudioManager.prototype._start = function () {
        if (!this._audioBuffer) return;

        this._source = this._ctx.createBufferSource();
        this._source.buffer = this._audioBuffer;
        this._source.connect(this._gainNode);
        this._source.start(0);
        this._startTime = this._ctx.currentTime;
        this._playing = true;

        var self = this;
        this._source.onended = function () {
            self._playing = false;
            self._source = null;
            log('✓ 播放完毕');
            if (self._onEndCb) self._onEndCb();
        };

        log('▶ 开始播放');
        if (this._onStartCb) this._onStartCb();
    };

    AudioManager.prototype.stop = function () {
        if (this._source) {
            try { this._source.stop(); } catch (e) {}
            this._source = null;
        }
        this._playing = false;
        this._audioBuffer = null;
    };

    /**
     * 获取实时音量 (0 ~ 1)
     * 供 Live2D ticker 每帧调用（旧版兼容，保留此方法）
     */
    AudioManager.prototype.getVolume = function () {
        return this.getSmoothedVolume();
    };

    /**
     * 🚨 偏差二修复：带底噪阈值 + 黄金比例 lerp 的平滑音量
     * 解决 AnalyserNode 频域数据平均音量过小、嘴巴“嘟嘟囔囔”不张开的问题
     * @returns {number} 0~1 平滑音量
     */
    AudioManager.prototype.getSmoothedVolume = function () {
        if (!this._playing || !this._analyser) {
            this._currentVolume = 0;
            return 0;
        }

        var dataArray = new Uint8Array(this._analyser.frequencyBinCount);
        this._analyser.getByteFrequencyData(dataArray);

        // 1. 提取有效能量（去除极微弱的环境底噪）
        var sum = 0;
        for (var i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        var average = sum / dataArray.length;

        // 2. 映射到 0~1 区间，底噪阈值 < 10 视为静音
        var targetVolume = average > 10 ? (average / 100) : 0;
        targetVolume = Math.min(1, targetVolume);

        // 3. 黄金比例 Lerp 平滑插值（0.4 最接近人类肌肉反应）
        this._currentVolume += (targetVolume - this._currentVolume) * 0.4;

        return this._currentVolume;
    };

    AudioManager.prototype.isPlaying = function () {
        return this._playing;
    };

    AudioManager.prototype.getDuration = function () {
        return this._duration;
    };

    AudioManager.prototype.getElapsed = function () {
        if (!this._playing || !this._ctx) return 0;
        return this._ctx.currentTime - this._startTime;
    };

    AudioManager.prototype.onStart = function (cb) { this._onStartCb = cb; };
    AudioManager.prototype.onEnd = function (cb) { this._onEndCb = cb; };

    AudioManager.prototype.destroy = function () {
        this.stop();
        if (this._ctx) {
            try { this._ctx.close(); } catch (e) {}
            this._ctx = null;
        }
        this._analyser = null;
        this._gainNode = null;
    };

    window.AudioManager = AudioManager;
})();
