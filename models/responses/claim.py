from typing import Optional

from pydantic import BaseModel, Field


class BadgeUpdate(BaseModel):
    badgeId: str
    level: int
    points: int
    previousLevel: int


class Metadata(BaseModel):
    badgeId: int
    level: int
    minValue: int
    points: int


class BadgeTier(BaseModel):
    points: str
    tier: str
    uri: str
    metadata: Metadata


class Metadata1(BaseModel):
    name: str
    description: str
    platform: str
    chains: list[str]
    condition: str
    image: str
    stack_image: str = Field(..., alias="stack-image")
    season: Optional[int]


class UpdatedBadge(BaseModel):
    badgeId: str
    badgeTiers: list[BadgeTier]
    uri: str
    metadata: Metadata1
    points: int
    tier: int
    claimableTier: int
    claimable: bool


class ClaimResponse(BaseModel):
    hash: str
    isLevelUp: bool
    totalPoints: int
    badgeUpdates: list[BadgeUpdate]
    updatedBadges: list[UpdatedBadge]
