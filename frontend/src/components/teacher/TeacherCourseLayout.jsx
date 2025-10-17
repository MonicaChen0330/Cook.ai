// frontend/src/components/teacher/TeacherCourseLayout.jsx
import { Outlet, useOutletContext } from 'react-router-dom'; // 引入 useOutletContext
import TeacherSidebar from './TeacherSidebar';
import './TeacherCourseLayout.css';

function TeacherCourseLayout() {
  const context = useOutletContext(); // 接收上層傳來的 context

  return (
    <div className="portal-body">
      <TeacherSidebar />
      <main className="portal-content">
        <Outlet context={context} /> 
      </main>
    </div>
  );
}

export default TeacherCourseLayout;