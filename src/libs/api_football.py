import os
from typing import Any, Dict, Optional, List

import requests
from dotenv import load_dotenv

from pydantic import ValidationError
from .api_football_models import (
	FixtureResult,
	FixtureTeam,
	PlayerSummary,
)
from .utils import ConfigLoader, CSVWriter

EXPECTED_BASE_URL = "https://v3.football.api-sports.io/"

load_dotenv()


# Funções de compatibilidade (para não quebrar imports externos)
def load_target_seasons(path: Optional[str] = None) -> List[int]:
	return ConfigLoader.load_seasons(path)


def load_target_leagues(path: Optional[str] = None) -> List[int]:
	return ConfigLoader.load_leagues(path)


class APIFootballClient:
	def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
		self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
		self.base_url = base_url or os.getenv("API_FOOTBALL_BASE_URL", EXPECTED_BASE_URL)
		if not self.api_key:
			raise ValueError("API_FOOTBALL_KEY nao configurada no ambiente.")
		if self.base_url.rstrip("/") != EXPECTED_BASE_URL.rstrip("/"):
			raise ValueError("Base URL da API deve ser https://v3.football.api-sports.io/ conforme documentacao.")
		self.session = requests.Session()
		self.session.headers.clear()
		self.session.headers.update({"x-apisports-key": self.api_key})

	def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
		url = self.base_url.rstrip("/") + "/" + endpoint.lstrip("/")
		response = self.session.get(url, params=params)
		response.raise_for_status()
		return response.json()


class MatchResultsService:
	def __init__(self, client: APIFootballClient):
		self.client = client

	def get_fixtures(self, **params) -> List[FixtureResult]:
		raw = self.client._get("fixtures", params)
		results: List[FixtureResult] = []
		for item in raw.get('response', []):
			fixture_info = item.get('fixture') or {}
			league_info = item.get('league') or {}
			teams_info = item.get('teams') or {}
			score_info = (item.get('score') or {}).get('fulltime') or {}

			home_team_data = teams_info.get('home') or {}
			away_team_data = teams_info.get('away') or {}

			try:
				results.append(
					FixtureResult(
						fixture_id=fixture_info.get('id'),
						date=fixture_info.get('date'),
						league_id=league_info.get('id'),
						league_name=league_info.get('name'),
						season=league_info.get('season'),
						home_team=FixtureTeam(
							id=home_team_data.get('id'),
							name=home_team_data.get('name'),
						),
						away_team=FixtureTeam(
							id=away_team_data.get('id'),
							name=away_team_data.get('name'),
						),
						fulltime_home=score_info.get('home'),
						fulltime_away=score_info.get('away'),
					)
				)
			except ValidationError as e:
				print(f"Erro de validação Fixture: {e}")
		CSVWriter.write_fixtures(results)
		return results


class TopScorersService:
	def __init__(self, client: APIFootballClient):
		self.client = client

	def get_topscorers(self, **params) -> List[PlayerSummary]:
		season_value = params.get("season")
		league_value = params.get("league")
		try:
			season_int = int(season_value) if season_value is not None else None
		except (TypeError, ValueError):
			season_int = None
		try:
			league_int = int(league_value) if league_value is not None else None
		except (TypeError, ValueError):
			league_int = None

		target_seasons = set(load_target_seasons())
		if target_seasons and (season_int is None or season_int not in target_seasons):
			return []
		target_leagues = set(load_target_leagues())
		if target_leagues and (league_int is None or league_int not in target_leagues):
			return []

		raw = self.client._get("players/topscorers", params)
		results: List[PlayerSummary] = []
		for item in raw.get('response', []):
			player_data = item.get('player') or {}
			statistics = (item.get('statistics') or [])
			primary_stat = statistics[0] if statistics else {}

			games = primary_stat.get('games') or {}
			goals = primary_stat.get('goals') or {}
			shots = primary_stat.get('shots') or {}
			team = primary_stat.get('team') or {}

			try:
				results.append(
					PlayerSummary(
						category="topscorers",
						player_id=player_data.get('id'),
						player_name=player_data.get('name'),
						team_id=team.get('id'),
						team_name=team.get('name'),
						league_id=league_int,
						season=season_int,
						appearences=games.get('appearences'),
						minutes=games.get('minutes'),
						goals=goals.get('total'),
						assists=goals.get('assists'),
						shots_total=shots.get('total'),
					)
				)
			except ValidationError as e:
				print(f"Erro de validação PlayerSummary (topscorers): {e}")
		if league_int is not None and season_int is not None:
			filename = f"top_scorers_league_{league_int}_season_{season_int}.csv"
		else:
			filename = 'top_scorers.csv'
		CSVWriter.write_players(filename, results)
		return results


class TopAssistsService:
	def __init__(self, client: APIFootballClient):
		self.client = client

	def get_topassists(self, **params) -> List[PlayerSummary]:
		season_value = params.get("season")
		league_value = params.get("league")
		try:
			season_int = int(season_value) if season_value is not None else None
		except (TypeError, ValueError):
			season_int = None
		try:
			league_int = int(league_value) if league_value is not None else None
		except (TypeError, ValueError):
			league_int = None

		target_seasons = set(load_target_seasons())
		if target_seasons and (season_int is None or season_int not in target_seasons):
			return []
		target_leagues = set(load_target_leagues())
		if target_leagues and (league_int is None or league_int not in target_leagues):
			return []

		raw = self.client._get("players/topassists", params)
		results: List[PlayerSummary] = []
		for item in raw.get('response', []):
			player_data = item.get('player') or {}
			statistics = (item.get('statistics') or [])
			primary_stat = statistics[0] if statistics else {}

			games = primary_stat.get('games') or {}
			goals = primary_stat.get('goals') or {}
			shots = primary_stat.get('shots') or {}
			team = primary_stat.get('team') or {}

			try:
				results.append(
					PlayerSummary(
						category="topassists",
						player_id=player_data.get('id'),
						player_name=player_data.get('name'),
						team_id=team.get('id'),
						team_name=team.get('name'),
						league_id=league_int,
						season=season_int,
						appearences=games.get('appearences'),
						minutes=games.get('minutes'),
						goals=goals.get('total'),
						assists=goals.get('assists'),
						shots_total=shots.get('total'),
					)
				)
			except ValidationError as e:
				print(f"Erro de validação PlayerSummary (topassists): {e}")
		if league_int is not None and season_int is not None:
			filename = f"top_assists_league_{league_int}_season_{season_int}.csv"
		else:
			filename = 'top_assists.csv'
		CSVWriter.write_players(filename, results)
		return results


class SeasonsService:
	def __init__(self, client: APIFootballClient):
		self.client = client

	def get_seasons(self) -> list:
		raw = self.client._get("leagues/seasons")
		seasons = raw.get('response', [])
		target_seasons = set(ConfigLoader.load_seasons())
		if target_seasons:
			filtered = [s for s in seasons if int(s) in target_seasons]
		else:
			filtered = seasons
		CSVWriter.save_json('sport/seasons', 'available_seasons.json', filtered)
		return filtered
