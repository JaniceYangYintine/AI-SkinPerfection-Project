-- ============================================================
-- AI Skin Analysis System - Database Schema
-- ============================================================
-- MySQL 8.0+ Compatible
-- Character Set: utf8mb4 (supports emoji and all Unicode)
-- Collation: utf8mb4_unicode_ci (case-insensitive, accent-sensitive)
-- ============================================================

-- Set default character set and collation
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- ============================================================
-- STATIC TABLES (Pre-populated data)
-- ============================================================

-- ------------------------------------------------------------
-- 1. Ingredients Table (成分表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `ingredients` (
    `ingredient_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '成分ID',
    `ingredient_name_zh` VARCHAR(100) NOT NULL COMMENT '成分中文名稱',
    `ingredient_name_en` JSON DEFAULT NULL COMMENT '成分英文名稱（可能有多個）',
    `spot_primary` TINYINT(1) DEFAULT 0 COMMENT '斑點主要功效',
    `spot_support` TINYINT(1) DEFAULT 0 COMMENT '斑點輔助功效',
    `wrinkle_primary` TINYINT(1) DEFAULT 0 COMMENT '皺紋主要功效',
    `wrinkle_support` TINYINT(1) DEFAULT 0 COMMENT '皺紋輔助功效',
    `pore_primary` TINYINT(1) DEFAULT 0 COMMENT '毛孔主要功效',
    `pore_support` TINYINT(1) DEFAULT 0 COMMENT '毛孔輔助功效',
    `acne_primary` TINYINT(1) DEFAULT 0 COMMENT '痘痘主要功效',
    `acne_support` TINYINT(1) DEFAULT 0 COMMENT '痘痘輔助功效',
    `comedone_primary` TINYINT(1) DEFAULT 0 COMMENT '粉刺主要功效',
    `comedone_support` TINYINT(1) DEFAULT 0 COMMENT '粉刺輔助功效',
    `dark_circle_primary` TINYINT(1) DEFAULT 0 COMMENT '黑眼圈主要功效',
    `dark_circle_support` TINYINT(1) DEFAULT 0 COMMENT '黑眼圈輔助功效',
    INDEX `idx_ingredient_name_zh` (`ingredient_name_zh`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='成分表';

-- ------------------------------------------------------------
-- 2. Products Table (產品表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `products` (
    `product_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '產品ID',
    `brand` VARCHAR(100) DEFAULT NULL COMMENT '品牌名稱',
    `price_tier` VARCHAR(20) DEFAULT NULL COMMENT '價格區間',
    `category` VARCHAR(100) DEFAULT NULL COMMENT '產品類別',
    `name` VARCHAR(255) NOT NULL COMMENT '產品名稱',
    `price` DECIMAL(10, 2) DEFAULT NULL COMMENT '產品價格',
    `description` TEXT DEFAULT NULL COMMENT '產品描述',
    `ingredients` JSON DEFAULT NULL COMMENT '成分列表',
    `concerns` JSON DEFAULT NULL COMMENT '適用肌膚問題',
    `skintypes` VARCHAR(100) DEFAULT NULL COMMENT '適用膚質',
    `sensitivity` VARCHAR(50) DEFAULT NULL COMMENT '敏感肌適用性',
    `anti_aging` TINYINT(1) DEFAULT 0 COMMENT '抗老功效',
    `moisturizing` TINYINT(1) DEFAULT 0 COMMENT '保濕功效',
    `product_url` VARCHAR(500) DEFAULT NULL COMMENT '產品連結',
    `image_url` VARCHAR(500) DEFAULT NULL COMMENT '產品圖片連結',
    `crawled_at` DATETIME DEFAULT NULL COMMENT '爬蟲時間',
    INDEX `idx_brand` (`brand`),
    INDEX `idx_category` (`category`),
    INDEX `idx_price_tier` (`price_tier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='產品表';

-- ------------------------------------------------------------
-- 3. Product-Ingredients Relationship Table (產品成分關聯表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `product_ingredients` (
    `relation_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '關聯ID',
    `ingredient_id` INT NOT NULL COMMENT '成分ID',
    `ingredient_name_zh` VARCHAR(100) NOT NULL COMMENT '成分中文名稱',
    `product_id` INT NOT NULL COMMENT '產品ID',
    `category` VARCHAR(100) DEFAULT NULL COMMENT '產品類別',
    `name` VARCHAR(255) DEFAULT NULL COMMENT '產品名稱',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    FOREIGN KEY (`ingredient_id`) REFERENCES `ingredients`(`ingredient_id`) ON DELETE CASCADE,
    FOREIGN KEY (`product_id`) REFERENCES `products`(`product_id`) ON DELETE CASCADE,
    INDEX `idx_ingredient_id` (`ingredient_id`),
    INDEX `idx_product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='產品成分關聯表';

-- ------------------------------------------------------------
-- 4. Actions Table (動作建議表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `actions` (
    `action_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '動作ID',
    `action_name` VARCHAR(200) NOT NULL COMMENT '動作名稱',
    `description` TEXT DEFAULT NULL COMMENT '動作描述',
    `target_issues` JSON DEFAULT NULL COMMENT '目標肌膚問題',
    `gif_url` VARCHAR(500) DEFAULT NULL COMMENT 'GIF動畫連結',
    `category` VARCHAR(50) DEFAULT NULL COMMENT '動作類別',
    INDEX `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='動作建議表';

-- ============================================================
-- DYNAMIC TABLES (User-generated data)
-- ============================================================

-- ------------------------------------------------------------
-- 5. Users Table (使用者表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` VARCHAR(50) PRIMARY KEY COMMENT '使用者ID（UUID）',
    `email` VARCHAR(255) DEFAULT NULL COMMENT '電子郵件',
    `name` VARCHAR(100) DEFAULT NULL COMMENT '使用者姓名',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '註冊時間',
    `last_login` DATETIME DEFAULT NULL COMMENT '最後登入時間',
    UNIQUE INDEX `idx_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='使用者表';

-- ------------------------------------------------------------
-- 6. Sessions Table (分析會話表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `sessions` (
    `session_id` VARCHAR(50) PRIMARY KEY COMMENT '會話ID（UUID）',
    `user_id` VARCHAR(50) DEFAULT NULL COMMENT '使用者ID',
    `photo_url` VARCHAR(500) DEFAULT NULL COMMENT '上傳照片URL',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '會話建立時間',
    `completed_at` DATETIME DEFAULT NULL COMMENT '會話完成時間',
    `status` ENUM('pending', 'analyzing', 'completed', 'failed') DEFAULT 'pending' COMMENT '會話狀態',
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE SET NULL,
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分析會話表';

-- ------------------------------------------------------------
-- 7. Questionnaire Answers Tags Table (問卷答案標籤表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `questionnaire_answers_tags` (
    `answer_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '答案ID',
    `session_id` VARCHAR(50) NOT NULL COMMENT '會話ID',
    `answer1_tag` VARCHAR(100) NOT NULL COMMENT '問題1答案標籤',
    `answer2_tag` VARCHAR(100) NOT NULL COMMENT '問題2答案標籤',
    `answer3_tag` VARCHAR(100) NOT NULL COMMENT '問題3答案標籤',
    `answer4_tag` VARCHAR(100) NOT NULL COMMENT '問題4答案標籤',
    `answer5_tag` VARCHAR(100) NOT NULL COMMENT '問題5答案標籤',
    `answer6_tag` VARCHAR(100) NOT NULL COMMENT '問題6答案標籤',
    `answer7_tag` VARCHAR(100) NOT NULL COMMENT '問題7答案標籤',
    `answer8_tag` VARCHAR(100) NOT NULL COMMENT '問題8答案標籤',
    `answer9_tag` VARCHAR(100) NOT NULL COMMENT '問題9答案標籤',
    `questionnaire_version` VARCHAR(20) DEFAULT NULL COMMENT '問卷版本',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`session_id`) ON DELETE CASCADE,
    INDEX `idx_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='問卷答案標籤表';

-- ------------------------------------------------------------
-- 8. Session LLM Analysis Table (LLM分析結果表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `session_llm_analysis` (
    `analysis_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '分析ID',
    `session_id` VARCHAR(50) NOT NULL COMMENT '會話ID',
    `llm_response` JSON NOT NULL COMMENT 'LLM完整回應（JSON格式）',
    `skin_summary` TEXT DEFAULT NULL COMMENT '肌膚狀況總結',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析時間',
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`session_id`) ON DELETE CASCADE,
    INDEX `idx_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='LLM分析結果表';

-- ------------------------------------------------------------
-- 9. Session Skin Scores Table (肌膚評分表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `session_skin_scores` (
    `score_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '評分ID',
    `session_id` VARCHAR(50) NOT NULL COMMENT '會話ID',
    `spot_score` DECIMAL(3, 1) DEFAULT NULL COMMENT '斑點評分（0-10）',
    `wrinkle_score` DECIMAL(3, 1) DEFAULT NULL COMMENT '皺紋評分（0-10）',
    `pore_score` DECIMAL(3, 1) DEFAULT NULL COMMENT '毛孔評分（0-10）',
    `acne_score` DECIMAL(3, 1) DEFAULT NULL COMMENT '痘痘評分（0-10）',
    `comedone_score` DECIMAL(3, 1) DEFAULT NULL COMMENT '粉刺評分（0-10）',
    `dark_circle_score` DECIMAL(3, 1) DEFAULT NULL COMMENT '黑眼圈評分（0-10）',
    `overall_score` DECIMAL(3, 1) DEFAULT NULL COMMENT '整體評分（0-10）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '評分時間',
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`session_id`) ON DELETE CASCADE,
    INDEX `idx_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='肌膚評分表';

-- ------------------------------------------------------------
-- 10. Session Recommendations Table (推薦結果表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `session_recommendations` (
    `recommendation_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '推薦ID',
    `session_id` VARCHAR(50) NOT NULL COMMENT '會話ID',
    `recommendation_type` ENUM('product', 'action', 'lifestyle') NOT NULL COMMENT '推薦類型',
    `item_id` INT DEFAULT NULL COMMENT '項目ID（產品ID或動作ID）',
    `item_name` VARCHAR(255) DEFAULT NULL COMMENT '項目名稱',
    `reason` TEXT DEFAULT NULL COMMENT '推薦理由',
    `priority` INT DEFAULT 0 COMMENT '優先順序',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '推薦時間',
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`session_id`) ON DELETE CASCADE,
    INDEX `idx_session_id` (`session_id`),
    INDEX `idx_type` (`recommendation_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='推薦結果表';

-- ------------------------------------------------------------
-- 11. GA Events Table (使用者行為事件表)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `ga_events` (
    `event_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '事件ID',
    `session_id` VARCHAR(50) DEFAULT NULL COMMENT '會話ID',
    `user_id` VARCHAR(50) DEFAULT NULL COMMENT '使用者ID',
    `event_name` VARCHAR(100) NOT NULL COMMENT '事件名稱',
    `event_category` VARCHAR(50) DEFAULT NULL COMMENT '事件類別',
    `event_params` JSON DEFAULT NULL COMMENT '事件參數（JSON格式）',
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '事件時間',
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`session_id`) ON DELETE SET NULL,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE SET NULL,
    INDEX `idx_session_id` (`session_id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_event_name` (`event_name`),
    INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='使用者行為事件表';

-- ============================================================
-- END OF SCHEMA
-- ============================================================
