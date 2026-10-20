from backend.etl.load.postgres_loader import PostgreSQLLoader


loader = PostgreSQLLoader()

loader.test_connection()