/**
 * 問卷答案映射模組
 * ======================================================
 * 將前端問卷答案（英文 value）轉換為 n8n 所需的中文標籤
 */

/**
 * 英文 value → 中文標籤 映射表
 * key: config.js 中的問卷 ID
 * value: { 英文value: 中文標籤 }
 */
export const VALUE_TO_TAG = {
    // Q1: 年齡區間
    age: {
        'under20': '20以下',
        '20-30': '20-30',
        '30-40': '30-40',
        'over40': '40以上'
    },
    // Q2: 膚質類型
    skinCondition: {
        'dry': '乾性肌',
        'oily': '油性肌',
        'combo': '混合肌',
        'comfortable': '中性肌'
    },
    // Q3: 敏感程度
    sensitivity: {
        'high': '敏感肌',
        'medium': '輕度敏感',
        'low': '不敏感'
    },
    // Q4: 保養節奏
    rhythm: {
        'complete': '保養節奏：早晚保養',
        'single': '保養節奏：單次保養',
        'random': '保養節奏：隨性保養'
    },
    // Q5: 睡眠時數
    sleepHours: {
        'less6': '睡眠時數：少於6小時',
        '6-7': '睡眠時數：6-7小時',
        '7-8': '睡眠時數：7-8小時',
        'over8': '睡眠時數：超過8小時'
    },
    // Q6: 壓力程度
    stress: {
        'none': '壓力程度：低壓力',
        'sometimes': '壓力程度：中度壓力',
        'often': '壓力程度：高壓力'
    },
    // Q7: 運動頻率
    exercise: {
        '0': '運動頻率：無運動',
        '1-2': '運動頻率：每週1-2次',
        '3-4': '運動頻率：每週3-4次',
        '5-7': '運動頻率：每週5-7次'
    },
    // Q8: 油炸食物頻率
    friedFood: {
        '0-1': '油炸食物頻率：很少',
        '2-3': '油炸食物頻率：偶爾',
        '4-5': '油炸食物頻率：經常',
        '6over': '油炸食物頻率：頻繁'
    },
    // Q9: 蔬果攝取量
    diet: {
        'balanced': '蔬果攝取量：每天3份以上',
        'low': '蔬果攝取量：每天1-2份',
        'none': '蔬果攝取量：很少'
    }
};

/**
 * 將前端問卷答案轉換為 n8n 所需的中文格式
 * @param {Object} answers - { age: "20-30", skinCondition: "oily", ... }
 * @returns {Object} { age: "20-30", skinCondition: "油性肌", ... }
 */
export function convertToChineseTags(answers) {
    const result = {};

    for (const [questionId, value] of Object.entries(answers)) {
        const mapping = VALUE_TO_TAG[questionId];
        result[questionId] = mapping?.[value] ?? value;
    }

    return result;
}

const ANSWER_TAG_ORDER = [
    { id: 'age', key: 'answer1_tag', prefix: '' },
    { id: 'skinCondition', key: 'answer2_tag', prefix: '' },
    { id: 'sensitivity', key: 'answer3_tag', prefix: '' },
    { id: 'rhythm', key: 'answer4_tag', prefix: '保養節奏：' },
    { id: 'sleepHours', key: 'answer5_tag', prefix: '睡眠時數：' },
    { id: 'stress', key: 'answer6_tag', prefix: '壓力程度：' },
    { id: 'exercise', key: 'answer7_tag', prefix: '運動頻率：' },
    { id: 'friedFood', key: 'answer8_tag', prefix: '油炸食物頻率：' },
    { id: 'diet', key: 'answer9_tag', prefix: '蔬果攝取量：' }
];

function applyPrefix(value, prefix) {
    if (!value) return '';
    if (!prefix) return value;
    if (value.startsWith(prefix)) return value;
    return `${prefix}${value}`;
}

/**
 * 將前端問卷答案轉為 DB 所需的 answer1_tag ~ answer9_tag
 * @param {Object} answers - { age: "20-30", skinCondition: "combo", ... }
 * @returns {Object} { answer1_tag: "20-30", answer2_tag: "混合肌", ... }
 */
export function convertToAnswerTags(answers) {
    const chinese = convertToChineseTags(answers);
    const tags = {};

    for (const item of ANSWER_TAG_ORDER) {
        tags[item.key] = applyPrefix(chinese[item.id], item.prefix);
    }

    return tags;
}
