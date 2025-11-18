import csv
import os
import json
from typing import Any, Dict, Optional, List

from .api_football_models import FixtureResult, PlayerSummary

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
DATA_DIR = os.path.join(BASE_DIR, 'data')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
DEFAULT_TARGETS_CONFIG = os.path.join(CONFIG_DIR, 'config.json')


class ConfigLoader:
	"""Gerencia carregamento de configurações de seasons e leagues."""
	
	@staticmethod
	def _get_config_path(path: Optional[str] = None) -> str:
		if path:
			return path
		os.makedirs(CONFIG_DIR, exist_ok=True)
		return DEFAULT_TARGETS_CONFIG

	@staticmethod
	def _load_config(path: Optional[str] = None) -> Dict[str, Any]:
		config_path = ConfigLoader._get_config_path(path)
		if not os.path.exists(config_path):
			return {}
		try:
			with open(config_path, 'r', encoding='utf-8') as f:
				return json.load(f)
		except (json.JSONDecodeError, TypeError, ValueError):
			return {}

	@staticmethod
	def load_seasons(path: Optional[str] = None) -> List[int]:
		data = ConfigLoader._load_config(path)
		seasons = data.get('seasons', [])
		loaded: List[int] = []
		for season in seasons:
			try:
				loaded.append(int(season))
			except (TypeError, ValueError):
				continue
		return loaded

	@staticmethod
	def load_leagues(path: Optional[str] = None) -> List[int]:
		data = ConfigLoader._load_config(path)
		leagues = data.get('leagues', [])
		loaded: List[int] = []
		for league in leagues:
			try:
				loaded.append(int(league))
			except (TypeError, ValueError):
				continue
		return loaded


class CSVWriter:
	"""Escreve CSVs de dados extraídos."""
	
	@staticmethod
	def _ensure_directory(path: str) -> None:
		os.makedirs(path, exist_ok=True)

	@staticmethod
	def _model_to_dict(model: Any) -> Dict[str, Any]:
		if hasattr(model, "model_dump"):
			return model.model_dump()
		if hasattr(model, "dict"):
			return model.dict()
		raise TypeError("Model does not provide a serialization method")

	@staticmethod
	def save_json(subfolder: str, filename: str, data: Any) -> None:
		"""Salva dados em formato JSON."""
		data_dir = os.path.join(DATA_DIR, subfolder)
		CSVWriter._ensure_directory(data_dir)
		file_path = os.path.join(data_dir, filename)
		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)

	@staticmethod
	def write_players(filename: str, players: List[PlayerSummary]) -> None:
		data_dir = os.path.join(DATA_DIR, 'sport/players')
		CSVWriter._ensure_directory(data_dir)
		file_path = os.path.join(data_dir, filename)

		fieldnames = [
			'category', 'player_id', 'player_name', 'team_id', 'team_name',
			'league_id', 'season', 'appearences', 'minutes', 'goals', 'assists', 'shots_total',
		]

		with open(file_path, 'w', newline='', encoding='utf-8') as f:
			writer = csv.DictWriter(f, fieldnames=fieldnames)
			writer.writeheader()
			for player in players:
				writer.writerow(CSVWriter._model_to_dict(player))

	@staticmethod
	def write_fixtures(results: List[FixtureResult]) -> None:
		data_dir = os.path.join(DATA_DIR, 'sport/seasons')
		CSVWriter._ensure_directory(data_dir)

		target_seasons = set(ConfigLoader.load_seasons())
		target_leagues = set(ConfigLoader.load_leagues())
		fieldnames = [
			'fixture_id', 'date', 'league_id', 'league_name', 'season',
			'home_team_id', 'home_team_name', 'away_team_id', 'away_team_name',
			'fulltime_home', 'fulltime_away',
		]

		grouped: Dict[int, List[FixtureResult]] = {}
		for result in results:
			if result.season is None:
				continue
			season_key = int(result.season)
			if target_seasons and season_key not in target_seasons:
				continue
			if target_leagues:
				try:
					league_key = int(result.league_id) if result.league_id is not None else None
				except (TypeError, ValueError):
					continue
				if league_key is None or league_key not in target_leagues:
					continue
			grouped.setdefault(season_key, []).append(result)

		for season, season_results in grouped.items():
			file_path = os.path.join(data_dir, f'season_{season}_results.csv')
			with open(file_path, 'w', newline='', encoding='utf-8') as f:
				writer = csv.DictWriter(f, fieldnames=fieldnames)
				writer.writeheader()
				for result in season_results:
					writer.writerow({
						'fixture_id': result.fixture_id,
						'date': result.date,
						'league_id': result.league_id,
						'league_name': result.league_name,
						'season': result.season,
						'home_team_id': result.home_team.id,
						'home_team_name': result.home_team.name,
						'away_team_id': result.away_team.id,
						'away_team_name': result.away_team.name,
						'fulltime_home': result.fulltime_home,
						'fulltime_away': result.fulltime_away,
					})
