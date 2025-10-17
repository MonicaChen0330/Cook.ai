import { useEffect } from 'react';
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

  useEffect(() => {
    if (context.setBreadcrumbPaths && courseId) {
      context.setBreadcrumbPaths([
        { name: '教師概覽', path: '/teacher' },
        { name: '課程', path: `/teacher/course/${courseId}` }, // TODO: 後端資料庫建好後，從 API 獲取 courseName
      ]);
    }
  }, [courseId, context.setBreadcrumbPaths]);

  return (
    <div className="flex flex-grow overflow-hidden">
      <TeacherSidebar courseId={courseId} />
      <main className="flex-grow p-8 overflow-y-auto flex justify-center items-center">
        <Outlet context={context} /> {/* Pass the context down here */}
      </main>
    </div>
  );
}

export default TeacherCourseLayout;