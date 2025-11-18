from pathlib import Path

from tqdm import tqdm

from .api_football import (
    APIFootballClient,
    MatchResultsService,
    SeasonsService,
    TopAssistsService,
    TopScorersService,
    load_target_leagues,
    load_target_seasons,
)
from .storage import GlueCrawlerRunner, PostgresLoader, S3Uploader


class APIFootballExtractionPipeline:
    def __init__(
        self, 
        client: APIFootballClient | None = None,
        data_dir: Path | None = None,
        enable_s3: bool = True,
        enable_postgres: bool = True,
        enable_glue: bool = True,
    ) -> None:
        self.client = client or APIFootballClient()
        self.seasons = load_target_seasons()
        self.leagues = load_target_leagues()
        self.seasons_service = SeasonsService(self.client)
        self.fixtures_service = MatchResultsService(self.client)
        self.scorers_service = TopScorersService(self.client)
        self.assists_service = TopAssistsService(self.client)
        
        if data_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self.data_dir = project_root / "data"
        else:
            self.data_dir = data_dir
        
        self.enable_s3 = enable_s3
        self.enable_postgres = enable_postgres
        self.enable_glue = enable_glue
        
        self.s3_uploader = None
        self.postgres_loader = None
        self.glue_runner = None

    def _has_targets(self) -> bool:
        """Verifica se há seasons e leagues configuradas."""
        if not self.seasons or not self.leagues:
            return False
        return True

    def _extract_data(self) -> None:
        """Extrai dados da API Football para todas as leagues e seasons configuradas."""
        self.seasons_service.get_seasons()

        total = len(self.leagues) * len(self.seasons)
        with tqdm(total=total, desc="Extraindo dados da API") as pbar:
            for league_id in self.leagues:
                for season in self.seasons:
                    params = {"league": league_id, "season": season}
                    self.fixtures_service.get_fixtures(**params)
                    self.scorers_service.get_topscorers(**params)
                    self.assists_service.get_topassists(**params)
                    pbar.update(1)

    def _upload_to_s3(self) -> None:
        """Faz upload dos CSVs para o bucket S3."""
        if not self.enable_s3:
            return
        
        try:
            self.s3_uploader = S3Uploader()
            self.s3_uploader.upload_sport_data(self.data_dir)
        except Exception as e:
            print(f"Erro no upload S3: {e}")

    def _load_to_postgres(self) -> None:
        """Cria schema e carrega dados no PostgreSQL."""
        if not self.enable_postgres:
            return
        
        try:
            self.postgres_loader = PostgresLoader()
            self.postgres_loader.create_schema()
            self.postgres_loader.load_all_data(self.data_dir)
        except Exception as e:
            print(f"Erro na carga PostgreSQL: {e}")

    def _run_glue_crawlers(self) -> None:
        """Executa os crawlers do AWS Glue."""
        if not self.enable_glue:
            return
        
        try:
            self.glue_runner = GlueCrawlerRunner()
            self.glue_runner.start_all_crawlers()
        except Exception as e:
            print(f"Erro ao executar crawlers: {e}")

    def run(self) -> None:
        """Executa o pipeline completo de extração, upload S3, carga PostgreSQL e crawlers Glue."""
        if not self._has_targets():
            return

        stages = []
        stages.append(("Extração API", self._extract_data))
        if self.enable_s3:
            stages.append(("Upload S3", self._upload_to_s3))
        if self.enable_postgres:
            stages.append(("Carga PostgreSQL", self._load_to_postgres))
        if self.enable_glue:
            stages.append(("Crawlers Glue", self._run_glue_crawlers))

        for stage_name, stage_func in tqdm(stages, desc="Pipeline"):
            tqdm.write(f"Executando: {stage_name}")
            stage_func()
