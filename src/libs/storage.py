import logging
import os
from pathlib import Path

import boto3
import psycopg2
from dotenv import load_dotenv

from .utils import setup_logger

load_dotenv()

logger = setup_logger(__name__)


class S3Uploader:
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME não configurado")
        self.s3_client = boto3.client('s3')

    def upload_file(self, local_path: Path, s3_key: str) -> None:
        """Faz upload de um arquivo local para o S3."""
        self.s3_client.upload_file(str(local_path), self.bucket_name, s3_key)

    def clear_sport_data(self) -> None:
        """Remove todos os arquivos da pasta sport/ no S3."""
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix='sport/')
        
        for page in pages:
            if 'Contents' in page:
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                if objects:
                    self.s3_client.delete_objects(
                        Bucket=self.bucket_name,
                        Delete={'Objects': objects}
                    )

    def upload_sport_data(self, data_dir: Path) -> None:
        """Faz upload de todos os CSVs de dados esportivos para o S3 com particionamento."""
        self.clear_sport_data()
        
        seasons_dir = data_dir / "sport" / "seasons"
        players_dir = data_dir / "sport" / "players"

        if seasons_dir.exists():
            for csv_file in seasons_dir.glob("season_*_league_*_results.csv"):
                parts = csv_file.stem.split('_')
                # season_2024_league_475_results -> parts[1]=2024, parts[3]=475
                season = parts[1]
                league = parts[3]
                s3_key = f"sport/seasons/season={season}/league={league}/{csv_file.name}"
                self.upload_file(csv_file, s3_key)

        if players_dir.exists():
            for csv_file in players_dir.glob("*.csv"):
                # Arquivo: top_scorers_league_71_season_2023.csv
                parts = csv_file.stem.split('_')
                stat_type = '_'.join(parts[:2])  # top_scorers
                league = parts[3]  # 71
                season = parts[5]  # 2023
                # Estrutura: sport/players/top_scorers/league=71/season=2023/arquivo.csv
                s3_key = f"sport/players/{stat_type}/league={league}/season={season}/{csv_file.name}"
                self.upload_file(csv_file, s3_key)

    def upload_financial_data(self, data_dir: Path) -> None:
        """Faz upload de todos os CSVs de dados financeiros para o S3."""
        financial_dir = data_dir / "financial"
        
        if not financial_dir.exists():
            return
        
        # Upload de transfers
        transfers_dir = financial_dir / "transfers"
        if transfers_dir.exists():
            for csv_file in transfers_dir.glob("*.csv"):
                s3_key = f"financial/_data_treated/transfers/{csv_file.name}"
                self.upload_file(csv_file, s3_key)
        
        # Upload de balances
        balances_dir = financial_dir / "balances"
        if balances_dir.exists():
            for csv_file in balances_dir.glob("*.csv"):
                s3_key = f"financial/_data_treated/balances/{csv_file.name}"
                self.upload_file(csv_file, s3_key)


class PostgresLoader:
    def __init__(self):
        self.conn_params = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "soccer_db"),
            "user": os.getenv("DB_USER", "admin"),
            "password": os.getenv("DB_PASSWORD"),
        }
        if not self.conn_params["password"]:
            raise ValueError("DB_PASSWORD não configurado")

    def _get_connection(self):
        """Cria e retorna uma conexão com o PostgreSQL."""
        return psycopg2.connect(**self.conn_params)

    def create_schema(self) -> None:
        """Cria as tabelas e índices no PostgreSQL."""
        schema_path = Path(__file__).parent.parent.parent / "data" / "sql" / "schema.sql"
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
                conn.commit()
        finally:
            conn.close()

    def truncate_tables(self) -> None:
        """Limpa todas as tabelas antes de recarregar os dados."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE fixtures, top_scorers, top_assists CASCADE;")
                conn.commit()
        finally:
            conn.close()

    def _parse_int(self, value: str | None) -> int | None:
        """Converte string para int, retornando None se vazio ou inválido."""
        if not value or value.strip() == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_timestamp(self, value: str | None) -> str | None:
        """Retorna timestamp como string, ou None se vazio."""
        if not value or value.strip() == '':
            return None
        return value.strip()

    def load_fixtures_csv(self, csv_path: Path) -> None:
        """Carrega CSV de fixtures extraindo season e league_id do nome do arquivo."""
        import csv
        
        # Extrai season e league_id do nome: season_2023_league_11_results.csv
        parts = csv_path.stem.split('_')
        season = int(parts[1])  # 2023
        league_id = int(parts[3])  # 11
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        fixture_id = self._parse_int(row.get('fixture_id'))
                        if fixture_id is None:
                            continue
                        
                        cur.execute(
                            """INSERT INTO fixtures 
                               (fixture_id, date, league_id, league_name, season,
                                home_team_id, home_team_name, away_team_id, away_team_name,
                                fulltime_home, fulltime_away)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               ON CONFLICT (fixture_id) DO NOTHING""",
                            (
                                fixture_id,
                                self._parse_timestamp(row.get('date')),
                                league_id,
                                row.get('league_name', '').strip() or None,
                                season,
                                self._parse_int(row.get('home_team_id')),
                                row.get('home_team_name', '').strip() or None,
                                self._parse_int(row.get('away_team_id')),
                                row.get('away_team_name', '').strip() or None,
                                self._parse_int(row.get('fulltime_home')),
                                self._parse_int(row.get('fulltime_away')),
                            )
                        )
                conn.commit()
        finally:
            conn.close()
    
    def load_players_csv(self, csv_path: Path, table_name: str) -> None:
        """Carrega CSV de players extraindo league_id e season do nome do arquivo."""
        import csv
        
        # Extrai league_id e season do nome: top_scorers_league_11_season_2023.csv
        parts = csv_path.stem.split('_')
        league_id = int(parts[3])  # 11
        season = int(parts[5])  # 2023
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        player_id = self._parse_int(row.get('player_id'))
                        if player_id is None:
                            continue
                        
                        cur.execute(
                            f"""INSERT INTO {table_name}
                               (category, player_id, player_name, team_id, team_name,
                                league_id, season, appearences, minutes, goals, assists, shots_total)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               ON CONFLICT (player_id, league_id, season) DO NOTHING""",
                            (
                                row.get('category', '').strip() or None,
                                player_id,
                                row.get('player_name', '').strip() or None,
                                self._parse_int(row.get('team_id')),
                                row.get('team_name', '').strip() or None,
                                league_id,
                                season,
                                self._parse_int(row.get('appearences')),
                                self._parse_int(row.get('minutes')),
                                self._parse_int(row.get('goals')),
                                self._parse_int(row.get('assists')),
                                self._parse_int(row.get('shots_total')),
                            )
                        )
                conn.commit()
        finally:
            conn.close()

    def load_all_data(self, data_dir: Path) -> None:
        """Carrega todos os CSVs nos respectivas tabelas PostgreSQL."""
        self.truncate_tables()
        
        seasons_dir = data_dir / "sport" / "seasons"
        players_dir = data_dir / "sport" / "players"

        if seasons_dir.exists():
            for csv_file in seasons_dir.glob("season_*_league_*_results.csv"):
                self.load_fixtures_csv(csv_file)

        if players_dir.exists():
            for csv_file in players_dir.glob("top_scorers_*.csv"):
                self.load_players_csv(csv_file, "top_scorers")

            for csv_file in players_dir.glob("top_assists_*.csv"):
                self.load_players_csv(csv_file, "top_assists")


class GlueCrawlerRunner:
    def __init__(self):
        self.glue_client = boto3.client('glue')

    def start_crawler(self, crawler_name: str) -> None:
        """Inicia um crawler do AWS Glue."""
        try:
            self.glue_client.start_crawler(Name=crawler_name)
        except self.glue_client.exceptions.CrawlerRunningException:
            pass

    def start_all_crawlers(self) -> None:
        """Inicia todos os crawlers configurados nas variáveis de ambiente."""
        sport_crawler = os.getenv("GLUE_SPORT_CRAWLER_NAME")
        # Crawler financeiro não é mais usado - tabelas são criadas manualmente no Terraform
        # financial_crawler = os.getenv("GLUE_FINANCIAL_CRAWLER_NAME")

        if sport_crawler:
            self.start_crawler(sport_crawler)
        # if financial_crawler:
        #     self.start_crawler(financial_crawler)
