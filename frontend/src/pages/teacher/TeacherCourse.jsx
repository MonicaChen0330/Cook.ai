// frontend/src/pages/teacher/TeacherCourseDashboard.jsx
import { useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import TeacherAICenter from '../../components/teacher/TeacherAICenter';

function TeacherCourseDashboard() {
  // 透過 context 取得設定麵包屑的工具
  const { setBreadcrumbPaths } = useOutletContext();

  // 在元件載入時，設定麵包屑路徑
  useEffect(() => {
    const paths = [
      { name: '教師總覽', path: '/teacher' },
      { name: 'Cook AI助教' }
    ];
    setBreadcrumbPaths(paths);

    // 元件卸載時清除麵包屑
    return () => setBreadcrumbPaths(null);
  }, [setBreadcrumbPaths]);

  return (
    <TeacherAICenter />
  );
}

export default TeacherCourseDashboard;