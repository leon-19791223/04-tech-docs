/**
 * DWS 部署工具集 — 图表组件
 * 纯 Canvas 2D 实现，零外部依赖。
 *
 * 包含: 雷达图, 柱状图, 状态摘要
 */
var DWSCharts = (function() {
    'use strict';

    /**
     * 绘制预检结果雷达图
     * @param {string} canvasId - Canvas 元素 ID
     * @param {Object} data - { categories: {name, pass, total, ...}, width, height }
     */
    function drawRadarChart(canvasId, data) {
        var canvas = document.getElementById(canvasId);
        if (!canvas) return;
        var ctx = canvas.getContext('2d');
        var W = data.width || 360;
        var H = data.height || 300;
        canvas.width = W;
        canvas.height = H;

        var cats = data.categories || [];
        if (!cats.length) {
            ctx.fillStyle = '#9ca0af';
            ctx.font = '14px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('暂无数据', W/2, H/2);
            return;
        }

        var cx = W * 0.45, cy = H * 0.5;
        var radius = Math.min(W * 0.35, H * 0.35);
        var n = cats.length;
        var levels = 4;

        // 清除
        ctx.clearRect(0, 0, W, H);

        // 辅助网格
        for (var l = 1; l <= levels; l++) {
            var r = radius * l / levels;
            ctx.beginPath();
            for (var i = 0; i < n; i++) {
                var angle = Math.PI * 2 * i / n - Math.PI / 2;
                var x = cx + r * Math.cos(angle);
                var y = cy + r * Math.sin(angle);
                i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.strokeStyle = 'rgba(208,213,221,0.5)';
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        // 轴线
        for (var i = 0; i < n; i++) {
            var angle = Math.PI * 2 * i / n - Math.PI / 2;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
            ctx.strokeStyle = 'rgba(208,213,221,0.5)';
            ctx.stroke();
        }

        // 数据区域
        ctx.beginPath();
        for (var i = 0; i < n; i++) {
            var cat = cats[i];
            var ratio = cat.total > 0 ? cat.pass / cat.total : 0;
            var angle = Math.PI * 2 * i / n - Math.PI / 2;
            var x = cx + radius * ratio * Math.cos(angle);
            var y = cy + radius * ratio * Math.sin(angle);
            i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = 'rgba(74,95,193,0.15)';
        ctx.fill();
        ctx.strokeStyle = '#4A5FC1';
        ctx.lineWidth = 2;
        ctx.stroke();

        // 数据点
        for (var i = 0; i < n; i++) {
            var cat = cats[i];
            var ratio = cat.total > 0 ? cat.pass / cat.total : 0;
            var angle = Math.PI * 2 * i / n - Math.PI / 2;
            var x = cx + radius * ratio * Math.cos(angle);
            var y = cy + radius * ratio * Math.sin(angle);
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fillStyle = ratio >= 0.9 ? '#0E7C4B' : ratio >= 0.7 ? '#E67E22' : '#C62828';
            ctx.fill();
        }

        // 标签
        ctx.fillStyle = '#1A1D26';
        ctx.font = '12px -apple-system, "PingFang SC", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        for (var i = 0; i < n; i++) {
            var angle = Math.PI * 2 * i / n - Math.PI / 2;
            var lx = cx + (radius + 22) * Math.cos(angle);
            var ly = cy + (radius + 22) * Math.sin(angle);
            var cat = cats[i];
            var pct = cat.total > 0 ? Math.round(cat.pass / cat.total * 100) : 0;
            ctx.fillStyle = '#6B7285';
            ctx.fillText(cat.name, lx, ly - 7);
            ctx.fillStyle = pct >= 90 ? '#0E7C4B' : pct >= 70 ? '#E67E22' : '#C62828';
            ctx.font = 'bold 11px sans-serif';
            ctx.fillText(pct + '% (' + cat.pass + '/' + cat.total + ')', lx, ly + 9);
            ctx.font = '12px -apple-system, "PingFang SC", sans-serif';
        }

        // 标题
        ctx.fillStyle = '#1A1D26';
        ctx.font = 'bold 14px -apple-system, "PingFang SC", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('预检通过率', 12, 20);
    }

    /**
     * 绘制柱状图（节点对比）
     */
    function drawBarChart(canvasId, data) {
        var canvas = document.getElementById(canvasId);
        if (!canvas) return;
        var ctx = canvas.getContext('2d');
        var W = data.width || 400;
        var H = data.height || 200;
        canvas.width = W;
        canvas.height = H;

        var bars = data.bars || [];
        if (!bars.length) {
            ctx.fillStyle = '#9ca0af';
            ctx.font = '14px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('暂无数据', W/2, H/2);
            return;
        }

        var pad = { top: 20, bottom: 30, left: 10, right: 10 };
        var chartW = W - pad.left - pad.right;
        var chartH = H - pad.top - pad.bottom;
        var barW = Math.min(chartW / bars.length * 0.6, 40);
        var gap = (chartW - barW * bars.length) / (bars.length + 1);

        ctx.clearRect(0, 0, W, H);

        // 标题
        ctx.fillStyle = '#1A1D26';
        ctx.font = 'bold 13px -apple-system, "PingFang SC", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(data.title || '节点对比', 12, 16);

        var maxVal = Math.max.apply(null, bars.map(function(b) { return b.value || 0; }));
        maxVal = Math.max(maxVal, 1);

        for (var i = 0; i < bars.length; i++) {
            var x = pad.left + gap + i * (barW + gap);
            var barH = (bars[i].value / maxVal) * chartH;
            var y = pad.top + chartH - barH;

            // 柱体
            ctx.fillStyle = bars[i].color || '#4A5FC1';
            ctx.beginPath();
            ctx.roundRect ? ctx.roundRect(x, y, barW, barH, 3) : ctx.rect(x, y, barW, barH);
            ctx.fill();

            // 标签
            ctx.fillStyle = '#6B7285';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(bars[i].label || '', x + barW/2, pad.top + chartH + 16);

            // 数值
            ctx.fillStyle = '#1A1D26';
            ctx.font = 'bold 11px sans-serif';
            ctx.fillText(bars[i].value + '', x + barW/2, y - 5);
        }
    }

    return {
        drawRadarChart: drawRadarChart,
        drawBarChart: drawBarChart
    };
})();
