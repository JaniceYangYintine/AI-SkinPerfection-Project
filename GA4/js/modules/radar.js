/**
 * 雷達圖模組
 * 使用 Canvas 繪製五角雷達圖
 */

import { CONFIG } from '../config.js';

/**
 * 繪製雷達圖
 * @param {HTMLCanvasElement} canvas - Canvas 元素
 * @param {Object} scores - 分數物件 { acne, comedone, darkCircle, spot, wrinkle }
 * @param {Object} options - 可選設定
 */
export function drawRadarChart(canvas, scores, options = {}) {
    const ctx = canvas.getContext('2d');
    const config = { ...CONFIG.RADAR, ...options };

    // 設定 Canvas 大小
    const size = config.SIZE;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    // 清除畫布
    ctx.clearRect(0, 0, size, size);

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size * 0.35; // 圖表半徑
    const dimensions = config.DIMENSIONS;
    const labels = config.LABELS;
    const maxValue = config.MAX_VALUE;
    const angleStep = (Math.PI * 2) / dimensions.length;
    const startAngle = -Math.PI / 2; // 從頂部開始

    // 繪製網格
    drawGrid(ctx, centerX, centerY, radius, dimensions.length, angleStep, startAngle, config);

    // 繪製標籤
    drawLabels(ctx, centerX, centerY, radius, labels, angleStep, startAngle, config);

    // 繪製數據
    drawData(ctx, centerX, centerY, radius, scores, dimensions, maxValue, angleStep, startAngle, config);
}

/**
 * 繪製網格
 */
function drawGrid(ctx, centerX, centerY, radius, sides, angleStep, startAngle, config) {
    const levels = 5; // 網格層數

    ctx.strokeStyle = config.COLORS.GRID;
    ctx.lineWidth = 1;

    // 繪製同心多邊形
    for (let level = 1; level <= levels; level++) {
        const levelRadius = (radius / levels) * level;

        ctx.beginPath();
        for (let i = 0; i <= sides; i++) {
            const angle = startAngle + angleStep * i;
            const x = centerX + Math.cos(angle) * levelRadius;
            const y = centerY + Math.sin(angle) * levelRadius;

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();
        ctx.stroke();
    }

    // 繪製軸線
    for (let i = 0; i < sides; i++) {
        const angle = startAngle + angleStep * i;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;

        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.stroke();
    }
}

/**
 * 繪製標籤
 */
function drawLabels(ctx, centerX, centerY, radius, labels, angleStep, startAngle, config) {
    ctx.fillStyle = config.COLORS.TEXT;
    ctx.font = '14px "Noto Sans TC", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const labelOffset = radius + 25; // 標籤距離中心的距離

    labels.forEach((label, i) => {
        const angle = startAngle + angleStep * i;
        let x = centerX + Math.cos(angle) * labelOffset;
        let y = centerY + Math.sin(angle) * labelOffset;

        // 微調位置
        if (Math.abs(Math.cos(angle)) < 0.1) {
            // 頂部或底部
            y += Math.sin(angle) > 0 ? 5 : -5;
        } else {
            // 左側或右側
            x += Math.cos(angle) > 0 ? 5 : -5;
        }

        ctx.fillText(label, x, y);
    });
}

/**
 * 繪製數據區域
 */
function drawData(ctx, centerX, centerY, radius, scores, dimensions, maxValue, angleStep, startAngle, config, animationProgress = 1) {
    const points = [];

    // 計算各點座標
    dimensions.forEach((dim, i) => {
        const value = scores[dim] || 0;
        const normalizedValue = Math.min(value / maxValue, 1) * animationProgress;
        const angle = startAngle + angleStep * i;
        const x = centerX + Math.cos(angle) * radius * normalizedValue;
        const y = centerY + Math.sin(angle) * radius * normalizedValue;
        points.push({ x, y, value });
    });

    // 繪製填充區域
    ctx.beginPath();
    points.forEach((point, i) => {
        if (i === 0) {
            ctx.moveTo(point.x, point.y);
        } else {
            ctx.lineTo(point.x, point.y);
        }
    });
    ctx.closePath();
    ctx.fillStyle = config.COLORS.FILL;
    ctx.fill();

    // 繪製邊框
    ctx.strokeStyle = config.COLORS.STROKE;
    ctx.lineWidth = 2;
    ctx.stroke();

    // 繪製數據點
    points.forEach(point => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = config.COLORS.STROKE;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
    });
}

/**
 * 繪製帶數值的雷達圖
 * @param {HTMLCanvasElement} canvas - Canvas 元素
 * @param {Object} scores - 分數物件
 * @param {Object} options - 可選設定
 */
export function drawRadarChartWithValues(canvas, scores, options = {}) {
    drawRadarChart(canvas, scores, options);

    const ctx = canvas.getContext('2d');
    const config = { ...CONFIG.RADAR, ...options };
    const size = config.SIZE;
    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size * 0.35;
    const dimensions = config.DIMENSIONS;
    const maxValue = config.MAX_VALUE;
    const angleStep = (Math.PI * 2) / dimensions.length;
    const startAngle = -Math.PI / 2;

    // 繪製數值標籤
    ctx.fillStyle = config.COLORS.STROKE;
    ctx.font = 'bold 12px "Noto Sans TC", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    dimensions.forEach((dim, i) => {
        const value = scores[dim] || 0;
        const normalizedValue = Math.min(value / maxValue, 1);
        const angle = startAngle + angleStep * i;
        const x = centerX + Math.cos(angle) * radius * normalizedValue;
        const y = centerY + Math.sin(angle) * radius * normalizedValue;

        // 數值標籤偏移
        const offsetX = Math.cos(angle) * 20;
        const offsetY = Math.sin(angle) * 20;

        ctx.fillText(value.toFixed(1), x + offsetX, y + offsetY);
    });
}

/**
 * 建立雷達圖容器
 * @param {Object} scores - 分數物件
 * @returns {HTMLElement} 容器元素
 */
export function createRadarChartElement(scores) {
    const container = document.createElement('div');
    container.className = 'radar-chart-container';

    const canvas = document.createElement('canvas');
    canvas.className = 'radar-chart';

    container.appendChild(canvas);

    // 延遲繪製，確保 DOM 已渲染
    requestAnimationFrame(() => {
        drawRadarChartWithValues(canvas, scores);
    });

    return container;
}

/**
 * 更新雷達圖
 * @param {HTMLCanvasElement} canvas - Canvas 元素
 * @param {Object} newScores - 新的分數物件
 * @param {boolean} animate - 是否動畫
 */
export function updateRadarChart(canvas, newScores, animate = true) {
    if (!animate) {
        drawRadarChartWithValues(canvas, newScores);
        return;
    }

    // 簡單的淡入動畫
    canvas.style.opacity = '0';
    canvas.style.transition = 'opacity 0.3s ease';

    setTimeout(() => {
        drawRadarChartWithValues(canvas, newScores);
        canvas.style.opacity = '1';
    }, 150);
}

/**
 * 繪製帶動畫的雷達圖
 * @param {HTMLCanvasElement} canvas - Canvas 元素
 * @param {Object} scores - 分數物件
 * @param {Object} options - 可選設定
 */
export function drawRadarChartAnimated(canvas, scores, options = {}) {
    const duration = 1000;
    const startTime = Date.now();
    const animatedScores = {};
    const dimensions = CONFIG.RADAR.DIMENSIONS;

    function animate() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3);

        dimensions.forEach(dim => {
            animatedScores[dim] = (scores[dim] || 0) * easeProgress;
        });

        drawRadarChartWithValues(canvas, animatedScores, options);

        if (progress < 1) {
            requestAnimationFrame(animate);
        }
    }
    animate();
}
