import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel de Auditoria de Notas", layout="wide")

st.title("📊 Painel de Auditoria de Notas Baixas")
st.write("Gerencie os atendimentos críticos de forma simples, direta e organizada.")

# Área de Upload
uploaded_file = st.file_uploader("Faça o upload do seu relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    # Lendo o arquivo
    df = pd.read_csv(uploaded_file)
    
    if 'feedback_score' in df.columns:
        
        # Garante que a coluna de texto exista
        if 'feedback_text' not in df.columns:
            df['feedback_text'] = None

        # REGRA 1: Nota de 0 a 3 (Ignorando o -1)
        nota_ruim = (df['feedback_score'] >= 0) & (df['feedback_score'] <= 3)
        
        # REGRA 2: Radar de Insatisfação Turbinado
        palavras_negativas = [
            'demora', 'horas', 'dias', 'esperando', 'aguardando', 'ninguém', 'ninguem', 
            'nunca', 'cadê', 'cade', 'não recebi', 'nao recebi', 'nada', 'robô', 'robo', 
            'descaso', 'falta de respeito', 'de novo', 'novamente', 'não adianta', 'nao adianta',
            'não funciona', 'nao funciona', 'caiu', 'caindo', 'oscilando', 'sem sinal', 
            'sem internet', 'instável', 'instabilidade', 'desconectando', 'lento', 
            'lentidão', 'ping', 'travando', 'não carrega', 'nao carrega', 'falha', 
            'problema', 'não conecta', 'nao conecta', 'sem conecta', 'quedas',
            'cancelar', 'cancelamento', 'lixo', 'ruim', 'péssimo', 'pessimo', 'horrível', 
            'horrivel', 'absurdo', 'ridículo', 'ridiculo', 'palhaçada', 'enganação', 
            'enganacao', 'procon', 'anatel', 'processo', 'insatisfeito', 'insatisfação', 
            'pelo amor', 'advogado'
        ]
        
        def eh_comentario_critico(texto):
            if pd.isna(texto):
                return False
            texto_str = str(texto).lower().strip()
            if texto_str in ['bom dia', 'boa tarde', 'boa noite', 'ok', 'sim', 'não', 'nao', 'obrigado', 'obrigada', 'valeu']:
                return False
            for palavra in palavras_negativas:
                if palavra in texto_str:
                    return True
            return False

        tem_comentario_ruim = df['feedback_text'].apply(eh_comentario_critico)
        
        # Junta as duas regras de filtro
        bad_ratings = df[nota_ruim | tem_comentario_ruim].copy()
        
        # Limpeza e Tratamento dos Dados
        bad_ratings['Atendente'] = bad_ratings['agent_login'].apply(
            lambda x: str(x).split('@')[0] if pd.notna(x) else 'Sem usuário (Em branco)'
        )
        bad_ratings['Tabulação'] = bad_ratings['tabulation'].fillna('Sem tabulação')
        bad_ratings['Comentário'] = bad_ratings['feedback_text'].fillna('Sem comentário')
        
        # Selecionando e renomeando as colunas
        final_df = bad_ratings[['id', 'Atendente', 'feedback_score', 'Tabulação', 'Comentário', 'created_at']]
        final_df.columns = ['ID do Atendimento', 'Atendente', 'Nota', 'Tabulação', 'Comentário', 'Data do Atendimento']
        
        # --- FILTROS COM MÚLTIPLA SELEÇÃO COMPACTA ---
        st.markdown("---")
        st.write("🔍 **Filtrar Dados do Relatório:**")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        
        lista_atendentes = sorted(final_df['Atendente'].unique().tolist())
        lista_notas = sorted(final_df['Nota'].unique().tolist())
        lista_tabulacoes = sorted(final_df['Tabulação'].unique().tolist())
        
        with col_f1:
            filtro_atendente = st.multiselect("👥 Atendente(s):", lista_atendentes, default=lista_atendentes)
            
        with col_f2:
            filtro_nota = st.multiselect("⭐ Nota(s):", lista_notas, default=lista_notas)
            
        with col_f3:
            filtro_tabulacao = st.multiselect("🏷️ Tabulação(ões):", lista_tabulacoes, default=lista_tabulacoes)
            
        # Aplicando os filtros
        df_filtrado = final_df[
            (final_df['Atendente'].isin(filtro_atendente)) &
            (final_df['Nota'].isin(filtro_nota)) &
            (final_df['Tabulação'].isin(filtro_tabulacao))
        ]
        st.markdown("---")
        # --------------------------------------------------------
        
        st.subheader(f"📋 Encontramos {len(df_filtrado)} atendimentos (com base nos filtros)")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # Resumo quantitativo com gráficos e expansores limpos
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.write("**Gargalos por Tabulação:**")
            resumo_motivo = df_filtrado.groupby('Tabulação').size().reset_index(name='Quantidade')
            st.dataframe(resumo_motivo, use_container_width=True)
            
            if not resumo_motivo.empty:
                st.bar_chart(resumo_motivo.set_index('Tabulação'))
            
            with st.expander("➕ Ver IDs por Tabulação"):
                ids_por_tab = df_filtrado.groupby('Tabulação')['ID do Atendimento'].apply(lambda x: ', '.join(x.astype(str))).reset_index()
                for _, row in ids_por_tab.iterrows():
                    st.markdown(f"**{row['Tabulação']}:** {row['ID do Atendimento']}")
                
        with col_r2:
            st.write("**Gargalos por Atendente:**")
            resumo_agente = df_filtrado.groupby('Atendente').size().reset_index(name='Quantidade')
            st.dataframe(resumo_agente, use_container_width=True)
            
            if not resumo_agente.empty:
                st.bar_chart(resumo_agente.set_index('Atendente'))
            
            with st.expander("➕ Ver IDs por Atendente"):
                ids_por_agente = df_filtrado.groupby('Atendente')['ID do Atendimento'].apply(lambda x: ', '.join(x.astype(str))).reset_index()
                for _, row in ids_por_agente.iterrows():
                    st.markdown(f"**{row['Atendente']}:** {row['ID do Atendimento']}")
        
        # Botão para baixar o relatório já filtrado
        csv_export = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Relatório Filtrado (CSV)",
            data=csv_export,
            file_name="relatorio_notas_filtrado.csv",
            mime="text/csv",
        )
    else:
        st.error("O arquivo enviado não possui a coluna 'feedback_score'. Verifique se é o relatório correto.")
