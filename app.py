import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
import calendar

# --- PREMIER BRANDING ---
st.set_page_config(page_title="Elite Protocol 2026 | Sai Sancharika Mohanty", layout="wide")

# Authority Styling
st.markdown("""
    <style>
    .main { background-color: #121212; color: white; }
    div[data-testid="stMetricValue"] { color: #00E5FF !important; font-size: 60px !important; }
    .stDataFrame { border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ ELITE PROTOCOL 2026")
st.subheader("Authority of: Sai Sancharika Mohanty")

# --- SIDEBAR ---
st.sidebar.title("PROTOCOL CONTROL")
st.sidebar.write("Sai Sancharika Mohanty")
days_left = (date(2026, 12, 31) - date.today()).days
st.sidebar.metric("DAYS REMAINING", days_left)

# --- DATA SYSTEM ---
if 'habits' not in st.session_state:
    st.session_state.habits = ["Stretch or do yoga", "Walk 10,000 steps", "Read a book"]

# --- GRID INTERFACE ---
month_name = st.selectbox("SELECT MONTH", list(calendar.month_name)[1:], index=date.today().month-1)
days_in_month = calendar.monthrange(2026, date.today().month)[1]

st.write(f"### {month_name.upper()} TRACKER")
df = pd.DataFrame(0, index=st.session_state.habits, columns=[str(d) for d in range(1, days_in_month + 1)])

# The Interactive Table
st.data_editor(df, use_container_width=True)

# --- ANALYTICS ---
st.write("---")
c1, c2, c3 = st.columns(3)
with c1: st.metric("MONTHLY PROGRESS", "0%", "REAL-TIME")
with c2: st.metric("21-DAY STREAK", "0", "NORMALIZED")
with c3: st.metric("MOMENTUM", "0%", "STABLE")

st.caption("Designed for the 2026 Elite cycle... Authority of Sai Sancharika Mohanty")
