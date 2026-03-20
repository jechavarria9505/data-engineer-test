import pandas as pd
import sqlalchemy as sa
import urllib
import time
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# =========================
# CONFIG
# =========================

server = "sql-dataeng-test123.database.windows.net"
database = "sqldb-dataeng-test"
username = "sqladminuser"
key_vault_url = "https://kv-data-engineer-test.vault.azure.net/"

# =========================
# AUTH
# =========================

credential = DefaultAzureCredential()
client = SecretClient(vault_url=key_vault_url, credential=credential)
password = client.get_secret("sql-password").value

print("Password obtenido desde Key Vault")

# =========================
# CONEXION
# =========================

params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

engine = sa.create_engine(
    f"mssql+pyodbc:///?odbc_connect={params}",
    fast_executemany=True
)

print("Conectado a SQL Server")

# =========================
# LIMPIEZA
# =========================

def clean_df(df):

    df.columns = [c.lower() for c in df.columns]

    for col in df.columns:
        if "fec_" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

    df = df.where(pd.notnull(df), None)

    return df

# =========================
# CARGA STREAMING
# =========================

def load_table_stream(path, table_name, chunksize):

    print(f"\nCargando {table_name}...")

    start = time.time()
    total = 0

    for chunk in pd.read_csv(path, chunksize=chunksize):

        chunk = clean_df(chunk)

        chunk.to_sql(
            table_name,
            engine,
            if_exists="append",
            index=False,
            method=None
        )

        total += len(chunk)
        print(f"{table_name}: {total} registros cargados")

    end = time.time()

    print(f"{table_name} COMPLETADA en {round(end-start,2)} segundos")

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    # tablas pequeñas
    load_table_stream("output/TB_CLIENTES_CORE.csv", "TB_CLIENTES_CORE", 2000)
    load_table_stream("output/TB_PRODUCTOS_CAT.csv", "TB_PRODUCTOS_CAT", 1000)
    load_table_stream("output/TB_SUCURSALES_RED.csv", "TB_SUCURSALES_RED", 1000)

    #tabla grande optimizada
    load_table_stream("output/TB_MOV_FINANCIEROS.csv", "TB_MOV_FINANCIEROS", 20000)

    # medianas
    load_table_stream("output/TB_OBLIGACIONES.csv", "TB_OBLIGACIONES", 10000)
    load_table_stream("output/TB_COMISIONES_LOG.csv", "TB_COMISIONES_LOG", 10000)

    print("\nCARGA COMPLETA OPTIMIZADA")