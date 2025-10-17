// frontend/src/pages/student/StudentCourse.jsx
import { useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';

// Define the type for a single breadcrumb path item
interface BreadcrumbPath {
  name: string;
  path?: string; // path is optional for the last item
}

// Define the type for the Outlet context
interface OutletContext {
  setBreadcrumbPaths: React.Dispatch<React.SetStateAction<BreadcrumbPath[] | null>>;
}

function StudentCourse() {
  const { setBreadcrumbPaths } = useOutletContext<OutletContext>();

  useEffect(() => {
    const paths: BreadcrumbPath[] = [
      { name: '學生總覽', path: '/student' },
      { name: '課程內容' }
    ];
    setBreadcrumbPaths(paths);

    return () => setBreadcrumbPaths(null);
  }, [setBreadcrumbPaths]);

  return (
    <div>
      <h2>課程內容</h2>
      <p className="text-lg text-gray-500">
        此區塊待開發...
      </p>
    </div>
  );
}

export default StudentCourse;