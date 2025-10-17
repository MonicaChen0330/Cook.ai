import { useEffect } from 'react';
import { Outlet, useParams, useOutletContext } from 'react-router-dom';
import StudentSidebar from './StudentSidebar';

// Define the type for the Outlet context
interface OutletContext {
  setBreadcrumbPaths: React.Dispatch<React.SetStateAction<Array<{ name: string; path: string }> | null>>;
  breadcrumbPaths: Array<{ name: string; path: string }> | null;
}

function StudentCourseLayout() {
  const { courseId } = useParams();
  const context = useOutletContext<OutletContext>(); // Get the entire context object

  useEffect(() => {
    if (context.setBreadcrumbPaths && courseId) {
      context.setBreadcrumbPaths([
        { name: '學生總覽', path: '/student' },
        { name: `課程`, path: `/student/course/${courseId}` },
      ]);
    }
  }, [courseId, context.setBreadcrumbPaths]);

  return (
    <div className="flex flex-grow overflow-hidden">
      <StudentSidebar courseId={courseId} />
      <main className="flex-grow p-8 overflow-y-auto">
        <Outlet context={context} /> {/* Pass the context down here */}
      </main>
    </div>
  );
}

export default StudentCourseLayout;