/**
 * C 區模組 - 生活建議
 * 負責渲染營養、作息、生活習慣建議
 */

/**
 * 載入 C 區資料
 * @param {Object} result - 分析結果
 */
export function loadSectionC(result) {
    console.log('🚀 loadSectionC 開始執行...');

    const lifestyle = result?.c_lifestyle_advice || result?.lifestyle_advice;

    if (!lifestyle) {
        console.warn('⚠️ 沒有生活建議資料');
        return;
    }

    // 渲染營養建議
    if (lifestyle.nutrition) {
        renderNutrition(lifestyle.nutrition);
    }

    // 渲染作息建議
    if (lifestyle.sleep) {
        renderSleep(lifestyle.sleep);
    }

    // 渲染生活習慣
    if (lifestyle.exercise) {
        renderExercise(lifestyle.exercise);
    }

    console.log('✅ loadSectionC 執行完成');
}

/**
 * 渲染營養建議
 * @param {Object} nutrition - 營養建議資料
 */
function renderNutrition(nutrition) {
    const summaryEl = document.getElementById('nutrition-summary');
    const detailEl = document.getElementById('nutrition-detail');
    const itemsEl = document.getElementById('nutrition-items');

    if (summaryEl && nutrition.summary) {
        summaryEl.textContent = nutrition.summary;
    }

    if (detailEl && nutrition.detail) {
        detailEl.textContent = nutrition.detail;
    }

    if (itemsEl && nutrition.items?.length > 0) {
        itemsEl.innerHTML = nutrition.items.map(item =>
            `<li>${item}</li>`
        ).join('');
    }
}

/**
 * 渲染作息建議
 * @param {Object} sleep - 作息建議資料
 */
function renderSleep(sleep) {
    const summaryEl = document.getElementById('sleep-summary');
    const detailEl = document.getElementById('sleep-detail');

    if (summaryEl && sleep.summary) {
        summaryEl.textContent = sleep.summary;
    }

    if (detailEl && sleep.detail) {
        detailEl.textContent = sleep.detail;
    }
}

/**
 * 渲染生活習慣建議
 * @param {Object} exercise - 生活習慣資料
 */
function renderExercise(exercise) {
    const summaryEl = document.getElementById('exercise-summary');
    const detailEl = document.getElementById('exercise-detail');

    if (summaryEl && exercise.summary) {
        summaryEl.textContent = exercise.summary;
    }

    if (detailEl && exercise.detail) {
        detailEl.textContent = exercise.detail;
    }
}
