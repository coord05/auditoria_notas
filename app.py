import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel de Auditoria de Comentários", layout="wide")

st.title("📊 Painel de Auditoria de Comentários dos Clientes")
st.write("Exibindo exclusivamente os atendimentos que possuem comentários reais dos clientes.")

# Área de Upload
uploaded_file = st.file_uploader("Faça o upload do seu relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    # Lendo o arquivo
    df = pd.read_csv(uploaded_file)
    
    if 'feedback_score' in df.columns and 'feedback_text' in df.columns:
        
        # TRATAMENTO INICIAL: Limpa valores nulos e garante texto string
        df['feedback_text'] = df['feedback_text'].fillna('')
        
        # Filtra estritamente para manter APENAS quem tem comentário real (ignora vazios, espaços ou apenas números)
        tem_texto = df['feedback_text'].astype(str).str.strip() != ''
        nao_e_so_numero = ~df['feedback_text'].astype(str).str.isnumeric()
        
        comentarios_reais = df[tem_texto & nao_e_so_numero].copy()
        
        # Limpeza e Tratamento dos Dados
        comentarios_reais['Atendente'] = comentarios_reais['agent_login'].apply(
            lambda x: str(x).split('@')[0] if pd.notna(x) else 'Sem usuário (Em branco)'
        )
        comentarios_reais['Tabulação'] = comentarios_reais['tabulation'].fillna('Sem tabulação')
        comentarios_reais['Comentário'] = comentarios_reais['feedback_text'].astype(str).str.strip()
        
        # Selecionando e renomeando as colunas
        final_df = comentarios_reais[['id', 'Atendente', 'feedback_score', 'Tabulação', 'Comentário', 'created_at']]
        final_df.columns = ['ID do Atendimento', 'Atendente', 'Nota', 'Tabulação', 'Comentário', 'Data do Atendimento']
        
        # --- FILTROS LATERAIS INTERATIVOS ---
        st.sidebar.header("🔍 Filtros Dinâmicos")
        st.sidebar.write("Refine a exibição dos comentários:")
        
        # Filtro por Atendente
        lista_atendentes = final_df['Atendente'].unique().tolist()
        filtro_atendente = st.sidebar.multiselect("👥 Atendente:", lista_atendentes, default=lista_atendentes)
        
        # Filtro por Nota
        lista_notas = final_df['Nota'].unique().tolist()
        filtro_nota = st.sidebar.multiselect("⭐ Nota:", lista_notas, default=lista_notas)
        
        # Filtro por Tabulação
        lista_tabulacoes = final_df['Tabulação'].unique().tolist()
        filtro_tabulacao = st.sidebar.multiselect("🏷️ Tabulação:", lista_tabulacoes, default=lista_tabulacoes)
        
        # Aplicando os filtros
        df_filtrado = final_df[
            (final_df['Atendente'].isin(filtro_atendente)) &
            (final_df['Nota'].isin(filtro_nota)) &
            (final_df['Tabulação'].isin(filtro_tabulacao))
        ]
        # ------------------------------------
        
        st.subheader(f"📋 Encontramos {len(df_filtrado)} atendimentos com comentários reais")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Resumo quantitativo com gráficos e expansores
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Gargalos por Tabulação:**")
            resumo_motivo = df_filtrado.groupby('Tabulação').size().reset_index(name='Quantidade')
            st.dataframe(resumo_motivo, use_container_width=True)
            
            if not resumo_motivo.empty:
                st.bar_chart(resumo_motivo.set_index('Tabulação'))
            
            with st.expander("➕ Ver IDs por Tabulação"):
                ids_por_tab = df_filtrado.groupby('Tabulação')['ID do Atendimento'].apply(lambda x: ', '.join(x.astype(str))).reset_index()
                for _, row in ids_por_tab.iterrows():
                    st.markdown(f"**{row['Tabulação']}:** {row['ID do Atendimento']}")
                
        with col2:
            st.write("**Gargalos por Atendente:**")
            resumo_agente = df_filtrado.groupby('Atendente').size().reset_index(name='Quantidade')
            st.dataframe(resumo_agente, use_container_width=True)
            
            if not resumo_agente.empty:
                st.bar_chart(resumo_agente.set_index('Atendente'))
            
            with st.expander("➕ Ver IDs por Atendente"):
                ids_por_agente = df_filtrado.groupby('Atendente')['ID do Atendimento'].apply(lambda x: ', '.join(x.astype(str))).reset_index()
                for _, row in ids_por_agente.iterrows():
                    st.markdown(f"**{row['Atendente']}:** {row['ID do Atendimento']}")
        
        # --- TABELA DE LEITURA DIRETA ---
        st.markdown("---")
        st.subheader("💬 Leitura Direta de IDs e Comentários")
        tabela_comentarios = df_filtrado[['ID do Atendimento', 'Atendente', 'Comentário']]
        st.dataframe(tabela_comentarios, use_container_width=True)
        # --------------------------------

        # Botão para baixar o relatório já filtrado
        csv_export = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Relatório de Comentários (CSV)",
            data=csv_export,
            file_name="relatorio_comentarios_clientes.csv",
            mime="text/csv",
        )
    else:
        st.error("O arquivo enviado não possui as colunas necessárias ('feedback_score' e 'feedback_text'). Verifique o relatório.")
