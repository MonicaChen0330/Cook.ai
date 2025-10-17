// frontend/src/pages/teacher/TeacherOverview.jsx
import { Link } from 'react-router-dom';
import InfoBlock from '../../components/student/InfoBlock';
import './TeacherOverview.css';

function TeacherOverview() {
  // 假資料
  const courses = [
    { id: 'cs-intro', name: "智慧型網路服務工程", teacher: "楊鎮華教師" },
    { id: 'creative', name: "創意學習", teacher: "楊鎮華教師" },
  ];
  const feedbacks = [];

  return (
    <div className="teacher-overview-dashboard">
      <h3 className="block-title">我的課程</h3>
      <div className="course-list">
        {courses.map((course) => (
          <Link to={`/teacher/course/${course.id}`} key={course.id} className="course-card">
            <h4>{course.name}</h4>
            <p>{course.teacher}</p>
          </Link>
        ))}
      </div>

      <InfoBlock title="學生回饋" items={feedbacks} />
    </div>
  );
}

export default TeacherOverview;