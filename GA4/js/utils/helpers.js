/**
 * 通用工具函數
 * ======================================================
 * 提供可重用的 DOM 操作、動畫、驗證等工具
 * 更新：2026-02-01
 */

/**
 * 初始化通用輪播元件
 * @param {HTMLElement} container - 輪播容器元素
 * @param {Object} options - 設定選項
 * @param {string} options.trackSelector - 軌道選擇器
 * @param {string} options.itemSelector - 項目選擇器
 * @param {string} options.indicatorSelector - 指示器選擇器
 * @param {number} options.gap - 項目間距 (預設 16)
 * @returns {Object} 輪播控制 API
 */
export function initCarousel(container, options = {}) {
    if (!container) {
        console.warn('[Carousel] 找不到輪播容器');
        return null;
    }

    const {
        trackSelector = '.carousel-track',
        itemSelector = '.carousel-item',
        indicatorSelector = '.indicator-dot',
        gap = 16
    } = options;

    const track = container.querySelector(trackSelector);
    const items = track?.querySelectorAll(itemSelector) || [];
    const dots = container.parentElement?.querySelectorAll(indicatorSelector) || [];

    if (items.length === 0) {
        return null;
    }

    let currentIndex = 0;
    let scrollTimeout = null;
    let isMouseDown = false;
    let startX = 0;
    let scrollLeftPos = 0;

    // 更新指示器
    const updateIndicator = (index) => {
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });
    };

    // 滾動事件處理
    const handleScroll = () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            if (items.length === 0) return;
            const scrollLeft = container.scrollLeft;
            const itemWidth = items[0].offsetWidth + gap;
            currentIndex = Math.round(scrollLeft / itemWidth);
            updateIndicator(currentIndex);
        }, 100);
    };

    // 滑鼠拖曳 - 開始
    const handleMouseDown = (e) => {
        isMouseDown = true;
        container.style.cursor = 'grabbing';
        startX = e.pageX - container.offsetLeft;
        scrollLeftPos = container.scrollLeft;
    };

    // 滑鼠拖曳 - 離開/放開
    const handleMouseUp = () => {
        isMouseDown = false;
        container.style.cursor = 'grab';
    };

    // 滑鼠拖曳 - 移動
    const handleMouseMove = (e) => {
        if (!isMouseDown) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const walk = (x - startX) * 2;
        container.scrollLeft = scrollLeftPos - walk;
    };

    // 綁定事件
    container.addEventListener('scroll', handleScroll, { passive: true });
    container.addEventListener('mousedown', handleMouseDown);
    container.addEventListener('mouseleave', handleMouseUp);
    container.addEventListener('mouseup', handleMouseUp);
    container.addEventListener('mousemove', handleMouseMove);

    // 設定初始樣式
    container.style.cursor = 'grab';

    // 返回控制 API
    return {
        /** 跳轉到指定索引 */
        goTo: (index) => {
            if (index < 0 || index >= items.length) return;
            const itemWidth = items[0].offsetWidth + gap;
            container.scrollTo({
                left: index * itemWidth,
                behavior: 'smooth'
            });
            currentIndex = index;
            updateIndicator(index);
        },
        /** 下一個 */
        next: () => {
            const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
            this.goTo(nextIndex);
        },
        /** 上一個 */
        prev: () => {
            const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
            this.goTo(prevIndex);
        },
        /** 取得目前索引 */
        getCurrentIndex: () => currentIndex,
        /** 銷毀輪播（清理事件監聽） */
        destroy: () => {
            container.removeEventListener('scroll', handleScroll);
            container.removeEventListener('mousedown', handleMouseDown);
            container.removeEventListener('mouseleave', handleMouseUp);
            container.removeEventListener('mouseup', handleMouseUp);
            container.removeEventListener('mousemove', handleMouseMove);
        }
    };
}

/**
 * 防抖函數
 * @param {Function} func - 要執行的函數
 * @param {number} wait - 等待時間 (ms)
 * @returns {Function} 防抖後的函數
 */
export function debounce(func, wait = 100) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 節流函數
 * @param {Function} func - 要執行的函數
 * @param {number} limit - 限制時間 (ms)
 * @returns {Function} 節流後的函數
 */
export function throttle(func, limit = 100) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => (inThrottle = false), limit);
        }
    };
}

/**
 * 安全取得物件屬性（避免 undefined 錯誤）
 * @param {Object} obj - 物件
 * @param {string} path - 屬性路徑，如 'a.b.c'
 * @param {*} defaultValue - 預設值
 * @returns {*} 屬性值或預設值
 */
export function get(obj, path, defaultValue = undefined) {
    const keys = path.split('.');
    let result = obj;

    for (const key of keys) {
        if (result === null || result === undefined) {
            return defaultValue;
        }
        result = result[key];
    }

    return result === undefined ? defaultValue : result;
}

/**
 * 格式化數字（加上千分位）
 * @param {number} num - 數字
 * @returns {string} 格式化後的字串
 */
export function formatNumber(num) {
    if (typeof num !== 'number') return '0';
    return num.toLocaleString('zh-TW');
}

/**
 * 產生 SVG 圖示 HTML
 * @param {string} iconPath - 圖示路徑
 * @param {Object} options - 選項
 * @param {number} options.size - 尺寸 (預設 24)
 * @param {string} options.className - CSS class
 * @param {string} options.ariaLabel - 無障礙標籤
 * @returns {string} HTML 字串
 */
export function renderIcon(iconPath, options = {}) {
    const { size = 24, className = 'icon', ariaLabel = '' } = options;

    if (ariaLabel) {
        return `<img src="${iconPath}" alt="${ariaLabel}" class="${className}" width="${size}" height="${size}" role="img">`;
    }

    return `<img src="${iconPath}" alt="" class="${className}" aria-hidden="true" width="${size}" height="${size}">`;
}

/**
 * 建立 DOM 元素
 * @param {string} tag - HTML 標籤
 * @param {Object} attrs - 屬性
 * @param {string|HTMLElement|Array} children - 子元素
 * @returns {HTMLElement}
 */
export function createElement(tag, attrs = {}, children = null) {
    const el = document.createElement(tag);

    // 設定屬性
    Object.entries(attrs).forEach(([key, value]) => {
        if (key === 'className') {
            el.className = value;
        } else if (key === 'dataset') {
            Object.entries(value).forEach(([dataKey, dataValue]) => {
                el.dataset[dataKey] = dataValue;
            });
        } else if (key.startsWith('on') && typeof value === 'function') {
            const eventName = key.slice(2).toLowerCase();
            el.addEventListener(eventName, value);
        } else {
            el.setAttribute(key, value);
        }
    });

    // 加入子元素
    if (children) {
        if (typeof children === 'string') {
            el.innerHTML = children;
        } else if (Array.isArray(children)) {
            children.forEach(child => {
                if (typeof child === 'string') {
                    el.appendChild(document.createTextNode(child));
                } else if (child instanceof HTMLElement) {
                    el.appendChild(child);
                }
            });
        } else if (children instanceof HTMLElement) {
            el.appendChild(children);
        }
    }

    return el;
}

/**
 * 顯示 Toast 提示（取代 alert）
 * @param {string} message - 訊息
 * @param {Object} options - 選項
 * @param {string} options.type - 類型：'info' | 'success' | 'warning' | 'error'
 * @param {number} options.duration - 顯示時間 (ms)
 */
export function showToast(message, options = {}) {
    const { type = 'info', duration = 3000 } = options;

    // 移除現有 toast
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }

    // 建立 toast
    const toast = createElement('div', {
        className: `toast-notification toast-${type}`,
        role: 'alert',
        'aria-live': 'polite'
    }, message);

    document.body.appendChild(toast);

    // 觸發動畫
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // 自動移除
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * 檢查是否在 LINE LIFF 環境
 * @returns {boolean}
 */
export function isLiffEnvironment() {
    return typeof liff !== 'undefined' && liff.isInClient?.();
}

/**
 * 檢查是否已登入 LIFF
 * @returns {boolean}
 */
export function isLiffLoggedIn() {
    return typeof liff !== 'undefined' && liff.isLoggedIn?.();
}
