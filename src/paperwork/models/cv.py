"""CV data model -- the contract between profile data and templates.

Every template receives an instance of CVData (serialized to dict).
Every profile YAML must validate against CVData.
This file IS the specification.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional


class ContactInfo(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website_link: Optional[str] = None


class Education(BaseModel):
    degree: str
    institution: str
    location: Optional[str] = None
    year: str
    grade: Optional[str] = None
    details: Optional[str] = None


class WorkExperience(BaseModel):
    position: str
    company: str
    years: str
    location: Optional[str] = None
    roles: list[str] = []


class CompetencyGroup(BaseModel):
    competency: str
    skills: list[str]


class Language(BaseModel):
    language: str
    level: str


class Certification(BaseModel):
    name: str
    issuer: str
    year: str


class CVData(BaseModel):
    """Root CV data object. Templates receive this as template context."""

    # Identity
    name: str
    titles: list[str] = []
    profile: Optional[str] = None
    photo: Optional[str] = None

    # Contact
    contact_info: ContactInfo = ContactInfo()

    # Sections (all optional -- templates render what they receive)
    competencies_and_skills: list[CompetencyGroup] = []
    education: list[Education] = []
    work_experience: list[WorkExperience] = []
    languages: list[Language] = []
    certifications: list[Certification] = []

    # Extensible: templates can access arbitrary extra fields
    extra: dict = {}
