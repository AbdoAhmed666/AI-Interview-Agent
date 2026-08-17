from pydantic import BaseModel


class CVUploadResponse(BaseModel):
    uploaded: bool
    filename: str
    detected_skills: list[str]
    recommended_roles: list[str]


class CVListResponse(BaseModel):
    active_cv: str | None
    versions: list[str]


class CVAnalysisResponse(BaseModel):
    skills: list[str]
    frameworks: list[str]
    databases: list[str]
    projects: list[str]
    recommended_roles: list[str]