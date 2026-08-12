import streamlit as st
import pandas as pd

st.set_page_config(page_title="Painel de Gestão e Auditoria", layout="wide")

st.title("📊 Painel de Gestão e Operação do Suporte")

uploaded_file = st.file_uploader("Faça o upload do relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Tratamento de Datas
    for col in ['created_at', 'attended_at', 'closed_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Mapeamento de Atendentes
    mapeamento_nomes = {
        'dolglas': 'Dolglas', 'gcastro': 'Gustavo', 'jonathan': 'Jonathan',
        'jpmairinque': 'Mairinque', 'jpmiranda': 'Miranda', 'lotavio': 'Luis Otavio',
        'luizedu': 'Luiz Eduardo', 'mariana': 'Mariana', 'matheusramao': 'Ramao',
        'moliveira': 'Michel', 'preis': 'Pedro', 'rgomes': 'Rodolpho',
        'ryan': 'Ryan', 'taicyane': 'Taicyane', 'tsouza': 'Tiago', 'luizlima': 'Luiz Felipe'
    }

    def traduzir_atendente(login):
        login_str = str(login).split('@')[0].strip().lower()
        for chave, nome in mapeamento_nomes.items():
            if chave in login_str: return nome
        return None # Retorna None se não estiver na lista (para filtrar)

    df['Atendente'] = df['agent_login'].apply(traduzir_atendente)
    df = df[df['Atendente'].notna()] # Filtra apenas os atendentes mapeados

    # Abas
    aba1, aba2 = st.tabs(["📋 Auditoria de Notas", "⏱️ Métricas de Tempo (TMA/Fila)"])

    with aba1:
        # Lógica de Auditoria (Mantendo sua estrutura preferida)
        df['feedback_text_clean'] = df['feedback_text'].fillna('').astype(str).str.strip()
        nota_ruim = (df['feedback_score'] >= 0) & (df['feedback_score'] <= 3)
        
        # Filtro de palavras-chave
        palavras = ['demora', 'ruim', 'falha', 'problema', 'caiu', 'lento']
        tem_palavra = df['feedback_text_clean'].apply(lambda x: any(p in x.lower() for p in palavras))
        
        final_df = df[nota_ruim | tem_palavra].copy()
        final_df['Tabulação'] = final_df['tabulation'].fillna('Sem tabulação')
        
        st.subheader("Filtros de Auditoria")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_at = st.multiselect("Atendente:", final_df['Atendente'].unique(), default=final_df['Atendente'].unique())
        
        df_f = final_df[final_df['Atendente'].isin(filtro_at)]
        st.dataframe(df_f[['id', 'Atendente', 'feedback_score', 'Tabulação', 'feedback_text']], use_container_width=True)

    with aba2:
        st.subheader("⏱️ Métricas de Tempo")
        
        # Cálculos
        df['Espera_Fila'] = (df['attended_at'] - df['created_at']).dt.total_seconds() / 60
        
        # TMA Fila Geral
        st.metric("Tempo Médio de Espera Geral (Fila)", f"{df['Espera_Fila'].mean():.2f} min")
        
        # TMA por atendente
        df['TMA'] = (df['closed_at'] - df['attended_at']).dt.total_seconds() / 60
        tma_atend = df.groupby('Atendente')[['Espera_Fila', 'TMA']].mean().reset_index()
        st.dataframe(tma_atend.round(2), use_container_width=True)

else:
    st.info("Aguardando upload do arquivo para iniciar a gestão!")
