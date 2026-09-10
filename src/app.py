import os
from analytics_engine import process_uac_data
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="UAC System Capacity & Care Load Analytics", layout="wide"
)

st.title("System Capacity & Care Load Analytics")
st.markdown(
    "**Program:** Unaccompanied Children (UAC) Pipeline Overview | CBP & HHS"
)

# File Ingestion Sidebar
st.sidebar.header("Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

try:
  if uploaded_file is not None:
    df = process_uac_data(uploaded_file)
  else:
    # Auto-load default dataset from data/ folder
    df = process_uac_data()

  df.set_index("Date", inplace=True)

  # Date Filtering Controls
  st.sidebar.header("Dashboard Controls")
  min_date = df.index.min().date()
  max_date = df.index.max().date()

  date_range = st.sidebar.date_input(
      "Select Date Range",
      [min_date, max_date],
      min_value=min_date,
      max_value=max_date,
  )

  if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df.loc[str(start_date) : str(end_date)].copy()
  else:
    filtered_df = df.copy()

  # Metric Cards
  latest = filtered_df.iloc[-1]
  col1, col2, col3, col4 = st.columns(4)

  col1.metric("Total System Load", f"{int(latest['Total_System_Load']):,}")
  col2.metric("Net Intake Pressure", f"{int(latest['Net_Intake_Pressure']):,}")
  col3.metric(
      "Discharge Offset Ratio", f"{latest['Discharge_Offset_Ratio']:.2f}"
  )
  col4.metric(
      "7-Day Load Volatility", f"{latest['Care_Load_Volatility_7D']:.1f}"
  )

  st.markdown("---")

  # Chart 1: Total System Load Trend
  st.subheader("1. System Load & Smoothing Trend")
  fig_load = go.Figure()
  fig_load.add_trace(
      go.Scatter(
          x=filtered_df.index,
          y=filtered_df["Total_System_Load"],
          name="Daily Total Load",
          line=dict(color="lightgrey"),
      )
  )
  fig_load.add_trace(
      go.Scatter(
          x=filtered_df.index,
          y=filtered_df["System_Load_7D_MA"],
          name="7-Day Moving Avg",
          line=dict(color="navy", width=2),
      )
  )
  fig_load.update_layout(
      xaxis_title="Date",
      yaxis_title="Active Care Load",
      hovermode="x unified",
  )
  st.plotly_chart(fig_load, use_container_width=True)

  # Chart 2: Active Capacity Split
  st.subheader("2. Facility Active Load Split (CBP vs HHS)")
  fig_split = go.Figure()
  fig_split.add_trace(
      go.Scatter(
          x=filtered_df.index,
          y=filtered_df["HHS_Care"],
          name="HHS Care",
          line=dict(color="teal"),
      )
  )
  fig_split.add_trace(
      go.Scatter(
          x=filtered_df.index,
          y=filtered_df["CBP_Custody"],
          name="CBP Custody",
          line=dict(color="coral"),
      )
  )
  fig_split.update_layout(
      xaxis_title="Date", yaxis_title="Active Count", hovermode="x unified"
  )
  st.plotly_chart(fig_split, use_container_width=True)

  # Chart 3: Net Intake Pressure Bars
  st.subheader("3. Net Intake Pressure (Inflow vs Outflow Balance)")
  colors = [
      "crimson" if val > 0 else "seagreen"
      for val in filtered_df["Net_Intake_Pressure"]
  ]
  fig_pressure = go.Figure()
  fig_pressure.add_trace(
      go.Bar(
          x=filtered_df.index,
          y=filtered_df["Net_Intake_Pressure"],
          marker_color=colors,
          name="Net Pressure",
      )
  )
  fig_pressure.update_layout(
      xaxis_title="Date",
      yaxis_title="Net Difference (Transfers - Discharges)",
      hovermode="x unified",
  )
  st.plotly_chart(fig_pressure, use_container_width=True)

except Exception as e:
  st.error(f"Error loading dashboard data: {e}")