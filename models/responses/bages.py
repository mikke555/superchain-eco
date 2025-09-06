from typing import Optional, Union

from pydantic import BaseModel


class BadgeMetadata(BaseModel):
    name: str


class CurrentBadge(BaseModel):
    badgeId: str
    metadata: BadgeMetadata
    points: int
    tier: int
    currentCount: Optional[Union[int, float]] = None


class BadgesResponse(BaseModel):
    currentBadges: list[CurrentBadge]

    def total_points(self) -> int:
        """
        Calculates the total points from all current badges.

        Returns:
            int: The sum of points from all badges.
        """
        return sum(badge.points for badge in self.currentBadges)

    def get_badges_info(self) -> list[CurrentBadge]:
        badges = []
        for badge in self.currentBadges:
            if int(badge.badgeId) in [1, 2, 3, 10, 17, 16]:
                badges.append(badge)

        return badges

    def get_badge_by_id(self, badge_id: str) -> CurrentBadge | None:
        for badge in self.currentBadges:
            if badge.badgeId == badge_id:
                return badge
        return None

    def filter_badges_by_tier(self, tier: int) -> list[CurrentBadge]:
        return [badge for badge in self.currentBadges if badge.tier == tier]
