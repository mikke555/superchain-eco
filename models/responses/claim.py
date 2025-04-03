from pydantic import BaseModel


class TierMetadata(BaseModel):
    badgeId: int
    level: int
    minValue: int
    points: int


class BadgeTier(BaseModel):
    points: str
    tier: str
    uri: str
    metadata: TierMetadata


class BadgeMetadata(BaseModel):
    name: str
    description: str


class UpdatedBadge(BaseModel):
    badgeId: str
    badgeTiers: list[BadgeTier]
    uri: str
    metadata: BadgeMetadata
    points: int
    tier: int
    claimableTier: int
    claimable: bool


class BadgeUpdate(BaseModel):
    badgeId: str
    level: int
    points: int
    previousLevel: int


class ClaimResponse(BaseModel):
    hash: str
    isLevelUp: bool
    totalPoints: int
    badgeUpdates: list[BadgeUpdate]
    updatedBadges: list[UpdatedBadge]
