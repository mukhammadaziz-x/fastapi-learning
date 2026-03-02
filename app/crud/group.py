"""Group CRUD operations."""
from sqlalchemy.orm import Session
from typing import Optional

from app.models.group import Group, GroupMembership
from app.schemas.group import GroupCreate, GroupUpdate


def create_group(db: Session, data: GroupCreate, owner_id: int) -> Group:
    group = Group(
        name=data.name,
        description=data.description,
        owner_id=owner_id,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def get_group(db: Session, group_id: int) -> Optional[Group]:
    return db.query(Group).filter(Group.id == group_id).first()


def get_groups_by_owner(db: Session, owner_id: int) -> list[Group]:
    return db.query(Group).filter(Group.owner_id == owner_id).order_by(Group.created_at.desc()).all()


def get_groups_for_user(db: Session, user_id: int) -> list[Group]:
    """Get all groups a user is member of."""
    memberships = db.query(GroupMembership).filter(GroupMembership.user_id == user_id).all()
    group_ids = [m.group_id for m in memberships]
    if not group_ids:
        return []
    return db.query(Group).filter(Group.id.in_(group_ids)).all()


def update_group(db: Session, group_id: int, data: GroupUpdate) -> Optional[Group]:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    db.commit()
    db.refresh(group)
    return group


def delete_group(db: Session, group_id: int) -> bool:
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        return False
    db.delete(group)
    db.commit()
    return True


def add_members(db: Session, group_id: int, user_ids: list[int]) -> list[GroupMembership]:
    added = []
    for uid in user_ids:
        existing = db.query(GroupMembership).filter(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == uid
        ).first()
        if existing:
            continue
        m = GroupMembership(group_id=group_id, user_id=uid)
        db.add(m)
        added.append(m)
    db.commit()
    for m in added:
        db.refresh(m)
    return added


def remove_member(db: Session, group_id: int, user_id: int) -> bool:
    m = db.query(GroupMembership).filter(
        GroupMembership.group_id == group_id,
        GroupMembership.user_id == user_id
    ).first()
    if not m:
        return False
    db.delete(m)
    db.commit()
    return True


def get_members(db: Session, group_id: int) -> list[GroupMembership]:
    return db.query(GroupMembership).filter(
        GroupMembership.group_id == group_id
    ).all()


def get_member_count(db: Session, group_id: int) -> int:
    return db.query(GroupMembership).filter(
        GroupMembership.group_id == group_id
    ).count()
