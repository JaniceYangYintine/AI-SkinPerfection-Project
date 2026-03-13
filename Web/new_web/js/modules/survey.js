/**
 * 問卷模組
 * 處理問卷顯示、答案收集、進度管理
 */

import { CONFIG, SURVEY_QUESTIONS } from '../config.js';

// 模組狀態
let currentQuestion = 0;
let answers = {};
let onProgressChange = null;
let onComplete = null;

/**
 * 初始化問卷模組
 * @param {Object} callbacks - 回調函數
 * @param {Function} callbacks.onProgressChange - 進度變化回調
 * @param {Function} callbacks.onComplete - 完成回調
 */
export function initSurvey(callbacks = {}) {
    onProgressChange = callbacks.onProgressChange || null;
    onComplete = callbacks.onComplete || null;

    // 從 localStorage 載入暫存答案
    loadSavedAnswers();

    return {
        totalQuestions: SURVEY_QUESTIONS.length,
        currentQuestion,
        answers
    };
}

/**
 * 載入暫存答案
 */
function loadSavedAnswers() {
    try {
        const saved = localStorage.getItem(CONFIG.STORAGE_KEYS.ANSWERS);
        if (saved) {
            answers = JSON.parse(saved);
            // 找到最後回答的題目
            const answeredIds = Object.keys(answers);
            if (answeredIds.length > 0) {
                const lastAnsweredIndex = SURVEY_QUESTIONS.findIndex(
                    q => q.id === answeredIds[answeredIds.length - 1]
                );
                currentQuestion = Math.min(lastAnsweredIndex + 1, SURVEY_QUESTIONS.length - 1);
            }
        }
    } catch (e) {
        console.error('loadSavedAnswers error:', e);
        answers = {};
    }
}

/**
 * 儲存答案到 localStorage
 */
function saveAnswers() {
    try {
        localStorage.setItem(CONFIG.STORAGE_KEYS.ANSWERS, JSON.stringify(answers));
    } catch (e) {
        console.error('saveAnswers error:', e);
    }
}

/**
 * 取得目前題目
 * @returns {Object} 題目物件
 */
export function getCurrentQuestion() {
    return SURVEY_QUESTIONS[currentQuestion];
}

/**
 * 取得所有題目
 * @returns {Array} 題目陣列
 */
export function getAllQuestions() {
    return SURVEY_QUESTIONS;
}

/**
 * 取得進度資訊
 * @returns {Object} 進度資訊
 */
export function getProgress() {
    return {
        current: currentQuestion + 1,
        total: SURVEY_QUESTIONS.length,
        percentage: ((currentQuestion + 1) / SURVEY_QUESTIONS.length) * 100
    };
}

/**
 * 選擇答案
 * @param {string} questionId - 題目 ID
 * @param {string} value - 答案值
 */
export function selectAnswer(questionId, value) {
    answers[questionId] = value;
    saveAnswers();
}

/**
 * 取得某題的答案
 * @param {string} questionId - 題目 ID
 * @returns {string|null} 答案值
 */
export function getAnswer(questionId) {
    return answers[questionId] || null;
}

/**
 * 取得所有答案
 * @returns {Object} 所有答案
 */
export function getAllAnswers() {
    return { ...answers };
}

/**
 * 檢查目前題目是否已回答
 * @returns {boolean}
 */
export function isCurrentAnswered() {
    const question = getCurrentQuestion();
    return !!answers[question.id];
}

/**
 * 前往下一題
 * @returns {Object} 結果 {success, isComplete, question}
 */
export function nextQuestion() {
    if (!isCurrentAnswered()) {
        return { success: false, error: '請先選擇答案' };
    }

    if (currentQuestion >= SURVEY_QUESTIONS.length - 1) {
        // 已是最後一題，問卷完成
        if (onComplete) {
            onComplete(answers);
        }
        return { success: true, isComplete: true, answers };
    }

    currentQuestion++;
    notifyProgress();

    return {
        success: true,
        isComplete: false,
        question: getCurrentQuestion()
    };
}

/**
 * 前往上一題
 * @returns {Object} 結果 {success, question}
 */
export function prevQuestion() {
    if (currentQuestion <= 0) {
        return { success: false, error: '已是第一題' };
    }

    currentQuestion--;
    notifyProgress();

    return {
        success: true,
        question: getCurrentQuestion()
    };
}

/**
 * 跳到指定題目
 * @param {number} index - 題目索引
 * @returns {Object} 結果
 */
export function goToQuestion(index) {
    if (index < 0 || index >= SURVEY_QUESTIONS.length) {
        return { success: false, error: '無效的題目索引' };
    }

    currentQuestion = index;
    notifyProgress();

    return {
        success: true,
        question: getCurrentQuestion()
    };
}

/**
 * 通知進度變化
 */
function notifyProgress() {
    if (onProgressChange) {
        onProgressChange(getProgress());
    }
}

/**
 * 檢查問卷是否完成
 * @returns {boolean}
 */
export function isComplete() {
    return SURVEY_QUESTIONS.every(q => !!answers[q.id]);
}

/**
 * 重置問卷
 */
export function resetSurvey() {
    currentQuestion = 0;
    answers = {};
    localStorage.removeItem(CONFIG.STORAGE_KEYS.ANSWERS);
    notifyProgress();
}

/**
 * 驗證所有答案
 * @returns {{valid: boolean, missing: string[]}}
 */
export function validateAnswers() {
    const missing = SURVEY_QUESTIONS
        .filter(q => !answers[q.id])
        .map(q => q.title);

    return {
        valid: missing.length === 0,
        missing
    };
}

/**
 * 渲染問卷 HTML
 * @param {HTMLElement} container - 容器元素
 */
export function renderSurvey(container) {
    const question = getCurrentQuestion();
    const progress = getProgress();
    const selectedAnswer = getAnswer(question.id);

    container.innerHTML = `
        <div class="survey-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress.percentage}%"></div>
            </div>
            <div class="progress-text">第 ${progress.current}/${progress.total} 題</div>
        </div>

        <div class="question-container">
            <h2 class="question-title">${question.title}</h2>
            <div class="options-list">
                ${question.options.map(opt => `
                    <label class="option ${selectedAnswer === opt.value ? 'selected' : ''}">
                        <input
                            type="radio"
                            name="${question.id}"
                            value="${opt.value}"
                            ${selectedAnswer === opt.value ? 'checked' : ''}
                        >
                        <span class="option-label">${opt.label}</span>
                    </label>
                `).join('')}
            </div>
        </div>

        <div class="nav-buttons">
            <button
                type="button"
                class="btn btn-secondary"
                id="prevBtn"
                ${currentQuestion === 0 ? 'disabled style="visibility:hidden"' : ''}
            >
                上一題
            </button>
            <button
                type="button"
                class="btn btn-primary"
                id="nextBtn"
            >
                ${currentQuestion === SURVEY_QUESTIONS.length - 1 ? '完成問卷' : '下一題'}
            </button>
        </div>
    `;

    // 綁定事件
    bindSurveyEvents(container);
}

/**
 * 綁定問卷事件
 * @param {HTMLElement} container - 容器元素
 */
function bindSurveyEvents(container) {
    // 選項點擊
    const options = container.querySelectorAll('.option input');
    options.forEach(input => {
        input.addEventListener('change', (e) => {
            const question = getCurrentQuestion();
            selectAnswer(question.id, e.target.value);

            // 更新選中狀態
            container.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
            e.target.closest('.option').classList.add('selected');

            // 自動跳下一題
            setTimeout(() => {
                const result = nextQuestion();
                if (!result.isComplete) {
                    renderSurvey(container);
                }
            }, CONFIG.SURVEY.AUTO_ADVANCE_DELAY);
        });
    });

    // 上一題按鈕
    const prevBtn = container.querySelector('#prevBtn');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            prevQuestion();
            renderSurvey(container);
        });
    }

    // 下一題按鈕
    const nextBtn = container.querySelector('#nextBtn');
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (!isCurrentAnswered()) {
                alert('請選擇一個選項');
                return;
            }

            const result = nextQuestion();
            if (result.isComplete) {
                // 問卷完成，由外部處理
            } else {
                renderSurvey(container);
            }
        });
    }
}
