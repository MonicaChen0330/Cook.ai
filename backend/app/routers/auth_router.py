"""
Authentication router: 處理使用者註冊、登入等功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy import Table, select, insert
from backend.app.utils.db_logger import engine, metadata

# 建立 Router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# 密碼加密設定 - 使用 Argon2（更安全，無長度限制）
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# 反射資料表
try:
    users_table = Table('users', metadata, autoload_with=engine)
    roles_table = Table('roles', metadata, autoload_with=engine)
    user_authentications_table = Table('user_authentications', metadata, autoload_with=engine)
    student_profiles_table = Table('student_profiles', metadata, autoload_with=engine)
except Exception as e:
    print(f"Error reflecting authentication tables: {e}")

# ==================== Pydantic Schemas ====================

class RegisterRequest(BaseModel):
    """註冊請求"""
    email: str = Field(..., description="使用者 Gmail 信箱 (必須包含 @gmail.com)")
    password: str = Field(..., min_length=6, description="使用者密碼 (至少 6 個字元)")
    full_name: str = Field(..., min_length=1, max_length=100, description="使用者姓名")
    student_id: str = Field(..., min_length=1, max_length=100, description="學號 (必填)")
    role: str = Field("student", description="使用者角色: teacher, student, TA (預設: student)")
    
    # 學生選填欄位
    major: Optional[str] = Field(None, max_length=100, description="科系 (可選)")
    enrollment_year: Optional[int] = Field(None, description="入學年份 (可選)")
    
    @field_validator('email')
    @classmethod
    def validate_gmail(cls, v: str) -> str:
        """檢查 Email 必須包含 @gmail.com"""
        if '@gmail.com' not in v:
            raise ValueError('Email 必須包含 @gmail.com')
        return v


class RegisterResponse(BaseModel):
    """註冊成功回應"""
    user_id: int
    email: str
    full_name: str
    role: str
    message: str = "註冊成功"


# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    """將明文密碼加密"""
    return pwd_context.hash(password)


def get_role_id(role_name: str) -> Optional[int]:
    """根據角色名稱取得 role_id"""
    with engine.connect() as conn:
        query = select(roles_table.c.id).where(roles_table.c.name == role_name)
        result = conn.execute(query).fetchone()
        return result[0] if result else None


# ==================== API Endpoints ====================

@router.post("/register", response_model=RegisterResponse)
async def register_user(request: RegisterRequest):
    """
    使用者註冊端點
    
    流程：
    1. 檢查 Email 和 Full Name 配對是否已存在（防止重複註冊）
    2. 驗證 Email 必須是 Gmail (@gmail.com)
    3. 驗證角色是否有效
    4. 建立 users 記錄
    5. 建立 user_authentications 記錄 (加密密碼)
    6. 如果是學生且有提供學號，建立 student_profiles 記錄
    """
    
    with engine.connect() as conn:
        # 1. 檢查 Email 和 Full Name 配對是否已存在（防止重複註冊）
        existing_user = conn.execute(
            select(users_table).where(
                (users_table.c.email == request.email) & 
                (users_table.c.full_name == request.full_name)
            )
        ).fetchone()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="此帳號已被註冊（Email 和姓名配對已存在）")
        
        # 2. 取得 role_id
        role_id = get_role_id(request.role)
        if not role_id:
            raise HTTPException(status_code=400, detail=f"無效的角色: {request.role}")
        
        # 3. 建立 users 記錄
        user_insert = insert(users_table).values(
            email=request.email,
            full_name=request.full_name,
            role_id=role_id
        )
        result = conn.execute(user_insert)
        user_id = result.inserted_primary_key[0]
        
        # 4. 建立 user_authentications 記錄
        hashed_password = hash_password(request.password)
        auth_insert = insert(user_authentications_table).values(
            user_id=user_id,
            provider="local",
            password=hashed_password
        )
        conn.execute(auth_insert)
        
        # 5. 建立 student_profiles 記錄（student_id 現在是必填）
        # 檢查學號是否重複
        existing_student = conn.execute(
            select(student_profiles_table).where(
                student_profiles_table.c.student_id == request.student_id
            )
        ).fetchone()
        
        if existing_student:
            conn.rollback()
            raise HTTPException(status_code=400, detail="此學號已被註冊")
        
        profile_insert = insert(student_profiles_table).values(
            user_id=user_id,
            student_id=request.student_id,
            major=request.major,
            enrollment_year=request.enrollment_year
        )
        conn.execute(profile_insert)
        
        # 提交事務
        conn.commit()
        
        return RegisterResponse(
            user_id=user_id,
            email=request.email,
            full_name=request.full_name,
            role=request.role
        )
