import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel de Auditoria de Atendimentos", layout="wide")

# Função de formatação de tempo inteligente (oculta 0h se for menor que uma hora)
def formatar_tempo(segundos):
    if pd.isna(segundos) or segundos <= 0: return "0min00seg"
    segundos = int(segundos)
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    if h > 0: return f"{h}h{m:02d}min{s:02d}seg"
    else: return f"{m}min{s:02d}seg"

st.title("📊 Painel de Auditoria de Atendimentos Críticos")
st.write("Gerencie notas baixas e reclamações reais com os nomes oficiais da equipe.")

# Área de Upload
uploaded_file = st.file_uploader("Faça o upload do seu relatório (.csv)", type=['csv'])

if uploaded_file is not None:
    # Lendo o arquivo
    df = pd.read_csv(uploaded_file)
    
    # Tratamento de Datas para o TMA
    for col in ['created_at', 'attended_at', 'closed_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'feedback_score' in df.columns:
        if 'feedback_text' not in df.columns: df['feedback_text'] = None
        df['feedback_text_clean'] = df['feedback_text'].fillna('').astype(str).str.strip()

        # Dicionário de Atendentes
        mapeamento_nomes = {
            'dolglas': 'Dolglas', 'gcastro': 'Gustavo', 'jonathan': 'Jonathan',
            'jpmairinque': 'Mairinque', 'jpmiranda': 'Miranda', 'lotavio': 'Luis Otavio',
            'luizedu': 'Luiz Eduardo', 'mariana': 'Mariana', 'matheusramao': 'Ramao',
            'moliveira': 'Michel', 'preis': 'Pedro', 'rgomes': 'Rodolpho',
            'ryan': 'Ryan', 'taicyane': 'Taicyane', 'tsouza': 'Tiago', 'luizlima': 'Luiz Felipe'
        }

        def traduzir_atendente(login):
            if pd.isna(login): return 'Sem usuário (Em branco)'
            login_str = str(login).split('@')[0].strip().lower()
            for chave, nome in mapeamento_nomes.items():
                if chave in login_str: return nome
            return login_str

        df['Atendente'] = df['agent_login'].apply(traduzir_atendente)
        
        # --- ABAS DO PAINEL ---
        aba1, aba2 = st.tabs(["📋 Auditoria de Notas", "⏱️ Métricas de Tempo"])

        with aba1:
            # Lógica de Auditoria (Sua estrutura original)
            nota_ruim = (df['feedback_score'] >= 0) & (df['feedback_score'] <= 3)
            palavras_negativas = ['demora', 'horas', 'dias', 'esperando', 'aguardando', 'ninguém', 'ninguem', 'nunca', 'cadê', 'cade', 'não recebi', 'nao recebi', 'nada', 'robô', 'robo', 'descaso', 'falta de respeito', 'de novo', 'novamente', 'não adianta', 'nao adianta', 'não funciona', 'nao funciona', 'caiu', 'caindo', 'oscilando', 'sem sinal', 'sem internet', 'instável', 'instabilidade', 'desconectando', 'lento', 'lentidão', 'ping', 'travando', 'não carrega', 'nao carrega', 'falha', 'problema', 'não conecta', 'nao conecta', 'sem conecta', 'quedas', 'cancelar', 'cancelamento', 'lixo', 'ruim', 'péssimo', 'pessimo', 'horrível', 'horrivel', 'absurdo', 'ridículo', 'ridiculo', 'palhaçada', 'enganação', 'enganacao', 'procon', 'anatel', 'processo', 'insatisfeito', 'insatisfação', 'pelo amor', 'advogado']
            
            def eh_comentario_critico(texto):
                if not texto or texto.lower() in ['nan', 'none', '']: return False
                if str(texto).isdigit(): return False
                texto_str = str(texto).lower()
                if texto_str in ['bom dia', 'boa tarde', 'boa noite', 'ok', 'sim', 'não', 'nao', 'obrigado', 'obrigada', 'valeu']: return False
                return any(p in texto_str for p in palavras_negativas)

            tem_comentario_critico_real = df['feedback_text_clean'].apply(eh_comentario_critico)
            bad_ratings = df[nota_ruim | tem_comentario_critico_real].copy()
            bad_ratings['Tabulação'] = bad_ratings['tabulation'].fillna('Sem tabulação')
            bad_ratings['Comentário'] = bad_ratings['feedback_text_clean'].replace('', 'Sem comentário')
            final_df = bad_ratings[['id', 'Atendente', 'feedback_score', 'Tabulação', 'Comentário', 'created_at', 'feedback_text_clean']]
            final_df.columns = ['ID do Atendimento', 'Atendente', 'Nota', 'Tabulação', 'Comentário', 'Data do Atendimento', 'Raw_Text']

            st.write("🔍 **Filtros de Visualização (Selecione abaixo):**")
            c1, c2, c3 = st.columns(3)
            with c1: f_at = st.multiselect("Atendente(s):", sorted(final_df['Atendente'].unique()), default=sorted(final_df['Atendente'].unique()))
            with c2: f_nota = st.multiselect("Nota(s):", sorted(final_df['Nota'].unique()), default=sorted(final_df['Nota'].unique()))
            with c3: f_tab = st.multiselect("Tabulação(ões):", sorted(final_df['Tabulação'].unique()), default=sorted(final_df['Tabulação'].unique()))
            
            df_filtrado = final_df[(final_df['Atendente'].isin(f_at)) & (final_df['Nota'].isin(f_nota)) & (final_df['Tabulação'].isin(f_tab))]
            
            st.subheader(f"📋 Encontramos {len(df_filtrado)} atendimentos críticos")
            st.dataframe(df_filtrado.drop(columns=['Raw_Text']), use_container_width=True)
            
            c_g1, c_g2 = st.columns(2)
            with c_g1: st.bar_chart(df_filtrado.groupby('Tabulação').size())
            with c_g2: st.bar_chart(df_filtrado.groupby('Atendente').size())
            
            st.subheader("💬 Leitura Direta de IDs e Comentários Críticos")
            df_comentarios = df_filtrado[df_filtrado['Raw_Text'].apply(eh_comentario_critico)][['ID do Atendimento', 'Atendente', 'Comentário']]
            st.dataframe(df_comentarios, use_container_width=True)

        with aba2:
            st.subheader("⏱️ Métricas de Tempo e Eficiência")
            df['Seg_Espera'] = (df['attended_at'] - df['created_at']).dt.total_seconds()
            df['Seg_TMA'] = (df['closed_at'] - df['attended_at']).dt.total_seconds()
            
            st.metric("Tempo Médio de Espera (Fila - Geral)", formatar_tempo(df['Seg_Espera'].mean()))
            
            tma_atend = df.groupby('Atendente')[['Seg_TMA']].mean().reset_index()
            tma_atend['Média TMA'] = tma_atend['Seg_TMA'].apply(formatar_tempo)
            st.table(tma_atend[['Atendente', 'Média TMA']].set_index('Atendente'))
