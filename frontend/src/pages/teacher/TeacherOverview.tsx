// frontend/src/pages/teacher/TeacherOverview.tsx
import { Link } from 'react-router-dom';
import InfoBlock from '../../components/common/InfoBlock';

// Define a type for the course object
interface Course {
  id: string;
  name: string;
  teacher: string;
}

function TeacherOverview() {
  // Add type to the courses array
  const courses: Course[] = [
    { id: 'cs-intro', name: "智慧型網路服務工程", teacher: "楊鎮華教師" },
    { id: 'creative', name: "創意學習", teacher: "楊鎮華教師" },
  ];
  const feedbacks: any[] = []; // Assuming feedbacks can be of any type for now

  return (
    <div className="px-16 pt-8 flex flex-col">
      <h3 className="mb-6 border-b border-gray-200 pb-4 text-lg text-gray-800 font-bold">我的課程</h3>
      <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-6">
        {courses.map((course) => (
          <Link 
            to={`/teacher/course/${course.id}`} 
            key={course.id} 
            className="block border border-gray-200 rounded-lg p-6 transition-all duration-200 ease-in-out no-underline text-gray-800 bg-white hover:-translate-y-1 hover:shadow-lg hover:border-blue-500"
          >
            <h4 className="mt-0 text-xl text-primary-dark">{course.name}</h4>
            <p className="text-sm text-gray-500 mb-0">{course.teacher}</p>
          </Link>
        ))}
      </div>

      <InfoBlock title="學生回饋" items={feedbacks} />
    </div>
  );
}

export default TeacherOverview;