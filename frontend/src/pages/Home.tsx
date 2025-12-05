import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FaChalkboardTeacher, FaUserGraduate } from 'react-icons/fa';
import Footer from '../components/common/Footer.tsx';
import RegisterModal from '../components/auth/RegisterModal';

function Home() {
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);

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

        {/* 註冊按鈕 */}
        <button
          onClick={() => setIsRegisterModalOpen(true)}
          className="
            mb-12 px-8 py-3 
            bg-gradient-to-r from-theme-button-gradient-from to-theme-button-gradient-to
            text-white font-medium rounded-lg
            shadow-default
            transition-all duration-300 ease-in-out
            hover:shadow-lg hover:-translate-y-0.5
          "
        >
          立即註冊
        </button>
        
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

      {/* 註冊 Modal */}
      <RegisterModal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
      />
    </div>
  );
}

export default Home;