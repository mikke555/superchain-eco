from pydantic import BaseModel


class ClaimResponse(BaseModel):
    hash: str
    isLevelUp: bool
    badgeImages: list[str]
    totalPoints: int
