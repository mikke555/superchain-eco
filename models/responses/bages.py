from pydantic import BaseModel


class Metadata1(BaseModel):
    name: str


class CurrentBadge(BaseModel):
    badgeId: str
    metadata: Metadata1
    points: int
    tier: int


class BadgesResponse(BaseModel):
    currentBadges: list[CurrentBadge]

    def total_points(self) -> int:
        """
        Calculates the total points from all current badges.

        Returns:
            int: The sum of points from all badges.
        """
        return sum(badge.points for badge in self.currentBadges)
