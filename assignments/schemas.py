from pydantic import BaseModel, Field, model_validator, field_validator, constr
from typing import Optional, List
from datetime import date, datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=3, max_length=60)
    description: Optional[str] = Field(default=None, max_length=250)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[date] = None
    tags: List[constr(min_length=2, max_length=20)] = Field(default=[], max_length=5)
    is_done: bool = False

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v):
        if v and v < date.today():
            raise ValueError("Date mustn't be in the past!")
        return v

    @model_validator(mode='after')
    def check_desc_or_tags(self):
        if not self.description and not self.tags:
            raise ValueError("At least enter 'description' or 'tags'")
        return self


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=60)
    description: Optional[str] = Field(default=None, max_length=250)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    due_date: Optional[date] = None
    tags: Optional[List[constr(min_length=2, max_length=20)]] = Field(default=None, max_length=5)
    is_done: Optional[bool] = None

    @model_validator(mode='before')
    @classmethod
    def check_empty_body(cls, data: dict):
        if not data:
            raise ValueError("Body is empty!")
        return data

class TaskOut(TaskCreate):
    id: int
    created_at: datetime