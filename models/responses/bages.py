from typing import List, Optional

from pydantic import BaseModel, Field


class BadgeTierMetadata(BaseModel):
    badgeId: int
    level: int
    minValue: int
    image_2D: str = Field(..., alias="2DImage")
    image_3D: str = Field(..., alias="3DImage")
    points: int


class BadgeTier(BaseModel):
    points: int
    tier: int
    uri: str
    metadata: BadgeTierMetadata


class BadgeMetadata(BaseModel):
    name: str
    description: str
    platform: str
    chain: str
    condition: str


class CurrentBadge(BaseModel):
    badgeId: str
    badgeTiers: List[BadgeTier]
    uri: str
    metadata: BadgeMetadata
    points: int
    tier: int
    claimableTier: Optional[int] = None
    claimable: bool


class Badges(BaseModel):
    currentBadges: List[CurrentBadge]

    def total_points(self) -> int:
        """
        Calculates the total points from all current badges.

        Returns:
            int: The sum of points from all badges.
        """
        return sum(badge.points for badge in self.currentBadges)
