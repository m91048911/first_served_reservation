from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer,HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash

import jwt

SECRET_KEY = "bbdcdbaf099180b47286dc9f9739d8566b9b1843c068e5642aefbbf9b8b1e682"
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

bearer_scheme = HTTPBearer()


# 비밀번호 해싱
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# 패스워드 검증
def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )

# jwt토큰 생성
def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

# jwt토큰 검증
def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except jwt.InvalidTokenError:
            raise ValueError("유효하지 않은 토큰입니다.")

# def get_current_user_id(
#     token: str = Depends(oauth2_scheme)
# ) -> int:
#     try:
#         payload = verify_access_token(token)
#         user_id = payload.get("sub")
#         if user_id is None:
#             raise ValueError("토큰에 사용자 ID가 없습니다.")
#         return int(user_id)
#     except (ValueError, jwt.InvalidTokenError):
#         raise HTTPException(
#             status_code=401,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    token = credentials.credentials

    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError("토큰에 사용자 ID가 없습니다.")

        return int(user_id)

    except (ValueError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )