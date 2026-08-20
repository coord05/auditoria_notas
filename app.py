import streamlit as st
import pandas as pd
import re

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Painel de Gestão e Auditoria",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. FUNÇÕES AUXILIARES / UTILITÁRIAS
# ==============================================================================
def formatar_tempo(segundos):
    """
    Converte segundos em uma string legível: 'Xh Ymin Zseg' ou 'Xmin Yseg'.
    Valores nulos, menores ou iguais a zero retornam '0min00seg'.
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


# Mapeamento de logins para exibição dos nomes dos colaboradores
MAPEAMENTO_NOMES = {
    'dolglas': 'Dolglas', 'gcastro': 'Gustavo', 'jonathan': 'Jonathan',
    'jpmairinque': 'Mairinque', 'jpmiranda': 'Miranda', 'lotavio': 'Luis Otavio',
    'luizedu': 'Luiz Eduardo', 'mariana': 'Mariana', 'matheusramao': 'Ramao',
    'moliveira': 'Michel', 'preis': 'Pedro', 'rgomes': 'Rodolpho',
    'ryan': 'Ryan', 'taicyane': 'Taicyane', 'tsouza': 'Tiago', 'luizlima': 'Luiz Felipe'
}

def traduzir_atendente(login):
    """Identifica o atendente correspondente a partir do login ou e-mail."""
    if pd.isna(login):
        return None
    login_str = str(login).split('@')[0].strip().lower()
    for chave, nome in MAPEAMENTO_NOMES.items():
        if chave in login_str:
            return nome
    return None

# Lista de palavras-chave para identificação de feedbacks negativos
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

PADRAO_PALAVRAS_CRITICAS = re.compile(
    r'|'.join(r'\b' + re.escape(p) + r'\b' for p in PALAVRAS_NEGATIVAS),
    re.IGNORECASE
)

def eh_comentario_critico(texto):
    """Verifica se a mensagem contém termos críticos ou de insatisfação."""
    if not texto or str(texto).lower() in ['nan', 'none', '']:
        return False
    texto_str = str(texto).strip().lower()
    
    # Ignora mensagens padrão ou vazias
    if texto_str.isdigit() or texto_str in ['bom dia', 'boa tarde', 'boa noite', 'ok', 'sim', 'não', 'nao', 'obrigado', 'obrigada', 'valeu']:
        return False
        
    return bool(PADRAO_PALAVRAS_CRITICAS.search(texto_str))


# ==============================================================================
# 3. INTERFACE E CARREGAMENTO DE ARQUIVOS
# ==============================================================================
st.title("📊 Painel de Gestão e Operação do Suporte")

uploaded_file = st.file_uploader("Faça o upload do relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")
        st.stop()

    # Validação de colunas mínimas
    colunas_obrigatorias = ['id', 'feedback_score', 'agent_login']
    colunas_faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
    
    if colunas_faltantes:
        st.error(f"Erro: O arquivo precisa conter as seguintes colunas: {', '.join(colunas_faltantes)}")
    else:
        # Tratamento de datas com segurança
        for col in ['created_at', 'attended_at', 'closed_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            else:
                df[col] = pd.NaT

        # Tratamento de colunas de texto
        if 'feedback_text' not in df.columns:
            df['feedback_text'] = ""
        if 'tabulation' not in df.columns:
            df['tabulation'] = "Sem tabulação"

        df['feedback_text_clean'] = df['feedback_text'].fillna('').astype(str).str.strip()
        df['Atendente'] = df['agent_login'].apply(traduzir_atendente)
        
        # Filtro com apenas atendentes mapeados
        df_mapeado = df[df['Atendente'].notna()].copy()

        # ==============================================================================
        # 4. PROCESSAMENTO DA AUDITORIA (ABA 1)
        # ==============================================================================
        nota_ruim = (df_mapeado['feedback_score'] >= 0) & (df_mapeado['feedback_score'] <= 3)
        tem_comentario_critico_real = df_mapeado['feedback_text_clean'].apply(eh_comentario_critico)
        
        bad_ratings = df_mapeado[nota_ruim | tem_comentario_critico_real].copy()
        bad_ratings['Tabulação'] = bad_ratings['tabulation'].fillna('Sem tabulação')
        bad_ratings['Comentário'] = bad_ratings['feedback_text_clean'].replace('', 'Sem comentário')
        
        final_df = bad_ratings[['id', 'Atendente', 'feedback_score', 'Tabulação', 'Comentário', 'created_at', 'feedback_text_clean']].copy()
        final_df.columns = ['ID do Atendimento', 'Atendente', 'Nota', 'Tabulação', 'Comentário', 'Data do Atendimento', 'Raw_Text']

        # ==============================================================================
        # 5. CONSTRUÇÃO DAS ABAS
        # ==============================================================================
        aba1, aba2 = st.tabs(["📋 Auditoria de Notas", "⏱️ Métricas de Tempo"])

        # --- ABA 1: AUDITORIA ---
        with aba1:
            st.write("🔍 **Filtros de Auditoria:**")
            c1, c2, c3 = st.columns(3)
            
            lista_at = sorted(final_df['Atendente'].unique().tolist())
            lista_nota = sorted(final_df['Nota'].unique().tolist())
            lista_tab = sorted(final_df['Tabulação'].unique().tolist())
            
            with c1: f_at = st.multiselect("Atendente(s):", lista_at, default=lista_at)
            with c2: f_nota = st.multiselect("Nota(s):", lista_nota, default=lista_nota)
            with c3: f_tab = st.multiselect("Tabulação(ões):", lista_tab, default=lista_tab)
            
            df_filtrado = final_df[
                (final_df['Atendente'].isin(f_at)) & 
                (final_df['Nota'].isin(f_nota)) & 
                (final_df['Tabulação'].isin(f_tab))
            ]
            
            st.subheader(f"📋 Encontramos {len(df_filtrado)} atendimentos críticos para análise")
            
            atendentes_filtrados = sorted(df_filtrado['Atendente'].unique().tolist())
            if not atendentes_filtrados:
                st.info("Nenhum atendimento encontrado com os filtros selecionados.")
            else:
                for colaborador in atendentes_filtrados:
                    df_colab = df_filtrado[df_filtrado['Atendente'] == colaborador]
                    with st.expander(f"👤 {colaborador} ({len(df_colab)} atendimentos)", expanded=False):
                        tabela_colab = df_colab[['ID do Atendimento', 'Nota', 'Comentário', 'Tabulação']]
                        st.dataframe(tabela_colab, use_container_width=True, hide_index=True)
            
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

            st.markdown("---")
            st.subheader("💬 Leitura Direta de IDs e Comentários Críticos")
            df_comentarios = df_filtrado[df_filtrado['Raw_Text'].apply(eh_comentario_critico)].copy()
            tabela_comentarios = df_comentarios[['ID do Atendimento', 'Atendente', 'Comentário']]
            st.dataframe(tabela_comentarios, use_container_width=True, hide_index=True)

        # --- ABA 2: MÉTRICAS DE TEMPO ---
        with aba2:
            st.subheader("⏱️ Métricas de Tempo e Eficiência (Geral da Base)")
            
            # Cálculos de diferenças de tempo de forma segura
            df_mapeado['Seg_Espera'] = (df_mapeado['attended_at'] - df_mapeado['created_at']).dt.total_seconds().fillna(0)
            df_mapeado['Seg_TMA'] = (df_mapeado['closed_at'] - df_mapeado['attended_at']).dt.total_seconds().fillna(0)

            # Métricas gerais
            media_espera_geral = df_mapeado['Seg_Espera'].mean()
            st.metric("Tempo Médio de Espera (Fila - Geral)", formatar_tempo(media_espera_geral))
            
            # 1. Obter todos os atendentes únicos cadastrados
            todos_atendentes = sorted(list(set(MAPEAMENTO_NOMES.values())))
            df_todos = pd.DataFrame({'Atendente': todos_atendentes})
            
            # 2. Calcular TMA médio apenas para os que possuem registros válidos
            tma_calculado = df_mapeado[df_mapeado['Seg_TMA'] > 0].groupby('Atendente')['Seg_TMA'].mean().reset_index()
            
            # 3. Unificar a lista completa de atendentes com os cálculos
            tma_completo = pd.merge(df_todos, tma_calculado, on='Atendente', how='left')
            tma_completo['Seg_TMA'] = tma_completo['Seg_TMA'].fillna(0)
            
            # 4. Formatar a coluna para texto legível
            tma_completo['Média TMA'] = tma_completo['Seg_TMA'].apply(formatar_tempo)
            
            # 5. Exibir a tabela final
            st.dataframe(
                tma_completo[['Atendente', 'Média TMA']],
                use_container_width=True,
                hide_index=True
            )
else:
    st.info("👆 Por favor, envie o arquivo CSV no campo acima para carregar o painel.")
