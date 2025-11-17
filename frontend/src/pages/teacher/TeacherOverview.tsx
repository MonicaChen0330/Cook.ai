import { Link } from 'react-router-dom';
import InfoBlock from '../../components/common/InfoBlock';

interface Course {
  id: string;
  name: string;
  teacher: string;
}

function TeacherOverview() {
  const courses: Course[] = [
    { id: 'cs-intro', name: "智慧型網路服務工程", teacher: "楊鎮華教師" },
    { id: 'creative', name: "創意學習", teacher: "楊鎮華教師" },
  ];
  const feedbacks: any[] = []; 

  return (
    <div className="px-16 pt-8 flex flex-col bg-neutral-background min-h-full">
      
      <h3 className="mb-6 border-b border-neutral-border pb-4 text-neutral-text-main font-bold">
        我的課程
      </h3>
      
      <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-6">
        {courses.map((course) => (
          <Link 
            to={`/teacher/course/${course.id}`} 
            key={course.id} 
            className="
              block 
              border border-neutral-border
              rounded-default
              p-6 
              transition-all duration-200 ease-in-out 
              no-underline 
              text-neutral-text-main 
              bg-white 
              shadow-default
              hover:-translate-y-1 
              hover:shadow-lg
              hover:border-theme-primary
              group
            "
          >
            <h4 className="mt-0 text-xl text-theme-primary transition-colors group-hover:text-theme-primary-hover">
              {course.name}
            </h4>
            <p className="text-sm text-neutral-text-secondary mb-0">{course.teacher}</p>
          </Link>
        ))}
      </div>

      <InfoBlock title="學生回饋" items={feedbacks} />
    </div>
  );
}

export default TeacherOverview;