import streamlit as st
import pandas as pd
from utils.database import get_snowflake_connection

def show_study(current_user):
    """Contenido de la pestaña Study"""
    st.header("🎴 Modo Estudio")
    
    if not current_user:
        st.warning("🔐 Debes iniciar sesión para ver el dashboard.")
        return
    
    try:
        conn = get_snowflake_connection()
        if not conn:
            st.error("No hay conexión a la base de datos")
            return
        
        # Selección de módulo
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Obtener módulos disponibles
            try:
                df = pd.read_sql("SELECT DISTINCT modulo FROM flashcards ORDER BY modulo", conn)
                modulos = df['MODULO'].tolist() if not df.empty else ['1']
            except:
                modulos = ['1']
            
            modulo = st.selectbox("Selecciona módulo:", modulos)
        
        with col2:
            st.write("###")
            if st.button("🔄 Nueva Pregunta", use_container_width=True):
                if 'current_question' in st.session_state:
                    st.session_state.current_question = None
        
        # Obtener pregunta aleatoria
        if 'current_question' not in st.session_state or st.session_state.current_question is None:
            try:
                df = pd.read_sql(f"""
                    SELECT * FROM flashcards 
                    WHERE modulo = '{modulo}'
                    ORDER BY RANDOM() 
                    LIMIT 1
                """, conn)
                
                if not df.empty:
                    st.session_state.current_question = df.iloc[0]
                else:
                    st.warning(f"No hay flashcards para el módulo {modulo}")
                    return
            except Exception as e:
                st.error(f"Error cargando pregunta: {e}")
                return
        
        # Mostrar pregunta actual
        question = st.session_state.current_question
        st.subheader(f"Pregunta Módulo {modulo}")
        
        # Tarjeta de pregunta
        with st.container():
            st.markdown(f"### ❓ {question['PREGUNTA']}")
            
            # Opciones de respuesta
            opciones = [
                question['OPCION_A'],
                question['OPCION_B'], 
                question['OPCION_C'],
                question['OPCION_D']
            ]
            
            respuesta = st.radio("Selecciona tu respuesta:", opciones, key="respuesta_actual")
            
            # Botones de acción
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✅ Verificar Respuesta", type="primary", use_container_width=True):
                    # Lógica de verificación
                    correcta = (respuesta == opciones[ord(question['RESPUESTA_CORRECTA']) - ord('A')])
                    
                    if correcta:
                        st.success("🎉 ¡Correcto!")
                    else:
                        st.error(f"❌ Incorrecto. La respuesta correcta es: {opciones[ord(question['RESPUESTA_CORRECTA']) - ord('A')]}")
                    
                    # Guardar progreso
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO progress_tracking (pregunta_id, respuesta_usuario, correcta, tiempo_segundos)
                            VALUES (%s, %s, %s, %s)
                        """, (question['ID'], respuesta, correcta, 30))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error guardando progreso: {e}")
            
            with col2:
                if st.button("➡️ Siguiente Pregunta", use_container_width=True):
                    st.session_state.current_question = None
                    st.rerun()
            
            with col3:
                if st.button("📊 Ver Estadísticas", use_container_width=True):
                    try:
                        stats_df = pd.read_sql(f"""
                            SELECT 
                                COUNT(*) as total,
                                SUM(CASE WHEN correcta THEN 1 ELSE 0 END) as correctas
                            FROM progress_tracking 
                            WHERE pregunta_id = {question['ID']}
                        """, conn)
                        st.info(f"Esta pregunta: {stats_df.iloc[0]['CORRECTAS']}/{stats_df.iloc[0]['TOTAL']} correctas")
                    except:
                        st.info("No hay estadísticas para esta pregunta")
                        
    except Exception as e:
        st.error(f"Error en modo estudio: {e}")

if __name__ == "__main__":
    show_study()