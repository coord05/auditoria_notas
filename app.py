import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel de Gestão e Auditoria", layout="wide")

# Função de formatação de tempo inteligente
def formatar_tempo(segundos):
    if pd.isna(segundos): return "0min00seg"
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    if h > 0: return f"{h}h{m:02d}min{s:02d}seg"
    else: return f"{m}min{s:02d}seg"

st.title("📊 Painel de Gestão e Operação do Suporte")

# Área de Upload
uploaded_file = st.file_uploader("Faça o upload do seu relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Tratamento de Datas para o TMA
    for col in ['created_at', 'attended_at', 'closed_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'feedback_score' in df.columns:
        if 'feedback_text' not in df.columns: df['feedback_text'] = None
        df['feedback_text_clean'] = df['feedback_text'].fillna('').astype(str).str.strip()

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
            return None 

        df['Atendente'] = df['agent_login'].apply(traduzir_atendente)
        df = df[df['Atendente'].notna()] # Foca apenas na nossa equipe

        # Lógica de Auditoria
        nota_ruim = (df['feedback_score'] >= 0) & (df['feedback_score'] <= 3)
        palavras_negativas = ['demora', 'ruim', 'falha', 'problema', 'caiu', 'lento', 'cancelar', 'insatisfeito']
        tem_palavra = df['feedback_text_clean'].apply(lambda x: any(p in x.lower() for p in palavras_negativas))
        
        final_df = df[nota_ruim | tem_palavra].copy()
        final_df['Tabulação'] = final_df['tabulation'].fillna('Sem tabulação')
        final_df['Comentário'] = final_df['feedback_text_clean'].replace('', 'Sem comentário')
        final_df.columns = [c if c != 'feedback_text_clean' else 'Raw_Text' for c in final_df.columns]

        # ABAS DO PAINEL
        aba1, aba2 = st.tabs(["📋 Auditoria de Notas", "⏱️ Métricas de Tempo"])

        with aba1:
            st.write("🔍 **Filtros de Auditoria:**")
            col_f1, col_f2, col_f3 = st.columns(3)
            lista_at = sorted(final_df['Atendente'].unique().tolist())
            lista_nota = sorted(final_df['feedback_score'].unique().tolist())
            lista_tab = sorted(final_df['Tabulação'].unique().tolist())
            
            with col_f1: f_at = st.multiselect("Atendente:", lista_at, default=lista_at)
            with col_f2: f_nota = st.multiselect("Nota:", lista_nota, default=lista_nota)
            with col_f3: f_tab = st.multiselect("Tabulação:", lista_tab, default=lista_tab)
            
            df_f = final_df[(final_df['Atendente'].isin(f_at)) & (final_df['feedback_score'].isin(f_nota)) & (final_df['Tabulação'].isin(f_tab))]
            
            st.subheader(f"📋 Encontramos {len(df_f)} atendimentos para análise")
            st.dataframe(df_f.drop(columns=['Raw_Text']), use_container_width=True)
            
            c1, c2 = st.columns(2)
            with c1: st.bar_chart(df_f.groupby('Tabulação').size())
            with c2: st.bar_chart(df_f.groupby('Atendente').size())
            
            st.subheader("💬 Leitura Direta de Comentários")
            st.dataframe(df_f[['id', 'Atendente', 'Comentário']], use_container_width=True)

        with aba2:
            st.subheader("⏱️ Métricas de Tempo e Eficiência")
            df['Seg_Espera'] = (df['attended_at'] - df['created_at']).dt.total_seconds()
            df['Seg_TMA'] = (df['closed_at'] - df['attended_at']).dt.total_seconds()
            
            st.metric("Tempo Médio de Espera (Fila - Geral)", formatar_tempo(df['Seg_Espera'].mean()))
            
            tma_atend = df.groupby('Atendente')[['Seg_TMA']].mean().reset_index()
            tma_atend['Média TMA'] = tma_atend['Seg_TMA'].apply(formatar_tempo)
            st.table(tma_atend[['Atendente', 'Média TMA']].set_index('Atendente'))

    else:
        st.error("O arquivo não possui a coluna 'feedback_score'.")
