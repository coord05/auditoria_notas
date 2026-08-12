import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Auditoria de Notas Huggy", layout="wide")

st.title("📊 Painel de Auditoria de Notas Baixas")
st.write("Arraste o arquivo CSV do sistema para gerar o relatório com os IDs, Atendentes e Tabulações.")

# Área de Upload
uploaded_file = st.file_uploader("Faça o upload do seu relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    # Lendo o arquivo
    df = pd.read_csv(uploaded_file)
    
    if 'feedback_score' in df.columns:
        # Filtrando notas de 0 a 3
        bad_ratings = df[(df['feedback_score'] >= 0) & (df['feedback_score'] <= 3)].copy()
        
        # Limpeza e Tratamento dos Dados: Ajuste dos termos vazios
        bad_ratings['Atendente'] = bad_ratings['agent_login'].apply(
            lambda x: str(x).split('@')[0] if pd.notna(x) else 'Sem usuário (Em branco)'
        )
        bad_ratings['Tabulação'] = bad_ratings['tabulation'].fillna('Sem tabulação')
        
        # Selecionando e renomeando as colunas que importam
        final_df = bad_ratings[['id', 'Atendente', 'feedback_score', 'Tabulação', 'created_at']]
        final_df.columns = ['ID do Atendimento', 'Atendente', 'Nota', 'Tabulação', 'Data do Atendimento']
        
        st.subheader(f"📋 Encontramos {len(final_df)} avaliações ruins")
        st.dataframe(final_df, use_container_width=True)
        
        # Resumo quantitativo
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Gargalos por Tabulação:**")
            resumo_motivo = final_df.groupby('Tabulação').size().reset_index(name='Quantidade')
            st.dataframe(resumo_motivo, use_container_width=True)
            
        with col2:
            st.write("**Gargalos por Atendente:**")
            resumo_agente = final_df.groupby('Atendente').size().reset_index(name='Quantidade')
            st.dataframe(resumo_agente, use_container_width=True)
        
        # Botão para baixar o relatório tratado
        csv_export = final_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Relatório Tratado para Planilha (CSV)",
            data=csv_export,
            file_name="relatorio_notas_ruins_tratado.csv",
            mime="text/csv",
        )
    else:
        st.error("O arquivo enviado não possui a coluna 'feedback_score'. Verifique se é o relatório correto.")
