from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field

Gender = Literal["male", "female"]
CalendarType = Literal["solar", "lunar"]
LoveStatus = Literal["solo", "dating", "married", "reunion"]
CareerStatus = Literal["employee", "student", "freelance", "job_change"]
ThemeKey = Literal["health", "wealth", "love", "business", "study", "career"]
PeriodKey = Literal["month", "year"]


class ProfileInput(BaseModel):
    nickname: str = Field(min_length=1, max_length=20)
    gender: Gender
    calendar_type: CalendarType = "solar"
    is_leap_month: bool = False
    birth_date: date
    birth_time: time | None = None
    time_unknown: bool = False
    love_status: LoveStatus = "solo"
    career_status: CareerStatus = "employee"


class AnalyzeRequest(ProfileInput):
    as_of: date | None = None


class ThemeRequest(AnalyzeRequest):
    theme: ThemeKey


class PeriodRequest(AnalyzeRequest):
    period: PeriodKey
