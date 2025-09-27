import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import get_snowflake_connection

def show_dashboard():
    """Contenido de la pestaña Dashboard"""
    st.header("📊 Dashboard de Estudio")
    
    try:
        conn = get_snowflake_connection()
        if not conn:
            st.error("No hay conexión a la base de datos")
            return
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Total flashcards
            try:
                df = pd.read_sql("SELECT COUNT(*) as total FROM flashcards", conn)
                st.metric("Total Flashcards", int(df.iloc[0]['TOTAL']))
            except:
                st.metric("Total Flashcards", 0)
        
        with col2:
            # Preguntas hoy
            try:
                df = pd.read_sql("""
                    SELECT COUNT(*) as hoy FROM progress_tracking 
                    WHERE DATE(fecha_respuesta) = CURRENT_DATE()
                """, conn)
                st.metric("Preguntas Hoy", int(df.iloc[0]['HOY']))
            except:
                st.metric("Preguntas Hoy", 0)
        
        with col3:
            # Tasa de aciertos
            try:
                df = pd.read_sql("""
                    SELECT ROUND(SUM(CASE WHEN correcta THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as tasa
                    FROM progress_tracking
                """, conn)
                tasa = df.iloc[0]['TASA'] or 0
                st.metric("Tasa Aciertos", f"{tasa}%")
            except:
                st.metric("Tasa Aciertos", "0%")
        
        with col4:
            # Módulos activos
            try:
                df = pd.read_sql("SELECT COUNT(DISTINCT modulo) as modulos FROM flashcards", conn)
                st.metric("Módulos", int(df.iloc[0]['MODULOS']))
            except:
                st.metric("Módulos", 0)
        
        # Gráfico de progreso
        st.subheader("📈 Progreso de Estudio")
        try:
            df = pd.read_sql("""
                SELECT DATE(fecha_respuesta) as fecha,
                       COUNT(*) as total_preguntas,
                       SUM(CASE WHEN correcta THEN 1 ELSE 0 END) as correctas
                FROM progress_tracking 
                GROUP BY DATE(fecha_respuesta)
                ORDER BY fecha
                LIMIT 30
            """, conn)
            
            if not df.empty:
                fig = px.line(df, x='FECHA', y='CORRECTAS', 
                             title='Respuestas Correctas por Día')
                st.plotly_chart(fig)
            else:
                st.info("Aún no hay datos de progreso")
        except Exception as e:
            st.info("Aún no hay datos de progreso disponibles")
        
        # Flashcards recientes
        st.subheader("🎴 Flashcards Recientes")
        try:
            df = pd.read_sql("SELECT * FROM flashcards ORDER BY id DESC LIMIT 5", conn)
            if not df.empty:
                st.dataframe(df[['PREGUNTA', 'MODULO', 'DIFICULTAD']])
            else:
                st.info("No hay flashcards disponibles")
        except:
            st.info("No hay flashcards disponibles")
            
    except Exception as e:
        st.error(f"Error cargando dashboard: {e}")

# Para testing individual
if __name__ == "__main__":
    show_dashboard()