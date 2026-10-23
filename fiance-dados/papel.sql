-- Papel próprio da fiance-dados no postgres-mercado: lê `mercado` como mercado_leitura e é dono só
-- de `acesso`. Rodar uma vez como o dono do cluster, depois das migrações do data-job e da API, e
-- em seguida: ALTER ROLE dados_api PASSWORD '<senha>'. Passo a passo em docs/dados/README.md.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dados_api') THEN
        CREATE ROLE dados_api LOGIN IN ROLE mercado_leitura;
    END IF;
END $$;

ALTER SCHEMA acesso OWNER TO dados_api;

DO $$
DECLARE
    t record;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'acesso' LOOP
        EXECUTE 'ALTER TABLE acesso.' || quote_ident(t.tablename) || ' OWNER TO dados_api';
    END LOOP;
END $$;
