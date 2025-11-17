/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    
    extend: {
      fontFamily: {
      'sans': ['Noto Sans TC', 'system-ui', 'sans-serif'],
      },
      colors: {
        'theme': {
          // LOGO漸層色彩
          'gradient-deep': '#1E3A8A',
          'gradient-middle': '#007BFF',
          'gradient-light': '#40E0D0',

          // 按鈕漸層
          'button-gradient-from': '#3B82F6',
          'button-gradient-to': '#2DD4BF',

          // 主要色彩
          'primary': '#007BFF',      // 主要藍色 (Primary Blue)
          'primary-hover': '#0069D9', // 主要藍色 Hover
          'primary-active': '#0056B3',// 主要藍色 Active
          'secondary': '#6C757D',    // 次要灰色 (Secondary Gray)
          'secondary-hover': '#5A6268', // 次要灰色 Hover
          'secondary-active': '#494F54',// 次要灰色 Active
          'success': '#28A745',      // 成功綠色
          'success-hover': '#218838', // 成功綠色 Hover
          'info': '#17A2B8',         // 資訊藍綠色
          'warning': '#FFC107',      // 警告黃色
          'danger': '#DC3545',       // 危險紅色
          'light': '#F8F9FA',        // 淺色背景
          'dark': '#343A40',         // 深色背景
          
          // UI 顏色
          'background': '#F0F9FF',   // UI 背景色 (Sky-50)
          'background-hover': '#E0F2FE', // UI 背景 Hover (Sky-100)
          'border': '#BAE6FD',       // UI 邊框色 (Sky-200)

          // Checkbox
          'checkbox': '#2563EB', 
          'ring': '#3B82F6',
        },
        'neutral': {
          'text-main': '#1F2937',
          'text-secondary': '#4B5563',
          'text-light': '#9CA3AF',
          'text-on-dark': '#D1D5DB',
          'border': '#E5E7EB',
          'background': '#F9FAFB',
          'icon': '#6B7280',

          // Footer
          'footer-bg': '#111827',
          'footer-border': '#374151',
        },
        'destructive': {
          'DEFAULT': '#EF4444', // (Red 500)
          'hover': '#DC2626', // (Red 600)
        },
      },
      // 圓角
      borderRadius: {
        'default': '8px',
        'sm': '4px',
        'md': '6px',
        'lg': '12px',
        'full': '9999px',
      },
      
      // 陰影
      boxShadow: {
        'default': '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      },

      // 動畫過渡時間
      transitionDuration: {
        '200': '200ms',
        '300': '300ms',
        '400': '400ms',
      },
    },
  },

  plugins: [
    require('@tailwindcss/forms'),
  ],
}