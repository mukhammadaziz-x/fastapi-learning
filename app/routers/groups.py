"""Group management router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import group as group_crud
from app.crud import user as user_crud
from app.schemas.group import GroupCreate, GroupUpdate, GroupResponse, GroupMemberAdd, GroupMemberResponse
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/groups", tags=["Groups"])


@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Create a student group."""
    group = group_crud.create_group(db, data, current_user.id)
    resp = GroupResponse.model_validate(group)
    resp.member_count = 0
    return resp


@router.get("/", response_model=list[GroupResponse])
def list_groups(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List groups. Teachers see owned groups; students see their groups."""
    if current_user.role in ("admin", "teacher"):
        groups = group_crud.get_groups_by_owner(db, current_user.id)
    else:
        groups = group_crud.get_groups_for_user(db, current_user.id)

    results = []
    for g in groups:
        resp = GroupResponse.model_validate(g)
        resp.member_count = group_crud.get_member_count(db, g.id)
        results.append(resp)
    return results


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    group = group_crud.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    resp = GroupResponse.model_validate(group)
    resp.member_count = group_crud.get_member_count(db, group_id)
    return resp


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int, data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    group = group_crud.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user.role == "teacher" and group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return group_crud.update_group(db, group_id, data)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    group = group_crud.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user.role == "teacher" and group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    group_crud.delete_group(db, group_id)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
def add_members(
    group_id: int, data: GroupMemberAdd,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Add members to a group."""
    group = group_crud.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if current_user.role == "teacher" and group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    added = group_crud.add_members(db, group_id, data.user_ids)
    return {"message": f"Added {len(added)} members"}


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
def list_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List group members."""
    members = group_crud.get_members(db, group_id)
    results = []
    for m in members:
        user = user_crud.get_user(db, m.user_id)
        results.append(GroupMemberResponse(
            id=m.id,
            user_id=m.user_id,
            username=user.username if user else "Unknown",
            full_name=user.full_name if user else None,
            joined_at=m.joined_at,
        ))
    return results


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int, user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "teacher")),
):
    """Remove member from group."""
    if not group_crud.remove_member(db, group_id, user_id):
        raise HTTPException(status_code=404, detail="Member not found")
