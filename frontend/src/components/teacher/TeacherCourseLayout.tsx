import { useEffect, useState } from 'react';
import { Outlet, useParams, useOutletContext } from 'react-router-dom';
import TeacherSidebar from './TeacherSidebar';

// Define the type for the Outlet context
interface OutletContext {
  setBreadcrumbPaths: React.Dispatch<React.SetStateAction<Array<{ name: string; path: string }> | null>>;
  breadcrumbPaths: Array<{ name: string; path: string }> | null;
}

function TeacherCourseLayout() {
  const { courseId } = useParams();
  const context = useOutletContext<OutletContext>(); // Get the entire context object

  // 1. 在這裡建立 "狀態"，預設為開啟 (true)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // 2. 這是切換狀態的函式
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  useEffect(() => {
    if (context.setBreadcrumbPaths && courseId) {
      context.setBreadcrumbPaths([
        { name: '教師概覽', path: '/teacher' },
        { name: '課程', path: `/teacher/course/${courseId}` }, // TODO: 後端資料庫建好後，從 API 獲取 courseName
      ]);
    }
  }, [courseId, context.setBreadcrumbPaths]);

  return (
    <div className="flex h-full bg-white">
      {/* 4. 將狀態和函式 "傳遞" 給 TeacherSidebar */}
      <TeacherSidebar 
        isSidebarOpen={isSidebarOpen} 
        onToggle={toggleSidebar} 
        courseId={courseId}
      />
      <main className="flex-1 overflow-y-auto bg-white">
        <Outlet context={context} /> {/* Pass the context down here */}
      </main>
    </div>
  );
}

export default TeacherCourseLayout;