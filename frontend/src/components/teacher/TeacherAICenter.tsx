// frontend/src/components/teacher/TeacherAICenter.jsx
import { useState } from 'react';
import { FaSearch, FaYoutube, FaFileAlt, FaEnvelope } from 'react-icons/fa';

function TeacherAICenter() {
  const [prompt, setPrompt] = useState('');
  const userName = "Ms. Chen"; // 假資料

  const handlePromptChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(e.target.value);
  };

  const handleChipClick = (suggestion: string) => {
    setPrompt(suggestion);
  };

  const suggestions = [
    { icon: <FaFileAlt />, text: '產生隨堂練習' },
    { icon: <FaEnvelope />, text: '撰寫公告並發送郵件給學生' },
    { icon: <FaYoutube />, text: '根據教學影片內容出題' },
  ];

  return (
    <div className="w-full max-w-3xl mx-auto my-16 text-center">
      <div className="inline-flex items-center gap-4 mb-8">
        <div className="text-3xl text-blue-500">✨</div> {/* Using a div for the sparkle icon as it was a character */} 
        <h2 className="m-0 text-3xl font-bold text-gray-800">嗨 {userName}，您需要甚麼教學上的幫助?</h2>
      </div>

      <div className="relative mb-6">
        <FaSearch className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="輸入您的指令製作教材或查詢任何問題..."
          className="w-full py-4 pl-14 pr-4 text-lg border border-gray-300 rounded-full shadow-md transition-all duration-200 ease-in-out focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-200"
          value={prompt}
          onChange={handlePromptChange}
        />
      </div>

      <div className="flex justify-center gap-4 flex-wrap">
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            className="inline-flex items-center gap-2 bg-white border border-gray-300 py-2.5 px-4 rounded-full text-sm cursor-pointer transition-all duration-200 ease-in-out hover:bg-gray-100 hover:border-blue-500 hover:text-blue-500"
            onClick={() => handleChipClick(suggestion.text)}
          >
            {suggestion.icon} {suggestion.text}
          </div>
        ))}
      </div>
    </div>
  );
}

export default TeacherAICenter;