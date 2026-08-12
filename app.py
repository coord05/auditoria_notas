import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel de Gestão e Auditoria", layout="wide")

st.title("📊 Painel de Gestão e Operação do Suporte")

# Função de formatação de tempo: XhXXminXXseg
def formatar_tempo(segundos):
    if pd.isna(segundos): return "0h00min00seg"
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h}h{m:02d}min{s:02d}seg"

uploaded_file = st.file_uploader("Faça o upload do relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Tratamento de Datas
    for col in ['created_at', 'attended_at', 'closed_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Dicionário de Atendentes
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
        return None # Retorna None se não estiver na lista para filtrar

    df['Atendente'] = df['agent_login'].apply(traduzir_atendente)
    df = df[df['Atendente'].notna()] # Filtra apenas os atendentes mapeados

    # Abas
    aba1, aba2 = st.tabs(["📋 Auditoria de Notas", "⏱️ Métricas de Tempo"])

    with aba1:
        # Auditoria (Mantendo sua lógica funcional)
        df['feedback_text_clean'] = df['feedback_text'].fillna('').astype(str).str.strip()
        nota_ruim = (df['feedback_score'] >= 0) & (df['feedback_score'] <= 3)
        
        palavras_negativas = ['demora', 'ruim', 'falha', 'problema', 'caiu', 'lento']
        tem_palavra = df['feedback_text_clean'].apply(lambda x: any(p in x.lower() for p in palavras_negativas))
        
        final_df = df[nota_ruim | tem_palavra].copy()
        final_df['Tabulação'] = final_df['tabulation'].fillna('Sem tabulação')
        
        st.write("🔍 **Filtros de Auditoria:**")
        lista_atendentes = sorted(final_df['Atendente'].unique().tolist())
        filtro_at = st.multiselect("Atendente:", lista_atendentes, default=lista_atendentes)
        
        df_f = final_df[final_df['Atendente'].isin(filtro_at)]
        st.dataframe(df_f[['id', 'Atendente', 'feedback_score', 'Tabulação', 'feedback_text']], use_container_width=True)

    with aba2:
        st.subheader("⏱️ Métricas de Tempo e Eficiência")
        
        # Cálculos de tempo em segundos
        df['Seg_Espera'] = (df['attended_at'] - df['created_at']).dt.total_seconds()
        df['Seg_TMA'] = (df['closed_at'] - df['attended_at']).dt.total_seconds()
        
        # Geral
        st.metric("Tempo Médio de Espera (Fila - Geral)", formatar_tempo(df['Seg_Espera'].mean()))
        
        # Por Atendente
        tma_atend = df.groupby('Atendente')[['Seg_Espera', 'Seg_TMA']].mean().reset_index()
        tma_atend['Média Espera Fila'] = tma_atend['Seg_Espera'].apply(formatar_tempo)
        tma_atend['Média TMA'] = tma_atend['Seg_TMA'].apply(formatar_tempo)
        
        st.dataframe(tma_atend[['Atendente', 'Média Espera Fila', 'Média TMA']], use_container_width=True)

else:
    st.info("Aguardando upload para iniciar a gestão!")
