"""Input contracts for forms and transactional data imports."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Login(StrictModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class Participant(StrictModel):
    lastName: str = Field(min_length=1, max_length=80)
    firstName: str = Field(min_length=1, max_length=80)
    organization: str = Field(default="", max_length=160)
    email: EmailStr
    role: Literal["докладчик", "слушатель", "организатор"] = "слушатель"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.casefold()


class BadgeUpdate(StrictModel):
    badgePrinted: bool


class Section(StrictModel):
    title: str = Field(min_length=1, max_length=160)
    room: str = Field(default="", max_length=80)
    startTime: str = Field(default="", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$|^$")
    capacity: int = Field(ge=1, le=10000)


class AttendanceCreate(StrictModel):
    participantId: int = Field(gt=0)
    sectionId: int = Field(gt=0)


class AttendanceUpdate(StrictModel):
    attended: bool


class ImportedParticipant(Participant):
    id: int = Field(gt=0)
    badgePrinted: bool = False
    createdAt: str = Field(default="", max_length=50)


class ImportedSection(Section):
    id: int = Field(gt=0)
    createdAt: str = Field(default="", max_length=50)


class ImportedAttendance(AttendanceCreate):
    id: int = Field(gt=0)
    status: Literal["зарегистрирован", "присутствовал", "отсутствовал"]
    registeredAt: str = Field(default="", max_length=50)
    updatedAt: str | None = Field(default=None, max_length=50)


class ImportBundle(StrictModel):
    confirm: Literal["REPLACE"]
    participants: list[ImportedParticipant] = Field(max_length=10000)
    sections: list[ImportedSection] = Field(max_length=1000)
    attendance: list[ImportedAttendance] = Field(max_length=50000)
    exportedAt: str = ""
    version: str = "3.0.0"

    @model_validator(mode="after")
    def coherent(self):
        pids = {p.id for p in self.participants}
        sids = {s.id for s in self.sections}
        if len(pids) != len(self.participants) or len(sids) != len(self.sections):
            raise ValueError("Повторяющиеся ID")
        if len({p.email for p in self.participants}) != len(self.participants):
            raise ValueError("Повторяющиеся email")
        pairs, aids, counts = set(), set(), {}
        for a in self.attendance:
            if a.participantId not in pids or a.sectionId not in sids:
                raise ValueError("Ссылка на отсутствующего участника или секцию")
            pair = (a.participantId, a.sectionId)
            if pair in pairs or a.id in aids:
                raise ValueError("Повторная регистрация")
            pairs.add(pair)
            aids.add(a.id)
            counts[a.sectionId] = counts.get(a.sectionId, 0) + 1
        if any(counts.get(s.id, 0) > s.capacity for s in self.sections):
            raise ValueError("Превышена вместимость секции")
        return self
