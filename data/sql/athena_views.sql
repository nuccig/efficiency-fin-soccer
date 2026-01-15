-- Views do Athena para converter formatos brasileiros
-- Execute estas queries no Athena após criar as tabelas
-- View para transfers com conversão de tipos
CREATE OR REPLACE VIEW transfers_parsed AS
SELECT team,
    player,
    "from" AS from_team,
    "to" AS to_team,
    "type",
    CAST(date AS DATE) AS date,
    date_ano_mes,
    -- Converte fee_eur de formato brasileiro para milhões de euros
    -- Exemplo: "1.500.000,00" -> 1.5 (milhões)
    ROUND(
        CASE
            WHEN TRIM(COALESCE(fee_eur, '')) = ''
            OR fee_eur IS NULL THEN NULL
            ELSE CAST(
                REPLACE(
                    REPLACE(TRIM(fee_eur), '.', ''),
                    ',',
                    '.'
                ) AS DOUBLE
            ) / 1000000.0
        END,
        2
    ) AS fee_eur,
    -- Converte fee_brl de formato brasileiro para milhões de reais
    ROUND(
        CASE
            WHEN TRIM(COALESCE(fee_brl, '')) = ''
            OR fee_brl IS NULL THEN NULL
            ELSE CAST(
                REPLACE(
                    REPLACE(TRIM(fee_brl), '.', ''),
                    ',',
                    '.'
                ) AS DOUBLE
            ) / 1000000.0
        END,
        2
    ) AS fee_brl,
    -- IPCA RATE mantém como percentual (não precisa converter para milhões)
    CASE
        WHEN TRIM(COALESCE(ipca_rate, '')) = ''
        OR ipca_rate IS NULL THEN NULL
        ELSE CAST(
            REPLACE(
                REPLACE(TRIM(ipca_rate), '.', ''),
                ',',
                '.'
            ) AS DOUBLE
        )
    END AS ipca_rate,
    -- Converte real_value de formato brasileiro para milhões de reais
    ROUND(
        CASE
            WHEN TRIM(COALESCE(real_value, '')) = ''
            OR real_value IS NULL THEN NULL
            ELSE CAST(
                REPLACE(
                    REPLACE(TRIM(real_value), '.', ''),
                    ',',
                    '.'
                ) AS DOUBLE
            ) / 1000000.0
        END,
        2
    ) AS real_value
FROM transfers;
-- View para balances com conversão de tipos
-- Valores convertidos para milhões de reais (ex: "83.000.000,00" -> 83.0)
CREATE OR REPLACE VIEW balances_parsed AS
SELECT time AS team,
    tipo AS type,
    classificacao AS classification,
    -- Converte 2022 de formato brasileiro para milhões de reais
    -- Exemplo: "83.000.000,00" -> 83.0 (milhões)
    ROUND(
        CASE
            WHEN TRIM(COALESCE(ano_2022, '')) = ''
            OR ano_2022 IS NULL THEN NULL
            ELSE CAST(
                REPLACE(
                    REPLACE(
                        REPLACE(TRIM(ano_2022), '"', ''),
                        '.',
                        ''
                    ),
                    ',',
                    '.'
                ) AS DOUBLE
            ) / 1000000.0
        END,
        2
    ) AS year_2022,
    -- Converte 2023 de formato brasileiro para milhões de reais
    ROUND(
        CASE
            WHEN TRIM(COALESCE(ano_2023, '')) = ''
            OR ano_2023 IS NULL THEN NULL
            ELSE CAST(
                REPLACE(
                    REPLACE(
                        REPLACE(TRIM(ano_2023), '"', ''),
                        '.',
                        ''
                    ),
                    ',',
                    '.'
                ) AS DOUBLE
            ) / 1000000.0
        END,
        2
    ) AS year_2023,
    -- Converte 2024 de formato brasileiro para milhões de reais
    ROUND(
        CASE
            WHEN TRIM(COALESCE(ano_2024, '')) = ''
            OR ano_2024 IS NULL THEN NULL
            ELSE CAST(
                REPLACE(
                    REPLACE(
                        REPLACE(TRIM(ano_2024), '"', ''),
                        '.',
                        ''
                    ),
                    ',',
                    '.'
                ) AS DOUBLE
            ) / 1000000.0
        END,
        2
    ) AS year_2024
FROM balances;