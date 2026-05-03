"""
Pydantic-модели для валидации входящих данных
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Participant(BaseModel):
    lastName:     str      = Field(..., min_length=1)
    firstName:    str      = Field(..., min_length=1)
    organization: str      = ""
    email:        EmailStr
    role:         str      = Field(..., pattern="^(докладчик|слушатель|организатор)$")


class ParticipantUpdate(BaseModel):
    badgePrinted: Optional[bool] = None


class Section(BaseModel):
    title:     str = Field(..., min_length=1)
    room:      str = ""
    startTime: str = ""
    capacity:  int = Field(..., ge=1)


class AttendanceCreate(BaseModel):
    participantId: int
    sectionId:     int


class AttendanceUpdate(BaseModel):
    attended: bool
