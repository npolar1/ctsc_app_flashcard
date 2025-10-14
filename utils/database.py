import pandas as pd
import streamlit as st
import snowflake.connector


@st.cache_resource
def get_snowflake_connection():
    """Obtener conexión cached a Snowflake"""
    try:

        conn = snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"].get("warehouse", "COMPUTE_WH"),
            database=st.secrets["snowflake"].get("database", "CTSC_STUDY_DB"),
            schema=st.secrets["snowflake"].get("schema", "STUDY_DATA")
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