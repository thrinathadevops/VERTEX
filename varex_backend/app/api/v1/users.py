from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_active_user, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_own_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/admin/all", response_model=list[UserResponse])
async def list_all_users(
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    raise HTTPException(status_code=501, detail="Implement with paginated DB query")
