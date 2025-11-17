// frontend/src/components/teacher/SourcePanel.tsx
import React, { useState } from 'react'; // 1. 匯入 useState
import { FaUpload, FaChevronLeft } from 'react-icons/fa'; 
import Button from '../common/Button'; 
import { Source } from './TeacherAICenter';

interface SourcePanelProps {
  isOpen: boolean;
  onToggle: () => void;
  availableSources: Source[];
  selectedSources: string[];
  onSelectSource: (id: string) => void;
}

function SourcePanel({ 
  isOpen, 
  onToggle, 
  availableSources, 
  selectedSources, 
  onSelectSource 
}: SourcePanelProps) {
  
  // 2. 建立一個 state 來 "模擬" 按鈕狀態
  const [btnState, setBtnState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  // 3. 模擬的上傳函式
  const handleUpload = () => {
    // 這是 "非同步" 函式，Button 會自動處理
    return new Promise<void>((resolve, reject) => {
      // 模擬 2 秒的上傳
      setTimeout(() => {
        // 成功或失敗
        if (Math.random() > 0.3) {
          resolve();
        } else {
          reject(new Error('Simulated upload fail'));
        }
      }, 2000);
    });
  };

  return (
    <div className="relative h-full">
      <div 
        className={`
          h-full 
          bg-theme-background
          rounded-xl
          transition-[width] duration-300 ease-in-out
          flex flex-col
          ${isOpen ? 'w-80' : 'w-0'} 
        `}
      >
        <div className="h-full flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-theme-border">
            <h2 className="text-lg font-bold text-neutral-text-main">參考資料</h2>
          </div>

          <div className="px-6 py-4">
            
            {/* 4. 在這裡使用 "新" 的 Button 組件 */}
            <Button 
              variant="primary"
              size="md"
              buttonState={btnState}
              onClick={handleUpload}
              idleText={
                <span className="flex items-center gap-2">
                  <FaUpload className="w-4 h-4" /> 上傳檔案
                </span>
              }
              loadingText="上傳中..."
              successText="上傳成功！"
              errorText="上傳失敗"
              className="w-full"
            />

          </div>

          <div className="flex-1 overflow-y-auto px-6 py-4">
            <p className="text-neutral-text-secondary text-sm mb-4">
              {availableSources.length} 個來源
            </p>
            
            <ul className="list-none p-0 m-0 space-y-1 text-gray-700 text-sm">
              {availableSources.map(source => (
                <li key={source.id} className="flex items-center gap-2 p-1 rounded-default hover:bg-theme-background-hover cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="form-checkbox h-4 w-4 text-theme-checkbox border-neutral-border rounded focus:ring-theme-ring" 
                    checked={selectedSources.includes(source.id)}
                    onChange={() => onSelectSource(source.id)}
                  />
                  <span className="truncate text-neutral-text-secondary">{source.name}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <button 
        onClick={onToggle} 
        className="absolute top-1/2 -right-4 z-10 p-2 rounded-full bg-white shadow-default text-neutral-icon hover:bg-neutral-background"
        style={{ transform: 'translateY(-50%)' }}
      >
        <FaChevronLeft 
          className={`w-5 h-5 transition-transform duration-300 ${!isOpen ? 'rotate-180' : ''}`} 
        />
      </button>
    </div>
  );
}

export default SourcePanel;