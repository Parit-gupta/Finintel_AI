import os

import psycopg2
from dotenv import load_dotenv


class PostgreSQLLoader:

    def __init__(self):

        load_dotenv()

        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

    # ==========================================================
    # DATABASE CONNECTION
    # ==========================================================

    def connect(self):

        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    # ==========================================================
    # CONNECTION TEST
    # ==========================================================

    def test_connection(self):

        connection = None

        try:

            connection = self.connect()

            print(
                "PostgreSQL connection successful."
            )

            return True

        except Exception as error:

            print(
                f"PostgreSQL connection failed: {error}"
            )

            return False

        finally:

            if connection:
                connection.close()

    # ==========================================================
    # CUSTOMER STAGING LOAD
    # ==========================================================

    def load_customers(self, dataframe):

        connection = None
        cursor = None

        try:

            connection = self.connect()
            cursor = connection.cursor()

            rows = dataframe.collect()

            insert_query = """
                INSERT INTO staging.stg_customers (
                    customer_id,
                    name,
                    gender,
                    age,
                    dob,
                    marital_status,
                    occupation,
                    annual_income,
                    employment_type,
                    education,
                    phone,
                    email,
                    city,
                    state,
                    country,
                    customer_since,
                    kyc_status
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s
                )
            """

            data = []

            for row in rows:

                data.append(
                    (
                        row["customer_id"],
                        row["name"],
                        row["gender"],
                        row["age"],
                        row["dob"],
                        row["marital_status"],
                        row["occupation"],
                        row["annual_income"],
                        row["employment_type"],
                        row["education"],
                        str(row["phone"])
                        if row["phone"] is not None
                        else None,
                        row["email"],
                        row["city"],
                        row["state"],
                        row["country"],
                        row["customer_since"],
                        row["kyc_status"],
                    )
                )

            cursor.executemany(
                insert_query,
                data
            )

            connection.commit()

            print(
                f"Customers loaded successfully : {len(data)} rows"
            )

            return len(data)

        except Exception as error:

            if connection:
                connection.rollback()

            print(
                f"Customer staging load failed : {error}"
            )

            raise

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()
    def load_dataframe_jdbc(self, dataframe, table_name, mode="append"):
        """
        Load a Spark DataFrame into PostgreSQL using Spark JDBC.
        This is scalable and does not use collect().
        """

        jdbc_url = (
            f"jdbc:postgresql://{self.host}:{self.port}/{self.database}"
        )

        properties = {
            "user": self.user,
            "password": self.password,
            "driver": "org.postgresql.Driver",
        }

        print(f"Loading DataFrame into PostgreSQL table: {table_name}")

        (
            dataframe.write
            .mode(mode)
            .jdbc(
                url=jdbc_url,
                table=table_name,
                properties=properties
            )
        )

        print(f"Successfully loaded into: {table_name}")