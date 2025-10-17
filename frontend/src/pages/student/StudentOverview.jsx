
import { Link } from 'react-router-dom'
import InfoBlock from '../../components/student/InfoBlock';
import './StudentOverview.css';

function StudentOverview() {
  const announcements = [];
  const events = [];
  const materials = [];
  const courses = [
    { id: 'cs-intro', name: "智慧型網路服務工程", teacher: "楊鎮華教師" },
    { id: 'ml', name: "機器學習", teacher: "黃鈺晴教師" },
    { id: 'creative', name: "創意學習", teacher: "楊鎮華教師" },
    { id: 'python', name: "Python", teacher: "黃鈺晴教師" },
  ];

  return (
    <div className="student-dashboard">
      <h3 className="block-title">我的課程</h3>
      <div className="course-list">
        {courses.map((course) => (
          <Link to={`/student/course/${course.id}`} key={course.id} className="course-card">
            <h4>{course.name}</h4>
            <p>{course.teacher}</p>
          </Link>
        ))}
      </div>
      <InfoBlock title="最新公告" items={announcements} />
      <InfoBlock title="最近教材" items={events} />
      <InfoBlock title="最近事件 (未完成)" items={materials} />

    </div>
  );
}

export default StudentOverview;