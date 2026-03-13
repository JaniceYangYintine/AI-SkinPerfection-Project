import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
    // 根目錄
    root: '.',

    // 開發伺服器設定
    server: {
        port: 8000,
        open: true
    },

    // 建置設定
    build: {
        outDir: 'dist',
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'index.html'),
                analyze: resolve(__dirname, 'analyze.html'),
                survey: resolve(__dirname, 'survey_new.html'),
                result: resolve(__dirname, 'result_new.html')
            }
        }
    }
});
