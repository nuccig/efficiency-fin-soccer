import os
from pathlib import Path

import boto3
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class S3Uploader:
    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME não configurado")
        self.s3_client = boto3.client('s3')

    def upload_file(self, local_path: Path, s3_key: str) -> None:
        """Faz upload de um arquivo local para o S3."""
        try:
            self.s3_client.upload_file(str(local_path), self.bucket_name, s3_key)
        except Exception as e:
            print(f"Erro upload {local_path.name}: {e}")

    def clear_sport_data(self) -> None:
        """Remove todos os arquivos da pasta sport/ no S3."""
        try:
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
        except Exception as e:
            print(f"Erro ao limpar bucket S3: {e}")

    def upload_sport_data(self, data_dir: Path) -> None:
        """Faz upload de todos os CSVs de dados esportivos para o S3 com particionamento."""
        self.clear_sport_data()
        
        seasons_dir = data_dir / "sport" / "seasons"
        players_dir = data_dir / "sport" / "players"

        if seasons_dir.exists():
            for csv_file in seasons_dir.glob("season_*.csv"):
                season = csv_file.stem.split('_')[1]
                s3_key = f"sport/seasons/season={season}/{csv_file.name}"
                self.upload_file(csv_file, s3_key)

        if players_dir.exists():
            for csv_file in players_dir.glob("*.csv"):
                parts = csv_file.stem.split('_')
                stat_type = '_'.join(parts[:2])
                league = parts[3]
                season = parts[5]
                s3_key = f"sport/players/{stat_type}/league={league}/season={season}/{csv_file.name}"
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
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema SQL não encontrado em: {schema_path}")

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                    conn.commit()
        except Exception as e:
            print(f"Erro ao criar schema: {e}")
            raise

    def truncate_tables(self) -> None:
        """Limpa todas as tabelas antes de recarregar os dados."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("TRUNCATE TABLE fixtures, top_scorers, top_assists CASCADE;")
                    conn.commit()
        except Exception as e:
            print(f"Erro ao limpar tabelas: {e}")

    def load_csv(self, csv_path: Path, table_name: str) -> None:
        """Carrega um arquivo CSV em uma tabela PostgreSQL usando COPY."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        cur.copy_expert(
                            f"COPY {table_name} FROM STDIN WITH (FORMAT CSV, HEADER true, NULL '')",
                            f
                        )
                    conn.commit()
        except Exception as e:
            print(f"Erro ao carregar {csv_path.name}: {e}")

    def load_all_data(self, data_dir: Path) -> None:
        """Carrega todos os CSVs nos respectivas tabelas PostgreSQL."""
        self.truncate_tables()
        
        seasons_dir = data_dir / "sport" / "seasons"
        players_dir = data_dir / "sport" / "players"

        if seasons_dir.exists():
            for csv_file in seasons_dir.glob("season_*.csv"):
                self.load_csv(csv_file, "fixtures")

        if players_dir.exists():
            for csv_file in players_dir.glob("top_scorers_*.csv"):
                self.load_csv(csv_file, "top_scorers")

            for csv_file in players_dir.glob("top_assists_*.csv"):
                self.load_csv(csv_file, "top_assists")


class GlueCrawlerRunner:
    def __init__(self):
        self.glue_client = boto3.client('glue')

    def start_crawler(self, crawler_name: str) -> None:
        """Inicia um crawler do AWS Glue."""
        try:
            self.glue_client.start_crawler(Name=crawler_name)
        except self.glue_client.exceptions.CrawlerRunningException:
            pass
        except Exception as e:
            print(f"Erro ao iniciar crawler {crawler_name}: {e}")

    def start_all_crawlers(self) -> None:
        """Inicia todos os crawlers configurados nas variáveis de ambiente."""
        sport_crawler = os.getenv("GLUE_SPORT_CRAWLER_NAME")
        financial_crawler = os.getenv("GLUE_FINANCIAL_CRAWLER_NAME")

        if sport_crawler:
            self.start_crawler(sport_crawler)
        if financial_crawler:
            self.start_crawler(financial_crawler)
