"""Group model - student groups within subjects."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Teacher

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    owner = relationship("User", back_populates="groups_owned", foreign_keys=[owner_id])
    members = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")


class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships", foreign_keys=[user_id])
