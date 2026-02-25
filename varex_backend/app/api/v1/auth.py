# PATH: varex-backend/app/api/v1/auth.py
# ADD this endpoint to your existing auth router

from pydantic import BaseModel
from app.core.security import verify_password, get_password_hash

class ChangePasswordPayload(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password", summary="Change authenticated user password")
async def change_password(
    payload: ChangePasswordPayload,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    current_user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}
