import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, List

import requests
from dotenv import load_dotenv

from pydantic import ValidationError
from .api_football_models import (
	FixtureResult,
	FixtureTeam,
	PlayerSummary,
)
from .utils import ConfigLoader, CSVWriter, setup_logger

EXPECTED_BASE_URL = "https://v3.football.api-sports.io/"

load_dotenv()

logger = setup_logger(__name__)


# Funções de compatibilidade (para não quebrar imports externos)
def load_target_seasons(path: Optional[str] = None) -> List[int]:
	return ConfigLoader.load_seasons(path)


def load_target_leagues(path: Optional[str] = None) -> List[int]:
	return ConfigLoader.load_leagues(path)


class APIFootballClient:
	def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, requests_per_minute: int = 10):
		self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")
		self.base_url = base_url or os.getenv("API_FOOTBALL_BASE_URL", EXPECTED_BASE_URL)
		self.requests_per_minute = requests_per_minute
		self.min_interval = 60.0 / requests_per_minute  # Intervalo mínimo entre requests em segundos
		self.last_request_time = 0.0
		
		if not self.api_key:
			raise ValueError("API_FOOTBALL_KEY nao configurada no ambiente.")
		if self.base_url.rstrip("/") != EXPECTED_BASE_URL.rstrip("/"):
			raise ValueError("Base URL da API deve ser https://v3.football.api-sports.io/ conforme documentacao.")
		self.session = requests.Session()
		self.session.headers.clear()
		self.session.headers.update({"x-apisports-key": self.api_key})

	def _wait_if_needed(self) -> None:
		"""Aguarda o tempo necessário para respeitar o rate limit."""
		current_time = time.time()
		time_since_last_request = current_time - self.last_request_time
		
		if time_since_last_request < self.min_interval:
			sleep_time = self.min_interval - time_since_last_request
			logger.info(f"Rate limit: aguardando {sleep_time:.2f}s")
			time.sleep(sleep_time)
		
		self.last_request_time = time.time()

	def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3) -> Any:
		url = self.base_url.rstrip("/") + "/" + endpoint.lstrip("/")
		params_str = f" | Params: {params}" if params else ""
		logger.info(f"API Call: {endpoint}{params_str}")
		
		for attempt in range(max_retries):
			self._wait_if_needed()
			
			response = self.session.get(url, params=params)
			logger.info(f"Status: {response.status_code}")
			
			# Verifica se há rate limit na resposta
			if response.status_code == 429:
				retry_after = int(response.headers.get('Retry-After', 60))
				logger.warning(f"Rate limit atingido. Tentativa {attempt + 1}/{max_retries}. Aguardando {retry_after}s")
				time.sleep(retry_after)
				continue
			
			response.raise_for_status()
			data = response.json()
			
			# Verifica se há mensagem de rate limit no corpo da resposta
			if isinstance(data, dict) and 'rateLimit' in data:
				logger.warning(f"Rate limit detectado: {data['rateLimit']}. Tentativa {attempt + 1}/{max_retries}. Aguardando 60s")
				time.sleep(60)
				continue
			
			response_count = len(data.get('response', []))
			logger.info(f"Response Count: {response_count} items")
			return data
		
		raise Exception(f"Falha após {max_retries} tentativas devido a rate limit")


class BaseService:
	"""Classe base para todos os serviços."""
	
	def __init__(self, client: APIFootballClient):
		self.client = client
	
	def _check_file_cache(self, file_path: Path) -> bool:
		"""Verifica se arquivo existe no cache."""
		if file_path.exists():
			logger.info(f"Cache: {file_path.name} já existe, pulando chamada API")
			return True
		return False


class MatchResultsService(BaseService):
	def get_fixtures(self, **params) -> List[FixtureResult]:
		season = params.get('season')
		league = params.get('league')
		
		if season and league:
			data_dir = Path(__file__).parent.parent.parent / 'data' / 'sport' / 'seasons'
			filename = f'season_{season}_league_{league}_results.csv'
			if self._check_file_cache(data_dir / filename):
				return []
		
		raw = self.client._get("fixtures", params)
		response_data = raw.get('response', [])

		if not response_data:
			logger.error(f"Nenhum fixture retornado para os parâmetros: {params}")
			print(raw)
			raise ValueError(f"Nenhum fixture retornado para os parâmetros: {params}")
		
		results: List[FixtureResult] = []
		for item in response_data:
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
				logger.warning(f"Erro de validação Fixture: {e}")
		CSVWriter.write_fixtures(results)
		return results


class BasePlayerService(BaseService):
	"""Classe base para serviços de estatísticas de jogadores."""
	
	def _parse_params(self, params: Dict[str, Any]) -> tuple[Optional[int], Optional[int]]:
		"""Extrai e valida league_id e season dos parâmetros."""
		try:
			season_int = int(params.get("season")) if params.get("season") is not None else None
		except (TypeError, ValueError):
			season_int = None
		try:
			league_int = int(params.get("league")) if params.get("league") is not None else None
		except (TypeError, ValueError):
			league_int = None
		return league_int, season_int
	
	def _check_targets(self, league_int: Optional[int], season_int: Optional[int]) -> bool:
		"""Verifica se league e season estão nos targets configurados."""
		target_seasons = set(load_target_seasons())
		if target_seasons and (season_int is None or season_int not in target_seasons):
			return False
		target_leagues = set(load_target_leagues())
		if target_leagues and (league_int is None or league_int not in target_leagues):
			return False
		return True
	
	def _check_cache(self, category: str, league_int: int, season_int: int) -> bool:
		"""Verifica se o arquivo já existe no cache."""
		data_dir = Path(__file__).parent.parent.parent / 'data' / 'sport' / 'players'
		filename = f"{category}_league_{league_int}_season_{season_int}.csv"
		return self._check_file_cache(data_dir / filename)
	
	def _parse_player_data(self, item: Dict[str, Any], category: str, league_int: int, season_int: int) -> Optional[PlayerSummary]:
		"""Extrai dados de um jogador da resposta da API."""
		player_data = item.get('player') or {}
		statistics = (item.get('statistics') or [])
		primary_stat = statistics[0] if statistics else {}

		games = primary_stat.get('games') or {}
		goals = primary_stat.get('goals') or {}
		shots = primary_stat.get('shots') or {}
		team = primary_stat.get('team') or {}

		try:
			return PlayerSummary(
				category=category,
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
		except ValidationError as e:
			logger.warning(f"Erro de validação PlayerSummary ({category}): {e}")
			return None


class TopScorersService(BasePlayerService):
	def get_topscorers(self, **params) -> List[PlayerSummary]:
		league_int, season_int = self._parse_params(params)
		
		if not self._check_targets(league_int, season_int):
			return []
		
		if league_int is not None and season_int is not None:
			if self._check_cache("top_scorers", league_int, season_int):
				return []

		raw = self.client._get("players/topscorers", params)
		response_data = raw.get('response', [])
		
		if not response_data:
			logger.error(f"Nenhum top scorer retornado para league={league_int}, season={season_int}")
			print(raw)
		
		results = [
			player for item in response_data
			if (player := self._parse_player_data(item, "topscorers", league_int, season_int)) is not None
		]
		
		filename = f"top_scorers_league_{league_int}_season_{season_int}.csv" if league_int and season_int else 'top_scorers.csv'
		CSVWriter.write_players(filename, results)
		return results


class TopAssistsService(BasePlayerService):
	def get_topassists(self, **params) -> List[PlayerSummary]:
		league_int, season_int = self._parse_params(params)
		
		if not self._check_targets(league_int, season_int):
			return []
		
		if league_int is not None and season_int is not None:
			if self._check_cache("top_assists", league_int, season_int):
				return []

		raw = self.client._get("players/topassists", params)
		response_data = raw.get('response', [])
		
		if not response_data:
			logger.warning(f"Nenhum top assist retornado para league={league_int}, season={season_int}")
			print(raw)
		
		results = [
			player for item in response_data
			if (player := self._parse_player_data(item, "topassists", league_int, season_int)) is not None
		]
		
		filename = f"top_assists_league_{league_int}_season_{season_int}.csv" if league_int and season_int else 'top_assists.csv'
		CSVWriter.write_players(filename, results)
		return results