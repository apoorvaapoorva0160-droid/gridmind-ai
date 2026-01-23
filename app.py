import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time
import sqlite3
import requests
import os

BOT_TOKEN = os.getenv("8596468894:AAEeaaC11ib9sn6HuaSl3MldwKZEJ4iO8GI")
CHAT_ID = os.getenv("8133102866")

# ================= PAGE CONFIG =================
st.set_page_config(page_title="GridMind AI", layout="wide")

# ================= CONFIG =================
BOT_TOKEN = "8596468894:AAEeaaC11ib9sn6HuaSl3MldwKZEJ4iO8GI"
CHAT_ID = "8133102866"

DB_NAME = "gridmind.db"
WINDOW_SIZE = 120
REFRESH_RATE = 1

# ================= DATABASE =================
@st.cache_resource
def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS energy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        value REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        message TEXT
    )
    """)
    conn.commit()
    return conn, cur

conn, cur = get_db()

# ================= TELEGRAM =================
def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(
            url,
            json={"chat_id": CHAT_ID, "text": message},
            timeout=2
        )
    except:
        pass  # never block app

# ================= UI =================
st.title("⚡ GridMind AI — Persistent Energy Monitoring")

# ================= ENERGY GENERATOR =================
def generate_energy(t):
    base = 200 + t * 0.03
    noise = np.random.normal(0, 4)
    if np.random.rand() < 0.04:
        noise += np.random.choice([35, -30])
    return base + noise

# ================= INSERT DATA =================
t = time.time()
energy = generate_energy(t)

cur.execute(
    "INSERT INTO energy (timestamp, value) VALUES (?, ?)",
    (datetime.datetime.now().isoformat(), energy)
)
conn.commit()

# ================= LOAD DATA =================
df = pd.read_sql(
    f"""
    SELECT * FROM energy
    ORDER BY id DESC
    LIMIT {WINDOW_SIZE}
    """,
    conn
).iloc[::-1]

# ================= ANOMALY DETECTION =================
df["mean"] = df["value"].rolling(20).mean()
df["std"] = df["value"].rolling(20).std()
df["anomaly"] = abs(df["value"] - df["mean"]) > 3 * df["std"]

# ================= ALERT =================
if not df.empty and df["anomaly"].iloc[-1]:
    msg = f"🔴 HIGH ALERT | Energy: {df['value'].iloc[-1]:.2f}"

    cur.execute(
        "INSERT INTO alerts (timestamp, message) VALUES (?, ?)",
        (datetime.datetime.now().isoformat(), msg)
    )
    conn.commit()

    send_telegram_alert(msg)
    st.toast("📲 Telegram alert sent", icon="🚨")

# ================= PLOT =================
plot_area = st.empty()

fig, ax = plt.subplots(figsize=(7, 3))
ax.plot(df["value"], label="Energy")
ax.scatter(
    df[df["anomaly"]].index,
    df[df["anomaly"]]["value"],
    label="Anomaly"
)
ax.legend()
plot_area.pyplot(fig, clear_figure=True)
plt.close(fig)

# ================= METRICS =================
c1, c2, c3 = st.columns(3)

c1.metric("⚡ Live Energy", f"{energy:.2f}")
c2.metric(
    "🚨 Total Alerts",
    cur.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
)
c3.metric(
    "🧠 Status",
    "Unstable" if df["anomaly"].iloc[-1] else "Healthy"
)

# ================= ALERT LOG =================
st.subheader("🚨 Alert History")
alerts_df = pd.read_sql(
    "SELECT * FROM alerts ORDER BY id DESC LIMIT 5",
    conn
)
st.dataframe(alerts_df, use_container_width=True)

# ================= AUTO REFRESH =================
time.sleep(REFRESH_RATE)
st.rerun()



