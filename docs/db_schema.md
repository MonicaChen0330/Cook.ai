```mermaid
erDiagram
    %% --- 核心使用者與角色 ---
    ROLES {
        INTEGER id PK "角色ID"
        "VARCHAR(50)" name UK "角色名稱: 'teacher' 或 'student'"
    }
    USERS {
        INTEGER id PK "使用者ID"
        "VARCHAR(255)" email UK "登入Email"
        "VARCHAR(100)" full_name "全名"
        INTEGER role_id FK "關聯的角色ID"
    }
    USER_AUTHENTICATIONS {
        INTEGER id PK "驗證ID"
        INTEGER user_id FK "關聯的使用者ID"
        "VARCHAR(50)" provider "驗證提供者"
        "VARCHAR(255)" provider_user_id "提供者的ID或密碼雜湊"
    }

    %% --- 課程與教材 ---
    COURSES {
        INTEGER id PK "課程ID"
        "VARCHAR(255)" name "課程名稱"
        TEXT description "課程簡介, *支援 Markdown 格式*"
        INTEGER teacher_id FK "授課教師ID"
    }
    MATERIALS {
        INTEGER id PK "教材ID"
        "VARCHAR(255)" title "教材標題"
        TEXT content_html "RAG 生成的 HTML 內容"
        INTEGER course_id FK "所屬課程ID"
    }

    %% --- 學生選課 (多對多關係) ---
    ENROLLMENTS {
        INTEGER user_id PK, FK "學生ID"
        INTEGER course_id PK, FK "課程ID"
        DATETIME enrolled_at "選課時間"
    }

    %% --- 關聯定義 ---
    USERS ||--|{ ROLES : "has role"
    USERS ||--o{ USER_AUTHENTICATIONS : "has auth"
    USERS ||--o{ COURSES : "creates"
    COURSES ||--o{ MATERIALS : "contains"
    
    %% 多對多關聯的畫法
    USERS }o--|| ENROLLMENTS : "enrolls in"
    COURSES }o--|| ENROLLMENTS : "is enrolled by"
```