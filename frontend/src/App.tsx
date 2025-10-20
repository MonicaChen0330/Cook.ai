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
            <Route path="materials-db" element={<h2>教材資料庫 (待開發)</h2>} />
            <Route path="materials-mgmt" element={<h2>教材管理 (待開發)</h2>} />
            <Route path="announcements" element={<h2>公告管理 (待開發)</h2>} />
            <Route path="students-dashboard" element={<h2>學生儀表板 (待開發)</h2>} />
            <Route path="literature-review" element={<h2>Literature Review (待開發)</h2>} />
            <Route path="ai-detector" element={<h2>AI Detector (待開發)</h2>} />
            <Route path="carbon-emission-calculator" element={<h2>碳排計算指標 (待開發)</h2>} />
        </Route>
      </Route>
      
      <Route path="/student" element={<StudentPortal />}>
          <Route index element={<StudentOverview />} />
          <Route path="course/:courseId" element={<StudentCourseLayout />}>
              <Route index element={<StudentCourse />} />
              <Route path="materials" element={<h2>課程教材 (待開發)</h2>} />
              <Route path="assignments" element={<h2>練習題與作業 (待開發)</h2>} />
              <Route path="coding" element={<h2>程式練習 (待開發)</h2>} />
              <Route path="dashboard" element={<h2>學習儀表板 (待開發)</h2>} />
          </Route>
      </Route>
    </Routes>
  );
}

export default App;
