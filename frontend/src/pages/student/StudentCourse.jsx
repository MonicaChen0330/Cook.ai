// frontend/src/pages/student/StudentCourse.jsx
import { useEffect } from 'react'; // 1. 引入 useEffect
import { useOutletContext } from 'react-router-dom'; // 2. 引入 useOutletContext

function StudentCourse() {
  // 3. 透過 useOutletContext 取得從 Student.jsx 傳來的 setBreadcrumbPaths 函式
  const { setBreadcrumbPaths } = useOutletContext();

  // 4. 使用 useEffect 在元件載入時，執行一次設定麵包屑的動作
  useEffect(() => {
    const paths = [
      { name: '學生總覽', path: '/student' },
      { name: '課程內容' }
    ];
    // 呼叫函式，更新 "大腦" (Student.jsx) 中的 state
    setBreadcrumbPaths(paths);

    // 在元件卸載時，清除麵包屑 (可選，但良好習慣)
    return () => setBreadcrumbPaths(null);
  }, [setBreadcrumbPaths]); // 依賴項

  return (
    <div>
      {/* 5. 這裡不再需要手動放置 Breadcrumb 元件 */}
      <h2>課程內容</h2>
      <p style={{ fontSize: '1.2rem', color: 'var(--text-color-muted)' }}>
        此區塊待開發...
      </p>
    </div>
  );
}

export default StudentCourse;