import pandas as pd
import streamlit as st
import snowflake.connector
import os
from dotenv import load_dotenv

@st.cache_resource
def get_snowflake_connection():
    """Obtener conexión cached a Snowflake"""
    try:
        load_dotenv()
        
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
            database=os.getenv('SNOWFLAKE_DATABASE', 'CTSC_STUDY_DB'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'STUDY_DATA')
        )
        return conn
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def execute_query(query, params=None):
    """Ejecutar query y retornar DataFrame"""
    try:
        conn = get_snowflake_connection()
        if conn:
            if params:
                return pd.read_sql(query, conn, params=params)
            else:
                return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error ejecutando query: {e}")
        return pd.DataFrame()