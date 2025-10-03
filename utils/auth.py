import uuid
import streamlit as st
import hashlib
from datetime import datetime, timedelta
from .database import get_snowflake_connection

class PasswordAuth:
    def __init__(self):
        self.conn = get_snowflake_connection()
    
    def hash_password(self, password):
        """Simple hash of the password (use bcrypt in production)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, user_id, password):
        """Verify user and password"""
        try:
            password_hash = self.hash_password(password)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT USER_ID, USER_NAME, EMAIL 
                FROM CTSC_STUDY_DB.STUDY_DATA.APP_USERS 
                WHERE USER_ID = %s 
                AND PASSWORD_HASH = %s 
                AND IS_ACTIVE = TRUE
            """, (user_id, password_hash))
            
            user = cursor.fetchone()
            cursor.close()
            
            if user:
                return {
                    'user_id': user[0],
                    'user_name': user[1],
                    'email': user[2]
                }
            return None
        except Exception as e:
            st.error(f"Error verifying user: {e}")
            return None
    
    def get_user_list(self):
        """Get list of active users"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT USER_ID, USER_NAME, EMAIL 
                    FROM APP_USERS 
                    WHERE IS_ACTIVE = TRUE 
                    ORDER BY USER_ID desc, USER_NAME
                """)
                users = cursor.fetchall()
                return [(user[0], user[1], user[2]) for user in users]
                
        except Exception as e:
            st.error(f"Error retrieving users: {e}")
            return []
    
    def create_session(self, user_id):
        """Create a new session for the user"""
        try:
            session_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO USER_SESSIONS (SESSION_ID, USER_ID, EXPIRES_AT)
                VALUES (%s, %s, %s)
            """, (session_id, user_id, expires_at))
            
            # Actualizar last_login del usuario
            cursor.execute("""
                UPDATE CTSC_STUDY_DB.STUDY_DATA.APP_USERS 
                SET LAST_LOGIN = CURRENT_TIMESTAMP() 
                WHERE USER_ID = %s
            """, (user_id,))
            
            self.conn.commit()
            cursor.close()
            return session_id
        except Exception as e:
            st.error(f"Error creating session: {e}")
            return None
    
    def validate_session(self, session_id):
        """Validate if the session is valid"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT u.USER_ID, u.USER_NAME, u.EMAIL, s.EXPIRES_AT
                FROM USER_SESSIONS s
                JOIN CTSC_STUDY_DB.STUDY_DATA.APP_USERS u ON s.USER_ID = u.USER_ID
                WHERE s.SESSION_ID = %s 
                AND s.EXPIRES_AT > CURRENT_TIMESTAMP()
                AND u.IS_ACTIVE = TRUE
            """, (session_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'user_name': result[1],
                    'email': result[2],
                    'expires_at': result[3]
                }
            return None
        except Exception as e:
            st.error(f"Error validating session: {e}")
            return None
    
    def logout(self, session_id):
        """Invalidate session"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM USER_SESSIONS 
                WHERE SESSION_ID = %s
            """, (session_id,))
            self.conn.commit()
            cursor.close()
            return True
        except Exception as e:
            st.error(f"Error logging out: {e}")
            return False

def get_current_user():
    """Get current user information from session_state"""
    if 'user_session' in st.session_state:
        auth = PasswordAuth()
        user_info = auth.validate_session(st.session_state.user_session)
        
        if user_info:
            return user_info
        else:
            # Sesión expirada, limpiar
            if 'user_session' in st.session_state:
                del st.session_state.user_session
    
    return None

def show_login_section():
    """Show login section with username and password"""
    st.sidebar.header("🔐 Login")
    
    auth = PasswordAuth()
    available_users = auth.get_user_list()
    
    if not available_users:
        st.sidebar.error("There are no users available in the database")
        return False
    
    # Selector de usuario
    user_options = {f"{user_name}": user_id for user_id, user_name, email in available_users}
    selected_user_display = st.sidebar.selectbox(
        "Select user:",
        options=list(user_options.keys())
    )
    
    selected_user_id = user_options[selected_user_display]
    
    # Campo de contraseña
    password = st.sidebar.text_input(
        "Password:",
        type="password",
        help="Enter the password for the selected user"
    )
    
    # Botón de login
    if st.sidebar.button("🚀 Login", type="primary", use_container_width=True):
        if not password:
            password = ""  # Evitar None
        
        user_info = auth.verify_user(selected_user_id, password)
        
        if user_info:
            session_id = auth.create_session(selected_user_id)
            
            if session_id:
                st.session_state.user_session = session_id
                st.sidebar.success(f"Welcome {user_info['user_name']}!")
                st.rerun()
            else:
                st.sidebar.error("Error creating session")
        else:
            st.sidebar.error("Incorrect username or password")
    
    return False

def show_logout_section():
    """Show logout section"""
    user_info = get_current_user()
    
    if user_info:
        st.sidebar.header("👤 Logged In User")
        
        # Información del usuario
        st.sidebar.success(f"**{user_info['user_name']}**")
        st.sidebar.info(f"📧 {user_info['email']}")
        
        # Tiempo restante de sesión
        time_left = user_info['expires_at'] - datetime.now()
        hours_left = max(0, int(time_left.total_seconds() / 3600))
        minutes_left = max(0, int((time_left.total_seconds() % 3600) / 60))
        st.sidebar.info(f"⏰ Session expires in: {hours_left}h {minutes_left}m")
        
        # Botón de logout
        if st.sidebar.button("🚪 Logout", type="secondary", use_container_width=True):
            auth = PasswordAuth()
            if auth.logout(st.session_state.user_session):
                del st.session_state.user_session
                st.sidebar.success("Session logged out successfully")
                st.rerun()
        
        return True
    return False

def require_auth():
    """Decorator for functions that require authentication"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                st.warning("🔐 Please sign in to access this function")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator