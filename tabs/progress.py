import streamlit as st
import pandas as pd
import plotly.express as px
from utils.database import get_snowflake_connection

def show_progress(current_user):
    """Contenido de la pestaña Progress"""
    st.header("📈 Tu Progreso")
    if not current_user:
        st.warning("🔐 Debes iniciar sesión para ver el dashboard.")
        return
    
    try:
        conn = get_snowflake_connection()
        if not conn:
            st.error("No hay conexión a la base de datos")
            return
        
        # Estadísticas generales
        st.subheader("📊 Estadísticas Generales")
        
        try:
            stats_df = pd.read_sql("""
                SELECT 
                    COUNT(*) as total_preguntas,
                    SUM(CASE WHEN correcta THEN 1 ELSE 0 END) as correctas,
                    ROUND(SUM(CASE WHEN correcta THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as tasa_acierto,
                    COUNT(DISTINCT DATE(fecha_respuesta)) as dias_estudiados,
                    AVG(tiempo_segundos) as tiempo_promedio
                FROM progress_tracking
            """, conn)
            
            if not stats_df.empty:
                stats = stats_df.iloc[0]
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Preguntas", int(stats['TOTAL_PREGUNTAS']))
                with col2:
                    st.metric("Tasa Acierto", f"{stats['TASA_ACIERTO'] or 0}%")
                with col3:
                    st.metric("Días Estudiados", int(stats['DIAS_ESTUDIADOS']))
                with col4:
                    st.metric("Tiempo Promedio", f"{stats['TIEMPO_PROMEDIO'] or 0:.1f}s")
        except:
            st.info("Aún no hay datos de progreso")
        
        # Gráficos de progreso
        st.subheader("📈 Evolución por Día")
        
        try:
            daily_df = pd.read_sql("""
                SELECT 
                    DATE(fecha_respuesta) as fecha,
                    COUNT(*) as total_preguntas,
                    SUM(CASE WHEN correcta THEN 1 ELSE 0 END) as correctas,
                    ROUND(SUM(CASE WHEN correcta THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as tasa_acierto
                FROM progress_tracking 
                GROUP BY DATE(fecha_respuesta)
                ORDER BY fecha
            """, conn)
            
            if not daily_df.empty:
                tab1, tab2 = st.tabs(["📈 Progreso", "📋 Datos"])
                
                with tab1:
                    fig = px.line(daily_df, x='FECHA', y='CORRECTAS', 
                                 title='Respuestas Correctas por Día')
                    st.plotly_chart(fig)
                    
                    fig2 = px.line(daily_df, x='FECHA', y='TASA_ACIERTO',
                                  title='Tasa de Acierto por Día (%)')
                    st.plotly_chart(fig2)
                
                with tab2:
                    st.dataframe(daily_df)
            else:
                st.info("No hay suficientes datos para mostrar gráficos")
        except Exception as e:
            st.info("No hay datos de progreso disponibles")
        
        # Progreso por módulo
        st.subheader("🎯 Progreso por Módulo")
        
        try:
            module_df = pd.read_sql("""
                SELECT 
                    f.modulo,
                    COUNT(*) as total_preguntas,
                    SUM(CASE WHEN p.correcta THEN 1 ELSE 0 END) as correctas,
                    ROUND(SUM(CASE WHEN p.correcta THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 1) as tasa_acierto
                FROM progress_tracking p
                JOIN flashcards f ON p.pregunta_id = f.id
                GROUP BY f.modulo
                ORDER BY f.modulo
            """, conn)
            
            if not module_df.empty:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig = px.bar(module_df, x='MODULO', y='TASA_ACIERTO',
                                title='Tasa de Acierto por Módulo (%)')
                    st.plotly_chart(fig)
                
                with col2:
                    st.dataframe(module_df)
            else:
                st.info("No hay datos por módulo")
        except:
            st.info("No hay datos por módulo disponibles")
            
    except Exception as e:
        st.error(f"Error cargando progreso: {e}")

if __name__ == "__main__":
    show_progress()