import streamlit as st
import pandas as pd
import re

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(page_title="Painel de Gestão e Auditoria", layout="wide")

# ==============================================================================
# FUNÇÕES AUXILIARES / UTILITÁRIAS
# ==============================================================================
def formatar_tempo(segundos):
    """
    Converte um valor numérico em segundos para uma string legível no formato 'Xh Ymin Zseg'.
    Retorna '0min00seg' para valores nulos ou menores/iguais a zero.
    """
    if pd.isna(segundos) or segundos <= 0:
        return "0min00seg"
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    
    if h > 0:
        return f"{h}h{m:02d}min{s:02d}seg"
    return f"{m}min{s:02d}seg"


# Mapeamento de Logins para Nomes Legíveis
MAPEAMENTO_NOMES = {
    'dolglas': 'Dolglas', 'gcastro': 'Gustavo', 'jonathan': 'Jonathan',
    'jpmairinque': 'Mairinque', 'jpmiranda': 'Miranda', 'lotavio': 'Luis Otavio',
    'luizedu': 'Luiz Eduardo', 'mariana': 'Mariana', 'matheusramao': 'Ramao',
    'moliveira': 'Michel', 'preis': 'Pedro', 'rgomes': 'Rodolpho',
    'ryan': 'Ryan', 'taicyane': 'Taicyane', 'tsouza': 'Tiago', 'luizlima': 'Luiz Felipe'
}

def traduzir_atendente(login):
    """Extrai o nome do atendente com base no login ou e-mail."""
    if pd.isna(login):
        return None
    login_str = str(login).split('@')[0].strip().lower()
    for chave, nome in MAPEAMENTO_NOMES.items():
        if chave in login_str:
            return nome
    return None

# Palavras-chave críticas para análise textual
PALAVRAS_NEGATIVAS = [
    'demora', 'horas', 'dias', 'esperando', 'aguardando', 'ninguém', 'ninguem', 'nunca',
    'cadê', 'cade', 'não recebi', 'nao recebi', 'nada', 'robô', 'robo', 'descaso',
    'falta de respeito', 'de novo', 'novamente', 'não adianta', 'nao adianta',
    'não funciona', 'nao funciona', 'caiu', 'caindo', 'oscilando', 'sem sinal',
    'sem internet', 'instável', 'instabilidade', 'desconectando', 'lento', 'lentidão',
    'ping', 'travando', 'não carrega', 'nao carrega', 'falha', 'problema',
    'não conecta', 'nao conecta', 'sem conecta', 'quedas', 'cancelar', 'cancelamento',
    'lixo', 'ruim', 'péssimo', 'pessimo', 'horrível', 'horrivel', 'absurdo',
    'ridículo', 'ridiculo', 'palhaçada', 'enganação', 'enganacao', 'procon', 'anatel',
    'processo', 'insatisfeito', 'insatisfação', 'pelo amor', 'advogado'
]

# Expressão regular para busca rápida de palavras-chave
PADRAO_PALAVRAS_CRITICAS = re.compile(r'|'.join(r'\b' + re.escape(p) + r'\b' for p in PALAVRAS_NEGATIVAS), re.IGNORECASE)

def eh_comentario_critico(texto):
    """Valida se o comentário contém termos de insatisfação."""
    if not texto or str(texto).lower() in ['nan', 'none', '']:
        return False
    texto_str = str(texto).strip().lower()
    
    # Descarta respostas genéricas curtas ou apenas números
    if texto_str.isdigit() or texto_str in ['bom dia', 'boa tarde', 'boa noite', 'ok', 'sim', 'não', 'nao', 'obrigado', 'obrigada', 'valeu']:
        return False
        
    return bool(PADRAO_PALAVRAS_CRITICAS.search(texto_str))


# ==============================================================================
# EXECUÇÃO PRINCIPAL
# ==============================================================================
st.title("📊 Painel de Gestão e Operação do Suporte")

uploaded_file = st.file_uploader("Faça o upload do relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # 1. Validação de colunas essenciais no arquivo
    colunas_obrigatorias = ['id', 'feedback_score', 'agent_login']
    colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
    
    if colunas_faltantes:
        st.error(f"Erro: O arquivo CSV precisa conter as colunas: {', '.join(colunas_faltantes)}")
    else:
        # 2. Tratamento e Normalização dos Dados
        for col in ['created_at', 'attended_at', 'closed_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        if 'feedback_text' not in df.columns:
            df['feedback_text'] = ""
            
        if 'tabulation' not in df.columns:
            df['tabulation'] = "Sem tabulação"

        df['feedback_text_clean'] = df['feedback_text'].fillna('').astype(str).str.strip()
        df['Atendente'] = df['agent_login'].apply(traduzir_atendente)
        
        # Filtra apenas registros com atendentes mapeados
        df_mapeado = df[df['Atendente'].notna()].copy()

        # 3. Lógica de Auditoria (Apenas para a Aba 1)
        nota_ruim = (df_mapeado['feedback_score'] >= 0) & (df_mapeado['feedback_score'] <= 3)
        tem_comentario_critico_real = df_mapeado['feedback_text_clean'].apply(eh_comentario_critico)
        
        bad_ratings = df_mapeado[nota_ruim | tem_comentario_critico_real].copy()
        bad_ratings['Tabulação'] = bad_ratings['tabulation'].fillna('Sem tabulação')
        bad_ratings['Comentário'] = bad_ratings['feedback_text_clean'].replace('', 'Sem comentário')
        
        final_df = bad_ratings[['id', 'Atendente', 'feedback_score', 'Tabulação', 'Comentário', 'created_at', 'feedback_text_clean']].copy()
        final_df.columns = ['ID do Atendimento', 'Atendente', 'Nota', 'Tabulação', 'Comentário', 'Data do Atendimento', 'Raw_Text']

        # 4. Construção das Abas da Interface
        aba1, aba2 = st.tabs(["📋 Auditoria de Notas", "⏱️ Métricas de Tempo"])

        # --- ABA 1: AUDITORIA ---
        with aba1:
            st.write("🔍 **Filtros de Auditoria (Selecione abaixo):**")
            c1, c2, c3 = st.columns(3)
            
            lista_at = sorted(final_df['Atendente'].unique().tolist())
            lista_nota = sorted(final_df['Nota'].unique().tolist())
            lista_tab = sorted(final_df['Tabulação'].unique().tolist())
            
            with c1: f_at = st.multiselect("Atendente(s):", lista_at, default=lista_at)
            with c2: f_nota = st.multiselect("Nota(s):", lista_nota, default=lista_nota)
            with c3: f_tab = st.multiselect("Tabulação(ões):", lista_tab, default=lista_tab)
            
            # Aplicação dos Filtros
            df_filtrado = final_df[
                (final_df['Atendente'].isin(f_at)) & 
                (final_df['Nota'].isin(f_nota)) & 
                (final_df['Tabulação'].isin(f_tab))
            ]
            
            st.subheader(f"📋 Encontramos {len(df_filtrado)} atendimentos críticos para análise")
            
            # Exibição por Colaborador
            atendentes_filtrados = sorted(df_filtrado['Atendente'].unique().tolist())
            if not atendentes_filtrados:
                st.info("Nenhum atendimento encontrado com os filtros selecionados.")
            else:
                for colaborador in atendentes_filtrados:
                    df_colab = df_filtrado[df_filtrado['Atendente'] == colaborador]
                    with st.expander(f"👤 {colaborador} ({len(df_colab)} atendimentos)", expanded=False):
                        tabela_colab = df_colab[['ID do Atendimento', 'Nota', 'Comentário', 'Tabulação']]
                        st.dataframe(tabela_colab, use_container_width=True, hide_index=True)
            
            # Visualizações Gráficas
            st.markdown("---")
            g1, g2 = st.columns(2)
            
            with g1:
                st.write("**Gargalos por Tabulação:**")
                resumo_tab = df_filtrado.groupby('Tabulação').size().reset_index(name='Quantidade')
                if not resumo_tab.empty:
                    st.bar_chart(resumo_tab.set_index('Tabulação'))
                with st.expander("➕ Ver IDs por Tabulação"):
                    ids_por_tab = df_filtrado.groupby('Tabulação')['ID do Atendimento'].apply(lambda x: ', '.join(x.astype(str))).reset_index()
                    for _, row in ids_por_tab.iterrows():
                        st.markdown(f"**{row['Tabulação']}:** {row['ID do Atendimento']}")
                        
            with g2:
                st.write("**Gargalos por Atendente:**")
                resumo_ag = df_filtrado.groupby('Atendente').size().reset_index(name='Quantidade')
                if not resumo_ag.empty:
                    st.bar_chart(resumo_ag.set_index('Atendente'))
                with st.expander("➕ Ver IDs por Atendente"):
                    ids_por_ag = df_filtrado.groupby('Atendente')['ID do Atendimento'].apply(lambda x: ', '.join(x.astype(str))).reset_index()
                    for _, row in ids_por_ag.iterrows():
                        st.markdown(f"**{row['Atendente']}:** {row['ID do Atendimento']}")

            # Leitura de Comentários
            st.markdown("---")
            st.subheader("💬 Leitura Direta de IDs e Comentários Críticos")
            df_comentarios = df_filtrado[df_filtrado['Raw_Text'].apply(eh_comentario_critico)].copy()
            tabela_comentarios = df_comentarios[['ID do Atendimento', 'Atendente', 'Comentário']]
            st.dataframe(tabela_comentarios, use_container_width=True, hide_index=True)

        # --- ABA 2: MÉTRICAS DE TEMPO ---
        with aba2:
            st.subheader("⏱️ Métricas de Tempo e Eficiência (Geral da Base)")
            
            # Cálculo dos tempos em segundos
            if 'attended_at' in df_mapeado.columns and 'created_at' in df_mapeado.columns:
                df_mapeado['Seg_Espera'] = (df_mapeado['attended_at'] - df_mapeado['created_at']).dt.total_seconds()
            else:
                df_mapeado['Seg_Espera'] = 0

            if 'closed_at' in df_mapeado.columns and 'attended_at' in df_mapeado.columns:
                df_mapeado['Seg_TMA'] = (df_mapeado['closed_at'] - df_mapeado['attended_at']).dt.total_seconds()
            else:
                df_mapeado['Seg_TMA'] = 0
            
            # Exibe tempo médio geral de espera na fila
            st.metric("Tempo Médio de Espera (Fila - Geral)", formatar_tempo(df_mapeado['Seg_Espera'].mean()))
            
            # 1. Cria DataFrame base com TODOS os atendentes cadastrados no dicionário
            todos_atendentes = sorted(list(set(MAPEAMENTO_NOMES.values())))
            df_todos = pd.DataFrame({'Atendente': todos_atendentes})
            
            # 2. Calcula as médias por atendente a partir dos atendimentos presentes no CSV
            tma_calculado = df_mapeado.groupby('Atendente')['Seg_TMA'].mean().reset_index()
            
            # 3. Faz o merge para incluir quem não teve atendimento (ficando com NaN ou 0)
            tma_completo = pd.merge(df_todos, tma_calculado, on='Atendente', how='left')
            
            # 4. Formata o tempo para exibição legível
            tma_completo['Média TMA'] = tma_completo['Seg_TMA'].apply(formatar_tempo)
            
            # 5. Exibe a tabela final
            st.table(tma_completo[['Atendente', 'Média TMA']].set_index('Atendente'))
