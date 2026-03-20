import pandas as pd
import numpy as np
import random
from faker import Faker
import os

# =========================
# CONFIG
# =========================
fake = Faker()
np.random.seed(42)
random.seed(42)

N_CLIENTES = 10000
N_PRODUCTOS = 50
N_MOV = 500000
N_OBLIG = 30000
N_SUC = 200
N_COM = 80000

START_DATE = pd.Timestamp("2023-01-01")
END_DATE = pd.Timestamp("2024-01-01")

# =========================
# UTILIDADES
# =========================

def random_dates(n):
    delta = (END_DATE - START_DATE).days
    return START_DATE + pd.to_timedelta(np.random.randint(0, delta, n), unit="D")

def generate_hours(n):
    return np.random.choice(
        [8,9,10,12,13,14,18,19,20],
        size=n,
        p=[0.08,0.1,0.1,0.1,0.12,0.1,0.15,0.15,0.1]
    )

def apply_nulls(df, pct=0.05):
    """
    Aplica nulos de forma controlada:
    - No afecta claves (id_)
    - No rompe booleanos
    """
    df = df.copy()

    for col in df.columns:

        if col.startswith("id"):
            continue

        # evitar columnas booleanas
        if df[col].dtype == bool:
            continue

        mask = np.random.rand(len(df)) < pct
        df.loc[mask, col] = None

    return df

# =========================
# TB_CLIENTES_CORE
# =========================

def gen_clientes(n):
    return pd.DataFrame({
        "id_cli": np.arange(1, n+1),
        "nomb_cli": [fake.first_name() for _ in range(n)],
        "apell_cli": [fake.last_name() for _ in range(n)],
        "tip_doc": np.random.choice(["CC","CE"], n),
        "num_doc": np.random.randint(1e8,1e9,n),
        "fec_nac": pd.to_datetime("1970-01-01") + pd.to_timedelta(np.random.randint(0,18000,n), unit="D"),
        "fec_alta": random_dates(n),
        "cod_segmento": np.random.choice(["BASICO","ESTANDAR","PREMIUM","ELITE"], n),
        "score_buro": np.clip(np.random.normal(650,100,n),300,850).astype(int),
        "ciudad_res": [fake.city() for _ in range(n)],
        "depto_res": [fake.state() for _ in range(n)],
        "estado_cli": np.random.choice(["ACTIVO","INACTIVO"], n),
        "canal_adquis": np.random.choice(["APP","WEB","OFICINA"], n)
    })

# =========================
# TB_PRODUCTOS_CAT
# =========================

def gen_productos(n):
    return pd.DataFrame({
        "cod_prod": [f"P{i:03}" for i in range(1,n+1)],
        "desc_prod": [f"Producto_{i}" for i in range(n)],
        "tip_prod": np.random.choice(["CREDITO","AHORRO","TRANSACCIONAL"], n),
        "tasa_ea": np.round(np.random.uniform(0.01,0.35,n),4),
        "plazo_max_meses": np.random.choice([12,24,36,48,60], n),
        "cuota_min": np.random.randint(50000,300000,n),
        "comision_admin": np.random.randint(0,20000,n),
        "estado_prod": np.random.choice(["ACTIVO","INACTIVO"], n)
    })

# =========================
# TB_SUCURSALES_RED
# =========================

def gen_sucursales(n):
    return pd.DataFrame({
        "cod_suc": [f"S{i:03}" for i in range(1,n+1)],
        "nom_suc": [f"Sucursal_{i}" for i in range(n)],
        "tip_punto": np.random.choice(["OFICINA","CAJERO","CORRESPONSAL"], n),
        "ciudad": [fake.city() for _ in range(n)],
        "depto": [fake.state() for _ in range(n)],
        "latitud": np.random.uniform(-90,90,n),
        "longitud": np.random.uniform(-180,180,n),
        "activo": np.random.choice([True,False], n)  # boolean limpio
    })

# =========================
# TB_MOV_FINANCIEROS
# =========================

def gen_movimientos(n, cli, prod):
    fechas = random_dates(n)

    df = pd.DataFrame({
        "id_mov": np.arange(1,n+1),
        "id_cli": np.random.choice(cli.id_cli, n),
        "cod_prod": np.random.choice(prod.cod_prod, n),
        "num_cuenta": np.random.randint(1e7,1e8,n),
        "fec_mov": fechas,
        "hra_mov": generate_hours(n),
        "vr_mov": np.random.lognormal(11,0.5,n),
        "tip_mov": np.random.choice(["PAGO","TRANSFERENCIA","RETIRO","COMPRA"], n),
        "cod_canal": np.random.choice(["APP","WEB","CAJERO","OFICINA"], n),
        "cod_ciudad": [fake.city() for _ in range(n)],
        "cod_estado_mov": "OK",
        "id_dispositivo": [fake.uuid4() for _ in range(n)]
    })

    # anomalías
    df = pd.concat([df, df.sample(100)], ignore_index=True)
    df.loc[df.sample(50).index, "vr_mov"] *= -1
    df.loc[df.sample(50).index, "fec_mov"] = pd.Timestamp("2099-01-01")

    return df

# =========================
# TB_OBLIGACIONES
# =========================

def gen_obligaciones(n, cli, prod):
    return pd.DataFrame({
        "id_oblig": np.arange(1,n+1),
        "id_cli": np.random.choice(cli.id_cli,n),
        "cod_prod": np.random.choice(prod.cod_prod,n),
        "vr_aprobado": np.random.randint(1e6,5e7,n),
        "vr_desembolsado": np.random.uniform(1e6,5e7,n),
        "sdo_capital": np.random.uniform(1e6,5e7,n),
        "vr_cuota": np.random.randint(50000,1e6,n),
        "fec_desembolso": random_dates(n),
        "fec_venc": random_dates(n),
        "dias_mora_act": np.random.choice([0,10,30,60,120],n),
        "num_cuotas_pend": np.random.randint(1,48,n),
        "calif_riesgo": np.random.choice(list("ABCDE"),n)
    })

# =========================
# TB_COMISIONES_LOG
# =========================

def gen_comisiones(n, cli, prod):
    return pd.DataFrame({
        "id_comision": np.arange(1,n+1),
        "id_cli": np.random.choice(cli.id_cli,n),
        "cod_prod": np.random.choice(prod.cod_prod,n),
        "fec_cobro": random_dates(n),
        "vr_comision": np.random.uniform(1000,20000,n),
        "tip_comision": np.random.choice(["ADMIN","RETIRO","TRANSFERENCIA"], n),
        "estado_cobro": np.random.choice(["COBRADO","PENDIENTE"], n)
    })

# =========================
# SAVE
# =========================

def save(df, name):
    os.makedirs("output", exist_ok=True)
    df.to_csv(f"output/{name}.csv", index=False)
    df.to_parquet(f"output/{name}.parquet", index=False)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print("Generando datos...")

    cli = gen_clientes(N_CLIENTES)
    prod = gen_productos(N_PRODUCTOS)
    suc = gen_sucursales(N_SUC)

    mov = gen_movimientos(N_MOV, cli, prod)
    obl = gen_obligaciones(N_OBLIG, cli, prod)
    com = gen_comisiones(N_COM, cli, prod)

    print("Aplicando nulos...")
    cli = apply_nulls(cli)
    prod = apply_nulls(prod)
    suc = apply_nulls(suc)
    mov = apply_nulls(mov)
    obl = apply_nulls(obl)
    com = apply_nulls(com)

    print("Guardando archivos...")
    save(cli, "TB_CLIENTES_CORE")
    save(prod, "TB_PRODUCTOS_CAT")
    save(suc, "TB_SUCURSALES_RED")
    save(mov, "TB_MOV_FINANCIEROS")
    save(obl, "TB_OBLIGACIONES")
    save(com, "TB_COMISIONES_LOG")

    print("FASE 1 COMPLETADA")