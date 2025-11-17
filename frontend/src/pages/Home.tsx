import { Link } from 'react-router-dom';
import { FaChalkboardTeacher, FaUserGraduate } from 'react-icons/fa';
import Footer from '../components/common/Footer.tsx';

function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <main className="flex-grow flex flex-col justify-center items-center">
        
        <h1 className="
          m-0 mb-4 text-6xl font-extrabold
          tracking-wide leading-normal 
          bg-gradient-to-r 
          from-theme-gradient-deep
          via-theme-gradient-middle
          to-theme-gradient-light 
          text-transparent bg-clip-text
        ">
          Cool Knowledge.ai Demo
        </h1>
        
        <p className="text-lg text-neutral-text-secondary mt-2 mb-12">
          您的智慧教學夥伴，讓學習與教學更有效率
        </p>
        
        <div className="flex gap-8">
          
          <Link 
            to="/teacher" 
            className="
              bg-white p-8 
              rounded-default shadow-default
              no-underline 
              text-neutral-text-main
              flex flex-col items-center justify-center 
              transition-all duration-300 ease-in-out 
              border border-neutral-border
              hover:-translate-y-1 hover:shadow-lg 
              hover:text-theme-primary
              group
            "
          >
            <FaChalkboardTeacher size={50} />
            <h2 className="mt-4 mb-2 transition-colors group-hover:text-theme-primary">
              教師平台
            </h2>
            
            <span className="text-neutral-text-secondary">教材生成與課程管理</span>
          </Link>
          
          <Link 
            to="/student" 
            className="
              bg-white p-8 
              rounded-default shadow-default 
              no-underline 
              text-neutral-text-main 
              flex flex-col items-center justify-center 
              transition-all duration-300 ease-in-out 
              border border-neutral-border 
              hover:-translate-y-1 hover:shadow-lg 
              hover:text-theme-primary
              group
            "
          >
            <FaUserGraduate size={50} />
            <h2 className="mt-4 mb-2 transition-colors group-hover:text-theme-primary">
              學生平台
            </h2>

            <span className="text-neutral-text-secondary">智慧學習與程式練習</span>
          </Link>
          
        </div>
      </main>
      <Footer />
    </div>
  );
}

export default Home;