erDiagram
    %% --- 1. 使用者與角色 ---
    ROLES {
        INTEGER id PK
        VARCHAR(50) name UK "角色名稱: 如teacher, student, TA"
    }
    
    %% 11/07已建立(FK未開)
    USERS {
        INTEGER id PK 
        VARCHAR(255) email UK "登入Email"
        VARCHAR(100) full_name "使用者名稱"
        INTEGER role_id FK "使用者角色 (FK -> ROLES.id)"
        DATETIME created_time 
        DATETIME last_login_time
    }
    
    USER_AUTHENTICATIONS {
        INTEGER id PK
        INTEGER user_id FK "使用者 (FK -> USERS.id)"
        VARCHAR(50) provider "驗證提供者: 如local, google"
        VARCHAR(255) password "加密後的使用者密碼"
    }
    STUDENT_PROFILES {
        INTEGER user_id PK, FK "-> USERS.id (一對一主鍵)"
        VARCHAR(100) student_id UK "學號 (e.g., '109xxxxxx')"
        VARCHAR(100) major "科系 (可選)"
        INTEGER enrollment_year "入學年份 (可選, e.g., 109)"
    }

    %% --- 2. 課程與選課 ---
    
    %% 11/07已建立(FK未開)
    COURSES {
        INTEGER id PK
        INTEGER teacher_id FK "授課教師(FK -> USERS.id)"
        VARCHAR(100) semester_name "學期名稱，如: 1141"
        VARCHAR(255) name "課程名稱，如: 創意學習"
        TEXT description "課程簡介"
        DATETIME created_at "課程建立時間"
    }
    
    ENROLLMENTS {
        INTEGER user_id PK, FK "學生ID (PK, FK -> USERS.id)"
        INTEGER course_id PK, FK "課程ID (PK, FK -> COURSES.id)"
        DATETIME enrolled_at "選課時間"
    }

    %% --- 3. 教材上傳與 RAG 處理 ---
    UNIQUE_CONTENTS {
        INTEGER id PK
        VARCHAR(64) content_hash UK "SHA-256 hash of the file content"
        INTEGER file_size_bytes
        VARCHAR(20) original_file_type "e.g., 'pdf', 'docx'"
        VARCHAR(20) processing_status "'pending', 'completed', 'failed'"
        DATETIME created_at "上傳時間"
    }
    
    MATERIALS {
        INTEGER id PK
        INTEGER course_id FK "FK -> COURSES.id"
        INTEGER uploader_id FK "上傳者 (FK -> USERS.id)"
        INTEGER course_unit_id FK "-> COURSE_UNITS.id (所屬單元, 可 NULL)"
        VARCHAR(255) file_name "教材檔名"
        INTEGER unique_content_id FK "FK -> UNIQUE_CONTENTS.id"
    }
    
    %% 教材對應的知識點(以老師輸入為主，AI提取+HITL為輔，多對多)
    MATERIAL_KNOWLEDGE_POINTS {
        INTEGER material_id PK, FK "-> MATERIALS.id"
        INTEGER knowledge_point_id PK, FK "-> KNOWLEDGE_POINTS.id"
    }
    
    MATERIAL_PREVIEWS {
        INTEGER id PK
        INTEGER unique_content_id FK "FK -> UNIQUE_CONTENTS.id"
        INTEGER page_number "在原文件中的頁碼或順序"
        TEXT extracted_text "該頁的純文字"
        TEXT ocr_text "該頁的 OCR 文字"
        VARCHAR(512) preview_image_path "該頁的預覽圖儲存路徑"
    }
    DOCUMENT_CHUNKS {
        INTEGER id PK
        INTEGER unique_content_id FK "FK -> UNIQUE_CONTENTS.id"
        TEXT chunk_text
        INTEGER chunk_order "在原文件中的順序"
        JSON metadata "額外資訊 (如頁碼、章節)"
        VECTOR(1536) embedding "文字向量"
    }

    %% --- 4. AI Agent 生成流程 ---
    %% 每個Query觸發紀錄一次
    ORCHESTRATION_JOBS {
        INTEGER id PK
        INTEGER user_id FK "Input Query的教師，FK -> USERS.id"
        TEXT input_prompt "教師輸入的Query"
        VARCHAR(50) status "'planning', 'rejected', etc., 'completed'"
        INTEGER final_output_id FK "-> GENERATED_CONTENTS.id"
        DATETIME created_at "任務開始時間"
        DATETIME updated_at "任務最後更新時間"
        
        %% 實驗設定
        VARCHAR(50) workflow_type "實驗組別, including '1_no_critic', '2_fact_only', '3_qual_only', 4_all_critics'"
			  JSON experiment_config "詳細實驗參數, e.g., {'ragas_threshold': 0.8}"
			  
			  %% 實驗數據logs
			  INTEGER total_iterations "總迭代次數"
        INTEGER total_latency_ms "總執行時間 (毫秒)"
        INTEGER total_prompt_tokens "總輸入 Tokens"
        INTEGER total_completion_tokens "總輸出 Tokens"
        DECIMAL estimated_carbon_g "預估碳排放 (克)"
    }
    ORCHESTRATION_JOB_SOURCES {
        INTEGER job_id PK, FK "-> ORCHESTRATION_JOBS.id"
        VARCHAR(20) source_type PK "'content' or 'chunk'"
        INTEGER source_id PK "e.g., unique_content_id or document_chunk_id"
    }
    
    %% 每個Agent被分派到工作時觸發紀錄一次
    AGENT_TASKS {
        INTEGER id PK
        INTEGER job_id FK "FK -> ORCHESTRATION_JOBS.id"
        INTEGER parent_task_id FK "Self-ref for dependency"
        INTEGER iteration_number "當前是第幾次迭代 (e.g., 1, 2...)"
        
        %% 執行任務內容
        VARCHAR(100) agent_name "Agent名稱(與負責任務有關)"
        TEXT task_description "給老師看的任務描述"
        JSON task_input "輸入Agent的完整Prompt或參數"
        TEXT output "Agent的原始輸出 (JSON 或文字)"
        VARCHAR(50) status "'pending', 'in_progress', 'completed', failed'"
        TEXT error_message "錯誤訊息 (如果失敗)"
        
        %% --- 效能與成本追蹤 ---
        INTEGER duration_ms "執行耗時 (毫秒)"
        INTEGER prompt_tokens "輸入 Tokens"
        INTEGER completion_tokens "輸出 Tokens"
        DECIMAL estimated_cost_usd "預估成本 (美金)"
        
        %% --- 模型版本控制 (確保實驗可重現) ---
        VARCHAR(100) model_name "使用的模型 (e.g., 'gpt-4o')"
        JSON model_parameters "模型參數 (e.g., {'temperature': 0.7})"
        
        DATETIME created_at "任務建立時間"
        DATETIME completed_at "任務完成時間"
    }
    AGENT_TASK_SOURCES {
        INTEGER task_id PK, FK "-> AGENT_TASKS.id"
        VARCHAR(20) source_type PK "'content' or 'chunk'"
        INTEGER source_id PK "e.g., unique_content_id or document_chunk_id"
    }
    
    TASK_EVALUATIONS {
        INTEGER id PK
        INTEGER task_id FK "-> AGENT_TASKS.id"
        
        %% --- 評估階段 ---
        INTEGER evaluation_stage "評估階段 (1=Fact, 2=Quality)"
        VARCHAR(50) critic_type "'fact_critic' or 'quality_critic'"
        
        %% --- 評估結果 ---
        BOOLEAN is_passed "此階段是否通過"
        TEXT feedback_for_generator "給 Generator 的具體修改建議 (用於下一輪迭代)"
        JSON metric_details "儲存 Ragas 或 G-Eval 的所有細項分數"
        
        DATETIME evaluated_at "評估時間"
    }
    
    GENERATED_CONTENTS {
        INTEGER id PK
        INTEGER source_agent_task_id FK "-> AGENT_TASKS.id"
        VARCHAR(50) content_type NOT NULL "e.g., 'multiple_choice', 'summary'"
        JSON content NOT NULL "儲存生成結果之結構化內容(json)"
        INTEGER teacher_rating "教師對於此次生成結果的回饋"
        VARCHAR(255) title NOT NULL "教材標題"
        DATETIME created_at
        DATETIME updated_at
    }
    
    CONTENT_EDIT_HISTORY {
        INTEGER id PK
        INTEGER generated_content_id FK "-> GENERATED_CONTENTS.id"
        INTEGER user_id FK "-> USERS.id"
        JSON diff_content "儲存修改的 diff"
        DATETIME edited_at
    }

    %% --- 5. 課程內容 (公告、作業、繳交) ---
    ANNOUNCEMENTS {
        INTEGER id PK
        INTEGER course_id FK "-> COURSES.id"
        INTEGER author_id FK "-> USERS.id (發布人)"
        VARCHAR(255) title "公告標題"
        TEXT content NOT NULL "公告內容"
        BOOLEAN is_visible "是否顯示給學生"
        DATETIME created_at
    }
    ANNOUNCEMENT_ATTACHMENTS {
        INTEGER id PK
        INTEGER announcement_id FK "-> ANNOUNCEMENTS.id"
        VARCHAR(255) file_name
        VARCHAR(512) file_path
    }
    ASSIGNMENTS {
        INTEGER id PK
        INTEGER course_id FK "-> COURSES.id"
        INTEGER course_unit_id FK "所屬章節 (FK -> COURSE_UNITS.id, 可為 NULL 如果是涵蓋多個單元的作業)"
        INTEGER author_id FK "發布人 (FK -> USERS.id)"
        VARCHAR(255) title "作業標題"
        TEXT description "作業說明"
        VARCHAR(50) assignment_type "'quiz', 'legacy_json', 'essay'"
        VARCHAR(50) assignment_timing "[新增] 作業時機 (e.g., 'pre_class', 'post_class', 可為 NULL)"
        JSON content "儲存作業的完整題目 (從 GENERATED_CONTENTS 複製, 可為 NULL)"
        INTEGER source_generated_content_id FK "-> GENERATED_CONTENTS(id) ON DELETE SET NULL"
        DATETIME due_date "截止日期"
        DATETIME created_at
    }
    ASSIGNMENT_ATTACHMENTS {
        INTEGER id PK
        INTEGER assignment_id FK "-> ASSIGNMENTS.id"
        VARCHAR(255) file_name
        VARCHAR(512) file_path
    }
    SUBMISSIONS {
        INTEGER id PK
        INTEGER assignment_id FK "-> ASSIGNMENTS.id"
        INTEGER user_id FK "-> USERS.id (繳交學生)"
        JSON content "學生提交的答案 (JSON 格式, e.g., {\answers\: [...]})"
        DECIMAL grade "分數"
        TEXT feedback "教師評語"
        DATETIME submitted_at "繳交時間"
    }
    SUBMISSION_ATTACHMENTS {
        INTEGER id PK
        INTEGER submission_id FK "-> SUBMISSIONS.id"
        VARCHAR(255) file_name
        VARCHAR(512) file_path
    }
    
    %% 教材管理，如設定學生是否可見或管理教材顯示順序
    COURSE_CONTENT_MAP {
        INTEGER id PK
        INTEGER course_id FK "-> COURSES.id"
        INTEGER course_unit_id FK "-> COURSE_UNITS.id (所屬單元)"
        
        %% --- 管理與排序 ---
        INTEGER display_order "在此單元中的手動拖曳順序"
        BOOLEAN is_visible "是否顯示給學生"
        DATETIME created_at "發布/建立日期 (用於日期排序)"
        
        %% --- 標題 (反正規化，方便查詢) ---
        VARCHAR(255) title "顯示的標題 (從來源複製)"

        %% --- 多態關聯 (Polymorphic Link) ---
        VARCHAR(50) content_type "內容類型 (e.g., 'material', 'generated', 'assignment')"
        INTEGER content_id "對應到 'material', 'generated_contents' 或 'assignments' 的 ID"
    }
    %% --- 6. 知識地圖 (Knowledge Map) ---
    COURSE_UNITS {
        INTEGER id PK
        INTEGER course_id FK "-> COURSES.id"
        VARCHAR(255) name "單元名稱 (e.g., 第三章 光合作用)"
        INTEGER week "周次"
        INTEGER display_order "單元顯示順序for教材管理與顯示"
    }
    KNOWLEDGE_POINTS {
        INTEGER id PK
        INTEGER unit_id FK "-> COURSE_UNITS.id"
        INTEGER course_id FK "-> COURSES.id"
        VARCHAR(255) name "知識點名稱 (e.g., 卡爾文循環)"
        INTEGER display_order "單元中知識點顯示順序for教材管理與顯示"
    }

    %% --- 7. 題庫 (Question Bank) ---
    QUESTIONS {
        INTEGER id PK
        INTEGER course_id FK "-> COURSES.id"
        INTEGER creator_id FK "-> USERS.id"
        INTEGER kp_id FK "-> KNOWLEDGE_POINTS.id"
        VARCHAR(50) question_type "'mcq', 'true_false', 'short_answer'"
        TEXT question_text "題幹"
        TEXT explanation "詳解 / 參考答案"
        VARCHAR(20) difficulty "'easy', 'medium', 'hard'"
        INTEGER source_generated_content_id FK "-> GENERATED_CONTENTS.id"
        DATETIME created_at
        DATETIME updated_at
    }
    QUESTION_OPTIONS {
        INTEGER id PK
        INTEGER question_id FK "-> QUESTIONS.id"
        TEXT option_text "選項文字 (e.g., 'A. ...')"
        BOOLEAN is_correct
        INTEGER sort_order
    }
    ASSIGNMENT_QUESTIONS {
        INTEGER assignment_id PK, FK "-> ASSIGNMENTS.id"
        INTEGER question_id PK, FK "-> QUESTIONS.id"
        INTEGER question_order
        DECIMAL points
    }

    %% --- 8. 知識追蹤 (Knowledge Tracing) 與回饋 ---
    STUDENT_KP_MASTERY {
        INTEGER user_id PK, FK "-> USERS.id"
        INTEGER kp_id PK, FK "-> KNOWLEDGE_POINTS.id"
        INTEGER course_id FK "-> COURSES.id"
        VARCHAR(50) mastery_label "掌握度標籤 (e.g., '精熟', '尚可', '待加強')"
        DATETIME last_updated_at
    }
    KT_MASTERY_LOG {
        INTEGER id PK
        INTEGER user_id FK "-> USERS.id"
        INTEGER kp_id FK "-> KNOWLEDGE_POINTS.id"
        INTEGER submission_id FK "-> SUBMISSIONS.id"
        INTEGER question_id FK "-> QUESTIONS.id"
        VARCHAR(50) mastery_label_before "計算前標籤 (e.g., '尚可')"
        VARCHAR(50) mastery_label_after "計算後標籤 (e.g., '精熟')"
        DATETIME calculated_at
    }
    KT_INTERPRETATIONS {
        INTEGER id PK
        INTEGER user_id FK "-> USERS.id"
        INTEGER course_id FK "-> COURSES.id"
        INTEGER triggering_submission_id FK "-> SUBMISSIONS.id"
        VARCHAR(50) status "'pending', 'completed'"
        VARCHAR(512) visualization_path "視覺化圖表儲存路徑 (e.g., /path/to/img.png)"
        DATETIME created_at
    }
    LEARNING_FEEDBACK {
        INTEGER id PK
        INTEGER interpretation_id FK "-> KT_INTERPRETATIONS.id"
        INTEGER recipient_user_id FK "-> USERS.id"
        VARCHAR(50) feedback_type "'student_personal', 'teacher_student_alert'"
        VARCHAR(50) feedback_timing "'pre_class', 'post_class'"
        TEXT content "Agent 生成的回饋文字 (e.g., '...掌握度待加強')"
        BOOLEAN is_read
        DATETIME created_at
    }
   

    %% --- 9. [新增] 推薦系統 ---
    STUDENT_RECOMMENDATIONS {
        INTEGER id PK
        INTEGER user_id FK "-> USERS.id"
        INTEGER course_id FK "-> COURSES.id"
        INTEGER kp_id FK "-> KNOWLEDGE_POINTS.id"
        INTEGER source_feedback_id FK "-> LEARNING_FEEDBACK.id"
        VARCHAR(50) recommendation_type "'question', 'material'"
        INTEGER recommended_question_id FK "-> QUESTIONS.id"
        INTEGER recommended_material_id FK "-> MATERIALS.id"
        TEXT recommendation_text "Agent 產生的推薦文字"
        VARCHAR(50) status "'pending', 'viewed', 'completed'"
        DATETIME created_at
    }


    %% --- 關聯定義 (Relationships) ---

    %% 原始關聯
    USERS ||--|{ ROLES : "has role"
    USERS ||--o{ USER_AUTHENTICATIONS : "has auth"
    USERS ||--|| STUDENT_PROFILES : "has profile"
    USERS ||--o{ ORCHESTRATION_JOBS : "starts"
    USERS ||--o{ CONTENT_EDIT_HISTORY : "edits"
    USERS ||--o{ COURSES : "teaches"
    USERS }o--|| ENROLLMENTS : "enrolls in"
    
    COURSES }o--|| ENROLLMENTS : "is enrolled by"
    USERS ||--o{ FEEDBACK : "submits"
    USERS ||--o{ MATERIALS : "uploads"
    USERS ||--o{ ASSIGNMENTS : "posts"
    USERS ||--o{ ANNOUNCEMENTS : "posts"
    COURSES ||--o{ MATERIALS : "has"
    COURSES ||--o{ ASSIGNMENTS : "has"
    COURSES ||--o{ ANNOUNCEMENTS : "has"
    COURSES ||--o{ FEEDBACK : "receives"
    COURSES ||--o{ MATERIALS : "has"
    UNIQUE_CONTENTS ||--|{ MATERIALS : "uploaded as"
    UNIQUE_CONTENTS ||--o{ MATERIAL_PREVIEWS : "has"
    UNIQUE_CONTENTS ||--o{ DOCUMENT_CHUNKS : "has"
    
    %% Agent Workflow關聯
    ORCHESTRATION_JOBS ||--o{ AGENT_TASKS : "comprises "
    AGENT_TASKS ||--o{ AGENT_TASKS : "parent of"
    AGENT_TASKS ||--o{ TASK_EVALUATIONS : "is evaluated by"
    AGENT_TASKS ||--o{ GENERATED_CONTENTS : "produces source for"
    ORCHESTRATION_JOBS ||--o{ GENERATED_CONTENTS : "results in"
    GENERATED_CONTENTS ||--o{ CONTENT_EDIT_HISTORY : "has history)"
    ORCHESTRATION_JOBS ||--o{ ORCHESTRATION_JOB_SOURCES : "references"
    AGENT_TASKS ||--o{ AGENT_TASK_SOURCES : "reference"
    
    ASSIGNMENTS ||--o{ ASSIGNMENT_ATTACHMENTS : "has"
    ANNOUNCEMENTS ||--o{ ANNOUNCEMENT_ATTACHMENTS : "has"
    USERS ||--o{ SUBMISSIONS : "submits"
    ASSIGNMENTS ||--o{ SUBMISSIONS : "receives"
    SUBMISSIONS ||--o{ SUBMISSION_ATTACHMENTS : "has"
    
    %% 教材管理關聯
    COURSES ||--o{ COURSE_CONTENT_MAP : "maps"
    COURSE_UNITS ||--o{ COURSE_CONTENT_MAP : "groups"

    %% 知識地圖 (Knowledge Map) 關聯
    COURSES ||--o{ COURSE_UNITS : "has"
    COURSE_UNITS ||--o{ KNOWLEDGE_POINTS : "has"
    COURSES ||--o{ KNOWLEDGE_POINTS : "contains"
    COURSE_UNITS ||--o{ ASSIGNMENTS : "organizes"
    COURSE_UNITS ||--o{ MATERIALS : "contains"
    MATERIALS }o--|| MATERIAL_KNOWLEDGE_POINTS : "is tagged to kp"
    KNOWLEDGE_POINTS }o--|| MATERIAL_KNOWLEDGE_POINTS : "has material"
    
    %% 題庫 (Question Bank) 關聯
    COURSES ||--o{ QUESTIONS : "has bank for"
    USERS ||--o{ QUESTIONS : "created by"
    GENERATED_CONTENTS ||--o{ QUESTIONS : "is source for"
    KNOWLEDGE_POINTS ||--o{ QUESTIONS : "is tested by"
    QUESTIONS ||--o{ QUESTION_OPTIONS : "has"
    ASSIGNMENTS }o--|| ASSIGNMENT_QUESTIONS : "is composed of"
    QUESTIONS }o--|| ASSIGNMENT_QUESTIONS : "is part of"

    %% KT 與回饋關聯
    USERS }o--|| STUDENT_KP_MASTERY : "has mastery"
    KNOWLEDGE_POINTS }o--|| STUDENT_KP_MASTERY : "is mastery of"
    COURSES }o--|| STUDENT_KP_MASTERY : "has mastery in"
    USERS ||--o{ KT_MASTERY_LOG : "generates log for"
    KNOWLEDGE_POINTS ||--o{ KT_MASTERY_LOG : "is log for"
    SUBMISSIONS ||--o{ KT_MASTERY_LOG : "triggers"
    QUESTIONS ||--o{ KT_MASTERY_LOG : "is about"
    USERS ||--o{ KT_INTERPRETATIONS : "is target for"
    COURSES ||--o{ KT_INTERPRETATIONS : "is for"
    SUBMISSIONS ||--o{ KT_INTERPRETATIONS : "is triggered by"
    KT_INTERPRETATIONS ||--o{ LEARNING_FEEDBACK : "generates"
    USERS ||--o{ LEARNING_FEEDBACK : "receives"

    %% [新增] 推薦系統關聯
    USERS ||--o{ STUDENT_RECOMMENDATIONS : "receives"
    COURSES ||--o{ STUDENT_RECOMMENDATIONS : "is for"
    KNOWLEDGE_POINTS ||--o{ STUDENT_RECOMMENDATIONS : "targets"
    LEARNING_FEEDBACK ||--o{ STUDENT_RECOMMENDATIONS : "is source for"
    QUESTIONS ||--o{ STUDENT_RECOMMENDATIONS : "is recommended"
    MATERIALS ||--o{ STUDENT_RECOMMENDATIONS : "is recommended"