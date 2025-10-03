import streamlit as st
import os


try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables for local development
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ python-dotenv not available - using environment variables directly")


# Importar módulos
from tabs import dashboard, study, progress
from utils.database import get_snowflake_connection
from utils.auth import show_login_section, show_logout_section, get_current_user

# Configuración de la página
st.set_page_config(
    page_title="CTSC Study System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar variables de entorno
load_dotenv()

def main():
    # Header principal
    st.title("CTSC Study System")
    st.markdown("---")
    
    # Sidebar - Gestión de usuarios y conexión
    with st.sidebar:
        st.header("🔗 System Status")
        
        # Verificar conexión a BD
        try:
            conn = get_snowflake_connection()
            if conn:
                st.success("✅ Connected to Snowflake")
                cursor = conn.cursor()
                cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()")
                db, schema = cursor.fetchone()
                st.info(f"**Database:** {db}")
                st.info(f"**Schema:** {schema if schema else 'None'}")
                cursor.close()
            else:
                st.error("❌ Not connected")
        except Exception as e:
            st.error(f"❌ Connection error: {e}")
        
        st.markdown("---")
        
        # Gestión de autenticación
        user_authenticated = show_logout_section()
        
        if not user_authenticated:
            show_login_section()

        st.markdown("---")
    
    # Verificar autenticación antes de mostrar contenido
    current_user = get_current_user()
    
    if not current_user:
        # Mostrar página de bienvenida para usuarios no autenticados
        show_welcome_page()
        return
    
    # Usuario autenticado - mostrar aplicación completa
    show_authenticated_app(current_user)

def show_welcome_page():
    """Página de bienvenida para usuarios no autenticados"""
    st.header("Welcome to the CTSC Study System")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📚 Flashcards System for APICS CTSC Certification
        
        **Main Features:**
        - 🎴 Interactive flashcards by module
        - 📊 Personalized progress tracking
        - 📈 Dashboard with study metrics
        - 👥 Multi-user with secure sessions
        
        **Getting Started:**
        1. Select your user in the sidebar
        2. Enter your password
        3. Start studying!
        """)
    
    with col2:
        st.info("""
        **First time?**
        Contact me (Nelson Polar) to obtain your access credentials.
        """)

def show_authenticated_app(current_user):
    """Mostrar aplicación completa para usuarios autenticados"""
    # Header personalizado
    st.success(f"👤 Active session: **{current_user['user_name']}**")
    
    # Crear pestañas
    tab1, tab2, tab3 = st.tabs(["🎴 Study", "📊 Dashboard",  "📈 Progress"])
    
    # Pestaña Dashboard
    with tab1:
        study.show_study(current_user)
    
    # Pestaña Study
    with tab2:
        dashboard.show_dashboard(current_user)
    
    # Pestaña Progress
    with tab3:
        progress.show_progress(current_user)

if __name__ == "__main__":
    main()