// frontend/src/App.jsx
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import TeacherPortal from './pages/Teacher';
import StudentPortal from './pages/Student';

import TeacherOverview from './pages/teacher/TeacherOverview';
import TeacherCourseLayout from './components/teacher/TeacherCourseLayout';
import TeacherCourse from './pages/teacher/TeacherCourse';

import StudentOverview from './pages/student/StudentOverview';
import StudentCourseLayout from './components/student/StudentCourseLayout';
import StudentCourse from './pages/student/StudentCourse';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      
      <Route path="/teacher" element={<TeacherPortal />}>
        <Route index element={<TeacherOverview />} />
        <Route path="course/:courseId" element={<TeacherCourseLayout />}>
            <Route index element={<TeacherCourse />} />
            <Route path="materials" element={<h2>教師教材庫 (待開發)</h2>} />
        </Route>
      </Route>
      
      <Route path="/student" element={<StudentPortal />}>
          <Route index element={<StudentOverview />} />
          <Route path="course/:courseId" element={<StudentCourseLayout />}>
              <Route index element={<StudentCourse />} />
          </Route>
      </Route>
    </Routes>
  );
}

export default App;