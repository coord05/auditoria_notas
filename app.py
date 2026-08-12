import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel de Gestão e Suporte", layout="wide")

st.title("📊 Painel de Gestão e Operação do Suporte")
st.write("Auditoria de notas e métricas de tempo (TMA/Fila).")

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
        if pd.isna(login): return 'Sem usuário'
        login_str = str(login).split('@')[0].strip().lower()
        for chave, nome in mapeamento_nomes.items():
            if chave in login_str: return nome
        return login_str

    df['Atendente'] = df['agent_login'].apply(traduzir_atendente)

    # Abas
    aba1, aba2 = st.tabs(["📋 Auditoria", "⏱️ Métricas de Tempo (TMA/Fila)"])

    with aba1:
        # (Mantendo sua lógica de auditoria de notas aqui)
        st.write("Painel de Auditoria - Filtros no topo...")
        # ... (O código anterior da aba de auditoria vai aqui)

    with aba2:
        st.subheader("⏱️ Métricas de Tempo Médio")
        
        # Cálculos de Tempo (convertidos para minutos)
        df['Tempo_Espera_Fila'] = (df['attended_at'] - df['created_at']).dt.total_seconds() / 60
        df['Tempo_Atendimento'] = (df['closed_at'] - df['attended_at']).dt.total_seconds() / 60
        
        # Agrupamento
        tma_df = df.groupby('Atendente')[['Tempo_Espera_Fila', 'Tempo_Atendimento']].mean().reset_index()
        tma_df.columns = ['Atendente', 'Média Espera Fila (min)', 'Média TMA (min)']
        
        st.dataframe(tabela := tma_df.round(2), use_container_width=True)
        st.bar_chart(tabela.set_index('Atendente'))

else:
    st.info("Por favor, faça o upload do arquivo para começarmos!")
