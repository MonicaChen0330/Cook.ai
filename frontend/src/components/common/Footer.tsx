import React from 'react';

const Footer: React.FC = () => {
  return (
    // 【樣式對應】bg-gray-900 對應 #212529，py-2.5 px-8 對應 padding，text-sm 對應 font-size
    <footer className="flex-shrink-0 bg-gray-900 text-white py-2.5 px-8 text-sm">
      
      {/* 【樣式對應】max-w-7xl 對應 max-width: 1200px，gap-10 對應 gap: 2.5rem */}
      <div className="max-w-7xl mx-auto flex justify-center items-center gap-10">
        
        {/* 1. 實驗室資訊 (內容已還原) */}
        <div className="flex flex-col text-center gap-1">
          {/* 【樣式對應】font-medium text-white 對應 .lab-name */}
          <p className="font-medium text-white">國立中央大學 人工智慧與知識系統實驗室</p>
          {/* 【樣式對應】text-gray-300 對應 color with opacity */}
          <p className="text-gray-300">NCU Artificial Intelligence & Knowledge System Lab</p>
        </div>

        {/* 分隔線 */}
        {/* 【樣式對應】h-12 對應 height: 50px，w-px 對應 width: 1px，bg-gray-700 對應 background-color */}
        <div className="h-12 w-px bg-gray-700"></div>

        {/* 2. 開發者與指導教授 (內容已還原) */}
        <div className="flex flex-col text-center gap-1">
          <p className="text-gray-300">開發者：陳淳瑜、陳玟樺、劉品媛</p>
          <p className="text-gray-300">指導教授：楊鎮華 教授</p>
        </div>

        {/* 分隔線 */}
        <div className="h-12 w-px bg-gray-700"></div>

        {/* 3. 聯絡資訊 (內容已還原) */}
        <div className="flex flex-col text-center gap-1">
          {/* 【樣式對應】text-gray-400 對應 color with more opacity */}
          <p className="text-gray-400">地址：(320317) 桃園市中壢區中大路300號 國立中央大學工程五館 E6-B320</p>
          <p className="text-gray-400">Tel：03 - 4227151 分機 : 35353</p>
        </div>

      </div>
    </footer>
  );
};

export default Footer;