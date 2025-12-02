// src/components/student/debugging/Sidebar.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = "http://localhost:8000";

// 1. 修改介面：將 id 改為 _id (配合 MongoDB/後端回傳格式)
interface Problem {
    _id: string;     // <--- 關鍵修改：從 id 改為 _id
    title: string;
}

interface Chapter {
    id: string;
    title: string;
}

interface SidebarProps {
    isOpen: boolean;
    selectedProblemId: string | null;
    onSelectProblem: (id: string) => void;
}

const STATIC_CHAPTERS: Chapter[] = [
    { id: "C1", title: "Chapter 1: 變數與輸入輸出" },
    { id: "C2", title: "Chapter 2: 數值資料與字串資料" },
    { id: "C3", title: "Chapter 3: List串列資料型態" },
    { id: "C4", title: "Chapter 4: if條件判斷" },
    { id: "C5", title: "Chapter 5: for迴圈" },
    { id: "C6", title: "Chapter 6: while迴圈" },
    { id: "C7", title: "Chapter 7: dict字典" },
    { id: "C8", title: "Chapter 8: 函式定義與應用" },
    { id: "P1", title: "西洋棋" },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, selectedProblemId, onSelectProblem }) => {
    const [chapterProblems, setChapterProblems] = useState<Record<string, Problem[]>>({});
    const [expandedChapters, setExpandedChapters] = useState<Record<string, boolean>>({
        'C1': true
    });

    useEffect(() => {
        const fetchAllProblems = async () => {
            const fetchedData: Record<string, Problem[]> = {};
            await Promise.all(STATIC_CHAPTERS.map(async (chapter) => {
                try {
                    const response = await axios.get(
                        `${API_BASE_URL}/debugging/problems/chapter/${chapter.id}`
                    );
                    fetchedData[chapter.id] = response.data;
                } catch (error) {
                    console.error(`Failed to fetch problems for ${chapter.id}`, error);
                    fetchedData[chapter.id] = [];
                }
            }));
            setChapterProblems(fetchedData);
        };
        fetchAllProblems();
    }, []);

    const toggleChapter = (chapterId: string) => {
        setExpandedChapters(prev => ({ ...prev, [chapterId]: !prev[chapterId] }));
    };

    return (
        <div className={`bg-gray-50 border-r border-gray-200 overflow-hidden flex flex-col shrink-0 transition-all duration-300 ease-in-out ${isOpen ? 'w-64 opacity-100' : 'w-0 opacity-0 border-none'}`}>
            <div className="flex-1 overflow-y-auto p-0 w-64">
                {STATIC_CHAPTERS.map((chapter) => (
                    <div key={chapter.id} className="border-b border-gray-100 last:border-0">
                        <div onClick={() => toggleChapter(chapter.id)} className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-200 transition-colors">
                            <h4 className="text-xs font-bold text-gray-500 uppercase truncate select-none" title={chapter.title}>{chapter.title}</h4>
                            <svg className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${expandedChapters[chapter.id] ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                        </div>
                        {expandedChapters[chapter.id] && (
                            <div className="bg-white pb-2">
                                {chapterProblems[chapter.id] && chapterProblems[chapter.id].length > 0 ? (
                                    chapterProblems[chapter.id].map((problem) => (
                                        <button
                                            key={problem._id} // 2. 修改 key 為 _id
                                            onClick={() => onSelectProblem(problem._id)} // 3. 修改傳遞參數為 _id
                                            className={`w-full text-left px-8 py-2 text-sm transition-colors truncate border-l-4 ${selectedProblemId === problem._id ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium' : 'border-transparent text-gray-600 hover:bg-gray-50'}`}
                                        >
                                            {/* 這裡也可以顯示 problem._id 如果需要除錯 */}
                                            {problem.title}
                                        </button>
                                    ))
                                ) : (
                                    <div className="px-8 py-2 text-xs text-gray-400 italic">載入中...</div>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};
export default Sidebar;