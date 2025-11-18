from typing import Optional

from pydantic import BaseModel


class FixtureTeam(BaseModel):
	id: Optional[int]
	name: Optional[str]


class FixtureResult(BaseModel):
	fixture_id: int
	date: str
	league_id: Optional[int]
	league_name: Optional[str]
	season: Optional[int]
	home_team: FixtureTeam
	away_team: FixtureTeam
	fulltime_home: Optional[int]
	fulltime_away: Optional[int]


class PlayerSummary(BaseModel):
	category: str
	player_id: Optional[int]
	player_name: Optional[str]
	team_id: Optional[int]
	team_name: Optional[str]
	league_id: Optional[int] = None
	season: Optional[int] = None
	appearences: Optional[int]
	minutes: Optional[int]
	goals: Optional[int]
	assists: Optional[int]
	shots_total: Optional[int]
