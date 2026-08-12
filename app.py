import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel de Gestão de Suporte", layout="wide")

def formatar_tempo(segundos):
    if pd.isna(segundos): return "0min00seg"
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h}h{m:02d}min{s:02d}seg" if h > 0 else f"{m}min{s:02d}seg"

st.title("📊 Painel de Gestão e Operação do Suporte")

uploaded_file = st.file_uploader("Faça o upload do relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Tratamento Inicial
    for col in ['created_at', 'attended_at', 'closed_at']:
        if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Mapeamento de Atendentes
    mapeamento_nomes = {
        'dolglas': 'Dolglas', 'gcastro': 'Gustavo', 'jonathan': 'Jonathan',
        'jpmairinque': 'Mairinque', 'jpmiranda': 'Miranda', 'lotavio': 'Luis Otavio',
        'luizedu': 'Luiz Eduardo', 'mariana': 'Mariana', 'matheusramao': 'Ramao',
        'moliveira': 'Michel', 'preis': 'Pedro', 'rgomes': 'Rodolpho',
        'ryan': 'Ryan', 'taicyane': 'Taicyane', 'tsouza': 'Tiago', 'luizlima': 'Luiz Felipe'
    }

    def traduzir_atendente(login):
        if pd.isna(login): return None
        login_str = str(login).split('@')[0].strip().lower()
        for chave, nome in mapeamento_nomes.items():
            if chave in login_str: return nome
        return None 

    df['Atendente'] = df['agent_login'].apply(traduzir_atendente)
    df = df[df['Atendente'].notna()]
    df['Tabulação'] = df['tabulation'].fillna('Sem tabulação')

    aba1, aba2 = st.tabs(["📋 Auditoria de Notas e Comentários", "⏱️ Métricas de Tempo"])

    with aba1:
        # Lógica de Auditoria
        df['feedback_text_clean'] = df['feedback_text'].fillna('').astype(str).str.strip()
        nota_ruim = (df['feedback_score'] >= 0) & (df['feedback_score'] <= 3)
        palavras_negativas = ['demora', 'ruim', 'falha', 'problema', 'caiu', 'lento']
        tem_palavra = df['feedback_text_clean'].apply(lambda x: any(p in x.lower() for p in palavras_negativas))
        
        final_df = df[nota_ruim | tem_palavra].copy()
        
        st.write("🔍 **Filtros:**")
        col_f1, col_f2 = st.columns(2)
        lista_at = sorted(final_df['Atendente'].unique().tolist())
        with col_f1: f_at = st.multiselect("Atendente:", lista_at, default=lista_at)
        
        df_f = final_df[final_df['Atendente'].isin(f_at)]
        
        st.dataframe(df_f[['id', 'Atendente', 'feedback_score', 'Tabulação', 'feedback_text']], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Gargalos por Tabulação:**")
            st.bar_chart(df_f.groupby('Tabulação').size())
        with col2:
            st.write("**Gargalos por Atendente:**")
            st.bar_chart(df_f.groupby('Atendente').size())
            
        st.subheader("💬 Leitura de Comentários Críticos")
        st.dataframe(df_f[['id', 'Atendente', 'feedback_text']], use_container_width=True)

    with aba2:
        st.subheader("⏱️ Métricas de Tempo e Eficiência")
        df['Seg_Espera'] = (df['attended_at'] - df['created_at']).dt.total_seconds()
        df['Seg_TMA'] = (df['closed_at'] - df['attended_at']).dt.total_seconds()
        
        st.metric("Tempo Médio de Espera (Fila - Geral)", formatar_tempo(df['Seg_Espera'].mean()))
        
        tma_atend = df.groupby('Atendente')[['Seg_TMA']].mean().reset_index()
        tma_atend['Média TMA'] = tma_atend['Seg_TMA'].apply(formatar_tempo)
        st.table(tma_atend[['Atendente', 'Média TMA']].set_index('Atendente'))

else:
    st.info("Aguardando upload para iniciar a gestão!")
