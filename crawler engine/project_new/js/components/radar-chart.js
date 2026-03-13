/**
 * 雷達圖元件
 * 負責繪製五角形雷達圖
 */

// 雷達圖標籤
const LABELS = ['斑', '皺紋', '毛孔', '痘痘', '粉刺'];

/**
 * 繪製雷達圖
 * @param {string} canvasId - Canvas 元素 ID
 * @param {Object} scores - 各項分數 { spot, wrinkle, pore, acne, comedone }
 * @param {number} size - 雷達圖大小 (預設 400)
 */
export function drawRadarChart(canvasId, scores, size = 400) {
    console.log('🎨 開始繪製雷達圖:', canvasId, scores);

    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`❌ 找不到 Canvas: ${canvasId}`);
        return;
    }

    const ctx = canvas.getContext('2d');
    canvas.width = size;
    canvas.height = size;

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size * 0.35;
    const startAngle = -Math.PI / 2;

    // 轉換分數陣列
    const scoreValues = [
        scores.spot || 0,
        scores.wrinkle || 0,
        scores.pore || 0,
        scores.acne || 0,
        scores.comedone || 0
    ];

    // 清除畫布
    ctx.clearRect(0, 0, size, size);

    // 繪製背景網格
    drawBackground(ctx, centerX, centerY, radius, startAngle);

    // 繪製數據區域
    drawDataArea(ctx, centerX, centerY, radius, startAngle, scoreValues);

    // 繪製標籤
    drawLabels(ctx, centerX, centerY, radius, startAngle, size);

    // 繪製數據點
    drawDataPoints(ctx, centerX, centerY, radius, startAngle, scoreValues);

    console.log('✅ 雷達圖繪製完成');
}

/**
 * 繪製背景網格
 */
function drawBackground(ctx, centerX, centerY, radius, startAngle) {
    const levels = 5;

    for (let level = 1; level <= levels; level++) {
        ctx.beginPath();
        const levelRadius = (radius / levels) * level;

        for (let i = 0; i <= 5; i++) {
            const angle = startAngle + (Math.PI * 2 / 5) * i;
            const x = centerX + levelRadius * Math.cos(angle);
            const y = centerY + levelRadius * Math.sin(angle);

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }

        ctx.closePath();
        ctx.strokeStyle = 'rgba(0,0,0,0.1)';
        ctx.stroke();
    }

    // 繪製軸線
    for (let i = 0; i < 5; i++) {
        const angle = startAngle + (Math.PI * 2 / 5) * i;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(
            centerX + radius * Math.cos(angle),
            centerY + radius * Math.sin(angle)
        );
        ctx.strokeStyle = 'rgba(0,0,0,0.1)';
        ctx.stroke();
    }
}

/**
 * 繪製數據區域
 */
function drawDataArea(ctx, centerX, centerY, radius, startAngle, scores) {
    ctx.beginPath();

    for (let i = 0; i <= 5; i++) {
        const index = i % 5;
        const angle = startAngle + (Math.PI * 2 / 5) * i;
        const value = scores[index] / 5;  // 1-5 分制
        const x = centerX + radius * value * Math.cos(angle);
        const y = centerY + radius * value * Math.sin(angle);

        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }

    ctx.closePath();
    ctx.fillStyle = 'rgba(212, 165, 116, 0.3)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(212, 165, 116, 0.8)';
    ctx.lineWidth = 2;
    ctx.stroke();
}

/**
 * 繪製標籤
 */
function drawLabels(ctx, centerX, centerY, radius, startAngle, size) {
    ctx.fillStyle = '#333';
    ctx.font = `${size * 0.035}px "PingFang TC", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let i = 0; i < 5; i++) {
        const angle = startAngle + (Math.PI * 2 / 5) * i;
        const labelRadius = radius * 1.15;
        const x = centerX + labelRadius * Math.cos(angle);
        const y = centerY + labelRadius * Math.sin(angle);

        ctx.fillText(LABELS[i], x, y);
    }
}

/**
 * 繪製數據點
 */
function drawDataPoints(ctx, centerX, centerY, radius, startAngle, scores) {
    for (let i = 0; i < 5; i++) {
        const angle = startAngle + (Math.PI * 2 / 5) * i;
        const value = scores[i] / 5;  // 1-5 分制
        const x = centerX + radius * value * Math.cos(angle);
        const y = centerY + radius * value * Math.sin(angle);

        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(212, 165, 116, 1)';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}
