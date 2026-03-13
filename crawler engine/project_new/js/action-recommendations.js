/**
 * 行動推薦管理模組
 * 用於載入和顯示 LLM 偵測後的行動建議
 */

class ActionRecommendationManager {
  constructor() {
    this.actionsData = null;
    this.initialized = false;
  }

  /**
   * 初始化：載入行動推薦資料
   */
  async init() {
    try {
      const response = await fetch('./data/action-recommendations.json');
      if (!response.ok) {
        throw new Error('Failed to load action recommendations data');
      }
      this.actionsData = await response.json();
      this.initialized = true;
      console.log('✅ Action recommendations loaded successfully');
      return true;
    } catch (error) {
      console.error('❌ Error loading action recommendations:', error);
      return false;
    }
  }

  /**
   * 根據 LLM 偵測結果顯示行動推薦
   * @param {Array<number>} detectedIssues - LLM 偵測到的問題 ID 陣列，例如 [1, 3, 5]
   * @param {string} containerSelector - 要顯示內容的容器選擇器
   * @param {string} summary - LLM 生成的總評文字（可選）
   */
  displayRecommendations(detectedIssues, containerSelector, summary = '') {
    if (!this.initialized) {
      console.error('❌ ActionRecommendationManager not initialized. Call init() first.');
      return;
    }

    const container = document.querySelector(containerSelector);
    if (!container) {
      console.error(`❌ Container not found: ${containerSelector}`);
      return;
    }

    // 清空容器
    container.innerHTML = '';

    // 建立 A 區結構
    const sectionA = document.createElement('div');
    sectionA.className = 'section-a-recommendations';
    sectionA.innerHTML = `
      <div class="recommendations-header">
        <h2>📊 肌膚分析總評</h2>
      </div>
      ${summary ? `<div class="summary-text">${summary}</div>` : ''}
      <div class="detected-issues">
        <h3>🔍 偵測到的問題</h3>
        <div class="issues-list"></div>
      </div>
      <div class="action-cards"></div>
    `;

    container.appendChild(sectionA);

    // 顯示偵測到的問題列表
    const issuesList = sectionA.querySelector('.issues-list');
    detectedIssues.forEach(issueId => {
      const action = this.actionsData.actions[issueId];
      if (action) {
        const issueTag = document.createElement('span');
        issueTag.className = 'issue-tag';
        issueTag.textContent = action.targetIssue;
        issuesList.appendChild(issueTag);
      }
    });

    // 顯示行動推薦卡片
    const actionCardsContainer = sectionA.querySelector('.action-cards');
    detectedIssues.forEach(issueId => {
      const action = this.actionsData.actions[issueId];
      if (action) {
        const card = this.createActionCard(action);
        actionCardsContainer.appendChild(card);
      }
    });
  }

  /**
   * 建立單個行動推薦卡片
   * @param {Object} action - 行動資料物件
   * @returns {HTMLElement} 卡片元素
   */
  createActionCard(action) {
    const card = document.createElement('div');
    card.className = 'action-card';
    card.setAttribute('data-action-id', action.id);

    // 判斷媒體類型
    const mediaElement = action.mediaType === 'video'
      ? `<video class="action-media" controls loop muted playsinline>
           <source src="${action.mediaUrl}" type="video/mp4">
           您的瀏覽器不支援影片播放。
         </video>`
      : `<img class="action-media" src="${action.mediaUrl}" alt="${action.targetIssue}">`;

    card.innerHTML = `
      <div class="card-header">
        <span class="issue-badge">${action.targetIssue}</span>
      </div>
      <div class="card-media">
        ${mediaElement}
      </div>
      <div class="card-content">
        <h4 class="action-title">💡 行動建議</h4>
        <p class="action-description">${action.actionName}</p>
        <div class="effect-section">
          <h5 class="effect-title">✨ 預期效果</h5>
          <p class="effect-description">${action.description}</p>
        </div>
      </div>
    `;

    return card;
  }

  /**
   * 取得單個行動資料
   * @param {number} actionId - 行動 ID
   * @returns {Object|null} 行動資料物件
   */
  getAction(actionId) {
    if (!this.initialized) {
      console.error('❌ ActionRecommendationManager not initialized.');
      return null;
    }
    return this.actionsData.actions[actionId] || null;
  }

  /**
   * 取得所有行動資料
   * @returns {Object|null} 所有行動資料
   */
  getAllActions() {
    if (!this.initialized) {
      console.error('❌ ActionRecommendationManager not initialized.');
      return null;
    }
    return this.actionsData.actions;
  }
}

// 建立全域實例
const actionRecommendationManager = new ActionRecommendationManager();

// 匯出供其他模組使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ActionRecommendationManager;
}
