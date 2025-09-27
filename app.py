import streamlit as st
import os
from dotenv import load_dotenv

# Importar módulos
from tabs import dashboard, study, progress
from utils.database import get_snowflake_connection
from utils.auth import show_login_section, show_logout_section, get_current_user, require_auth

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
    st.title(" CTSC Study System")
    st.markdown("---")
    
    # Sidebar - Gestión de usuarios y conexión
    with st.sidebar:
        st.header("🔗 Estado del Sistema")
        
        # Verificar conexión a BD
        try:
            conn = get_snowflake_connection()
            if conn:
                st.success("✅ Conectado a Snowflake")
                cursor = conn.cursor()
                cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_USER()")
                db, schema, user = cursor.fetchone()
                st.info(f"**Database:** {db}")
                st.info(f"**Schema:** {schema if schema else 'None'}")
                cursor.close()
            else:
                st.error("❌ No conectado")
        except Exception as e:
            st.error(f"❌ Error de conexión: {e}")
        
        st.markdown("---")
        
        # Gestión de autenticación
        user_authenticated = show_logout_section()
        
        if not user_authenticated:
            show_login_section()
        
        st.markdown("---")
        st.header("📊 Navegación")
    
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
    st.header("Bienvenido al Sistema de Estudio CTSC")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 📚 Sistema de Flashcards para Certificación APICS CTSC
        
        **Características principales:**
        - 🎴 Flashcards interactivas por módulo
        - 📊 Seguimiento de progreso personalizado
        - 📈 Dashboard con métricas de estudio
        - 👥 Multi-usuario con sesiones seguras
        
        **Para comenzar:**
        1. Selecciona tu usuario en la barra lateral
        2. Ingresa tu contraseña
        3. ¡Comienza a estudiar!
        """)
    
    with col2:
        st.info("""
        **¿Primera vez?**
        Contacta al administrador para obtener tus credenciales de acceso.
        """)

def show_authenticated_app(current_user):
    """Mostrar aplicación completa para usuarios autenticados"""
    # Header personalizado
    st.success(f"👤 Sesión activa: **{current_user['user_name']}** - {current_user['email']}")
    
    # Crear pestañas
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎴 Study", "📈 Progress"])
    
    # Pestaña Dashboard
    with tab1:
        dashboard.show_dashboard(current_user)
    
    # Pestaña Study
    with tab2:
        study.show_study(current_user)
    
    # Pestaña Progress
    with tab3:
        progress.show_progress(current_user)

if __name__ == "__main__":
    main()