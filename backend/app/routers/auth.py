from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from datetime import timedelta
from app.core import get_db_dependency, verify_password, get_password_hash, create_access_token, get_current_user, settings

router = APIRouter(prefix="/api/auth", tags=["认证"])


class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None
    is_admin: bool
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, conn = Depends(get_db_dependency)):
    """用户注册"""
    with conn.cursor() as cursor:
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (user_data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 检查邮箱是否已存在
        if user_data.email:
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_data.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="邮箱已被注册")

        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        cursor.execute(
            "INSERT INTO users (username, email, hashed_password, is_admin, is_active) VALUES (%s, %s, %s, %s, %s)",
            (user_data.username, user_data.email, hashed_password, False, True)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            "SELECT id, username, email, is_admin, is_active FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

    return user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), conn = Depends(get_db_dependency)):
    """用户登录"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT id, username, email, hashed_password, is_admin, is_active FROM users WHERE username = %s",
            (form_data.username,)
        )
        user = cursor.fetchone()

    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user['is_active']:
        raise HTTPException(status_code=400, detail="用户已被禁用")

    # 创建token (sub 必须是字符串)
    access_token = create_access_token(
        data={"sub": str(user['id'])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "is_admin": user['is_admin'],
            "is_active": user['is_active']
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """用户登出 (客户端删除token即可)"""
    return {"message": "登出成功"}


# 预留第三方登录接口
@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """第三方登录 (待实现)"""
    raise HTTPException(status_code=501, detail=f"{provider} 登录暂未实现")


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str):
    """第三方登录回调 (待实现)"""
    raise HTTPException(status_code=501, detail=f"{provider} 登录暂未实现")
