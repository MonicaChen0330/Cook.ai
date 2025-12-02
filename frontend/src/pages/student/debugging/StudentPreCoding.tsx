// src/pages/student/debugging/StudentPreCoding.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Student } from './StudentCoding';
import Sidebar from '../../../components/student/debugging/Sidebar';

const API_BASE_URL = "http://localhost:8000";

// 定義題目詳細資料介面 (更新版 - 對應後端 JSON 結構)
interface ProblemDetail {
    _id: string;
    title: string;
    description: string;        // HTML 格式的題目描述
    input_description: string;  // HTML 格式的輸入說明
    output_description: string; // HTML 格式的輸出說明
    samples: Array<{            // 範例陣列
        input: string;
        output: string;
    }>;
}

interface PreCodingProps {
    student: Student;
}

const PreCoding: React.FC<PreCodingProps> = ({ student }) => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);
    const [problemData, setProblemData] = useState<ProblemDetail | null>(null);
    const [studentCode, setStudentCode] = useState<string | null>(null);
    const [result, setResult] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // 當選擇題目時，抓取「題目詳情」與「學生程式碼」
    useEffect(() => {
        const fetchData = async () => {
            if (!selectedProblemId) return;
            setLoading(true);
            try {
                // 1. 抓取題目詳細資料 (Real API)
                // 假設後端路徑是 /debugging/problems/{problem_id}
                const problemRes = await axios.get(`${API_BASE_URL}/debugging/problems/${selectedProblemId}`);
                setProblemData(problemRes.data);

                // 2. 抓取學生程式碼 (Real API)
                // 假設後端路徑是 /student_code/{student_id}/{problem_id}
                const codeRes = await axios.get(`${API_BASE_URL}/student_code/${student.stu_id}/${selectedProblemId}`);

                const { status, data } = codeRes.data;
                if (status === "success" || status === "code_accepted") {
                    setStudentCode(data.code);
                    setResult(data.result);
                } else {
                    setStudentCode(""); // 或預設樣板
                    setResult(null);
                }

            } catch (error) {
                console.error("Fetch data failed:", error);
                // 錯誤處理：如果程式碼 API 失敗 (例如學生還沒寫過)，通常不該讓整個頁面壞掉
                // 這裡可以只設定 studentCode 為空
                setStudentCode("");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selectedProblemId, student.stu_id]);

    return (
        <div className="flex h-full w-full bg-white">
            <Sidebar
                isOpen={isSidebarOpen}
                selectedProblemId={selectedProblemId}
                onSelectProblem={setSelectedProblemId}
            />

            <div className="flex-1 flex flex-col h-full min-w-0 bg-white">
                <div className="h-12 border-b border-gray-200 flex items-center px-2 bg-white shrink-0">
                    <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 rounded-md hover:bg-gray-100 text-gray-500 mr-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
                    </button>
                    <h2 className="text-lg font-bold text-gray-800 truncate flex items-center">
                        <span className="mr-2 text-gray-300 font-normal">|</span>
                        {problemData ? problemData.title : '請選擇題目'}
                    </h2>
                </div>

                <div className="flex-1 flex gap-0 overflow-hidden">
                    {/* 左側：題目描述 */}
                    <div className="w-1/2 flex flex-col border-r border-gray-200">
                        <div className="flex-1 overflow-y-auto p-6">
                            {problemData ? (
                                <>
                                    <div
                                        className="text-gray-600 mb-6 leading-relaxed whitespace-pre-wrap prose max-w-none"
                                        dangerouslySetInnerHTML={{ __html: problemData.description }}
                                    />

                                    {/* 2. 輸入與輸出說明 (解析 HTML) */}
                                    <div className="mb-6 grid grid-cols-1 gap-4">
                                        <div>
                                            <h4 className="text-sm font-bold text-gray-700 mb-1">輸入說明</h4>
                                            <div
                                                className="text-gray-600 text-sm"
                                                dangerouslySetInnerHTML={{ __html: problemData.input_description }}
                                            />
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-bold text-gray-700 mb-1">輸出說明</h4>
                                            <div
                                                className="text-gray-600 text-sm"
                                                dangerouslySetInnerHTML={{ __html: problemData.output_description }}
                                            />
                                        </div>
                                    </div>

                                    {/* 3. 範例區 (遍歷 samples 陣列) */}
                                    <div className="space-y-6">
                                        {problemData.samples && problemData.samples.length > 0 ? (
                                            problemData.samples.map((sample, index) => (
                                                <div key={index} className="bg-gray-50 p-3 rounded border border-gray-200">
                                                    <span className="text-xs font-bold text-gray-500 uppercase block mb-2 border-b border-gray-200 pb-1">
                                                        Sample {index + 1}
                                                    </span>

                                                    <div className="space-y-3">
                                                        {/* Input Sample */}
                                                        <div>
                                                            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                                                                Input
                                                            </span>
                                                            <div className="bg-white p-2 rounded border border-gray-200 font-mono text-sm whitespace-pre-wrap">
                                                                {sample.input}
                                                            </div>
                                                        </div>

                                                        {/* Output Sample */}
                                                        <div>
                                                            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                                                                Output
                                                            </span>
                                                            <div className="bg-white p-2 rounded border border-gray-200 font-mono text-sm whitespace-pre-wrap">
                                                                {sample.output}
                                                            </div>
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
                                <div className="text-gray-400 mt-10 text-center">請從左側列表選擇一個題目開始練習。</div>
                            )}
                        </div>
                    </div>

                    {/* 右側：IDE 區 */}
                    <div className="w-1/2 flex flex-col bg-gray-50">
                        <div className="flex-1 bg-[#1e1e1e] text-gray-300 font-mono text-sm overflow-auto p-4 relative">
                            {loading && !studentCode ? (
                                <div className="absolute inset-0 flex items-center justify-center text-gray-500">Loading...</div>
                            ) : (
                                <pre className="whitespace-pre-wrap">{studentCode || "# Write your code here"}</pre>
                            )}
                        </div>
                        <div className="h-1/3 bg-white border-t border-gray-200 flex flex-col">
                            <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex justify-between items-center shrink-0">
                                <span className="text-xs font-bold text-gray-500 uppercase">Terminal</span>
                                <button className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-4 py-1.5 rounded">Run Code</button>
                            </div>
                            <div className="flex-1 p-4 overflow-auto font-mono text-sm text-gray-800">
                                {result || "Ready to run..."}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
export default PreCoding;