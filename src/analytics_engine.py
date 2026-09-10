import os
import numpy as np
import pandas as pd


def process_uac_data(filepath: str = None) -> pd.DataFrame:
  """Ingests, cleans, validates, and engineers healthcare capacity features

  for the UAC Care Load Analytics pipeline.
  """
  # Default path relative to src/ directory
  if filepath is None:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_path = os.path.join(base_dir, 'data', 'processed_uac_analytics.csv')
    raw_path = os.path.join(
        base_dir, 'data', 'HHS_Unaccompanied_Alien_Children_Program.csv'
    )

    if os.path.exists(processed_path):
      filepath = processed_path
    elif os.path.exists(raw_path):
      filepath = raw_path
    else:
      raise FileNotFoundError(
          f'Could not locate dataset in data/ folder. Checked: {processed_path}'
      )

  # 1. Ingestion
  df = pd.read_csv(filepath)

  # Check if already processed
  if 'Total_System_Load' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)
    return df

  # 2. Date Formatting & Sorting
  df = df.dropna(subset=['Date']).copy()
  df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
  df = df.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)

  # 3. String Cleaning
  if 'Children in HHS Care' in df.columns and df[
      'Children in HHS Care'
  ].dtype == object:
    df['Children in HHS Care'] = (
        df['Children in HHS Care'].str.replace(',', '').astype(float)
    )

  # 4. Standard Column Mapping
  col_map = {
      'Children apprehended and placed in CBP custody*': 'CBP_Intake',
      'Children in CBP custody': 'CBP_Custody',
      'Children transferred out of CBP custody': 'CBP_Transfers',
      'Children in HHS Care': 'HHS_Care',
      'Children discharged from HHS Care': 'HHS_Discharges',
  }
  df = df.rename(columns=col_map)

  # 5. Boundary Constraints Enforcement
  df['CBP_Transfers'] = np.minimum(df['CBP_Transfers'], df['CBP_Custody'])
  df['HHS_Discharges'] = np.minimum(df['HHS_Discharges'], df['HHS_Care'])

  # 6. Feature Engineering
  df['Total_System_Load'] = df['CBP_Custody'] + df['HHS_Care']
  df['Net_Intake_Pressure'] = df['CBP_Transfers'] - df['HHS_Discharges']
  df['Discharge_Offset_Ratio'] = np.where(
      df['CBP_Transfers'] > 0,
      df['HHS_Discharges'] / df['CBP_Transfers'],
      1.0,
  )
  df['System_Load_7D_MA'] = (
      df['Total_System_Load'].rolling(window=7, min_periods=1).mean()
  )
  df['Care_Load_Volatility_7D'] = (
      df['Total_System_Load'].rolling(window=7, min_periods=1).std().fillna(0)
  )
  df['Cumulative_Backlog'] = df['Net_Intake_Pressure'].cumsum()

  return df