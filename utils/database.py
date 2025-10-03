import pandas as pd
import streamlit as st
import snowflake.connector
import os


@st.cache_resource
def get_snowflake_connection():
    """
    Get Snowflake connection with fallback from Streamlit secrets to environment variables.
    Returns connection object or None if all methods fail.
    """
    connection_method = None
    config = {}
    
    try:
        # Method 1: Try Streamlit secrets first
        try:
            if hasattr(st, 'secrets') and 'snowflake' in st.secrets:
                secrets = st.secrets["snowflake"]
                
                # Check if all required fields are present in secrets
                required_fields = ['user', 'password', 'account']
                if all(secrets.get(field) for field in required_fields):
                    config = {
                        'user': secrets['user'],
                        'password': secrets['password'],
                        'account': secrets['account'],
                        'warehouse': secrets.get('warehouse', 'COMPUTE_WH'),
                        'database': secrets.get('database', 'CTSC_STUDY_DB'),
                        'schema': secrets.get('schema', 'STUDY_DATA')
                    }
                    connection_method = "Streamlit Secrets"
                    print(f"✅ Using {connection_method} for database connection")
                else:
                    missing = [field for field in required_fields if not secrets.get(field)]
                    print(f"⚠️ Streamlit secrets missing fields: {missing}")
                    
        except Exception as secrets_error:
            print(f"⚠️ Streamlit secrets error: {secrets_error}")
        
        # Method 2: Fall back to environment variables if secrets failed or incomplete
        if not config:
            env_config = {
                'user': os.getenv('SNOWFLAKE_USER'),
                'password': os.getenv('SNOWFLAKE_PASSWORD'),
                'account': os.getenv('SNOWFLAKE_ACCOUNT'),
                'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
                'database': os.getenv('SNOWFLAKE_DATABASE', 'CTSC_STUDY_DB'),
                'schema': os.getenv('SNOWFLAKE_SCHEMA', 'STUDY_DATA')
            }
            
            # Check if environment variables have all required fields
            required_fields = ['user', 'password', 'account']
            if all(env_config[field] for field in required_fields):
                config = env_config
                connection_method = "Environment Variables"
                print(f"✅ Using {connection_method} for database connection")
            else:
                missing = [field for field in required_fields if not env_config[field]]
                print(f"⚠️ Environment variables missing: {missing}")
        
        # Method 3: If both methods failed, return None with helpful error
        if not config:
            error_msg = """
❌ No valid database configuration found.

Please configure one of these methods:

OPTION 1 - Streamlit Secrets (Recommended for production):
Create .streamlit/secrets.toml with:
[snowflake]
user = "your_username"
password = "your_password"
account = "your_account"

OPTION 2 - Environment Variables (For development):
Export these environment variables:
export SNOWFLAKE_USER="your_username"
export SNOWFLAKE_PASSWORD="your_password" 
export SNOWFLAKE_ACCOUNT="your_account"

Missing required fields: user, password, account
"""
            print(error_msg)
            return None
        
        # Validate the final configuration
        required_fields = ['user', 'password', 'account']
        missing_fields = [field for field in required_fields if not config.get(field)]
        if missing_fields:
            print(f"❌ Configuration incomplete. Missing: {missing_fields}")
            return None
        
        # Attempt to establish connection
        print(f"🔗 Attempting to connect to Snowflake using {connection_method}...")
        print(f"   Account: {config['account']}")
        print(f"   User: {config['user']}")
        print(f"   Database: {config.get('database', 'CTSC_STUDY_DB')}")
        
        conn = snowflake.connector.connect(**config)
        
        # Test the connection with a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        
        print(f"✅ Successfully connected to Snowflake (v{version}) using {connection_method}")
        return conn
        
    except snowflake.connector.errors.DatabaseError as db_error:
        print(f"❌ Snowflake Database Error: {db_error}")
        return None
    except snowflake.connector.errors.ProgrammingError as prog_error:
        print(f"❌ Snowflake Programming Error: {prog_error}")
        return None
    except snowflake.connector.errors.OperationalError as op_error:
        print(f"❌ Snowflake Operational Error: {op_error}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during connection: {str(e)}")
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