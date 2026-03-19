import pandas as pd
import numpy as np
import random
from faker import Faker
import yaml
from datetime import datetime
import os

# =========================
# CONFIG
# =========================
fake = Faker()
np.random.seed(42)
random.seed(42)

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

START_DATE = pd.Timestamp(config["date_range"]["start"])
END_DATE = pd.Timestamp(config["date_range"]["end"])


# =========================
# UTILIDADES
# =========================
def random_dates(n):
    delta = (END_DATE - START_DATE).days
    return START_DATE + pd.to_timedelta(np.random.randint(0, delta, n), unit="D")


def apply_nulls(df, pct):
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]).columns:
        mask = np.random.rand(len(df)) < pct
        df.loc[mask, col] = None
    return df


def inject_anomalies(df):
    df = df.copy()

    df = pd.concat([df, df.sample(100)])

    idx = df.sample(50).index
    df.loc[idx, "fec_mov"] = "2099-01-01"

    idx = df.sample(50).index
    df.loc[idx, "vr_mov"] *= -1

    return df


def fix_dtypes(df):
    df = df.copy()
    for col in df.columns:
        if "fec_" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def save_data(df, name):
    os.makedirs("output", exist_ok=True)
    df.to_csv(f"output/{name}.csv", index=False)
    df.to_parquet(f"output/{name}.parquet", index=False)


# =========================
# GENERADORES
# =========================

def generate_clientes(n):
    return pd.DataFrame({
        "id_cli": np.arange(1, n+1),
        "nomb_cli": [fake.first_name() for _ in range(n)],
        "apell_cli": [fake.last_name() for _ in range(n)],
        "tip_doc": np.random.choice(["CC", "CE"], n),
        "num_doc": np.random.randint(100000000, 999999999, n, dtype=np.int64),

        # 🔥 FIX DEFINITIVO (sin timestamp)
        "fec_nac": pd.Timestamp("1970-01-01") + pd.to_timedelta(
            np.random.randint(0, 365*50, n), unit="D"
        ),

        "fec_alta": random_dates(n),
        "cod_segmento": np.random.choice(["BASICO", "ESTANDAR", "PREMIUM", "ELITE"], n),
        "score_buro": np.random.randint(300, 850, n),
        "ciudad_res": [fake.city() for _ in range(n)],
        "depto_res": [fake.state() for _ in range(n)],
        "estado_cli": np.random.choice(["ACTIVO", "INACTIVO"], n),
        "canal_adquis": np.random.choice(["APP", "WEB", "OFICINA"], n)
    })


def generate_productos(n):
    return pd.DataFrame({
        "cod_prod": [f"P{i:03}" for i in range(1, n+1)],
        "desc_prod": [f"Producto_{i}" for i in range(1, n+1)],
        "tip_prod": np.random.choice(["CREDITO", "AHORRO", "TRANSACCIONAL"], n),
        "tasa_ea": np.round(np.random.uniform(0.01, 0.35, n), 4),
        "plazo_max_meses": np.random.choice([12, 24, 36, 48, 60], n),
        "cuota_min": np.random.randint(50000, 300000, n),
        "comision_admin": np.random.randint(0, 20000, n),
        "estado_prod": np.random.choice(["ACTIVO", "INACTIVO"], n)
    })


def generate_sucursales(n):
    return pd.DataFrame({
        "cod_suc": [f"S{i:03}" for i in range(1, n+1)],
        "nom_suc": [f"Sucursal_{i}" for i in range(1, n+1)],
        "tip_punto": np.random.choice(["OFICINA", "CAJERO", "CORRESPONSAL"], n),
        "ciudad": [fake.city() for _ in range(n)],
        "depto": [fake.state() for _ in range(n)],
        "latitud": np.random.uniform(-90, 90, n),
        "longitud": np.random.uniform(-180, 180, n),
        "activo": np.random.choice([True, False], n)
    })


def generate_movimientos(n, df_clientes, df_productos):
    fechas = random_dates(n)

    return pd.DataFrame({
        "id_mov": np.arange(1, n+1),
        "id_cli": np.random.choice(df_clientes["id_cli"], n),
        "cod_prod": np.random.choice(df_productos["cod_prod"], n),
        "num_cuenta": np.random.randint(10000000, 99999999, n),
        "fec_mov": fechas,
        "hra_mov": fechas.time,
        "vr_mov": np.abs(np.random.normal(100000, 50000, n)),
        "tip_mov": np.random.choice(["PAGO", "TRANSFERENCIA", "RETIRO", "COMPRA"], n),
        "cod_canal": np.random.choice(["APP", "WEB", "CAJERO", "OFICINA"], n),
        "cod_ciudad": [fake.city() for _ in range(n)],
        "cod_estado_mov": "OK",
        "id_dispositivo": [fake.uuid4() for _ in range(n)]
    })


def generate_obligaciones(n, df_clientes, df_productos):
    productos_credito = df_productos[df_productos["tip_prod"] == "CREDITO"]["cod_prod"]

    return pd.DataFrame({
        "id_oblig": np.arange(1, n+1),
        "id_cli": np.random.choice(df_clientes["id_cli"], n),
        "cod_prod": np.random.choice(productos_credito, n),
        "vr_aprobado": np.random.randint(1000000, 50000000, n),
        "vr_desembolsado": np.random.uniform(1000000, 50000000, n),
        "sdo_capital": np.random.uniform(1000000, 50000000, n),
        "vr_cuota": np.random.randint(50000, 1000000, n),
        "fec_desembolso": random_dates(n),
        "fec_venc": random_dates(n),
        "dias_mora_act": np.random.choice([0, 10, 30, 60, 120], n),
        "num_cuotas_pend": np.random.randint(1, 48, n),
        "calif_riesgo": np.random.choice(list("ABCDE"), n)
    })


def generate_comisiones(n, df_clientes, df_productos):
    return pd.DataFrame({
        "id_comision": np.arange(1, n+1),
        "id_cli": np.random.choice(df_clientes["id_cli"], n),
        "cod_prod": np.random.choice(df_productos["cod_prod"], n),
        "fec_cobro": random_dates(n),
        "vr_comision": np.random.uniform(1000, 20000, n),
        "tip_comision": np.random.choice(["ADMIN", "RETIRO", "TRANSFERENCIA"], n),
        "estado_cobro": np.random.choice(["COBRADO", "PENDIENTE"], n)
    })


# =========================
# MAIN
# =========================
if __name__ == "__main__":

    print("Generando datos...")

    df_clientes = generate_clientes(config["volumes"]["clientes"])
    df_productos = generate_productos(config["volumes"]["productos"])
    df_sucursales = generate_sucursales(config["volumes"]["sucursales"])
    df_movimientos = generate_movimientos(config["volumes"]["movimientos"], df_clientes, df_productos)
    df_obligaciones = generate_obligaciones(config["volumes"]["obligaciones"], df_clientes, df_productos)
    df_comisiones = generate_comisiones(config["volumes"]["comisiones"], df_clientes, df_productos)

    print("Aplicando nulos...")
    df_clientes = apply_nulls(df_clientes, config["null_percentage"])
    df_productos = apply_nulls(df_productos, config["null_percentage"])
    df_sucursales = apply_nulls(df_sucursales, config["null_percentage"])
    df_movimientos = apply_nulls(df_movimientos, config["null_percentage"])
    df_obligaciones = apply_nulls(df_obligaciones, config["null_percentage"])
    df_comisiones = apply_nulls(df_comisiones, config["null_percentage"])

    print("Inyectando anomalías...")
    df_movimientos = inject_anomalies(df_movimientos)

    print("Corrigiendo tipos...")
    df_clientes = fix_dtypes(df_clientes)
    df_productos = fix_dtypes(df_productos)
    df_sucursales = fix_dtypes(df_sucursales)
    df_movimientos = fix_dtypes(df_movimientos)
    df_obligaciones = fix_dtypes(df_obligaciones)
    df_comisiones = fix_dtypes(df_comisiones)

    print("Guardando archivos...")
    save_data(df_clientes, "clientes")
    save_data(df_productos, "productos")
    save_data(df_sucursales, "sucursales")
    save_data(df_movimientos, "movimientos")
    save_data(df_obligaciones, "obligaciones")
    save_data(df_comisiones, "comisiones")

    print("✅ FASE 1 COMPLETADA")