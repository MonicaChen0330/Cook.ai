import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Student } from './StudentCoding';
import Sidebar from '../../../components/student/debugging/Sidebar';

const API_BASE_URL = "http://localhost:8000";

// 復用與 PreCoding 相同的題目資料介面
interface ProblemDetail {
    _id: string;
    title: string;
    description: string;
    input_description: string;
    output_description: string;
    samples: Array<{
        input: string;
        output: string;
    }>;
}

interface CodingHelpProps {
    student: Student;
}

const CodingHelp: React.FC<CodingHelpProps> = ({ student }) => {
    // --- 狀態管理 ---
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    // 1. 初始值設為 null，與 PreCoding 保持一致
    const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);

    // 題目資料狀態
    const [problemData, setProblemData] = useState<ProblemDetail | null>(null);

    // 聊天室狀態
    const [messages, setMessages] = useState<Array<{ role: string, content: string }>>([]);
    const [input, setInput] = useState('');

    // --- 資料抓取與對話初始化 ---
    useEffect(() => {
        const fetchData = async () => {
            if (!selectedProblemId) {
                setProblemData(null); // 清空題目資料
                return;
            }

            try {
                // 1. 抓取題目詳細資料
                const res = await axios.get(`${API_BASE_URL}/debugging/problems/${selectedProblemId}`);
                setProblemData(res.data);

                // 2. 初始化歡迎訊息 (帶入題目名稱)
                setMessages([
                    {
                        role: 'system',
                        content: `嗨 ${student.name}，我是 AI 助教。\n針對題目「${res.data.title}」，你有什麼程式上的疑問嗎？`
                    }
                ]);
            } catch (error) {
                console.error("Failed to fetch problem info", error);
                // 錯誤時的 fallback
                setProblemData(null);
                setMessages([
                    { role: 'system', content: `嗨 ${student.name}，請選擇一個題目以開始求救。` }
                ]);
            }
        };

        fetchData();
    }, [selectedProblemId, student.name]);

    // --- 發送訊息邏輯 ---
    const handleSend = () => {
        if (!input.trim()) return;

        const userMsg = input;
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setInput('');

        // 模擬 AI 回覆
        setTimeout(() => {
            setMessages(prev => [...prev, {
                role: 'system',
                content: `(AI 模擬回覆) 針對你的問題：「${userMsg}」，建議檢查輸入格式是否符合題目要求。`
            }]);
        }, 800);
    };

    return (
        <div className="flex h-full w-full bg-white">

            {/* 1. Sidebar */}
            <Sidebar
                isOpen={isSidebarOpen}
                selectedProblemId={selectedProblemId}
                onSelectProblem={setSelectedProblemId}
            />

            {/* 2. 主內容區 */}
            <div className="flex-1 flex flex-col h-full min-w-0 bg-white">

                {/* 頂部 Header */}
                <div className="h-12 border-b border-gray-200 flex items-center px-2 bg-white shrink-0">
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-2 rounded-md hover:bg-gray-100 text-gray-500 mr-2 focus:outline-none transition-colors"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                    </button>

                    <h2 className="text-lg font-bold text-gray-800 truncate flex items-center gap-2">
                        <span className="mr-2 text-gray-300 font-normal">|</span>
                        {problemData ? problemData.title : '請選擇題目'}
                    </h2>
                </div>

                {/* 左右分割內容區 */}
                <div className="flex-1 flex gap-0 overflow-hidden">

                    {/* 左側：題目描述 */}
                    <div className="w-1/2 flex flex-col border-r border-gray-200">
                        <div className="flex-1 overflow-y-auto p-6">
                            {problemData ? (
                                <>
                                    <h3 className="text-xl font-bold text-gray-800 mb-4">{problemData.title}</h3>

                                    {/* 題目描述 */}
                                    <div
                                        className="text-gray-600 mb-6 leading-relaxed whitespace-pre-wrap prose max-w-none"
                                        dangerouslySetInnerHTML={{ __html: problemData.description }}
                                    />

                                    {/* 輸入輸出說明 */}
                                    <div className="mb-6 grid grid-cols-1 gap-4">
                                        <div>
                                            <h4 className="text-sm font-bold text-gray-700 mb-1">輸入說明</h4>
                                            <div className="text-gray-600 text-sm" dangerouslySetInnerHTML={{ __html: problemData.input_description }} />
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-bold text-gray-700 mb-1">輸出說明</h4>
                                            <div className="text-gray-600 text-sm" dangerouslySetInnerHTML={{ __html: problemData.output_description }} />
                                        </div>
                                    </div>

                                    {/* 範例 */}
                                    <div className="space-y-6">
                                        {problemData.samples && problemData.samples.length > 0 ? (
                                            problemData.samples.map((sample, index) => (
                                                <div key={index} className="bg-gray-50 p-3 rounded border border-gray-200">
                                                    <span className="text-xs font-bold text-gray-500 uppercase block mb-2 border-b border-gray-200 pb-1">Sample {index + 1}</span>
                                                    <div className="space-y-3">
                                                        <div>
                                                            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Input</span>
                                                            <div className="bg-white p-2 rounded border border-gray-200 font-mono text-sm whitespace-pre-wrap">{sample.input}</div>
                                                        </div>
                                                        <div>
                                                            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">Output</span>
                                                            <div className="bg-white p-2 rounded border border-gray-200 font-mono text-sm whitespace-pre-wrap">{sample.output}</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))
                                        ) : (
                                            <div className="text-gray-400 text-sm italic">無範例資料</div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                // 空狀態顯示 (與 PreCoding 類似)
                                <div className="text-gray-400 mt-10 text-center">請從左側列表選擇一個題目以查看詳細內容。</div>
                            )}
                        </div>
                    </div>

                    {/* 右側：AI 對話視窗 */}
                    <div className="w-1/2 flex flex-col bg-gray-50">

                        {/* 聊天訊息列表 */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4">
                            {problemData ? (
                                messages.map((msg, idx) => (
                                    <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div
                                            className={`max-w-[90%] p-3 rounded-lg text-sm shadow-sm whitespace-pre-wrap ${msg.role === 'user'
                                                ? 'bg-red-600 text-white rounded-br-none'
                                                : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none'
                                                }`}
                                        >
                                            {msg.content}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                // 空狀態顯示 (提示先選題目)
                                <div className="flex h-full items-center justify-center text-gray-400 flex-col gap-2">
                                    <svg className="w-12 h-12 opacity-20" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>
                                    <p>請先從左側選擇題目...</p>
                                </div>
                            )}
                        </div>

                        {/* 輸入框區域 */}
                        <div className="p-4 bg-white border-t border-gray-200 shrink-0">
                            <div className="flex gap-2 w-full">
                                <input
                                    className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-red-500 transition-all"
                                    placeholder={problemData ? "輸入你的問題..." : "請先選擇題目"}
                                    value={input}
                                    onChange={e => setInput(e.target.value)}
                                    onKeyPress={e => e.key === 'Enter' && handleSend()}
                                    disabled={!problemData}
                                />
                                <button
                                    onClick={handleSend}
                                    disabled={!problemData || !input.trim()}
                                    className={`
                                        px-6 py-2 rounded-lg font-medium transition-colors shadow-sm
                                        ${!problemData || !input.trim()
                                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                            : 'bg-red-600 text-white hover:bg-red-700'
                                        }
                                    `}
                                >
                                    發送
                                </button>
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};

export default CodingHelp;