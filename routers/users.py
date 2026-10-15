from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.user import UserCreate, UserResponse, UserUpdate, UserLogin
from security import hash_password, verify_password, create_access_token, get_current_user_id

router = APIRouter()

# jwt로 본인인증
@router.get("/users/me", response_model=UserResponse)
def get_me(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    db_user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return db_user


# 전체유저조회
@router.get(
        "/users",
        response_model=list[UserResponse]
    )
def get_users(db : Session = Depends(get_db)):
    return db.query(User).all()

# 유저한명조회
@router.get(
        "/users/{user_id}",
        response_model=UserResponse
    )
def get_user(
    user_id : int,
    db : Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        # 유저가 없으면 강제로 에러발생
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return db_user

# 유저생성
@router.post(
        "/users",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED
    )
def create_user(
    user : UserCreate,
    db : Session = Depends(get_db)
):
    db_user = User(
        name = user.name,
        age = user.age,
        password_hash = hash_password(user.password)
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except:
        db.rollback()
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Failed to create user"
        )

# 유저 정보 수정
@router.put(
        "/users/{user_id}",
        response_model=UserResponse
    )
def update_user(
    user_id : int,
    user : UserUpdate,
    db : Session = Depends(get_db)
):
    # 검색된 유저가 없으면 404에러
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None :
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    db_user.name = user.name
    db_user.age = user.age
    db.commit()
    db.refresh(db_user)
    return db_user

# 유저 삭제
@router.delete("/users/{user_id}")
def delete_user(
    user_id : int,
    db : Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None :
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    db.delete(db_user)
    db.commit()
    return {"message" : "User Deleted"}

# 로그인
@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db),
):
    db_user = (
        db.query(User)
        .filter(User.name == user.name)
        .first()
    )
    # 유저가 없을 때
    if db_user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )
    # 비밀번호가 틀릴 때
    if not verify_password(
        user.password,
        db_user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )
    access_token = create_access_token(db_user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
