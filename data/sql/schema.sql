DROP TABLE IF EXISTS fixtures CASCADE;
DROP TABLE IF EXISTS top_scorers CASCADE;
DROP TABLE IF EXISTS top_assists CASCADE;

CREATE TABLE IF NOT EXISTS fixtures (
    fixture_id INTEGER PRIMARY KEY,
    date TIMESTAMP,
    league_id INTEGER,
    league_name VARCHAR(255),
    season INTEGER,
    home_team_id INTEGER,
    home_team_name VARCHAR(255),
    away_team_id INTEGER,
    away_team_name VARCHAR(255),
    fulltime_home INTEGER,
    fulltime_away INTEGER
);

CREATE TABLE IF NOT EXISTS top_scorers (
    category VARCHAR(50),
    player_id INTEGER,
    player_name VARCHAR(255),
    team_id INTEGER,
    team_name VARCHAR(255),
    league_id INTEGER,
    season INTEGER,
    appearences INTEGER,
    minutes INTEGER,
    goals INTEGER,
    assists INTEGER,
    shots_total INTEGER,
    PRIMARY KEY (player_id, league_id, season)
);

CREATE TABLE IF NOT EXISTS top_assists (
    category VARCHAR(50),
    player_id INTEGER,
    player_name VARCHAR(255),
    team_id INTEGER,
    team_name VARCHAR(255),
    league_id INTEGER,
    season INTEGER,
    appearences INTEGER,
    minutes INTEGER,
    goals INTEGER,
    assists INTEGER,
    shots_total INTEGER,
    PRIMARY KEY (player_id, league_id, season)
);

CREATE INDEX IF NOT EXISTS idx_fixtures_season ON fixtures(season);
CREATE INDEX IF NOT EXISTS idx_fixtures_league ON fixtures(league_id);
CREATE INDEX IF NOT EXISTS idx_scorers_goals ON top_scorers(goals);
CREATE INDEX IF NOT EXISTS idx_assists_assists ON top_assists(assists);
CREATE INDEX IF NOT EXISTS idx_scorers_season ON top_scorers(season);
CREATE INDEX IF NOT EXISTS idx_assists_season ON top_assists(season);
