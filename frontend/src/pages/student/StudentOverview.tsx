
// frontend/src/pages/student/StudentOverview.jsx
import { Link } from 'react-router-dom';
import InfoBlock from '../../components/common/InfoBlock';

// Define a type for the course object
interface Course {
  id: string;
  name: string;
  teacher: string;
}

function StudentOverview() {
  const announcements: any[] = [];
  const events: any[] = [];
  const materials: any[] = [];
  const courses: Course[] = [
    { id: 'cs-intro', name: "智慧型網路服務工程", teacher: "楊鎮華教師" },
    { id: 'ml', name: "機器學習", teacher: "黃鈺晴教師" },
    { id: 'creative', name: "創意學習", teacher: "楊鎮華教師" },
    { id: 'python', name: "Python", teacher: "黃鈺晴教師" },
  ];

  return (
    <div className="px-16 pb-8 flex flex-col">
      <h3 className="mt-8 mb-6 border-b border-gray-200 pb-4 text-lg text-gray-800 font-bold">我的課程</h3>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-6">
        {courses.map((course) => (
          <Link 
            to={`/student/course/${course.id}`} 
            key={course.id} 
            className="block border border-gray-200 rounded-lg p-6 transition-all duration-200 ease-in-out no-underline text-gray-800 bg-white hover:-translate-y-1 hover:shadow-lg hover:border-blue-500"
          >
            <h4 className="mt-0 text-xl text-primary-dark">{course.name}</h4>
            <p className="text-sm text-gray-500 mb-0">{course.teacher}</p>
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