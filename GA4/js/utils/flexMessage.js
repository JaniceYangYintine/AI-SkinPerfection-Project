/**
 * LINE Flex Message 建構工具
 * 負責生成各種類型的 Flex Message JSON
 */

/**
 * 建立分析報告的 Flex Message
 * @param {Object} data - 分析結果資料
 * @returns {Object} Flex Message JSON
 */
export function buildAnalysisFlexMessage(data) {
    const topIssues = data.sectionB?.topIssues?.slice(0, 2) || [];
    const suggestions = data.sectionC?.suggestions?.slice(0, 3) || [];
    const ingredients = data.sectionD?.ingredients?.slice(0, 5) || [];
    const massages = data.sectionA?.massages?.slice(0, 2) || [];

    // 建立內容陣列
    const contents = [
        // 標題
        { type: 'text', text: 'AI 肌膚分析報告', weight: 'bold', size: 'xl', color: '#1DB446' },
        { type: 'separator', margin: 'lg' },

        // A 區：活力氣色分數
        { type: 'text', text: `活力氣色分數：${data.sectionA?.score || 0} 分`, margin: 'lg', size: 'md', weight: 'bold', color: '#333333' }
    ];

    // A 區：推薦按摩動作
    if (massages.length > 0) {
        contents.push({ type: 'text', text: '推薦按摩動作', margin: 'lg', weight: 'bold', color: '#666666', size: 'sm' });
        massages.forEach((massage, idx) => {
            contents.push({
                type: 'text',
                text: `${idx + 1}. ${massage.name || ''}`,
                margin: 'sm',
                size: 'sm',
                color: '#999999'
            });
        });
    }

    // B 區：主要問題
    if (topIssues.length > 0) {
        contents.push({ type: 'text', text: '主要問題', margin: 'lg', weight: 'bold', color: '#666666', size: 'sm' });
        topIssues.forEach((issue, idx) => {
            contents.push({
                type: 'text',
                text: `${idx + 1}. ${issue.name || ''}`,
                margin: 'sm',
                size: 'sm',
                color: '#999999'
            });
        });
    }

    // C 區：飲食建議 (顯示食物)
    if (suggestions.length > 0) {
        contents.push({ type: 'text', text: '飲食建議', margin: 'lg', weight: 'bold', color: '#666666', size: 'sm' });
        suggestions.forEach((suggestion, idx) => {
            // 顯示建議標題
            contents.push({
                type: 'text',
                text: `${idx + 1}. ${suggestion.title || ''}`,
                margin: 'sm',
                size: 'sm',
                color: '#999999',
                weight: 'bold'
            });
            // 顯示食物/成分
            if (suggestion.ingredients && suggestion.ingredients.length > 0) {
                const foodList = suggestion.ingredients.join('、');
                contents.push({
                    type: 'text',
                    text: `   推薦：${foodList}`,
                    margin: 'xs',
                    size: 'xs',
                    color: '#AAAAAA',
                    wrap: true
                });
            }
        });
    }

    // D 區：推薦成分
    if (ingredients.length > 0) {
        contents.push({ type: 'text', text: '推薦保養成分', margin: 'lg', weight: 'bold', color: '#666666', size: 'sm' });
        const ingredientNames = ingredients.map(i => i.name).join('、');
        contents.push({
            type: 'text',
            text: ingredientNames,
            margin: 'sm',
            size: 'sm',
            color: '#999999',
            wrap: true
        });
    }

    return {
        type: 'flex',
        altText: 'AI 肌膚分析報告',
        contents: {
            type: 'bubble',
            hero: {
                type: 'image',
                url: data.sectionA?.photoUrl || 'https://via.placeholder.com/800x400',
                size: 'full',
                aspectRatio: '20:13',
                aspectMode: 'cover'
            },
            body: {
                type: 'box',
                layout: 'vertical',
                contents: contents
            }
        }
    };
}
