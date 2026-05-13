
# INCLUISRM V30 - Plano AEE IA com histórico em horário local e relatórios visuais
# Atualização: corrige fuso horário America/Recife e preserva layout visual dos relatórios.

import os
import re
import sqlite3
import calendar
from datetime import datetime, date, time, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
from pathlib import Path
from html import escape

import streamlit as st
import pandas as pd
import altair as alt

if "form_reset" not in st.session_state:
    st.session_state.form_reset = {}


def get_form_key(nome):
    if nome not in st.session_state.form_reset:
        st.session_state.form_reset[nome] = 0
    return f"{nome}_{st.session_state.form_reset[nome]}"


def resetar_form(nome):
    if nome not in st.session_state.form_reset:
        st.session_state.form_reset[nome] = 0
    st.session_state.form_reset[nome] += 1


try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# ======================================================
# CONFIGURAÇÕES GERAIS
# ======================================================
st.set_page_config(
    page_title="INCLUISRM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path("inclui_paee.db")
LOGO_PATH = "logosrm.png"

# Pastas da Base de Conhecimento IA
BASE_CONHECIMENTO_DIR = Path("base_conhecimento")
PASTA_CIENTIFICA = BASE_CONHECIMENTO_DIR / "cientifica"
PASTA_PEDAGOGICA = BASE_CONHECIMENTO_DIR / "pedagogica"
CHROMA_DIR = Path("chroma_db_incluisrm")
DOCUMENTOS_AVALIACOES_DIR = Path("documentos_avaliacoes")

BASE_CONHECIMENTO_DIR.mkdir(parents=True, exist_ok=True)
PASTA_CIENTIFICA.mkdir(parents=True, exist_ok=True)
PASTA_PEDAGOGICA.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTOS_AVALIACOES_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "INCLUISRM"
APP_SUBTITLE = "Sistema Inteligente de Articulação Pedagógica Inclusiva"
APP_VERSION = "V30"
APP_VERSION_LABEL = "Perfil Pedagógico unificado • Relatórios Visuais por identidade • Estudo Pedagógico visual"
# Fuso fixo UTC-3 usado por Recife/Pernambuco.
# Usar timezone/timedelta evita erro em ambientes Render sem base tzdata completa.
FUSO_LOCAL = timezone(timedelta(hours=-3), name="America/Recife")
os.environ["TZ"] = "America/Recife"
try:
    import time as _time_module
    if hasattr(_time_module, "tzset"):
        _time_module.tzset()
except Exception:
    pass


def agora_local():
    """Retorna data/hora no fuso local America/Recife, independente do UTC do servidor."""
    return datetime.now(timezone.utc).astimezone(FUSO_LOCAL)


# ======================================================
# CSS / LAYOUT PROFISSIONAL
# ======================================================
st.markdown(
    """
<style>
/* =============================
   INCLUISRM - Layout profissional
   ============================= */

.stApp {
    background: linear-gradient(180deg, #f7f9fc 0%, #eef3f9 100%);
}

.block-container {
    padding-top: 2.2rem;
    padding-bottom: 2.5rem;
    padding-left: 2.4rem;
    padding-right: 2.4rem;
    max-width: 1400px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.14);
}

.sidebar-logo-card {
    background: transparent;
    border-radius: 0;
    padding: 0;
    margin: 4px 0 14px 0;
    box-shadow: none;
}

.sidebar-logo-card img {
    border-radius: 14px;
}

.sidebar-title {
    font-size: 20px;
    font-weight: 900;
    letter-spacing: 0.5px;
    margin-top: 8px;
}

.sidebar-subtitle {
    font-size: 12px;
    color: #cbd5e1 !important;
    line-height: 1.35;
    margin-bottom: 12px;
}

/* Hero */
.app-hero {
    background: linear-gradient(135deg, #ffffff 0%, #edf7ff 100%);
    border: 1px solid #dbeafe;
    border-radius: 24px;
    padding: 26px 30px;
    margin-bottom: 22px;
    box-shadow: 0 14px 35px rgba(15, 23, 42, 0.08);
}

.app-title {
    font-size: 38px;
    font-weight: 900;
    color: #0f172a;
    margin: 0;
    line-height: 1.05;
    letter-spacing: -0.5px;
}

.app-subtitle {
    font-size: 17px;
    color: #475569;
    margin-top: 8px;
    margin-bottom: 0;
}

.app-badge {
    display: inline-block;
    background: #dcfce7;
    color: #166534 !important;
    border: 1px solid #bbf7d0;
    border-radius: 999px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 10px;
}

.subtitulo {
    font-size: 23px;
    font-weight: 850;
    color: #0f172a;
    margin-bottom: 12px;
}

.descricao {
    color: #64748b;
    font-size: 16px;
    margin-bottom: 20px;
}

/* Containers com borda do Streamlit */
div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);
    background: #ffffff;
}

/* Métricas */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

[data-testid="stMetricValue"] {
    font-size: 34px;
    font-weight: 900;
    color: #0f172a;
}

/* Botões */
.stButton > button,
.stDownloadButton > button,
div[data-testid="stLinkButton"] a {
    border-radius: 12px !important;
    font-weight: 700 !important;
    border: 1px solid #cbd5e1 !important;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
}

/* Inputs */
div[data-baseweb="input"],
div[data-baseweb="select"],
div[data-baseweb="textarea"] {
    border-radius: 12px;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}

div[data-testid="stAlert"] {
    border-radius: 14px;
}

.streamlit-expanderHeader {
    border-radius: 12px;
    font-weight: 700;
}

hr {
    margin-top: 1.1rem;
    margin-bottom: 1.2rem;
    border-color: #e2e8f0;
}



/* Ajuste de largura da barra lateral para nomes longos no menu */
section[data-testid="stSidebar"] {
    min-width: 360px !important;
    max-width: 360px !important;
    width: 360px !important;
}

section[data-testid="stSidebar"] > div {
    min-width: 360px !important;
    max-width: 360px !important;
    width: 360px !important;
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    white-space: normal !important;
    overflow-wrap: normal !important;
    word-break: normal !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label {
    padding-top: 4px !important;
    padding-bottom: 4px !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


# ======================================================
# BANCO DE DADOS
# ======================================================
# ======================================================
# CONEXÃO COM BANCO DE DADOS
# - No Render: usa PostgreSQL pela variável DATABASE_URL
# - Localmente: se não houver DATABASE_URL, usa SQLite para testes
# ======================================================
try:
    import psycopg2
except Exception:
    psycopg2 = None

DATABASE_URL = os.getenv("DATABASE_URL")
USAR_POSTGRES = bool(DATABASE_URL)

if psycopg2 is not None:
    INTEGRITY_ERRORS = (sqlite3.IntegrityError, psycopg2.IntegrityError)
else:
    INTEGRITY_ERRORS = (sqlite3.IntegrityError,)


class CursorPostgresCompat:
    """Pequena camada de compatibilidade para reaproveitar o código escrito para SQLite.
    Converte placeholders ? para %s e AUTOINCREMENT para SERIAL.
    """
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("SERIAL PRIMARY KEY", "SERIAL PRIMARY KEY")
        query = query.replace("?", "%s")
        if params is None:
            return self.cursor.execute(query)
        return self.cursor.execute(query, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        return self.cursor.close()


class ConexaoPostgresCompat:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return CursorPostgresCompat(self.conn.cursor())

    def commit(self):
        return self.conn.commit()

    def rollback(self):
        return self.conn.rollback()

    def close(self):
        return self.conn.close()


def conectar():
    if USAR_POSTGRES:
        if psycopg2 is None:
            raise RuntimeError("psycopg2-binary não está instalado. Adicione psycopg2-binary ao requirements.txt")
        return ConexaoPostgresCompat(psycopg2.connect(DATABASE_URL))
    return sqlite3.connect(DB_PATH)


def obter_conexao_pandas(conn):
    """Retorna a conexão real para uso com pandas.
    No PostgreSQL, a conexão do app é envolvida por ConexaoPostgresCompat;
    o pandas precisa receber a conexão psycopg2 original.
    """
    return conn.conn if hasattr(conn, "conn") else conn


def listar_tabelas_banco():
    """Lista tabelas do banco atual com compatibilidade SQLite e PostgreSQL.
    Evita o uso de sqlite_master quando o sistema está no Render/PostgreSQL.
    """
    conn = conectar()
    conn_pandas = obter_conexao_pandas(conn)
    if USAR_POSTGRES:
        query = """
        SELECT table_name AS name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    else:
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    df = pd.read_sql_query(query, conn_pandas)
    conn.close()
    return df["name"].tolist()


def carregar_tabela_dataframe(tabela):
    """Carrega uma tabela em DataFrame com conexão compatível com SQLite/PostgreSQL."""
    conn = conectar()
    conn_pandas = obter_conexao_pandas(conn)
    df = pd.read_sql_query(f'SELECT * FROM {tabela}', conn_pandas)
    conn.close()
    return df


def limpar_cache_dados():
    """Limpa os caches de consulta após qualquer gravação/edição/exclusão.
    Isso evita dados desatualizados depois de cadastrar, editar ou excluir registros.
    """
    try:
        st.cache_data.clear()
    except Exception:
        pass


def coluna_existe(cursor, tabela, coluna):
    if USAR_POSTGRES:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (tabela, coluna),
        )
        return cursor.fetchone() is not None
    cursor.execute(f"PRAGMA table_info({tabela})")
    return coluna in [c[1] for c in cursor.fetchall()]


def adicionar_coluna_se_nao_existe(cursor, tabela, coluna, definicao):
    if not coluna_existe(cursor, tabela, coluna):
        cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estudantes (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            ano_serie TEXT,
            turma TEXT,
            perfil TEXT,
            observacoes TEXT,
            criado_em TEXT
        )
        """
    )
    adicionar_coluna_se_nao_existe(cursor, "estudantes", "turno", "TEXT")
    adicionar_coluna_se_nao_existe(cursor, "estudantes", "dias_atendimento", "TEXT")
    adicionar_coluna_se_nao_existe(cursor, "estudantes", "horario_preferencial", "TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS professores (
            id SERIAL PRIMARY KEY,
            nome_referencia TEXT,
            escola TEXT,
            regional TEXT,
            formacao TEXT,
            carga_horaria TEXT,
            turno_atuacao TEXT,
            observacoes TEXT,
            criado_em TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estudante_professor (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            professor_id INTEGER NOT NULL,
            criado_em TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id),
            FOREIGN KEY(professor_id) REFERENCES professores(id),
            UNIQUE(estudante_id, professor_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS entrevistas_familia (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_registro TEXT,
            rotina TEXT,
            saude TEXT,
            comunicacao TEXT,
            autonomia TEXT,
            socializacao TEXT,
            interesses TEXT,
            observacoes TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    # Campos ampliados da Entrevista com a Família
    # Mantém compatibilidade com bancos antigos e adiciona as novas colunas automaticamente.
    for coluna, definicao in [
        # Controle histórico da entrevista familiar por ano letivo
        ("ano_letivo", "TEXT"),
        ("tipo_registro", "TEXT"),
        ("auxilio_governamental", "TEXT"),
        ("auxilio_quais", "TEXT"),
        ("historico_familiar", "TEXT"),
        ("historico_quais", "TEXT"),
        ("repetiu_ano", "TEXT"),
        ("repetiu_qtd", "TEXT"),
        ("trocou_escola", "TEXT"),
        ("trocou_qtd", "TEXT"),
        ("motivo_troca", "TEXT"),
        ("situacao_escolar", "TEXT"),
        ("interesse_escola", "TEXT"),
        ("organiza_materiais", "TEXT"),
        ("resistencia_escola", "TEXT"),
        ("relacao_colegas", "TEXT"),
        ("relacao_professores", "TEXT"),
        ("leva_alimentacao", "TEXT"),
        ("merenda_escolar", "TEXT"),
        ("alergia_alimentar", "TEXT"),
        ("alergia_quais", "TEXT"),
        ("obs_diversas", "TEXT"),
        ("motivo_escolha", "TEXT"),
        ("outros_motivos", "TEXT"),
        ("conhecimento_aee", "TEXT"),
        ("doenca_preexistente", "TEXT"),
        ("convulsoes", "TEXT"),
        ("acompanhamentos", "TEXT"),
        ("acompanhamento_outro", "TEXT"),
        ("frequencia_acompanhamento", "TEXT"),
        ("frequencia_outro", "TEXT"),
        ("alimentacao_saudavel", "TEXT"),
        ("seletividade_alimentar", "TEXT"),
        ("dieta_sensorial", "TEXT"),
        ("suplemento_alimentar", "TEXT"),
        ("suplemento_qual", "TEXT"),
        ("alimenta_sonda", "TEXT"),
        ("dorme_bem", "TEXT"),
        ("medicacao", "TEXT"),
        ("medicacao_qual", "TEXT"),
        ("tempo_medicacao_tratamentos", "TEXT"),
        ("obs_saude", "TEXT"),
        ("lateralidade", "TEXT"),
        ("estereotipias", "TEXT"),
        ("estereotipias_quais", "TEXT"),
        ("segura_objetos_duas_maos", "TEXT"),
        ("tamanho_objetos", "TEXT"),
        ("pega_lapis", "TEXT"),
        ("engatinhou", "TEXT"),
        ("idade_andou", "TEXT"),
        ("usa_fraldas", "TEXT"),
        ("usa_sonda_alivio", "TEXT"),
        ("autonomia_atividades", "TEXT"),
        ("autonomia_outros", "TEXT"),
        ("atende_comandos", "TEXT"),
        ("gosta_toque", "TEXT"),
        ("obs_psicomotor", "TEXT"),
        ("verbal", "TEXT"),
        ("consegue_comunicar", "TEXT"),
        ("problemas_fala", "TEXT"),
        ("ecolalia", "TEXT"),
        ("da_recado", "TEXT"),
        ("comunicacao_alternativa", "TEXT"),
        ("comunicacao_alternativa_qual", "TEXT"),
        ("relacao_pai", "TEXT"),
        ("relacao_mae", "TEXT"),
        ("relacao_parentes", "TEXT"),
        ("relacao_irmaos", "TEXT"),
        ("relacao_estudantes", "TEXT"),
        ("tem_melhor_amigo", "TEXT"),
        ("tipo_melhor_amigo", "TEXT"),
        ("adapta_ambiente", "TEXT"),
        ("flexivel_rotina", "TEXT"),
        ("respeita_regras", "TEXT"),
        ("chora_facilidade", "TEXT"),
        ("brinca_como", "TEXT"),
        ("interesses_lazer", "TEXT"),
        ("familia_gosta", "TEXT"),
        ("familia_nao_gosta", "TEXT"),
        ("ambiente_estudo_casa", "TEXT"),
        ("habilidades", "TEXT"),
        ("oportunidades_melhoria", "TEXT"),
        ("outras_info_familia", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "entrevistas_familia", coluna, definicao)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_registro TEXT,
            barreiras TEXT,
            potencialidades TEXT,
            comunicacao TEXT,
            interacao TEXT,
            autonomia TEXT,
            aprendizagem TEXT,
            resumo_laudo TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    # Controle histórico por ano letivo e apoio da IA para Avaliação Pedagógica.
    # Mantém compatibilidade com bancos antigos e adiciona as novas colunas automaticamente.
    for coluna, definicao in [
        ("ano_letivo", "TEXT"),
        ("tipo_registro", "TEXT"),
        ("avaliacao_anterior_id", "INTEGER"),
        ("analise_comparativa_ia", "TEXT"),
        ("sugestao_nova_avaliacao_ia", "TEXT"),
        ("origem_documento", "TEXT"),
        ("texto_documento_extra", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "avaliacoes", coluna, definicao)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes_documentos (
            id SERIAL PRIMARY KEY,
            avaliacao_id INTEGER,
            estudante_id INTEGER NOT NULL,
            ano_letivo TEXT,
            tipo_documento TEXT,
            nome_original TEXT,
            nome_arquivo_salvo TEXT,
            caminho_arquivo TEXT,
            observacao TEXT,
            data_upload TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id),
            FOREIGN KEY(avaliacao_id) REFERENCES avaliacoes(id)
        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS escutas_docentes (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_registro TEXT,
            ano_letivo TEXT,
            professor_nome TEXT,
            codigo_docente TEXT,
            componente_curricular TEXT,
            outro_componente TEXT,
            turma TEXT,
            tempo_acompanhamento TEXT,
            participacao_sala TEXT,
            comunicacao TEXT,
            interacao_social TEXT,
            aprendizagem TEXT,
            barreiras_percebidas TEXT,
            potencialidades_observadas TEXT,
            estrategias_funcionam TEXT,
            adaptacoes_utilizadas TEXT,
            recomendacoes_docente TEXT,
            nivel_participacao INTEGER DEFAULT 5,
            nivel_autonomia INTEGER DEFAULT 5,
            nivel_engajamento INTEGER DEFAULT 5,
            observacoes TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    adicionar_coluna_se_nao_existe(cursor, "escutas_docentes", "codigo_docente", "TEXT")

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS relatorios_docente (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_geracao TEXT,
            ano_letivo TEXT,
            componente_destino TEXT,
            professor_destino TEXT,
            titulo TEXT,
            conteudo TEXT,
            fontes_utilizadas TEXT,
            observacoes TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estudos_caso (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_registro TEXT,
            contextualizacao TEXT,
            queixa_principal TEXT,
            potencialidades TEXT,
            dificuldades TEXT,
            estrategias TEXT,
            intervencoes TEXT,
            avaliacao TEXT,
            consideracoes TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    # Campos ampliados do Estudo de Caso / Plano AEE conforme modelo GRE.
    # Não armazenamos CPF, RG, endereço ou laudo médico completo; esses campos ficam em branco nos documentos finais.
    # Armazenamos apenas CID e síntese pedagógica/funcional do laudo, quando pertinente ao AEE.
    for coluna, definicao in [
        ("etapa_modalidade", "TEXT"),
        ("ano_etapa", "TEXT"),
        ("laudo", "TEXT"),
        ("deficiencia", "TEXT"),
        ("cid", "TEXT"),
        ("observacoes_laudo", "TEXT"),
        ("altas_habilidades", "TEXT"),
        ("bpc", "TEXT"),
        ("escola_nome", "TEXT"),
        ("unidade_aee", "TEXT"),
        ("gestor_nome", "TEXT"),
        ("gestor_contato", "TEXT"),
        ("professor_nome", "TEXT"),
        ("professor_contato", "TEXT"),
        ("matricula_professor", "TEXT"),
        ("especialidade_professor", "TEXT"),
        ("periodo_inicio", "TEXT"),
        ("periodo_fim", "TEXT"),
        ("frequencia_atendimento", "TEXT"),
        ("tempo_atendimento_semana", "TEXT"),
        ("formato_atendimento", "TEXT"),
        ("percurso_educacional", "TEXT"),
        ("motivo_encaminhamento_aee", "TEXT"),
        ("precisa_transporte_inclusivo", "TEXT"),
        ("recebe_transporte_inclusivo", "TEXT"),
        ("precisa_profissional_apoio", "TEXT"),
        ("justificativa_apoio", "TEXT"),
        ("acompanhado_profissional_apoio", "TEXT"),
        ("nome_profissional_apoio", "TEXT"),
        ("recursos_tecnologia_assistiva", "TEXT"),
        ("observacoes_ambiente_educacional", "TEXT"),
        ("habilidades_observadas", "TEXT"),
        ("habilidades_a_desenvolver", "TEXT"),
        ("indicadores_altas_habilidades", "TEXT"),
        ("recursos_surdez", "TEXT"),
        ("observacoes_surdez", "TEXT"),
        # Controle histórico por ano letivo e apoio da IA para novo estudo de caso
        ("ano_letivo", "TEXT"),
        ("tipo_registro", "TEXT"),
        ("estudo_anterior_id", "INTEGER"),
        ("analise_comparativa_ia", "TEXT"),
        ("sugestao_novo_estudo_ia", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "estudos_caso", coluna, definicao)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS planos_aee (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_registro TEXT,
            habilidades_prioritarias TEXT,
            recursos_acessibilidade TEXT,
            objetivos_gerais TEXT,
            objetivos_especificos TEXT,
            metodologia TEXT,
            estrategias TEXT,
            prazo TEXT,
            acoes_escola TEXT,
            barreiras_identificadas TEXT,
            parcerias TEXT,
            avaliacao_acompanhamento TEXT,
            observacoes TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    # Campos completos da Parte 2 - Plano de Atendimento Educacional Especializado (modelo GRE).
    # Mantém compatibilidade com bancos antigos, incluindo instalações já publicadas no Render/PostgreSQL.
    for coluna, definicao in [
        ("habilidades_prioritarias", "TEXT"),
        ("recursos_acessibilidade", "TEXT"),
        ("objetivos_gerais", "TEXT"),
        ("objetivos_especificos", "TEXT"),
        ("metodologia", "TEXT"),
        ("estrategias", "TEXT"),
        ("prazo", "TEXT"),
        ("acoes_escola", "TEXT"),
        ("barreiras_identificadas", "TEXT"),
        ("parcerias", "TEXT"),
        ("avaliacao_acompanhamento", "TEXT"),
        ("observacoes", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "planos_aee", coluna, definicao)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS paees (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_geracao TEXT,
            conteudo TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS plano_aee_ia (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_geracao TEXT,
            mes_referencia TEXT,
            ano_referencia TEXT,
            qtd_atendimentos_semana INTEGER DEFAULT 1,
            tipo_geracao TEXT,
            diagnostico_ia TEXT,
            sugestao_geral TEXT,
            objetivos_prioritarios TEXT,
            recursos_sugeridos TEXT,
            estrategias_recomendadas TEXT,
            plano_mensal TEXT,
            sugestoes_semanais TEXT,
            observacoes TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    # Histórico do módulo Plano AEE - IA: sugestão geral, plano mensal e evolução.
    for coluna, definicao in [
        ("mes_referencia", "TEXT"),
        ("ano_referencia", "TEXT"),
        ("qtd_atendimentos_semana", "INTEGER DEFAULT 1"),
        ("tipo_geracao", "TEXT"),
        ("diagnostico_ia", "TEXT"),
        ("sugestao_geral", "TEXT"),
        ("objetivos_prioritarios", "TEXT"),
        ("recursos_sugeridos", "TEXT"),
        ("estrategias_recomendadas", "TEXT"),
        ("plano_mensal", "TEXT"),
        ("sugestoes_semanais", "TEXT"),
        ("observacoes", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "plano_aee_ia", coluna, definicao)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS relatorios (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_geracao TEXT,
            titulo TEXT,
            conteudo TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS atendimentos (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_atendimento TEXT,
            objetivo TEXT,
            atividade TEXT,
            resposta_estudante TEXT,
            avancos TEXT,
            dificuldades TEXT,
            evolucao TEXT,
            qtd_atividades INTEGER DEFAULT 1,
            nivel_resposta INTEGER DEFAULT 5,
            nivel_avanco INTEGER DEFAULT 5,
            nivel_dificuldade INTEGER DEFAULT 5,
            nivel_engajamento INTEGER DEFAULT 5,
            nivel_evolucao REAL DEFAULT 5,
            encaminhamentos TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    for coluna, definicao in [
        ("evolucao", "TEXT"),
        ("qtd_atividades", "INTEGER DEFAULT 1"),
        ("nivel_resposta", "INTEGER DEFAULT 5"),
        ("nivel_avanco", "INTEGER DEFAULT 5"),
        ("nivel_dificuldade", "INTEGER DEFAULT 5"),
        ("nivel_engajamento", "INTEGER DEFAULT 5"),
        ("nivel_evolucao", "REAL DEFAULT 5"),
        ("encaminhamentos", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "atendimentos", coluna, definicao)

    # Recursos pedagógicos vinculados a cada atendimento.
    # Armazena apenas nomes, categorias, links e observações do material usado,
    # sem upload de imagens ou registro visual do estudante.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recursos_atendimento (
            id SERIAL PRIMARY KEY,
            atendimento_id INTEGER NOT NULL,
            estudante_id INTEGER NOT NULL,
            nome_recurso TEXT,
            categoria_recurso TEXT,
            link_recurso TEXT,
            observacao_uso TEXT,
            criado_em TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id),
            FOREIGN KEY(atendimento_id) REFERENCES atendimentos(id)
        )
        """
    )

    for coluna, definicao in [
        ("atendimento_id", "INTEGER"),
        ("estudante_id", "INTEGER"),
        ("nome_recurso", "TEXT"),
        ("categoria_recurso", "TEXT"),
        ("link_recurso", "TEXT"),
        ("observacao_uso", "TEXT"),
        ("criado_em", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "recursos_atendimento", coluna, definicao)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agenda (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER NOT NULL,
            data_agendamento TEXT,
            dia_semana TEXT,
            hora_inicio TEXT,
            hora_fim TEXT,
            tipo_atendimento TEXT,
            observacoes TEXT,
            criado_em TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    # Campos ampliados da Agenda para controle de presença e integração com o Quadro Semanal GRE.
    # Mantém compatibilidade com bancos antigos.
    for coluna, definicao in [
        ("status_presenca", "TEXT DEFAULT 'Agendado'"),
        ("atendimento_id", "INTEGER"),
        ("preenchimento_ia", "TEXT"),
    ]:
        adicionar_coluna_se_nao_existe(cursor, "agenda", coluna, definicao)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documentos_gre_gerados (
            id SERIAL PRIMARY KEY,
            estudante_id INTEGER,
            tipo_documento TEXT,
            nome_arquivo TEXT,
            data_geracao TEXT,
            observacao TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    conn.commit()
    conn.close()
    limpar_cache_dados()


# Cria/atualiza as tabelas apenas uma vez por sessão do Streamlit.
# Isso reduz o tempo de troca entre telas, principalmente usando PostgreSQL.
if "tabelas_criadas" not in st.session_state:
    criar_tabelas()
    st.session_state.tabelas_criadas = True


# ======================================================
# FUNÇÕES UTILITÁRIAS
# ======================================================
PERFIS = [
    "Não informado",
    "Deficiência intelectual",
    "Deficiência visual",
    "Deficiência auditiva/surdez",
    "Deficiência física",
    "TEA",
    "TEA - Nível I",
    "TEA - Nível II",
    "TEA - Nível III",
    "Altas habilidades/superdotação",
    "Deficiência múltipla",
    "Outro",
]

DIAS_SEMANA = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
]

MAPA_MESES = {
    "Janeiro": 1,
    "Fevereiro": 2,
    "Março": 3,
    "Abril": 4,
    "Maio": 5,
    "Junho": 6,
    "Julho": 7,
    "Agosto": 8,
    "Setembro": 9,
    "Outubro": 10,
    "Novembro": 11,
    "Dezembro": 12,
}

MAPA_DIAS_SEMANA = {
    "Segunda-feira": 0,
    "Terça-feira": 1,
    "Quarta-feira": 2,
    "Quinta-feira": 3,
    "Sexta-feira": 4,
}

def gerar_datas_atendimentos_mes(ano, mes_nome, dias_atendimento):
    """Calcula automaticamente as datas reais de atendimento do mês.

    Usa o mês, ano e os dias de atendimento cadastrados/selecionados para gerar
    a quantidade correta de encontros. Ex.: segunda e sexta em um mês podem gerar
    8, 9 ou 10 atendimentos, conforme o calendário.
    """
    try:
        ano_int = int(ano)
    except Exception:
        ano_int = agora_local().year

    mes_num = MAPA_MESES.get(str(mes_nome), agora_local().month)
    dias_codigo = [MAPA_DIAS_SEMANA[d] for d in dias_atendimento if d in MAPA_DIAS_SEMANA]

    if not dias_codigo:
        return []

    total_dias = calendar.monthrange(ano_int, mes_num)[1]
    datas = []
    for dia in range(1, total_dias + 1):
        data_atual = date(ano_int, mes_num, dia)
        if data_atual.weekday() in dias_codigo:
            datas.append(data_atual)
    return datas

def datas_atendimentos_para_texto(datas):
    if not datas:
        return "Nenhuma data calculada. Verifique mês, ano e dias de atendimento."
    linhas = []
    for idx, data_atual in enumerate(datas, start=1):
        nome_dia = DIAS_SEMANA[data_atual.weekday()] if data_atual.weekday() < len(DIAS_SEMANA) else "Dia"
        linhas.append(f"Atendimento {idx}: {data_atual.strftime('%d/%m/%Y')} ({nome_dia})")
    return "\n".join(linhas)


CAMPOS_ENTREVISTA_FAMILIA = [
    "data_registro",
    "ano_letivo", "tipo_registro",
    "auxilio_governamental", "auxilio_quais", "historico_familiar", "historico_quais",
    "repetiu_ano", "repetiu_qtd", "trocou_escola", "trocou_qtd", "motivo_troca",
    "situacao_escolar", "interesse_escola", "organiza_materiais", "resistencia_escola",
    "relacao_colegas", "relacao_professores", "leva_alimentacao", "merenda_escolar",
    "alergia_alimentar", "alergia_quais", "obs_diversas",
    "motivo_escolha", "outros_motivos", "conhecimento_aee",
    "doenca_preexistente", "convulsoes", "acompanhamentos", "acompanhamento_outro",
    "frequencia_acompanhamento", "frequencia_outro", "alimentacao_saudavel",
    "seletividade_alimentar", "dieta_sensorial", "suplemento_alimentar", "suplemento_qual",
    "alimenta_sonda", "dorme_bem", "medicacao", "medicacao_qual",
    "tempo_medicacao_tratamentos", "obs_saude",
    "lateralidade", "estereotipias", "estereotipias_quais", "segura_objetos_duas_maos",
    "tamanho_objetos", "pega_lapis", "engatinhou", "idade_andou",
    "usa_fraldas", "usa_sonda_alivio", "autonomia_atividades", "autonomia_outros",
    "atende_comandos", "gosta_toque", "obs_psicomotor",
    "verbal", "consegue_comunicar", "problemas_fala", "ecolalia", "da_recado",
    "comunicacao_alternativa", "comunicacao_alternativa_qual",
    "relacao_pai", "relacao_mae", "relacao_parentes", "relacao_irmaos", "relacao_estudantes",
    "tem_melhor_amigo", "tipo_melhor_amigo", "adapta_ambiente", "flexivel_rotina",
    "respeita_regras", "chora_facilidade", "brinca_como", "interesses_lazer",
    "familia_gosta", "familia_nao_gosta", "ambiente_estudo_casa",
    "habilidades", "oportunidades_melhoria", "outras_info_familia",
]

OPCOES_TIPO_ENTREVISTA_FAMILIA = [
    "Registro histórico",
    "Entrevista familiar atual",
]

CAMPOS_AVALIACAO = [
    "data_registro",
    "ano_letivo",
    "tipo_registro",
    "avaliacao_anterior_id",
    "analise_comparativa_ia",
    "sugestao_nova_avaliacao_ia",
    "origem_documento",
    "texto_documento_extra",
    "barreiras",
    "potencialidades",
    "comunicacao",
    "interacao",
    "autonomia",
    "aprendizagem",
    "resumo_laudo",
]

OPCOES_TIPO_AVALIACAO = [
    "Registro histórico",
    "Avaliação pedagógica atual",
    "Nova avaliação com base em avaliação anterior",
    "Avaliação Pedagógica - Extra / Documento Livre",
]


OPCOES_AREAS_CONHECIMENTO = [
    "Matemática",
    "Português",
    "História",
    "Geografia",
    "Ciências",
    "Biologia",
    "Física",
    "Química",
    "Artes",
    "Educação Física",
    "Inglês",
    "Espanhol",
    "Filosofia",
    "Sociologia",
    "Tecnologia / Computação",
    "Projeto de Vida",
    "Sala de Leitura",
    "Outras",
]

OPCOES_ESTRATEGIAS_INCLUSIVAS = [
    "Apoio visual",
    "Rotina estruturada",
    "Instruções curtas e objetivas",
    "Tempo ampliado",
    "Atividades concretas/manipuláveis",
    "Mediação gradual",
    "Atividades em dupla ou pequenos grupos",
    "Comunicação alternativa/aumentativa",
    "Tecnologia assistiva",
    "Gamificação",
    "Recursos sensoriais",
    "Recursos de impressão 3D / maker",
    "Leitura compartilhada",
    "Avaliação oral ou por demonstração prática",
    "Redução de cópia extensa",
    "Outro",
]

CAMPOS_ESCUTA_DOCENTE = [
    "data_registro",
    "ano_letivo",
    "codigo_docente",
    "componente_curricular",
    "outro_componente",
    "turma",
    "tempo_acompanhamento",
    "participacao_sala",
    "comunicacao",
    "interacao_social",
    "aprendizagem",
    "barreiras_percebidas",
    "potencialidades_observadas",
    "estrategias_funcionam",
    "adaptacoes_utilizadas",
    "recomendacoes_docente",
    "nivel_participacao",
    "nivel_autonomia",
    "nivel_engajamento",
    "observacoes",
]

CAMPOS_RELATORIO_DOCENTE = [
    "data_geracao",
    "ano_letivo",
    "componente_destino",
    "professor_destino",
    "titulo",
    "conteudo",
    "fontes_utilizadas",
    "observacoes",
]

CAMPOS_ESTUDO_CASO = [
    "data_registro",
    "ano_letivo", "tipo_registro", "estudo_anterior_id", "analise_comparativa_ia", "sugestao_novo_estudo_ia",
    "contextualizacao", "queixa_principal", "potencialidades", "dificuldades", "estrategias", "intervencoes", "avaliacao", "consideracoes",
    "etapa_modalidade", "ano_etapa", "laudo", "deficiencia", "cid", "observacoes_laudo", "altas_habilidades", "bpc",
    "escola_nome", "unidade_aee", "gestor_nome", "gestor_contato",
    "professor_nome", "professor_contato", "matricula_professor", "especialidade_professor",
    "periodo_inicio", "periodo_fim", "frequencia_atendimento", "tempo_atendimento_semana", "formato_atendimento",
    "percurso_educacional", "motivo_encaminhamento_aee", "precisa_transporte_inclusivo", "recebe_transporte_inclusivo",
    "precisa_profissional_apoio", "justificativa_apoio", "acompanhado_profissional_apoio", "nome_profissional_apoio",
    "recursos_tecnologia_assistiva", "observacoes_ambiente_educacional",
    "habilidades_observadas", "habilidades_a_desenvolver", "indicadores_altas_habilidades",
    "recursos_surdez", "observacoes_surdez",
]

CAMPOS_PLANO_AEE = [
    "data_registro",
    "habilidades_prioritarias",
    "recursos_acessibilidade",
    "objetivos_gerais",
    "objetivos_especificos",
    "metodologia",
    "estrategias",
    "prazo",
    "acoes_escola",
    "barreiras_identificadas",
    "parcerias",
    "avaliacao_acompanhamento",
    "observacoes",
]

CAMPOS_PLANO_AEE_IA = [
    "data_geracao",
    "mes_referencia",
    "ano_referencia",
    "qtd_atendimentos_semana",
    "tipo_geracao",
    "diagnostico_ia",
    "sugestao_geral",
    "objetivos_prioritarios",
    "recursos_sugeridos",
    "estrategias_recomendadas",
    "plano_mensal",
    "sugestoes_semanais",
    "observacoes",
]

MESES_REFERENCIA = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


OPCOES_ANO_ETAPA = [
    # Ensino Fundamental
    "1º ano do EF", "2º ano do EF", "3º ano do EF", "4º ano do EF", "5º ano do EF",
    "6º ano do EF", "7º ano do EF", "8º ano do EF", "9º ano do EF",
    # Ensino Médio
    "1º ano do EM", "2º ano do EM", "3º ano do EM",
    # EJA - Ensino Fundamental
    "EJA Ensino Fundamental - Módulo 5", "EJA Ensino Fundamental - Módulo 6",
    "EJA Ensino Fundamental - Módulo 7", "EJA Ensino Fundamental - Módulo 8",
    # EJA - Ensino Médio
    "EJA Ensino Médio - Módulo 1", "EJA Ensino Médio - Módulo 2", "EJA Ensino Médio - Módulo 3",
    "Outro / não informado",
]

OPCOES_ESPECIALIDADE_AEE = [
    "Professor(a) do AEE",
    "Professor(a) Brailista",
    "Professor(a) Instrutor(a) de LIBRAS",
    "Professor(a) Intérprete de LIBRAS",
]

OPCOES_FORMATO_ATENDIMENTO = [
    "Individual",
    "Coletivo",
    "Em sala de aula",
    "Domiciliar",
    "Hospitalar",
    "Outro",
]

OPCOES_HABILIDADES_PEDAGOGICAS = [
    "Inteligência Interpessoal (interesse pelo sentimento do outro)",
    "Interesse e habilidade em atividades sensoriais (tátil, auditivo ou outros sentidos)",
    "Raciocínio lógico-matemático (interesse por cálculos e números)",
    "Realiza as quatro operações",
    "Resolve situações-problema com autonomia e de maneira diversificada",
    "Interesse em temas científicos",
    "Compreende explicações e cumpre comandos",
    "Demonstra criatividade",
    "Acompanha as atividades propostas do grupo/classe",
    "Usa recursos tecnológicos com autonomia (tablet, celular, computador)",
    "Fluência na leitura",
    "Escreve textos com autonomia",
    "Apropriação do sistema de escrita alfabética adequada à idade",
    "Habilidades artísticas",
    "Comunica seus desejos e necessidades",
    "Apresenta atenção compartilhada",
    "Interesse por leitura",
    "Domina Libras",
    "Domina Braille",
    "Possui identidade surda",
    "Usa comunicação aumentativa e alternativa com autonomia",
    "Outro",
]

OPCOES_HABILIDADES_A_DESENVOLVER = [
    "Inteligência Interpessoal",
    "Atividades sensoriais",
    "Raciocínio lógico-matemático",
    "Resolução de situações-problema com autonomia",
    "Compreensão de explicações e comandos",
    "Criatividade",
    "Utilização de recursos tecnológicos com autonomia",
    "Fluência na leitura",
    "Escrita de textos com autonomia",
    "Apropriação do sistema de escrita alfabética",
    "Expressão de seus desejos e necessidades",
    "Atenção compartilhada",
    "Interesse por leitura",
    "Domínio de Libras",
    "Domínio de Braille",
    "Utilização da comunicação aumentativa e alternativa com autonomia",
    "Outro",
]

OPCOES_INDICADORES_AHSD = [
    "Aprende fácil e rapidamente",
    "Original, imaginativa, criativa, não convencional",
    "Pensa de forma incomum para resolver problemas",
    "Persistente, independente, autodirecionada",
    "Persuasiva, capaz de influenciar os outros",
    "Inquisitiva, cética, curiosa",
    "Adapta-se a uma variedade de situações e novos ambientes",
    "Criativa ao construir com materiais incomuns",
    "Habilidade nas artes (música, desenho, dança etc.)",
    "Entende a importância da natureza (tempo, lua, sol, estrelas, solo etc.)",
    "Vocabulário excepcional, verbalmente fluente",
    "Aprende facilmente novas línguas",
    "Trabalha independente, mostra iniciativa",
    "Bom julgamento, lógica",
    "Usa recursos tecnológicos com autonomia",
    "Versátil, muitos interesses, interesse além da idade cronológica",
    "Mostra insights e percepções incomuns",
    "Demonstra alto nível de sensibilidade e empatia com relação aos outros",
    "Apresenta excelente senso de humor",
    "Expressa ideias e reações, frequentemente de forma argumentativa",
    "Outro",
]

OPCOES_RECURSOS_TA = [
    "Recursos de comunicação alternativa/aumentativa",
    "Pranchas de CAA",
    "Tablet/celular/computador com recurso acessível",
    "Chromebook",
    "Materiais concretos/manipuláveis",
    "Recursos táteis/sensoriais",
    "Jogos pedagógicos acessíveis",
    "Wordwall",
    "Impressão 3D/recurso maker inclusivo",
    "Robótica educacional",
    "Recursos em Libras",
    "Recursos em Braille",
    "Leitor de tela/ampliação",
    "Órteses/adaptações de acesso",
    "Outro",
]

OPCOES_RECURSOS_SURDEZ = [
    "Aparelho auditivo",
    "Implante coclear",
    "Libras",
    "Leitura labial",
    "Intérprete de Libras",
    "Não se aplica",
]

OPCOES_HABILIDADES_PRIORITARIAS_SRM = [
    "Desenvolvimento de vida autônoma",
    "Enriquecimento curricular (para aluno com altas habilidades e superdotação)",
    "Ensino da informática acessível",
    "Ensino da Língua Brasileira de Sinais",
    "Ensino da Língua Portuguesa como segunda língua",
    "Ensino das técnicas de cálculo no soroban",
    "Ensino do sistema Braille",
    "Ensino de técnicas de orientação e mobilidade",
    "Ensino do uso da comunicação aumentativa e alternativa",
    "Ensino do uso de recursos ópticos e não ópticos",
]

OPCOES_RECURSOS_ACESSIBILIDADE = [
    "Recurso de auxílio à escrita",
    "Colmeia para teclado",
    "Teclado expandido",
    "Suporte de punho ajustável",
    "Mouses especiais",
    "Acionadores",
    "Leitor automático",
    "Ampliador de texto",
    "Réguas braille",
    "Multiplano",
    "Reglete",
    "Máquina braille",
    "Pranchas de CAA",
    "Texto apoiado",
    "Textos e livros em Braille",
    "Audiodescrição",
    "Descrição de imagens",
    "Hand Talk",
    "Wordwall",
    "Gemini",
    "Copilot",
    "Tablet",
    "Chromebook",
    "Impressão 3D",
    "Robótica educacional",
    "Outros",
]

OPCOES_ACOES_ESCOLA = [
    "Implemento de tecnologia assistiva para uso do(a) estudante",
    "Formação continuada de professores, profissionais de apoio, equipe gestora, demais funcionários da escola e famílias com a temática da educação inclusiva",
    "Parcerias com profissionais de saúde, UBS, USF, Conselho Tutelar, CREAS e CRAS",
    "Articulação sobre o PDDE Equidade",
    "Articulação de horários para o diálogo entre professor do AEE, professor da sala comum e profissional de apoio",
    "Solicitação de transporte escolar inclusivo",
    "Outros",
]

OPCOES_BARREIRAS = [
    "Barreiras atitudinais",
    "Barreiras arquitetônicas",
    "Barreiras comunicacionais",
    "Barreiras curriculares",
    "Outros",
]

def hoje_str():
    """Data/hora local para salvar histórico e documentos."""
    return agora_local().strftime("%d/%m/%Y %H:%M")


def normalizar_data_historico(data_texto):
    """Mantém o texto salvo. Registros antigos em UTC não são alterados automaticamente.
    Novos registros usam hoje_str() em America/Recife.
    """
    return data_texto or "Data não informada"


def formatar_data(data_obj):
    if isinstance(data_obj, (datetime, date)):
        return data_obj.strftime("%d/%m/%Y")
    return str(data_obj)


def data_para_date(data_texto):
    try:
        return datetime.strptime(data_texto, "%d/%m/%Y").date()
    except Exception:
        return agora_local().date()


def hora_para_time(hora_texto, padrao="08:00"):
    try:
        return datetime.strptime(str(hora_texto)[:5], "%H:%M").time()
    except Exception:
        return datetime.strptime(padrao, "%H:%M").time()


def limitar_escala(valor, padrao=5):
    try:
        valor = int(valor)
    except Exception:
        valor = padrao
    return max(1, min(10, valor))


def calcular_indice_geral(nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento):
    resposta = limitar_escala(nivel_resposta)
    avanco = limitar_escala(nivel_avanco)
    dificuldade = limitar_escala(nivel_dificuldade)
    engajamento = limitar_escala(nivel_engajamento)
    barreira_invertida = 11 - dificuldade
    indice = (resposta * 0.30) + (avanco * 0.35) + (engajamento * 0.20) + (barreira_invertida * 0.15)
    return round(max(1, min(10, indice)), 1)


def interpretar_indice(indice):
    if indice <= 3:
        return "Baixa evolução / necessidade de maior apoio"
    if indice <= 6:
        return "Evolução parcial / acompanhamento em desenvolvimento"
    if indice <= 8:
        return "Boa evolução / resposta positiva"
    return "Evolução elevada / maior autonomia e participação"


def opcoes_estudantes_por_id(estudantes):
    ids = [e[0] for e in estudantes]
    mapa = {e[0]: f"{e[1]} - {e[2] or 'Ano/Série não informado'} - {e[4] or 'Perfil não informado'}" for e in estudantes}
    return ids, mapa


def render_app_header():
    st.markdown(
        f"""
        <div class="app-hero">
            <span class="app-badge">AEE • Memória Pedagógica • Articulação Docente • IA • {APP_VERSION} {APP_VERSION_LABEL}</span>
            <h1 class="app-title">INCLUISRM</h1>
            <p class="app-subtitle">Sistema Inteligente de Articulação Pedagógica Inclusiva</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def gerar_docx_documento(conteudo, nome_base, tipo="documento"):
    """Gera documento Word editável com os mesmos textos do PDF.
    Observação: dados sensíveis permanecem como linhas em branco para preenchimento manual.
    """
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    nome_arquivo = f"{tipo}_{nome_base}.docx".replace("/", "-").replace("\\", "-")
    doc = Document()

    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run("INCLUISRM\nSistema Inteligente de Articulação Pedagógica Inclusiva")
    run.bold = True
    run.font.size = Pt(12)

    doc.add_paragraph("")

    for linha in conteudo.split("\n"):
        linha = linha.rstrip()
        if not linha:
            doc.add_paragraph("")
            continue

        par = doc.add_paragraph()
        texto_limpo = linha.strip()
        run = par.add_run(texto_limpo)

        if texto_limpo.isupper() or (len(texto_limpo) > 2 and texto_limpo[:2].isdigit() and "." in texto_limpo[:4]):
            run.bold = True
        run.font.size = Pt(11)

    doc.add_paragraph("")
    rodape = doc.add_paragraph(f"Gerado em {agora_local().strftime('%d/%m/%Y %H:%M')} pelo INCLUISRM.")
    rodape.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in rodape.runs:
        r.font.size = Pt(9)

    doc.save(nome_arquivo)
    return nome_arquivo



# ======================================================
# RELATÓRIOS VISUAIS - PADRÃO INCLUISRM
# ======================================================
# Regra pedagógica adotada:
# - Evitar "diagnóstico" em títulos e seções pedagógicas do AEE.
# - Usar "diagnóstico" apenas quando a informação vier de laudo/documento clínico.
# - Aplicar identidade visual própria por tipo de relatório.

CORES_RELATORIOS = {
    "perfil_pedagogico": {
        "titulo": "PERFIL PEDAGÓGICO DO ESTUDANTE - AEE",
        "subtitulo": "Relatório pedagógico de apoio ao Atendimento Educacional Especializado",
        "icone": "🧩",
        "cor_principal": "0F172A",
        "cor_titulo": "1D4ED8",
        "cor_secundaria": "DBEAFE",
        "cor_clara": "F8FAFC",
    },
    "plano_mensal": {
        "titulo": "PLANO MENSAL AEE - IA",
        "subtitulo": "Relatório visual de planejamento pedagógico",
        "icone": "📅",
        "cor_principal": "166534",
        "cor_titulo": "15803D",
        "cor_secundaria": "DCFCE7",
        "cor_clara": "F7FEE7",
    },
    "plano_aee": {
        "titulo": "PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO - AEE",
        "subtitulo": "Documento pedagógico para organização dos atendimentos",
        "icone": "📝",
        "cor_principal": "075985",
        "cor_titulo": "0369A1",
        "cor_secundaria": "E0F2FE",
        "cor_clara": "F0F9FF",
    },
    "avaliacao_pedagogica": {
        "titulo": "AVALIAÇÃO PEDAGÓGICA DO AEE",
        "subtitulo": "Registro educacional de observação, barreiras, potencialidades e aprendizagem",
        "icone": "📋",
        "cor_principal": "0E7490",
        "cor_titulo": "0891B2",
        "cor_secundaria": "CFFAFE",
        "cor_clara": "ECFEFF",
    },
    "estudo_pedagogico": {
        "titulo": "ESTUDO PEDAGÓGICO DO ESTUDANTE - AEE",
        "subtitulo": "Síntese pedagógica para planejamento, acompanhamento e articulação escolar",
        "icone": "📘",
        "cor_principal": "581C87",
        "cor_titulo": "7E22CE",
        "cor_secundaria": "F3E8FF",
        "cor_clara": "FAF5FF",
    },
    "relatorio_docente": {
        "titulo": "RELATÓRIO DE ARTICULAÇÃO DOCENTE",
        "subtitulo": "Orientações pedagógicas para diálogo entre AEE e sala comum",
        "icone": "👩‍🏫",
        "cor_principal": "7C2D12",
        "cor_titulo": "C2410C",
        "cor_secundaria": "FFEDD5",
        "cor_clara": "FFF7ED",
    },
    "escuta_docente": {
        "titulo": "ESCUTA DOCENTE - AEE",
        "subtitulo": "Registro pedagógico de observações do professor da sala comum",
        "icone": "🗣️",
        "cor_principal": "4338CA",
        "cor_titulo": "4F46E5",
        "cor_secundaria": "E0E7FF",
        "cor_clara": "EEF2FF",
    },
    "entrevista_familiar": {
        "titulo": "ENTREVISTA COM A FAMÍLIA - AEE",
        "subtitulo": "Registro de informações familiares relevantes ao planejamento pedagógico",
        "icone": "🏠",
        "cor_principal": "BE123C",
        "cor_titulo": "E11D48",
        "cor_secundaria": "FFE4E6",
        "cor_clara": "FFF1F2",
    },
    "atendimento": {
        "titulo": "REGISTRO DE ATENDIMENTO AEE",
        "subtitulo": "Acompanhamento pedagógico das atividades realizadas na Sala de Recursos",
        "icone": "✅",
        "cor_principal": "854D0E",
        "cor_titulo": "CA8A04",
        "cor_secundaria": "FEF3C7",
        "cor_clara": "FEFCE8",
    },
    "evolucao": {
        "titulo": "RELATÓRIO DE EVOLUÇÃO PEDAGÓGICA - AEE",
        "subtitulo": "Análise educacional do acompanhamento e das respostas às mediações",
        "icone": "📈",
        "cor_principal": "115E59",
        "cor_titulo": "0F766E",
        "cor_secundaria": "CCFBF1",
        "cor_clara": "F0FDFA",
    },
    "cadastro": {
        "titulo": "FICHA DE IDENTIFICAÇÃO EDUCACIONAL",
        "subtitulo": "Cadastro pedagógico e informações escolares do estudante",
        "icone": "🗂️",
        "cor_principal": "334155",
        "cor_titulo": "475569",
        "cor_secundaria": "E2E8F0",
        "cor_clara": "F8FAFC",
    },
    "professor": {
        "titulo": "FICHA DO PROFESSOR AEE",
        "subtitulo": "Registro profissional para articulação pedagógica inclusiva",
        "icone": "👤",
        "cor_principal": "374151",
        "cor_titulo": "4B5563",
        "cor_secundaria": "E5E7EB",
        "cor_clara": "F9FAFB",
    },
    "documento": {
        "titulo": "RELATÓRIO PEDAGÓGICO AEE",
        "subtitulo": "Documento pedagógico de apoio ao Atendimento Educacional Especializado",
        "icone": "📄",
        "cor_principal": "0F172A",
        "cor_titulo": "1D4ED8",
        "cor_secundaria": "E2E8F0",
        "cor_clara": "F8FAFC",
    },
}

MAPA_TIPOS_VISUAIS = {
    "plano_ia_visual": "plano_mensal",
    "plano": "plano_aee",
    "avaliacao": "avaliacao_pedagogica",
    "estudo": "estudo_pedagogico",
    "estudo_ia_previa": "estudo_pedagogico",
    "relatorio": "evolucao",
    "atendimento": "atendimento",
    "escuta_docente": "escuta_docente",
    "entrevista": "entrevista_familiar",
    "cadastro": "cadastro",
    "professor": "professor",
    "relatorio_docente": "relatorio_docente",
    "relatorio_docente_salvo": "relatorio_docente",
    "perfil_pedagogico": "perfil_pedagogico",
    "documento": "documento",
}


def obter_tema_relatorio(tipo_relatorio="documento", titulo_doc=None, subtitulo_doc=None):
    chave = MAPA_TIPOS_VISUAIS.get(tipo_relatorio, tipo_relatorio)
    tema = CORES_RELATORIOS.get(chave, CORES_RELATORIOS["documento"]).copy()
    if titulo_doc:
        tema["titulo"] = titulo_doc
    if subtitulo_doc:
        tema["subtitulo"] = subtitulo_doc
    return tema


def limpar_marcadores_relatorio(texto):
    """Remove marcações simples de Markdown usadas pela IA para melhorar Word/PDF."""
    texto = str(texto or "")
    texto = texto.replace("**", "")
    texto = re.sub(r"^#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = texto.replace("---", "")
    # Ajuste terminológico global para títulos pedagógicos
    texto = texto.replace("PERFIL PEDAGÓGICO DO ESTUDANTE - AEE", "PERFIL PEDAGÓGICO DO ESTUDANTE - AEE")
    texto = texto.replace("DIAGNÓSTICO PEDAGÓGICO INICIAL", "PERFIL PEDAGÓGICO INICIAL")
    texto = texto.replace("Perfil Pedagógico AEE", "Perfil Pedagógico do Estudante - AEE")
    texto = texto.replace("perfil pedagógico", "perfil pedagógico")
    texto = texto.replace("Esse diagnóstico visa", "Este perfil pedagógico tem como objetivo")
    texto = texto.replace("Este diagnóstico visa", "Este perfil pedagógico tem como objetivo")
    return texto.strip()


def eh_titulo_relatorio(linha):
    linha = linha.strip()
    if not linha:
        return False
    if linha.upper() == linha and len(linha) > 8:
        return True
    if re.match(r"^(\d+\.|SEMANA\s+\d+|ATENDIMENTO\s+\d+|Semana\s+\d+|Atendimento\s+\d+)", linha, flags=re.I):
        return True
    palavras_chave = [
        "Identificação", "Objetivo", "Habilidades", "Recursos", "Estratégias", "Avaliação",
        "Indicadores", "Ajustes", "Registro", "Organização", "Perfil", "Mapeamento", "Sugestão",
        "Síntese", "Potencialidades", "Barreiras", "Necessidades", "Cuidados", "Observação",
    ]
    return any(linha.lower().startswith(k.lower()) for k in palavras_chave)


def extrair_linhas_chave_valor(texto):
    pares = []
    for raw in str(texto or "").splitlines():
        linha = limpar_marcadores_relatorio(raw).strip(" -•\t")
        if ":" in linha and len(linha) < 150:
            chave, valor = linha.split(":", 1)
            if chave and valor and len(chave) <= 52:
                pares.append((chave.strip(), valor.strip()))
    return pares


def gerar_docx_relatorio_visual(conteudo, nome_base, tipo_relatorio="documento", titulo_doc=None, subtitulo_doc=None):
    """Gera Word com layout visual padronizado e identidade por tipo de relatório."""
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tema = obter_tema_relatorio(tipo_relatorio, titulo_doc, subtitulo_doc)

    def set_cell_bg(cell, fill):
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd')
        shd.set(qn('w:fill'), fill)
        tc_pr.append(shd)

    def set_cell_text(cell, text, bold=False, color="111827", size=9):
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(str(text or ""))
        r.bold = bold
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor.from_string(color)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    nome_arquivo = f"relatorio_visual_{nome_base}.docx".replace("/", "-").replace("\\", "-")
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.45)
    sec.bottom_margin = Inches(0.45)
    sec.left_margin = Inches(0.55)
    sec.right_margin = Inches(0.55)

    header = doc.add_table(rows=1, cols=2)
    header.alignment = WD_TABLE_ALIGNMENT.CENTER
    header.autofit = True
    set_cell_bg(header.cell(0, 0), tema["cor_principal"])
    set_cell_bg(header.cell(0, 1), tema["cor_secundaria"])
    set_cell_text(header.cell(0, 0), "INCLUISRM\nSistema Inteligente de Articulação Pedagógica Inclusiva", True, "FFFFFF", 11)
    set_cell_text(header.cell(0, 1), f"{tema['icone']} {tema['titulo']}\n{tema['subtitulo']}", True, tema["cor_principal"], 12)

    doc.add_paragraph("")

    pares = extrair_linhas_chave_valor(conteudo)[:8]
    if pares:
        doc.add_heading("Identificação segura", level=2)
        t = doc.add_table(rows=0, cols=2)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for chave, valor in pares:
            row = t.add_row().cells
            set_cell_bg(row[0], tema["cor_secundaria"])
            set_cell_bg(row[1], tema["cor_clara"])
            set_cell_text(row[0], chave, True, tema["cor_principal"], 9)
            set_cell_text(row[1], valor, False, "111827", 9)

    doc.add_paragraph("")
    doc.add_heading("Conteúdo pedagógico", level=2)

    texto = limpar_marcadores_relatorio(conteudo)
    for raw in texto.splitlines():
        linha = raw.strip()
        if not linha or linha == "---":
            continue
        if eh_titulo_relatorio(linha):
            p = doc.add_paragraph()
            r = p.add_run(linha)
            r.bold = True
            r.font.size = Pt(12)
            r.font.color.rgb = RGBColor.from_string(tema["cor_titulo"])
            continue
        if linha.startswith("-") or linha.startswith("•"):
            p = doc.add_paragraph(style=None)
            p.paragraph_format.left_indent = Inches(0.18)
            r = p.add_run("• " + linha.lstrip("-• "))
            r.font.size = Pt(10)
            continue
        p = doc.add_paragraph()
        r = p.add_run(linha)
        r.font.size = Pt(10)

    doc.add_paragraph("")
    foot = doc.add_table(rows=1, cols=1)
    set_cell_bg(foot.cell(0, 0), "F1F5F9")
    set_cell_text(
        foot.cell(0, 0),
        f"Documento gerado em {agora_local().strftime('%d/%m/%Y %H:%M')} pelo INCLUISRM • LabTec3DI/UFRPE • Uso pedagógico no AEE",
        False,
        "475569",
        8,
    )

    doc.save(nome_arquivo)
    return nome_arquivo


def gerar_docx_plano_aee_ia_visual(conteudo, nome_base, titulo_doc="PLANO MENSAL AEE - IA"):
    """Compatibilidade: mantém a chamada antiga do Plano Mensal."""
    return gerar_docx_relatorio_visual(conteudo, nome_base, tipo_relatorio="plano_mensal", titulo_doc=titulo_doc)


def gerar_pdf_relatorio_visual(conteudo, nome_base, tipo_relatorio="documento", titulo_doc=None, subtitulo_doc=None):
    """Gera PDF com layout profissional, cards e identidade visual por relatório."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    tema = obter_tema_relatorio(tipo_relatorio, titulo_doc, subtitulo_doc)
    nome_arquivo = f"relatorio_visual_{nome_base}.pdf".replace("/", "-").replace("\\", "-")
    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=A4,
        rightMargin=1.35 * cm,
        leftMargin=1.35 * cm,
        topMargin=1.15 * cm,
        bottomMargin=1.15 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleVisualINCLUISRM",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#" + tema["cor_principal"]),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleVisualINCLUISRM",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    sec_style = ParagraphStyle(
        "SecVisualINCLUISRM",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#" + tema["cor_titulo"]),
        spaceBefore=8,
        spaceAfter=5,
    )
    normal_style = ParagraphStyle(
        "NormalVisualINCLUISRM",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4,
    )
    bullet_style = ParagraphStyle("BulletVisualINCLUISRM", parent=normal_style, leftIndent=12, firstLineIndent=-8)
    small_style = ParagraphStyle(
        "SmallVisualINCLUISRM",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        textColor=colors.HexColor("#64748b"),
    )

    elementos = []
    capa = Table(
        [[
            Paragraph("<b>INCLUISRM</b><br/>Sistema Inteligente de Articulação Pedagógica Inclusiva", normal_style),
            Paragraph(f"<b>{escape(tema['icone'] + ' ' + tema['titulo'])}</b><br/>{escape(tema['subtitulo'])}", normal_style),
        ]],
        colWidths=[7.3 * cm, 10.2 * cm],
    )
    capa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#" + tema["cor_principal"])),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#" + tema["cor_secundaria"])),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elementos.append(capa)
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(escape(tema["titulo"]), title_style))
    elementos.append(Paragraph(escape(tema["subtitulo"]), subtitle_style))

    pares = extrair_linhas_chave_valor(conteudo)[:8]
    if pares:
        dados = [[Paragraph("<b>Campo</b>", normal_style), Paragraph("<b>Informação</b>", normal_style)]]
        for chave, valor in pares:
            dados.append([Paragraph(escape(chave), normal_style), Paragraph(escape(valor), normal_style)])
        tabela = Table(dados, colWidths=[5.2 * cm, 12.3 * cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#" + tema["cor_principal"])),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#" + tema["cor_secundaria"])),
            ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#" + tema["cor_clara"])),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 10))

    texto = limpar_marcadores_relatorio(conteudo)
    for raw in texto.splitlines():
        linha = raw.strip()
        if not linha:
            continue
        if eh_titulo_relatorio(linha):
            elementos.append(Spacer(1, 4))
            elementos.append(Paragraph(escape(linha), sec_style))
        elif linha.startswith("-") or linha.startswith("•"):
            elementos.append(Paragraph("• " + escape(linha.lstrip("-• ")), bullet_style))
        else:
            elementos.append(Paragraph(escape(linha), normal_style))

    elementos.append(Spacer(1, 14))
    rodape = Table(
        [[Paragraph(
            f"Gerado em {agora_local().strftime('%d/%m/%Y %H:%M')} pelo INCLUISRM • LabTec3DI/UFRPE • Documento pedagógico de apoio ao AEE",
            small_style,
        )]],
        colWidths=[17.5 * cm],
    )
    rodape.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(rodape)
    doc.build(elementos)
    return nome_arquivo


def gerar_pdf_plano_aee_ia_visual(conteudo, nome_base, titulo_doc="PLANO MENSAL AEE - IA"):
    """Compatibilidade: mantém a chamada antiga do Plano Mensal."""
    return gerar_pdf_relatorio_visual(conteudo, nome_base, tipo_relatorio="plano_mensal", titulo_doc=titulo_doc)


def export_buttons(texto, nome_base, tipo_pdf="documento"):
    col_txt, col_pdf, col_word = st.columns(3)

    with col_txt:
        st.download_button(
            "Baixar em .txt",
            data=texto,
            file_name=f"{nome_base}.txt",
            mime="text/plain",
            key=f"txt_{nome_base}_{tipo_pdf}",
        )

    with col_pdf:
        if st.button("Gerar PDF", key=f"gerar_pdf_{nome_base}_{tipo_pdf}"):
            if tipo_pdf in MAPA_TIPOS_VISUAIS:
                arquivo = gerar_pdf_relatorio_visual(texto, nome_base, tipo_relatorio=tipo_pdf)
            else:
                arquivo = gerar_pdf_documento(texto, nome_base, tipo=tipo_pdf)
            st.session_state[f"pdf_{nome_base}_{tipo_pdf}"] = arquivo

        if f"pdf_{nome_base}_{tipo_pdf}" in st.session_state:
            with open(st.session_state[f"pdf_{nome_base}_{tipo_pdf}"], "rb") as f:
                st.download_button(
                    "Baixar PDF",
                    data=f,
                    file_name=f"{nome_base}.pdf",
                    mime="application/pdf",
                    key=f"download_pdf_{nome_base}_{tipo_pdf}",
                )

    with col_word:
        if st.button("Gerar Word", key=f"gerar_docx_{nome_base}_{tipo_pdf}"):
            try:
                if tipo_pdf in MAPA_TIPOS_VISUAIS:
                    arquivo = gerar_docx_relatorio_visual(texto, nome_base, tipo_relatorio=tipo_pdf)
                else:
                    arquivo = gerar_docx_documento(texto, nome_base, tipo=tipo_pdf)
                st.session_state[f"docx_{nome_base}_{tipo_pdf}"] = arquivo
            except ModuleNotFoundError:
                st.error("Biblioteca python-docx não instalada. Rode: pip install python-docx")

        if f"docx_{nome_base}_{tipo_pdf}" in st.session_state:
            with open(st.session_state[f"docx_{nome_base}_{tipo_pdf}"], "rb") as f:
                st.download_button(
                    "Baixar Word",
                    data=f,
                    file_name=f"{nome_base}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download_docx_{nome_base}_{tipo_pdf}",
                )


# ======================================================
# CRUD - ESTUDANTES
# ======================================================
def cadastrar_estudante(codigo, ano_serie, turma, turno, perfil, observacoes, dias_atendimento, horario_preferencial):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO estudantes (
            codigo, ano_serie, turma, turno, perfil, observacoes,
            dias_atendimento, horario_preferencial, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (codigo, ano_serie, turma, turno, perfil, observacoes, dias_atendimento, horario_preferencial, hoje_str()),
    )
    conn.commit()
    conn.close()
    limpar_cache_dados()


@st.cache_data(ttl=30, show_spinner=False)
def listar_estudantes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, codigo, ano_serie, turma, perfil, observacoes, turno, dias_atendimento, horario_preferencial
        FROM estudantes
        ORDER BY codigo
        """
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


@st.cache_data(ttl=30, show_spinner=False)
def buscar_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, codigo, ano_serie, turma, perfil, observacoes, turno, dias_atendimento, horario_preferencial
        FROM estudantes
        WHERE id = ?
        """,
        (estudante_id,),
    )
    dado = cursor.fetchone()
    conn.close()
    return dado


def atualizar_estudante(estudante_id, codigo, ano_serie, turma, turno, perfil, observacoes, dias_atendimento, horario_preferencial):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE estudantes
        SET codigo=?, ano_serie=?, turma=?, turno=?, perfil=?, observacoes=?,
            dias_atendimento=?, horario_preferencial=?
        WHERE id=?
        """,
        (codigo, ano_serie, turma, turno, perfil, observacoes, dias_atendimento, horario_preferencial, estudante_id),
    )
    conn.commit()
    conn.close()
    limpar_cache_dados()


def excluir_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    for tabela in [
        "agenda", "atendimentos", "relatorios", "paees", "plano_aee_ia", "planos_aee",
        "estudos_caso", "avaliacoes", "entrevistas_familia", "estudante_professor"
    ]:
        cursor.execute(f"DELETE FROM {tabela} WHERE estudante_id=?", (estudante_id,))
    cursor.execute("DELETE FROM estudantes WHERE id=?", (estudante_id,))
    conn.commit()
    conn.close()
    limpar_cache_dados()


# ======================================================
# CRUD - PROFESSOR
# ======================================================
def salvar_professor(nome_referencia, escola, regional, formacao, carga_horaria, turno_atuacao, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO professores (
            nome_referencia, escola, regional, formacao, carga_horaria,
            turno_atuacao, observacoes, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (nome_referencia, escola, regional, formacao, carga_horaria, turno_atuacao, observacoes, hoje_str()),
    )
    conn.commit()
    conn.close()
    limpar_cache_dados()


@st.cache_data(ttl=30, show_spinner=False)
def listar_professores():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nome_referencia, escola, regional, formacao, carga_horaria, turno_atuacao, observacoes, criado_em
        FROM professores
        ORDER BY id DESC
        """
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def atualizar_professor(professor_id, nome_referencia, escola, regional, formacao, carga_horaria, turno_atuacao, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE professores
        SET nome_referencia=?, escola=?, regional=?, formacao=?,
            carga_horaria=?, turno_atuacao=?, observacoes=?
        WHERE id=?
        """,
        (nome_referencia, escola, regional, formacao, carga_horaria, turno_atuacao, observacoes, professor_id),
    )
    conn.commit()
    conn.close()
    limpar_cache_dados()


def excluir_professor(professor_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM estudante_professor WHERE professor_id=?", (professor_id,))
    cursor.execute("DELETE FROM professores WHERE id=?", (professor_id,))
    conn.commit()
    conn.close()
    limpar_cache_dados()


@st.cache_data(ttl=30, show_spinner=False)
def contar_alunos_do_professor(professor_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM estudante_professor WHERE professor_id=?",
        (professor_id,),
    )
    total = cursor.fetchone()[0]
    conn.close()
    return total


def vincular_professor_estudante(estudante_id, professor_id):
    """Vincula professor ao estudante, limitando cada professor a até 14 estudantes."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM estudante_professor WHERE professor_id=?",
        (professor_id,),
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT id FROM estudante_professor
        WHERE estudante_id=? AND professor_id=?
        """,
        (estudante_id, professor_id),
    )
    ja_existe = cursor.fetchone()

    if ja_existe:
        conn.close()
        return False, "Este estudante já está vinculado a este professor."

    if total >= 14:
        conn.close()
        return False, "Este professor já possui 14 estudantes vinculados."

    cursor.execute(
        """
        INSERT INTO estudante_professor (estudante_id, professor_id, criado_em)
        VALUES (?, ?, ?)
        """,
        (estudante_id, professor_id, hoje_str()),
    )
    conn.commit()
    conn.close()
    limpar_cache_dados()
    return True, "Vínculo realizado com sucesso."


def remover_vinculo_professor_estudante(vinculo_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM estudante_professor WHERE id=?", (vinculo_id,))
    conn.commit()
    conn.close()
    limpar_cache_dados()


@st.cache_data(ttl=30, show_spinner=False)
def listar_estudantes_do_professor(professor_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ep.id, e.id, e.codigo, e.ano_serie, e.turma, e.perfil
        FROM estudante_professor ep
        JOIN estudantes e ON e.id = ep.estudante_id
        WHERE ep.professor_id=?
        ORDER BY e.codigo
        """,
        (professor_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


@st.cache_data(ttl=30, show_spinner=False)
def listar_professores_do_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ep.id, p.id, p.nome_referencia, p.escola, p.regional, p.carga_horaria, p.turno_atuacao
        FROM estudante_professor ep
        JOIN professores p ON p.id = ep.professor_id
        WHERE ep.estudante_id=?
        ORDER BY p.nome_referencia
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


@st.cache_data(ttl=30, show_spinner=False)
def buscar_professor_responsavel():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nome_referencia, escola, regional, formacao,
               carga_horaria, turno_atuacao, observacoes, criado_em
        FROM professores
        ORDER BY id DESC
        LIMIT 1
        """
    )
    dado = cursor.fetchone()
    conn.close()
    return dado


def texto_professor_responsavel():
    professor = buscar_professor_responsavel()
    if not professor:
        return "Nenhum professor AEE cadastrado."
    return (
        f"{professor[1] or 'Não informado.'} | "
        f"Escola: {professor[2] or 'Não informado.'} | "
        f"Regional/GRE: {professor[3] or 'Não informado.'} | "
        f"Carga horária: {professor[5] or 'Não informado.'} | "
        f"Turno: {professor[6] or 'Não informado.'}"
    )


def texto_professores_vinculados(estudante_id=None):
    """Protótipo personalizado: usa o professor responsável mais recente."""
    return texto_professor_responsavel()


# ======================================================
# CRUD - ENTREVISTA, AVALIAÇÃO, ESTUDO, PLANO
# ======================================================
def inserir_registro(tabela, campos, valores):
    conn = conectar()
    cursor = conn.cursor()
    placeholders = ", ".join(["?"] * len(valores))
    cursor.execute(
        f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({placeholders})",
        valores,
    )
    conn.commit()
    conn.close()
    limpar_cache_dados()


@st.cache_data(ttl=30, show_spinner=False)
def listar_por_estudante(tabela, campos, estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT id, {', '.join(campos)} FROM {tabela} WHERE estudante_id=? ORDER BY id DESC",
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def excluir_registro(tabela, registro_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {tabela} WHERE id=?", (registro_id,))
    conn.commit()
    conn.close()
    limpar_cache_dados()


def atualizar_registro(tabela, campos, valores, registro_id):
    conn = conectar()
    cursor = conn.cursor()
    sets = ", ".join([f"{campo}=?" for campo in campos])
    cursor.execute(f"UPDATE {tabela} SET {sets} WHERE id=?", list(valores) + [registro_id])
    conn.commit()
    conn.close()
    limpar_cache_dados()


@st.cache_data(ttl=30, show_spinner=False)
def ultima_linha(tabela, campos, estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT {', '.join(campos)} FROM {tabela} WHERE estudante_id=? ORDER BY id DESC LIMIT 1",
        (estudante_id,),
    )
    dado = cursor.fetchone()
    conn.close()
    return dado


# ======================================================
# CRUD - AVALIAÇÃO
# ======================================================
def salvar_avaliacao(
    estudante_id,
    barreiras="",
    potencialidades="",
    comunicacao="",
    interacao="",
    autonomia="",
    aprendizagem="",
    resumo_laudo="",
    ano_letivo="",
    tipo_registro="Avaliação pedagógica atual",
    avaliacao_anterior_id=None,
    analise_comparativa_ia="",
    sugestao_nova_avaliacao_ia="",
    origem_documento="",
    texto_documento_extra="",
):
    inserir_registro(
        "avaliacoes",
        [
            "estudante_id", "data_registro",
            "ano_letivo", "tipo_registro", "avaliacao_anterior_id", "analise_comparativa_ia", "sugestao_nova_avaliacao_ia",
            "origem_documento", "texto_documento_extra",
            "barreiras", "potencialidades", "comunicacao", "interacao", "autonomia", "aprendizagem", "resumo_laudo",
        ],
        [
            estudante_id, hoje_str(),
            ano_letivo, tipo_registro, avaliacao_anterior_id, analise_comparativa_ia, sugestao_nova_avaliacao_ia,
            origem_documento, texto_documento_extra,
            barreiras, potencialidades, comunicacao, interacao, autonomia, aprendizagem, resumo_laudo,
        ],
    )


@st.cache_data(ttl=30, show_spinner=False)
def listar_avaliacoes(estudante_id):
    return listar_por_estudante(
        "avaliacoes",
        CAMPOS_AVALIACAO,
        estudante_id,
    )


@st.cache_data(ttl=30, show_spinner=False)
def ultima_avaliacao(estudante_id):
    return ultima_linha(
        "avaliacoes",
        CAMPOS_AVALIACAO,
        estudante_id,
    )


@st.cache_data(ttl=30, show_spinner=False)
def buscar_avaliacao_por_id(avaliacao_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT id, {', '.join(CAMPOS_AVALIACAO)} FROM avaliacoes WHERE id=?",
        (avaliacao_id,),
    )
    dado = cursor.fetchone()
    conn.close()
    return dado


def salvar_documento_avaliacao(
    estudante_id,
    avaliacao_id,
    ano_letivo,
    tipo_documento,
    arquivo,
    observacao="",
):
    """Salva documento anexado à avaliação pedagógica.

    Observação importante:
    - No Render, arquivos salvos em pasta local podem ser perdidos em novo deploy.
    - Para produção, o ideal é usar armazenamento persistente/externo.
    """
    if arquivo is None:
        return None

    pasta_estudante = DOCUMENTOS_AVALIACOES_DIR / f"estudante_{estudante_id}"
    pasta_estudante.mkdir(parents=True, exist_ok=True)

    timestamp = agora_local().strftime("%Y%m%d_%H%M%S")
    nome_seguro = arquivo.name.replace("/", "_").replace("\\", "_")
    nome_salvo = f"{timestamp}_{nome_seguro}"
    caminho = pasta_estudante / nome_salvo

    with open(caminho, "wb") as f:
        f.write(arquivo.getbuffer())

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO avaliacoes_documentos (
            avaliacao_id, estudante_id, ano_letivo, tipo_documento,
            nome_original, nome_arquivo_salvo, caminho_arquivo,
            observacao, data_upload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            avaliacao_id,
            estudante_id,
            ano_letivo,
            tipo_documento,
            arquivo.name,
            nome_salvo,
            str(caminho),
            observacao,
            hoje_str(),
        ),
    )
    conn.commit()
    conn.close()
    limpar_cache_dados()
    return str(caminho)


@st.cache_data(ttl=30, show_spinner=False)
def listar_documentos_avaliacao(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, avaliacao_id, ano_letivo, tipo_documento,
               nome_original, caminho_arquivo, observacao, data_upload
        FROM avaliacoes_documentos
        WHERE estudante_id=?
        ORDER BY id DESC
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def excluir_documento_avaliacao(documento_id, caminho_arquivo):
    try:
        if caminho_arquivo and Path(caminho_arquivo).exists():
            Path(caminho_arquivo).unlink()
    except Exception:
        pass

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM avaliacoes_documentos WHERE id=?", (documento_id,))
    conn.commit()
    conn.close()
    limpar_cache_dados()


# ======================================================
# CRUD - ARTICULAÇÃO PEDAGÓGICA INCLUSIVA / ESCUTA DOCENTE
# ======================================================
def salvar_escuta_docente(
    estudante_id,
    ano_letivo,
    codigo_docente,
    componente_curricular,
    outro_componente,
    turma,
    tempo_acompanhamento,
    participacao_sala,
    comunicacao,
    interacao_social,
    aprendizagem,
    barreiras_percebidas,
    potencialidades_observadas,
    estrategias_funcionam,
    adaptacoes_utilizadas,
    recomendacoes_docente,
    nivel_participacao,
    nivel_autonomia,
    nivel_engajamento,
    observacoes,
):
    inserir_registro(
        "escutas_docentes",
        [
            "estudante_id",
            "data_registro",
            "ano_letivo",
            "codigo_docente",
            "componente_curricular",
            "outro_componente",
            "turma",
            "tempo_acompanhamento",
            "participacao_sala",
            "comunicacao",
            "interacao_social",
            "aprendizagem",
            "barreiras_percebidas",
            "potencialidades_observadas",
            "estrategias_funcionam",
            "adaptacoes_utilizadas",
            "recomendacoes_docente",
            "nivel_participacao",
            "nivel_autonomia",
            "nivel_engajamento",
            "observacoes",
        ],
        [
            estudante_id,
            hoje_str(),
            ano_letivo,
            codigo_docente,
            componente_curricular,
            outro_componente,
            turma,
            tempo_acompanhamento,
            participacao_sala,
            comunicacao,
            interacao_social,
            aprendizagem,
            barreiras_percebidas,
            potencialidades_observadas,
            estrategias_funcionam,
            adaptacoes_utilizadas,
            recomendacoes_docente,
            nivel_participacao,
            nivel_autonomia,
            nivel_engajamento,
            observacoes,
        ],
    )


@st.cache_data(ttl=30, show_spinner=False)
def listar_escutas_docentes(estudante_id):
    """Lista escutas docentes sem expor nome pessoal.
    Usa codigo_docente como campo principal e mantém fallback técnico para registros antigos.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id,
               data_registro,
               ano_letivo,
               COALESCE(NULLIF(codigo_docente, ''), NULLIF(professor_nome, ''), 'Não informado') AS codigo_docente,
               componente_curricular,
               outro_componente,
               turma,
               tempo_acompanhamento,
               participacao_sala,
               comunicacao,
               interacao_social,
               aprendizagem,
               barreiras_percebidas,
               potencialidades_observadas,
               estrategias_funcionam,
               adaptacoes_utilizadas,
               recomendacoes_docente,
               nivel_participacao,
               nivel_autonomia,
               nivel_engajamento,
               observacoes
        FROM escutas_docentes
        WHERE estudante_id=?
        ORDER BY id DESC
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def excluir_escuta_docente(escuta_id):
    excluir_registro("escutas_docentes", escuta_id)


def texto_escuta_docente(estudante, escuta):
    dados = dict(zip(["id"] + CAMPOS_ESCUTA_DOCENTE, escuta))

    def v(campo):
        valor = dados.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    componente = v("componente_curricular")
    if componente == "Outras" and dados.get("outro_componente"):
        componente = dados.get("outro_componente")

    return f"""
ARTICULAÇÃO PEDAGÓGICA INCLUSIVA - ESCUTA DOCENTE

Código interno do estudante: {estudante[1]}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Data do registro: {v('data_registro')}
Ano letivo: {v('ano_letivo')}

Código interno do docente / referência pedagógica: {v('codigo_docente')}
Componente curricular / área: {componente}
Turma observada: {v('turma')}
Tempo de acompanhamento: {v('tempo_acompanhamento')}

PARTICIPAÇÃO EM SALA:
{v('participacao_sala')}

COMUNICAÇÃO:
{v('comunicacao')}

INTERAÇÃO SOCIAL:
{v('interacao_social')}

APRENDIZAGEM:
{v('aprendizagem')}

BARREIRAS PERCEBIDAS:
{v('barreiras_percebidas')}

POTENCIALIDADES OBSERVADAS:
{v('potencialidades_observadas')}

ESTRATÉGIAS QUE FUNCIONAM:
{v('estrategias_funcionam')}

ADAPTAÇÕES UTILIZADAS:
{v('adaptacoes_utilizadas')}

RECOMENDAÇÕES DO DOCENTE:
{v('recomendacoes_docente')}

INDICADORES:
Participação: {v('nivel_participacao')}/10
Autonomia: {v('nivel_autonomia')}/10
Engajamento: {v('nivel_engajamento')}/10

OBSERVAÇÕES:
{v('observacoes')}
""".strip()


def salvar_relatorio_docente(
    estudante_id,
    ano_letivo,
    componente_destino,
    professor_destino,
    titulo,
    conteudo,
    fontes_utilizadas,
    observacoes="",
):
    inserir_registro(
        "relatorios_docente",
        [
            "estudante_id",
            "data_geracao",
            "ano_letivo",
            "componente_destino",
            "professor_destino",
            "titulo",
            "conteudo",
            "fontes_utilizadas",
            "observacoes",
        ],
        [
            estudante_id,
            hoje_str(),
            ano_letivo,
            componente_destino,
            professor_destino,
            titulo,
            conteudo,
            fontes_utilizadas,
            observacoes,
        ],
    )


@st.cache_data(ttl=30, show_spinner=False)
def listar_relatorios_docente(estudante_id):
    return listar_por_estudante("relatorios_docente", CAMPOS_RELATORIO_DOCENTE, estudante_id)


def excluir_relatorio_docente(relatorio_id):
    excluir_registro("relatorios_docente", relatorio_id)


def texto_relatorio_docente(estudante, relatorio):
    dados = dict(zip(["id"] + CAMPOS_RELATORIO_DOCENTE, relatorio))

    def v(campo):
        valor = dados.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    return f"""
{v('titulo')}

Código interno do estudante: {estudante[1]}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Ano letivo: {v('ano_letivo')}
Componente/área de destino: {v('componente_destino')}
Destinatário: ________________________________________
Data de geração: {v('data_geracao')}

{v('conteudo')}

FONTES UTILIZADAS PELO SISTEMA:
{v('fontes_utilizadas')}

OBSERVAÇÕES:
{v('observacoes')}

Observação institucional:
Este relatório possui finalidade exclusivamente pedagógica. Seu objetivo é apoiar o planejamento inclusivo do docente, sem substituir a avaliação profissional do professor, da equipe pedagógica ou do AEE.
""".strip()


def montar_contexto_relatorio_docente(estudante_id, limite_atendimentos=12):
    estudante = buscar_estudante(estudante_id)

    avaliacoes = listar_avaliacoes(estudante_id)[:5]
    estudos = listar_por_estudante("estudos_caso", CAMPOS_ESTUDO_CASO, estudante_id)[:3]
    entrevistas = listar_por_estudante("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)[:2]
    escutas = listar_escutas_docentes(estudante_id)[:10]
    atendimentos = listar_atendimentos(estudante_id)[:limite_atendimentos]
    documentos = listar_documentos_avaliacao(estudante_id)

    textos_avaliacoes = []
    for av in avaliacoes:
        try:
            textos_avaliacoes.append(texto_avaliacao(estudante, av))
        except Exception:
            textos_avaliacoes.append(str(av))

    textos_estudos = []
    for est in estudos:
        try:
            textos_estudos.append(texto_estudo_caso(estudante, est))
        except Exception:
            textos_estudos.append(str(est))

    textos_escutas = []
    for esc in escutas:
        try:
            textos_escutas.append(texto_escuta_docente(estudante, esc))
        except Exception:
            textos_escutas.append(str(esc))

    texto_entrevistas = "\n\n".join([str(e) for e in entrevistas]) or "Nenhuma entrevista familiar localizada."
    texto_atendimentos = "\n".join([str(a) for a in atendimentos]) or "Nenhum atendimento registrado."
    texto_documentos = "\n".join([
        f"- {d[4]} | Ano: {d[2] or 'não informado'} | Tipo: {d[3] or 'não informado'} | Obs.: {d[6] or ''}"
        for d in documentos
    ]) or "Nenhum documento histórico anexado."

    fontes = []
    if avaliacoes:
        fontes.append(f"{len(avaliacoes)} avaliação(ões) pedagógica(s)")
    if estudos:
        fontes.append(f"{len(estudos)} estudo(s) de caso")
    if escutas:
        fontes.append(f"{len(escutas)} escuta(s) docente(s)")
    if atendimentos:
        fontes.append(f"{len(atendimentos)} atendimento(s)")
    if documentos:
        fontes.append(f"{len(documentos)} documento(s) histórico(s) anexado(s)")
    if entrevistas:
        fontes.append(f"{len(entrevistas)} entrevista(s) familiar(es) usada(s) apenas como contexto pedagógico")

    contexto = f"""
DADOS DO ESTUDANTE
Código interno: {estudante[1]}
Ano/Série: {estudante[2]}
Turma: {estudante[3]}
Perfil educacional cadastrado: {estudante[4]}
Observações gerais do cadastro: {estudante[5] or ''}

AVALIAÇÕES PEDAGÓGICAS / DOCUMENTOS LIVRES:
{chr(10).join(textos_avaliacoes) if textos_avaliacoes else 'Nenhuma avaliação pedagógica localizada.'}

ESTUDOS DE CASO:
{chr(10).join(textos_estudos) if textos_estudos else 'Nenhum estudo de caso localizado.'}

ESCUTAS DOCENTES DA SALA REGULAR:
{chr(10).join(textos_escutas) if textos_escutas else 'Nenhuma escuta docente registrada.'}

ATENDIMENTOS DO AEE:
{texto_atendimentos}

DOCUMENTOS HISTÓRICOS ANEXADOS:
{texto_documentos}

ENTREVISTAS FAMILIARES:
{texto_entrevistas}
""".strip()

    return contexto, "; ".join(fontes) if fontes else "Nenhuma fonte registrada."


def gerar_relatorio_apoio_docente_ia(
    estudante_id,
    ano_letivo,
    componente_destino,
    professor_destino="",
    foco_docente="",
):
    estudante = buscar_estudante(estudante_id)
    contexto, fontes = montar_contexto_relatorio_docente(estudante_id)

    client = obter_cliente_openai()
    if client is None:
        conteudo_fallback = f"""
1. SÍNTESE PEDAGÓGICA FUNCIONAL
IA não configurada. Configure OPENAI_API_KEY para gerar a síntese automática. Ainda assim, o sistema reuniu as fontes pedagógicas disponíveis para revisão manual.

2. POTENCIALIDADES OBSERVADAS
Preencher com base nas avaliações pedagógicas, estudos de caso, escutas docentes e atendimentos registrados.

3. BARREIRAS PEDAGÓGICAS OBSERVADAS
Preencher com base nos registros do AEE e nas observações dos docentes da sala regular.

4. ESTRATÉGIAS PEDAGÓGICAS RECOMENDADAS
Preencher com orientações objetivas, como apoio visual, instruções curtas, mediação gradual, tempo ampliado e diferentes formas de participação.

5. RECOMENDAÇÕES AVALIATIVAS
Considerar participação, evolução individual, comunicação funcional, engajamento e diferentes formas de expressão do conhecimento.

6. ORIENTAÇÕES PARA O DOCENTE
Usar este relatório como apoio pedagógico, sem expor dados familiares ou informações sensíveis desnecessárias.

Fontes reunidas: {fontes}
""".strip()
        return conteudo_fallback, fontes

    prompt = f"""
Você é um especialista em Atendimento Educacional Especializado, educação inclusiva, desenho universal para aprendizagem e articulação pedagógica entre AEE e sala regular.

TAREFA:
Gerar um RELATÓRIO PEDAGÓGICO DE APOIO AO DOCENTE para orientar o professor da área indicada, cruzando as informações do sistema.

NOME DO RELATÓRIO:
Relatório Pedagógico de Apoio ao Docente

DESTINATÁRIO:
Componente/área: {componente_destino}
Destinatário: campo em branco para preenchimento manual no documento final
Ano letivo: {ano_letivo}
Foco solicitado pelo AEE: {foco_docente or 'Não informado'}

REGRAS OBRIGATÓRIAS:
- Não usar linguagem médica ou clínica.
- Não expor dados familiares.
- Não citar CPF, endereço, telefone, nomes de responsáveis ou dados sensíveis.
- Não inventar informações.
- Trabalhar somente com os dados fornecidos.
- Usar linguagem pedagógica, objetiva, acolhedora e institucional.
- O documento deve orientar o professor da sala regular, sem rotular o estudante.
- Focar em participação, aprendizagem, barreiras, potencialidades, estratégias e avaliação inclusiva.
- Quando os dados forem insuficientes, escrever que a informação não foi localizada nos registros.

DADOS DISPONÍVEIS NO SISTEMA:
{contexto}

Produza o relatório com as seções abaixo:

1. FINALIDADE DO DOCUMENTO
Explique que o relatório apoia o planejamento pedagógico inclusivo do docente.

2. SÍNTESE PEDAGÓGICA FUNCIONAL
Síntese objetiva de como o estudante aprende, participa e responde às mediações.

3. POTENCIALIDADES OBSERVADAS
Listar potencialidades pedagógicas observadas nos registros.

4. BARREIRAS PEDAGÓGICAS E DESAFIOS EM SALA
Listar barreiras educacionais sem linguagem medicalizante.

5. ESTRATÉGIAS QUE TENDEM A FAVORECER A PARTICIPAÇÃO
Recomendações práticas para o docente da área.

6. RECOMENDAÇÕES PARA ADAPTAÇÃO DAS ATIVIDADES
Orientações de adaptação curricular, acessibilidade pedagógica e mediação.

7. RECOMENDAÇÕES AVALIATIVAS
Orientar formas de avaliação inclusiva considerando participação, evolução individual, comunicação, engajamento e diferentes formas de expressão.

8. PONTOS DE ATENÇÃO PARA ARTICULAÇÃO COM O AEE
Indicar como o professor pode dialogar com o AEE, sem expor dados sensíveis.

9. FECHAMENTO INSTITUCIONAL
Finalizar com uma mensagem pedagógica, acolhedora e profissional.
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return (resposta.output_text or "").strip(), fontes
    except Exception as e:
        return f"Não foi possível gerar o relatório com IA agora. Erro: {e}", fontes



# ======================================================
# CRUD - ATENDIMENTOS
# ======================================================
def salvar_atendimento(
    estudante_id, data_atendimento, objetivo, atividade, resposta_estudante,
    avancos, dificuldades, evolucao, qtd_atividades, nivel_resposta,
    nivel_avanco, nivel_dificuldade, nivel_engajamento, nivel_evolucao,
    encaminhamentos,
):
    """Salva atendimento e retorna o ID criado para vincular recursos pedagógicos."""
    campos = [
        "estudante_id", "data_atendimento", "objetivo", "atividade", "resposta_estudante",
        "avancos", "dificuldades", "evolucao", "qtd_atividades", "nivel_resposta",
        "nivel_avanco", "nivel_dificuldade", "nivel_engajamento", "nivel_evolucao",
        "encaminhamentos",
    ]
    valores = [
        estudante_id, data_atendimento, objetivo, atividade, resposta_estudante,
        avancos, dificuldades, evolucao, qtd_atividades, nivel_resposta,
        nivel_avanco, nivel_dificuldade, nivel_engajamento, nivel_evolucao,
        encaminhamentos,
    ]

    conn = conectar()
    cursor = conn.cursor()
    placeholders = ", ".join(["?"] * len(valores))
    colunas = ", ".join(campos)

    if USAR_POSTGRES:
        cursor.execute(
            f"INSERT INTO atendimentos ({colunas}) VALUES ({placeholders}) RETURNING id",
            valores,
        )
        atendimento_id = cursor.fetchone()[0]
    else:
        cursor.execute(
            f"INSERT INTO atendimentos ({colunas}) VALUES ({placeholders})",
            valores,
        )
        atendimento_id = cursor.lastrowid

    conn.commit()
    conn.close()
    limpar_cache_dados()
    return atendimento_id


@st.cache_data(ttl=30, show_spinner=False)
def listar_atendimentos(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT data_atendimento, objetivo, atividade, resposta_estudante,
               avancos, dificuldades, evolucao, qtd_atividades, nivel_resposta,
               nivel_avanco, nivel_dificuldade, nivel_engajamento,
               nivel_evolucao, encaminhamentos
        FROM atendimentos
        WHERE estudante_id = ?
        ORDER BY id DESC
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


@st.cache_data(ttl=30, show_spinner=False)
def listar_atendimentos_com_id(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, data_atendimento, objetivo, atividade, resposta_estudante,
               avancos, dificuldades, evolucao, qtd_atividades, nivel_resposta,
               nivel_avanco, nivel_dificuldade, nivel_engajamento,
               nivel_evolucao, encaminhamentos
        FROM atendimentos
        WHERE estudante_id = ?
        ORDER BY id DESC
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def atualizar_atendimento(atendimento_id, data_atendimento, objetivo, atividade, resposta_estudante, avancos, dificuldades, evolucao, qtd_atividades, nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento, nivel_evolucao, encaminhamentos):
    atualizar_registro(
        "atendimentos",
        [
            "data_atendimento", "objetivo", "atividade", "resposta_estudante", "avancos",
            "dificuldades", "evolucao", "qtd_atividades", "nivel_resposta", "nivel_avanco",
            "nivel_dificuldade", "nivel_engajamento", "nivel_evolucao", "encaminhamentos",
        ],
        [
            data_atendimento, objetivo, atividade, resposta_estudante, avancos, dificuldades,
            evolucao, qtd_atividades, nivel_resposta, nivel_avanco, nivel_dificuldade,
            nivel_engajamento, nivel_evolucao, encaminhamentos,
        ],
        atendimento_id,
    )


def excluir_atendimento(atendimento_id):
    excluir_recursos_por_atendimento(atendimento_id)
    excluir_registro("atendimentos", atendimento_id)


# ======================================================
# CRUD - RECURSOS PEDAGÓGICOS DO ATENDIMENTO
# ======================================================
def salvar_recurso_atendimento(atendimento_id, estudante_id, nome_recurso, categoria_recurso, link_recurso, observacao_uso):
    inserir_registro(
        "recursos_atendimento",
        [
            "atendimento_id", "estudante_id", "nome_recurso", "categoria_recurso",
            "link_recurso", "observacao_uso", "criado_em",
        ],
        [
            atendimento_id, estudante_id, nome_recurso, categoria_recurso,
            link_recurso, observacao_uso, hoje_str(),
        ],
    )


@st.cache_data(ttl=30, show_spinner=False)
def listar_recursos_atendimento(atendimento_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nome_recurso, categoria_recurso, link_recurso, observacao_uso, criado_em
        FROM recursos_atendimento
        WHERE atendimento_id = ?
        ORDER BY id ASC
        """,
        (atendimento_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def excluir_recursos_por_atendimento(atendimento_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recursos_atendimento WHERE atendimento_id=?", (atendimento_id,))
    conn.commit()
    conn.close()
    limpar_cache_dados()


def texto_recursos_atendimento(atendimento_id):
    recursos = listar_recursos_atendimento(atendimento_id)
    if not recursos:
        return "Nenhum recurso pedagógico com link registrado para este atendimento."

    linhas = []
    for i, r in enumerate(recursos, start=1):
        _, nome, categoria, link, observacao, criado_em = r
        linhas.append(
            f"{i}. {nome or 'Recurso não informado'}\n"
            f"   Categoria: {categoria or 'Não informada'}\n"
            f"   Link: {link or 'Não informado'}\n"
            f"   Observação de uso: {observacao or 'Não informada'}"
        )
    return "\n\n".join(linhas)


# ======================================================
# CRUD - AGENDA
# ======================================================
def salvar_agendamento(estudante_id, data_agendamento, dia_semana, hora_inicio, hora_fim, tipo_atendimento, observacoes):
    inserir_registro(
        "agenda",
        ["estudante_id", "data_agendamento", "dia_semana", "hora_inicio", "hora_fim", "tipo_atendimento", "observacoes", "criado_em"],
        [estudante_id, data_agendamento, dia_semana, hora_inicio, hora_fim, tipo_atendimento, observacoes, hoje_str()],
    )


@st.cache_data(ttl=30, show_spinner=False)
def listar_agenda():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT agenda.id, estudantes.codigo, estudantes.ano_serie, estudantes.perfil,
               agenda.data_agendamento, agenda.dia_semana, agenda.hora_inicio,
               agenda.hora_fim, agenda.tipo_atendimento, agenda.observacoes
        FROM agenda
        JOIN estudantes ON estudantes.id = agenda.estudante_id
        ORDER BY agenda.data_agendamento, agenda.hora_inicio
        """
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def listar_agenda_com_id():
    return listar_agenda()


@st.cache_data(ttl=30, show_spinner=False)
def contar_registros_tabela(tabela):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    total = cursor.fetchone()[0]
    conn.close()
    return total


def excluir_agendamento(agenda_id):
    excluir_registro("agenda", agenda_id)


def data_texto_para_date_seguro(data_texto):
    """Converte data em formato dd/mm/aaaa para date. Retorna None se inválida."""
    try:
        return datetime.strptime(str(data_texto), "%d/%m/%Y").date()
    except Exception:
        return None


@st.cache_data(ttl=30, show_spinner=False)
def listar_agenda_detalhada(estudante_id=None, data_inicio=None, data_fim=None):
    """Lista agenda com status de presença calculado automaticamente.
    Status calculado:
    - Compareceu: se houver atendimento vinculado ou atendimento do estudante na mesma data.
    - Faltou: se a data já passou e não houver atendimento.
    - Agendado: se ainda não ocorreu.
    """
    conn = conectar()
    cursor = conn.cursor()
    if estudante_id:
        cursor.execute(
            """
            SELECT a.id, a.estudante_id, e.codigo, e.ano_serie, e.perfil,
                   a.data_agendamento, a.dia_semana, a.hora_inicio, a.hora_fim,
                   a.tipo_atendimento, a.observacoes,
                   COALESCE(a.status_presenca, 'Agendado') AS status_presenca,
                   a.atendimento_id,
                   COALESCE(a.preenchimento_ia, '') AS preenchimento_ia
            FROM agenda a
            JOIN estudantes e ON e.id = a.estudante_id
            WHERE a.estudante_id = ?
            ORDER BY a.data_agendamento, a.hora_inicio
            """,
            (estudante_id,),
        )
    else:
        cursor.execute(
            """
            SELECT a.id, a.estudante_id, e.codigo, e.ano_serie, e.perfil,
                   a.data_agendamento, a.dia_semana, a.hora_inicio, a.hora_fim,
                   a.tipo_atendimento, a.observacoes,
                   COALESCE(a.status_presenca, 'Agendado') AS status_presenca,
                   a.atendimento_id,
                   COALESCE(a.preenchimento_ia, '') AS preenchimento_ia
            FROM agenda a
            JOIN estudantes e ON e.id = a.estudante_id
            ORDER BY a.data_agendamento, a.hora_inicio
            """
        )
    dados = cursor.fetchall()

    # Busca atendimentos para status automático.
    cursor.execute("SELECT id, estudante_id, data_atendimento FROM atendimentos")
    atendimentos = cursor.fetchall()
    conn.close()

    atend_por_estudante_data = {}
    for atendimento_id, est_id, data_at in atendimentos:
        atend_por_estudante_data[(est_id, data_at)] = atendimento_id

    hoje = agora_local().date()
    filtrados = []
    for row in dados:
        row = list(row)
        data_ag = data_texto_para_date_seguro(row[5])
        if data_inicio and data_ag and data_ag < data_inicio:
            continue
        if data_fim and data_ag and data_ag > data_fim:
            continue

        ag_id, est_id = row[0], row[1]
        status_original = row[11] or "Agendado"
        atendimento_vinculado = row[12]
        atendimento_mesma_data = atend_por_estudante_data.get((est_id, row[5]))

        if atendimento_vinculado or atendimento_mesma_data:
            status_calc = "Compareceu"
            if not atendimento_vinculado and atendimento_mesma_data:
                row[12] = atendimento_mesma_data
        elif status_original in ["Compareceu", "Faltou", "Justificado", "Cancelado"]:
            status_calc = status_original
        elif data_ag and data_ag < hoje:
            status_calc = "Faltou"
        else:
            status_calc = "Agendado"
        row[11] = status_calc
        filtrados.append(tuple(row))
    return filtrados


def atualizar_status_agenda(agenda_id, status_presenca, atendimento_id=None, preenchimento_ia=None):
    conn = conectar()
    cursor = conn.cursor()
    if atendimento_id is not None and preenchimento_ia is not None:
        cursor.execute(
            "UPDATE agenda SET status_presenca=?, atendimento_id=?, preenchimento_ia=? WHERE id=?",
            (status_presenca, atendimento_id, preenchimento_ia, agenda_id),
        )
    elif atendimento_id is not None:
        cursor.execute(
            "UPDATE agenda SET status_presenca=?, atendimento_id=? WHERE id=?",
            (status_presenca, atendimento_id, agenda_id),
        )
    elif preenchimento_ia is not None:
        cursor.execute(
            "UPDATE agenda SET status_presenca=?, preenchimento_ia=? WHERE id=?",
            (status_presenca, preenchimento_ia, agenda_id),
        )
    else:
        cursor.execute(
            "UPDATE agenda SET status_presenca=? WHERE id=?",
            (status_presenca, agenda_id),
        )
    conn.commit()
    conn.close()
    limpar_cache_dados()


def montar_dataframe_quadro_semanal(estudante_id=None, data_inicio=None, data_fim=None):
    agenda = listar_agenda_detalhada(estudante_id=estudante_id, data_inicio=data_inicio, data_fim=data_fim)
    colunas = [
        "Agenda ID", "Estudante ID", "Código", "Ano/Série", "Perfil", "Data", "Dia", "Início", "Fim",
        "Tipo", "Observações da agenda", "Status", "Atendimento ID", "Sugestão IA"
    ]
    df_ag = pd.DataFrame(agenda, columns=colunas)
    if df_ag.empty:
        return df_ag

    # Traz dados do atendimento quando houver atendimento no mesmo dia.
    linhas = []
    for _, row in df_ag.iterrows():
        estudante = buscar_estudante(int(row["Estudante ID"]))
        atendimentos = listar_atendimentos(int(row["Estudante ID"]))
        at_data = None
        for a in atendimentos:
            if a[0] == row["Data"]:
                at_data = a
                break

        atividade = at_data[2] if at_data else row["Observações da agenda"]
        resposta = at_data[3] if at_data else ""
        dificuldades = at_data[5] if at_data else ""
        evolucao = at_data[6] if at_data else ""
        encaminhamentos = at_data[13] if at_data and len(at_data) > 13 else ""
        observacoes = " | ".join([x for x in [resposta, dificuldades, evolucao, encaminhamentos, row["Sugestão IA"]] if str(x).strip()])

        tipo = str(row["Tipo"] or "").lower()
        linhas.append({
            "Data": row["Data"],
            "Código": row["Código"],
            "Estudante": estudante[1] if estudante else row["Código"],
            "Individual": "X" if "individual" in tipo else "",
            "Coletivo": "X" if ("grupo" in tipo or "coletivo" in tipo) else "",
            "Recursos/Atividades desenvolvidas": atividade or "",
            "Observação em sala": "X" if "observ" in tipo else "",
            "Formação em serviço": "",
            "Diversos": "X" if str(row["Status"]) in ["Faltou", "Justificado", "Cancelado"] else "",
            "Presença": row["Status"],
            "Observações": observacoes or row["Observações da agenda"] or "",
            "Assinatura/Rúbrica": "",
        })
    return pd.DataFrame(linhas)


def gerar_texto_quadro_semanal_gre(professor, df_quadro, mes, ano, escola_manual="", regional_manual=""):
    escola = escola_manual or (professor[2] if professor else "") or "______________________________________________"
    regional = regional_manual or (professor[3] if professor else "") or "__________"
    professor_nome = (professor[1] if professor else "") or "______________________________________________"
    mes = mes or "________________"
    ano = ano or "20____"

    linhas = []
    if df_quadro is not None and not df_quadro.empty:
        for _, r in df_quadro.iterrows():
            linhas.append(
                f"Data: {r['Data']} | Individual: {r['Individual']} | Coletivo: {r['Coletivo']} | "
                f"Recursos/Atividades: {r['Recursos/Atividades desenvolvidas']} | "
                f"Observação em sala: {r['Observação em sala']} | Formação: {r['Formação em serviço']} | "
                f"Diversos: {r['Diversos']} | Presença: {r['Presença']} | Observações: {r['Observações']} | "
                f"Assinatura/Rúbrica: ____________________"
            )
    else:
        linhas.append("Nenhum atendimento/agendamento encontrado no período selecionado.")

    return f"""
{texto_cabecalho_gre("QUADRO DE ACOMPANHAMENTO SEMANAL - AÇÕES/PRÁTICAS DO PROFESSOR DO AEE")}

Escola: {escola}
Regional: {regional}
Professor(a): {professor_nome}
Mês: {mes}    Ano: {ano}

QUADRO DE ACOMPANHAMENTO SEMANAL - AÇÕES/PRÁTICAS DO PROFESSOR DO AEE

""".strip() + "\n\n" + "\n".join(linhas) + "\n\n*Este documento poderá ser editado ao longo do tempo para atender às necessidades e atualizações da atividade."


def gerar_docx_quadro_semanal_gre(professor, df_quadro, nome_base, mes, ano, escola_manual="", regional_manual=""):
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.section import WD_ORIENT

    nome_arquivo = f"Quadro_Semanal_GRE_{nome_base}.docx".replace("/", "-").replace("\\", "-")
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    section.left_margin = Inches(0.35)
    section.right_margin = Inches(0.35)
    section.top_margin = Inches(0.35)
    section.bottom_margin = Inches(0.35)

    cab = doc.add_paragraph()
    cab.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = cab.add_run(
        "SECRETARIA DE EDUCAÇÃO E ESPORTES\n"
        "GERÊNCIA METROPOLITANA NORTE DE EDUCAÇÃO\n"
        "CGDE - COORDENAÇÃO GERAL DE DESENVOLVIMENTO DA EDUCAÇÃO\n"
        "NÚCLEO DE EDUCAÇÃO INCLUSIVA, DIREITOS HUMANOS E CIDADANIA"
    )
    run.bold = True
    run.font.size = Pt(8)

    escola = escola_manual or (professor[2] if professor else "") or "______________________________________________"
    regional = regional_manual or (professor[3] if professor else "") or "__________"
    professor_nome = (professor[1] if professor else "") or "______________________________________________"
    mes = mes or "________________"
    ano = ano or "20____"

    doc.add_paragraph(f"ESCOLA: {escola}    REGIONAL: {regional}")
    doc.add_paragraph(f"PROFESSOR(A): {professor_nome}    MÊS: {mes}    ANO: {ano}")

    titulo = doc.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = titulo.add_run("Quadro de Acompanhamento Semanal - Ações/Práticas do Professor do AEE")
    rt.bold = True
    rt.underline = True
    rt.font.size = Pt(10)

    headers = [
        "DATA", "INDIVIDUAL", "COLETIVO", "RECURSOS UTILIZADOS / ATIVIDADES DESENVOLVIDAS",
        "OBSERVAÇÃO EM SALA", "FORMAÇÃO EM SERVIÇO", "DIVERSOS", "PRESENÇA", "OBSERVAÇÕES", "ASSINATURA/RÚBRICA"
    ]
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(7)

    if df_quadro is not None and not df_quadro.empty:
        for _, r in df_quadro.iterrows():
            row = table.add_row().cells
            valores = [
                r.get("Data", ""), r.get("Individual", ""), r.get("Coletivo", ""),
                r.get("Recursos/Atividades desenvolvidas", ""), r.get("Observação em sala", ""),
                r.get("Formação em serviço", ""), r.get("Diversos", ""), r.get("Presença", ""),
                r.get("Observações", ""), ""
            ]
            for i, val in enumerate(valores):
                row[i].text = str(val or "")
                for p in row[i].paragraphs:
                    for rr in p.runs:
                        rr.font.size = Pt(7)
    else:
        for _ in range(5):
            table.add_row()

    rod = doc.add_paragraph("*Este documento poderá ser editado ao longo do tempo para atender às necessidades e atualizações da atividade.")
    for r in rod.runs:
        r.font.size = Pt(7)

    doc.save(nome_arquivo)
    return nome_arquivo


def gerar_sugestao_ia_quadro_semanal(df_quadro, foco=""):
    client = obter_cliente_openai()
    if client is None:
        return "IA não configurada. Configure OPENAI_API_KEY para usar esta função."

    dados = df_quadro.to_string(index=False) if df_quadro is not None and not df_quadro.empty else "Nenhum dado encontrado."
    prompt = f"""
Você é um especialista em Atendimento Educacional Especializado (AEE).
Analise os registros de agenda/atendimentos abaixo e sugira um preenchimento objetivo para o Quadro de Acompanhamento Semanal do Professor do AEE.

REGRAS:
- Não invente dados pessoais.
- Use linguagem institucional e pedagógica.
- Considere presença automática: Compareceu, Faltou, Justificado, Cancelado ou Agendado.
- Para faltas, sugira observação breve e encaminhamento adequado.
- Para comparecimento, sintetize recursos utilizados, atividades e observações pedagógicas.
- Responda em formato de tabela textual com as colunas: Data | Recursos/Atividades | Outros atendimentos | Observações.

FOCO/ORIENTAÇÃO DO PROFESSOR:
{foco}

DADOS:
{dados}
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return resposta.output_text
    except Exception as e:
        return f"Não foi possível gerar sugestão com IA agora. Erro: {e}"


# ======================================================
# HISTÓRICO DE GERAÇÃO DOS DOCUMENTOS GRE
# ======================================================
def registrar_documento_gre(estudante_id, tipo_documento, nome_arquivo, observacao="Gerado sob demanda; arquivo não armazenado no banco."):
    """Registra apenas a data/tipo do documento GRE gerado.
    O conteúdo do PDF/Word não é armazenado para evitar dados sensíveis e excesso de arquivos.
    """
    inserir_registro(
        "documentos_gre_gerados",
        ["estudante_id", "tipo_documento", "nome_arquivo", "data_geracao", "observacao"],
        [estudante_id, tipo_documento, nome_arquivo, hoje_str(), observacao],
    )


@st.cache_data(ttl=30, show_spinner=False)
def listar_documentos_gre_gerados(estudante_id=None):
    conn = conectar()
    cursor = conn.cursor()
    if estudante_id:
        cursor.execute(
            """
            SELECT d.id, e.codigo, d.tipo_documento, d.nome_arquivo, d.data_geracao, d.observacao
            FROM documentos_gre_gerados d
            LEFT JOIN estudantes e ON e.id = d.estudante_id
            WHERE d.estudante_id = ?
            ORDER BY d.id DESC
            """,
            (estudante_id,),
        )
    else:
        cursor.execute(
            """
            SELECT d.id, e.codigo, d.tipo_documento, d.nome_arquivo, d.data_geracao, d.observacao
            FROM documentos_gre_gerados d
            LEFT JOIN estudantes e ON e.id = d.estudante_id
            ORDER BY d.id DESC
            LIMIT 50
            """
        )
    dados = cursor.fetchall()
    conn.close()
    return dados


def excluir_historico_documento_gre(registro_id):
    excluir_registro("documentos_gre_gerados", registro_id)


# ======================================================
# TEXTOS PARA EXPORTAÇÃO
# ======================================================
def texto_cadastro_estudante(estudante):
    return f"""
CADASTRO DO ESTUDANTE - INCLUISRM

Código interno: {estudante[1] or 'Não informado.'}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Turno: {estudante[6] or 'Não informado.'}
Perfil educacional: {estudante[4] or 'Não informado.'}
Dias de atendimento: {estudante[7] or 'Não informado.'}
Horário preferencial: {estudante[8] or 'Não informado.'}

Campos sensíveis para preenchimento manual:
Nome completo: ___________________________________________
CPF/RG: _________________________________________________
Data de nascimento: ______________________________________
Responsável: ____________________________________________
Telefone: _______________________________________________
Endereço: _______________________________________________

Observações pedagógicas:
{estudante[5] or 'Não informado.'}
""".strip()



def texto_matricula_srm(estudante):
    codigo = estudante[1] or "Não informado."
    ano_serie = estudante[2] or "Não informado."
    turma = estudante[3] or "Não informado."
    perfil = estudante[4] or "Não informado."
    observacoes = estudante[5] or "Não informado."
    turno = estudante[6] or "Não informado."
    dias = estudante[7] or "Não informado."
    horario = estudante[8] or "Não informado."

    return f"""
MATRÍCULA PARA O ATENDIMENTO EDUCACIONAL ESPECIALIZADO
SALA DE RECURSOS MULTIFUNCIONAIS - SRM

1. IDENTIFICAÇÃO DO ESTUDANTE

Código interno: {codigo}
Ano/Série: {ano_serie}
Turma: {turma}
Turno: {turno}
Perfil educacional informado: {perfil}
Dias preferenciais de atendimento: {dias}
Horário preferencial: {horario}

Professor(a) AEE responsável:
{texto_professores_vinculados(estudante[0])}

2. DADOS SENSÍVEIS PARA PREENCHIMENTO MANUAL

Nome completo do estudante: ___________________________________________

Data de nascimento: ____/____/________

CPF/RG do estudante: _________________________________________________

Nome do responsável: _________________________________________________

CPF/RG do responsável: _______________________________________________

Telefone: ___________________________________________________________

Endereço: ___________________________________________________________

3. INFORMAÇÕES PEDAGÓGICAS INICIAIS

Observações registradas no sistema:
{observacoes}

4. DECLARAÇÃO

Declaro ciência da matrícula do estudante acima identificado no Atendimento Educacional Especializado (AEE), na Sala de Recursos Multifuncionais - SRM, conforme organização pedagógica da unidade escolar e orientações da rede de ensino.

Data: ____/____/________


__________________________________________
Assinatura do responsável


__________________________________________
Professor(a) do Atendimento Educacional Especializado - AEE


__________________________________________
Gestão / Coordenação Pedagógica
""".strip()

def texto_professor(p):
    return f"""
FICHA DE IDENTIFICAÇÃO DO(A) PROFESSOR(A) AEE - INCLUISRM

Referência/Nome profissional: {p[1] or 'Não informado.'}
Escola: {p[2] or 'Não informado.'}
Regional/GRE: {p[3] or 'Não informado.'}
Formação: {p[4] or 'Não informado.'}
Carga horária: {p[5] or 'Não informado.'}
Turno de atuação: {p[6] or 'Não informado.'}
Data de cadastro: {p[8] or 'Não informado.'}

Observações:
{p[7] or 'Não informado.'}

Assinatura do(a) Professor(a) AEE:
________________________________________________________
""".strip()


def texto_avaliacao(estudante, a):
    dados = dict(zip(["id"] + CAMPOS_AVALIACAO, a))

    def v(campo):
        valor = dados.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    tipo = dados.get("tipo_registro") or ""

    if tipo == "Avaliação Pedagógica - Extra / Documento Livre":
        return f"""
AVALIAÇÃO PEDAGÓGICA EXTRA - DOCUMENTO LIVRE - INCLUISRM

Código interno do estudante: {estudante[1]}
Data do registro: {v('data_registro')}
Ano letivo: {v('ano_letivo')}
Tipo de registro: {v('tipo_registro')}
Avaliação anterior vinculada: {v('avaliacao_anterior_id')}
Origem do documento: {v('origem_documento')}

CONTEÚDO DO DOCUMENTO / RELATÓRIO ANTERIOR:

{v('texto_documento_extra')}

Observação:
Este registro foi lançado em formato livre para preservar documentos pedagógicos anteriores, pareceres, relatórios ou registros que não se enquadram no modelo estruturado da avaliação pedagógica.
""".strip()

    return f"""
AVALIAÇÃO PEDAGÓGICA - INCLUISRM

Código interno do estudante: {estudante[1]}
Data do registro: {v('data_registro')}
Ano letivo: {v('ano_letivo')}
Tipo de registro: {v('tipo_registro')}
Avaliação anterior vinculada: {v('avaliacao_anterior_id')}

Barreiras enfrentadas:
{v('barreiras')}

Potencialidades e habilidades:
{v('potencialidades')}

Comunicação:
{v('comunicacao')}

Interação social:
{v('interacao')}

Autonomia:
{v('autonomia')}

Aprendizagem:
{v('aprendizagem')}

Resumo pedagógico do laudo, sem identificação:
{v('resumo_laudo')}

Análise comparativa gerada com IA:
{v('analise_comparativa_ia')}

Sugestão de nova avaliação pedagógica gerada com IA:
{v('sugestao_nova_avaliacao_ia')}
""".strip()

def texto_entrevista(estudante, e):
    dados = dict(zip(CAMPOS_ENTREVISTA_FAMILIA, e[1:]))
    def v(campo):
        valor = dados.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    return f"""
ENTREVISTA COM A FAMÍLIA - INCLUISRM

Código interno do estudante: {estudante[1]}
Data do registro: {v('data_registro')}
Ano letivo: {v('ano_letivo')}
Tipo de registro: {v('tipo_registro')}

Campos sensíveis para preenchimento manual:
Nome do estudante: _______________________________________
Responsável: ____________________________________________
CPF do responsável: ______________________________________
Contato: ________________________________________________

1. INFORMAÇÕES DIVERSAS
Participa de programa de auxílio governamental: {v('auxilio_governamental')}
Qual(is): {v('auxilio_quais')}
Histórico familiar de doenças graves, deficiência ou transtornos: {v('historico_familiar')}
Qual(is): {v('historico_quais')}
Já repetiu de ano: {v('repetiu_ano')} | Quantas vezes: {v('repetiu_qtd')}
Trocou de escola: {v('trocou_escola')} | Quantas vezes: {v('trocou_qtd')}
Motivo da troca: {v('motivo_troca')}
Situação na escola: {v('situacao_escolar')}
Demonstra interesse em frequentar a escola: {v('interesse_escola')}
Cuida/organiza os materiais: {v('organiza_materiais')}
Apresenta resistência à escola: {v('resistencia_escola')}
Relaciona-se bem com colegas: {v('relacao_colegas')}
Relaciona-se bem com professores: {v('relacao_professores')}
Leva alimentação de casa: {v('leva_alimentacao')}
Alimenta-se da merenda escolar: {v('merenda_escolar')}
Possui alergia alimentar: {v('alergia_alimentar')}
Qual(is) alergias: {v('alergia_quais')}
Outras observações: {v('obs_diversas')}

1.1 SOBRE A ESCOLHA DA ESCOLA
Motivo da escolha da escola: {v('motivo_escolha')}
Outros motivos: {v('outros_motivos')}
O que conhece sobre o serviço do AEE: {v('conhecimento_aee')}

2. INFORMAÇÕES SOBRE A SAÚDE
Possui doença preexistente: {v('doenca_preexistente')}
Convulsões: {v('convulsoes')}
Acompanhamentos profissionais: {v('acompanhamentos')}
Outro acompanhamento: {v('acompanhamento_outro')}
Frequência dos acompanhamentos: {v('frequencia_acompanhamento')}
Outra frequência: {v('frequencia_outro')}
Alimentação saudável: {v('alimentacao_saudavel')}
Seletividade alimentar: {v('seletividade_alimentar')}
Dieta sensorial: {v('dieta_sensorial')}
Usa suplemento alimentar: {v('suplemento_alimentar')}
Qual suplemento: {v('suplemento_qual')}
Alimenta-se por sonda: {v('alimenta_sonda')}
Dorme bem: {v('dorme_bem')}
Faz uso de medicação: {v('medicacao')}
Qual(is) medicação(ões): {v('medicacao_qual')}
Tempo de uso/tratamentos realizados: {v('tempo_medicacao_tratamentos')}
Outras observações de saúde: {v('obs_saude')}

3. DESENVOLVIMENTO PSICOMOTOR
Lateralidade: {v('lateralidade')}
Apresenta estereotipias: {v('estereotipias')}
Qual(is): {v('estereotipias_quais')}
Segura objetos com as duas mãos: {v('segura_objetos_duas_maos')}
Tamanho dos objetos que segura: {v('tamanho_objetos')}
Faz a pega correta do lápis: {v('pega_lapis')}
Engatinhou: {v('engatinhou')}
Andou com que idade: {v('idade_andou')}
Usa fraldas na escola: {v('usa_fraldas')}
Usa sonda de alívio: {v('usa_sonda_alivio')}
O que consegue fazer sem ajuda: {v('autonomia_atividades')}
Outras atividades de autonomia: {v('autonomia_outros')}
Atende comandos: {v('atende_comandos')}
Gosta do toque: {v('gosta_toque')}
Outras observações psicomotoras: {v('obs_psicomotor')}

4. LINGUAGEM
É verbal: {v('verbal')}
Consegue se comunicar: {v('consegue_comunicar')}
Possui problemas na fala: {v('problemas_fala')}
Tem ecolalia: {v('ecolalia')}
Consegue dar recado: {v('da_recado')}
Usa comunicação alternativa: {v('comunicacao_alternativa')}
Qual comunicação alternativa: {v('comunicacao_alternativa_qual')}

5. SOCIALIZAÇÃO
Relaciona-se bem com o pai: {v('relacao_pai')}
Relaciona-se bem com a mãe: {v('relacao_mae')}
Relaciona-se bem com outros parentes: {v('relacao_parentes')}
Relaciona-se bem com irmãos: {v('relacao_irmaos')}
Relaciona-se bem com outros estudantes: {v('relacao_estudantes')}
Tem melhor amigo(a): {v('tem_melhor_amigo')}
Esse(a) melhor amigo(a) é: {v('tipo_melhor_amigo')}
Adapta-se facilmente ao ambiente: {v('adapta_ambiente')}
É flexível na rotina: {v('flexivel_rotina')}
Respeita regras: {v('respeita_regras')}
Chora com facilidade: {v('chora_facilidade')}
Gosta de brincar: {v('brinca_como')}
Assunto ou lazer de interesse: {v('interesses_lazer')}
O que a família mais gosta no(a) estudante: {v('familia_gosta')}
O que a família não gosta/necesita melhorar: {v('familia_nao_gosta')}
Ambiente físico em casa para estudos/brincadeiras: {v('ambiente_estudo_casa')}

6. CONTEXTO FAMILIAR
Principais habilidades:
{v('habilidades')}

Principais oportunidades de melhoria:
{v('oportunidades_melhoria')}

7. OUTRAS INFORMAÇÕES
{v('outras_info_familia')}

Assinatura do responsável:
________________________________________________________
""".strip()


def buscar_entrevista_familia_por_id(registro_id):
    """Busca uma entrevista familiar completa pelo ID, mantendo o formato (id, campos...)."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT id, {', '.join(CAMPOS_ENTREVISTA_FAMILIA)} FROM entrevistas_familia WHERE id=?",
        (registro_id,),
    )
    dado = cursor.fetchone()
    conn.close()
    return dado


def _normalizar_valor_comparacao(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    if texto.lower() in ["", "não informado", "nao informado", "none", "null"]:
        return ""
    return texto


def _dict_entrevista_familia(registro):
    if not registro:
        return {}
    return dict(zip(["id"] + CAMPOS_ENTREVISTA_FAMILIA, registro))


def gerar_relatorio_comparativo_entrevistas_familia(estudante, entrevista_anterior=None, entrevista_atual=None):
    """Gera relatório comparativo manual/regra de entrevistas familiares, sem IA.
    Objetivo: identificar mudanças no contexto familiar que possam influenciar participação,
    autorregulação, vínculo, rotina, saúde, socialização e aprendizagem.
    """
    registros = listar_por_estudante("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante[0])
    if not registros or len(registros) < 2:
        return f"""
RELATÓRIO COMPARATIVO DAS ENTREVISTAS COM A FAMÍLIA - INCLUISRM

Código interno do estudante: {estudante[1] or 'Não informado.'}

Ainda não há entrevistas familiares suficientes para comparação.
Registre pelo menos duas entrevistas, preferencialmente de anos letivos diferentes, para gerar uma análise comparativa.
""".strip()

    if entrevista_anterior is None or entrevista_atual is None:
        # Como listar_por_estudante retorna do mais recente para o mais antigo, usa as duas últimas registradas.
        entrevista_atual = registros[0]
        entrevista_anterior = registros[1]

    ant = _dict_entrevista_familia(entrevista_anterior)
    atu = _dict_entrevista_familia(entrevista_atual)

    rotulos = {
        "auxilio_governamental": "Participação em programa de auxílio governamental",
        "auxilio_quais": "Programas de auxílio informados",
        "historico_familiar": "Histórico familiar de doenças, deficiência ou transtornos",
        "historico_quais": "Históricos familiares informados",
        "repetiu_ano": "Repetência",
        "repetiu_qtd": "Quantidade de repetências",
        "trocou_escola": "Mudança de escola",
        "trocou_qtd": "Quantidade de mudanças de escola",
        "motivo_troca": "Motivo da troca de escola",
        "situacao_escolar": "Situação escolar",
        "interesse_escola": "Interesse em frequentar a escola",
        "organiza_materiais": "Organização dos materiais",
        "resistencia_escola": "Resistência à escola",
        "relacao_colegas": "Relação com colegas",
        "relacao_professores": "Relação com professores",
        "doenca_preexistente": "Doença preexistente",
        "convulsoes": "Convulsões",
        "acompanhamentos": "Acompanhamentos profissionais",
        "frequencia_acompanhamento": "Frequência dos acompanhamentos",
        "alimentacao_saudavel": "Alimentação saudável",
        "seletividade_alimentar": "Seletividade alimentar",
        "dieta_sensorial": "Dieta sensorial",
        "dorme_bem": "Sono",
        "medicacao": "Uso de medicação",
        "medicacao_qual": "Medicações informadas",
        "lateralidade": "Lateralidade",
        "estereotipias": "Estereotipias observadas",
        "autonomia_atividades": "Atividades de autonomia",
        "atende_comandos": "Atende comandos",
        "gosta_toque": "Aceitação do toque",
        "verbal": "Comunicação verbal",
        "consegue_comunicar": "Capacidade de comunicação",
        "problemas_fala": "Problemas na fala",
        "ecolalia": "Ecolalia",
        "comunicacao_alternativa": "Uso de comunicação alternativa",
        "relacao_pai": "Relação com o pai",
        "relacao_mae": "Relação com a mãe",
        "relacao_parentes": "Relação com outros parentes",
        "relacao_irmaos": "Relação com irmãos",
        "relacao_estudantes": "Relação com outros estudantes",
        "tem_melhor_amigo": "Presença de melhor amigo(a)",
        "adapta_ambiente": "Adaptação ao ambiente",
        "flexivel_rotina": "Flexibilidade na rotina",
        "respeita_regras": "Respeito às regras",
        "chora_facilidade": "Choro com facilidade",
        "brinca_como": "Forma de brincar",
        "interesses_lazer": "Interesses e lazer",
        "familia_gosta": "Aspectos que a família mais valoriza",
        "familia_nao_gosta": "Aspectos que a família aponta para melhorar",
        "ambiente_estudo_casa": "Ambiente físico em casa para estudo/brincadeiras",
        "habilidades": "Habilidades percebidas pela família",
        "oportunidades_melhoria": "Oportunidades de melhoria percebidas pela família",
        "outras_info_familia": "Outras informações familiares relevantes",
    }

    campos_ignorar = {"id", "data_registro", "ano_letivo", "tipo_registro"}
    campos_sensiveis_pedagogicos = {
        "relacao_pai", "relacao_mae", "relacao_parentes", "relacao_irmaos",
        "ambiente_estudo_casa", "familia_gosta", "familia_nao_gosta", "outras_info_familia",
        "interesse_escola", "resistencia_escola", "chora_facilidade", "flexivel_rotina",
        "dorme_bem", "medicacao", "medicacao_qual", "seletividade_alimentar",
        "acompanhamentos", "interesses_lazer", "adapta_ambiente"
    }

    alteracoes = []
    destaques = []
    for campo in CAMPOS_ENTREVISTA_FAMILIA:
        if campo in campos_ignorar:
            continue
        valor_ant = _normalizar_valor_comparacao(ant.get(campo))
        valor_atu = _normalizar_valor_comparacao(atu.get(campo))
        if valor_ant != valor_atu:
            rotulo = rotulos.get(campo, campo.replace("_", " ").capitalize())
            linha = f"- {rotulo}: antes: {valor_ant or 'não informado'} | atual: {valor_atu or 'não informado'}"
            alteracoes.append(linha)
            if campo in campos_sensiveis_pedagogicos:
                destaques.append(linha)

    if alteracoes:
        texto_alteracoes = "\n".join(alteracoes)
    else:
        texto_alteracoes = "Não foram identificadas alterações objetivas nos campos comparados."

    if destaques:
        texto_destaques = "\n".join(destaques)
    else:
        texto_destaques = "Não foram identificadas alterações em campos familiares de maior impacto pedagógico imediato."

    return f"""
RELATÓRIO COMPARATIVO DAS ENTREVISTAS COM A FAMÍLIA - INCLUISRM

Código interno do estudante: {estudante[1] or 'Não informado.'}
Ano/Série atual: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Perfil educacional informado: {estudante[4] or 'Não informado.'}

Entrevista anterior:
- ID do registro: {ant.get('id') or 'Não informado.'}
- Data do registro: {ant.get('data_registro') or 'Não informado.'}
- Ano letivo: {ant.get('ano_letivo') or 'Não informado.'}
- Tipo de registro: {ant.get('tipo_registro') or 'Não informado.'}

Entrevista atual/comparada:
- ID do registro: {atu.get('id') or 'Não informado.'}
- Data do registro: {atu.get('data_registro') or 'Não informado.'}
- Ano letivo: {atu.get('ano_letivo') or 'Não informado.'}
- Tipo de registro: {atu.get('tipo_registro') or 'Não informado.'}

1. OBJETIVO DO RELATÓRIO
Este relatório compara entrevistas familiares registradas em momentos diferentes, com o objetivo de identificar alterações no contexto familiar, na rotina, na saúde, na socialização, na comunicação, na autonomia e nas condições de apoio ao estudante. A comparação apoia a leitura pedagógica do professor do AEE, especialmente quando mudanças familiares podem influenciar autorregulação, comportamento, participação escolar, vínculo afetivo, aprendizagem e necessidade de acolhimento.

2. ALTERAÇÕES IDENTIFICADAS ENTRE AS ENTREVISTAS
{texto_alteracoes}

3. CAMPOS DE ATENÇÃO PEDAGÓGICA E FAMILIAR
{texto_destaques}

4. LEITURA PEDAGÓGICA PARA ACOMPANHAMENTO
As alterações registradas devem ser analisadas com cuidado pelo professor do AEE, em diálogo com a família, equipe pedagógica e professores da sala comum. Mudanças como perda de familiar, alteração de moradia, novos responsáveis, conflitos familiares, mudança no sono, alimentação, medicação, humor, rotina ou vínculo podem repercutir diretamente na participação do estudante, na autorregulação emocional e na resposta às intervenções pedagógicas.

5. ENCAMINHAMENTOS SUGERIDOS PARA REGISTRO MANUAL
- Verificar se as alterações familiares coincidem com mudanças no comportamento, frequência, participação ou desempenho escolar.
- Registrar observações nos atendimentos do AEE, especialmente sinais de desregulação, isolamento, agitação, tristeza, resistência à escola ou mudança na interação social.
- Dialogar com a família para compreender melhor o contexto atual, sem exposição de dados sensíveis.
- Atualizar, se necessário, a Avaliação Pedagógica, o Estudo de Caso e o Plano AEE/PAEE.
- Acionar a equipe pedagógica ou rede de apoio da escola quando houver necessidade de acolhimento, cuidado emocional ou acompanhamento intersetorial.

6. OBSERVAÇÃO IMPORTANTE
Este relatório pode ser gerado em modo comparativo manual/regra ou com apoio de IA na etapa de análise. A entrevista familiar permanece sempre como registro manual e fiel ao que foi informado pela família; a IA não cria, altera nem preenche entrevistas. Quando utilizada, a IA apenas apoia a leitura comparativa para subsidiar a decisão pedagógica do professor do AEE.

Professor(a) AEE: _______________________________________
Coordenação/Gestão: _____________________________________
Data: ____/____/________
""".strip()


def gerar_analise_ia_comparativo_entrevistas_familia(estudante, entrevista_anterior=None, entrevista_atual=None, observacao_professor=""):
    """Gera análise comparativa com IA a partir de duas entrevistas familiares.
    A IA NÃO cria nem altera entrevistas; apenas analisa diferenças para apoiar o AEE.
    """
    client = obter_cliente_openai()
    if client is None:
        return "IA não configurada. Configure OPENAI_API_KEY para usar esta função."

    if entrevista_anterior is None or entrevista_atual is None:
        return "Selecione duas entrevistas familiares diferentes para gerar a análise com IA."

    ant = _dict_entrevista_familia(entrevista_anterior)
    atu = _dict_entrevista_familia(entrevista_atual)
    relatorio_base = gerar_relatorio_comparativo_entrevistas_familia(
        estudante,
        entrevista_anterior=entrevista_anterior,
        entrevista_atual=entrevista_atual,
    )

    prompt = f"""
Você é especialista em Atendimento Educacional Especializado (AEE), educação inclusiva e análise pedagógica contextual.

TAREFA:
Analise comparativamente duas entrevistas familiares do mesmo estudante.

REGRA CENTRAL:
A IA NÃO deve criar, alterar, complementar ou inventar dados da entrevista familiar.
A entrevista é um registro manual e fiel ao que a família informou.
Sua função é apenas analisar as diferenças entre os registros e apoiar a leitura pedagógica do professor do AEE.

IDENTIFICAÇÃO NÃO SENSÍVEL DO ESTUDANTE:
Código interno: {estudante[1] or 'Não informado'}
Ano/Série: {estudante[2] or 'Não informado'}
Turma: {estudante[3] or 'Não informado'}
Perfil educacional informado: {estudante[4] or 'Não informado'}

ENTREVISTA ANTERIOR / BASE:
{ant}

ENTREVISTA ATUAL / COMPARADA:
{atu}

RELATÓRIO COMPARATIVO BASE GERADO PELO SISTEMA:
{relatorio_base}

OBSERVAÇÃO DO PROFESSOR DO AEE PARA ORIENTAR A ANÁLISE:
{observacao_professor or 'Não informada.'}

RESPONDA EM LINGUAGEM INSTITUCIONAL, CUIDADOSA E PEDAGÓGICA, COM AS SEÇÕES:
1. Síntese comparativa geral
2. Mudanças na estrutura familiar e rede de apoio
3. Mudanças na rotina, saúde, sono, alimentação ou acompanhamento
4. Possíveis sinais de desregulação observáveis no contexto escolar
5. Possíveis avanços ou fatores de proteção
6. Pontos de atenção para o professor do AEE
7. Sugestões pedagógicas de acompanhamento, sem diagnóstico clínico
8. Cuidados éticos: dados que precisam ser confirmados com família/equipe antes de qualquer encaminhamento

LIMITES:
- Não diagnosticar.
- Não afirmar causalidade sem evidência.
- Não expor dados sensíveis desnecessários.
- Não inventar fatos.
- Usar expressões como “pode indicar”, “sugere atenção”, “recomenda-se observar”, quando houver incerteza.
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return resposta.output_text
    except Exception as e:
        return f"Não foi possível gerar a análise comparativa com IA agora. Erro: {e}"


def texto_campos_sensiveis_em_branco_estudante():
    return """
DADOS SENSÍVEIS PARA PREENCHIMENTO MANUAL NO DOCUMENTO IMPRESSO/WORD
Nome completo do(a) estudante: ___________________________________________
CPF/RG do(a) estudante: _________________________________________________
Data de nascimento: ____/____/________
Nome do responsável: _________________________________________________
CPF/RG do responsável: _______________________________________________
Telefone do responsável: ______________________________________________
Endereço: ____________________________________________________________
""".strip()


def texto_estudo_caso(estudante, e):
    """Texto oficial do Estudo de Caso no formato GRE, sem armazenar dados sensíveis."""
    # Compatibilidade com estudos antigos: e = (id, data, contextualizacao, queixa, ...)
    if len(e) <= 10:
        return f"""
ESTUDO DE CASO - INCLUISRM

Código interno do estudante: {estudante[1]}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Perfil educacional: {estudante[4] or 'Não informado.'}
Data do registro: {e[1]}

{texto_campos_sensiveis_em_branco_estudante()}

1. Contextualização
{e[2] or 'Não informado.'}

2. Queixa principal / motivo do acompanhamento
{e[3] or 'Não informado.'}

3. Potencialidades
{e[4] or 'Não informado.'}

4. Dificuldades observadas
{e[5] or 'Não informado.'}

5. Estratégias pedagógicas
{e[6] or 'Não informado.'}

6. Intervenções / encaminhamentos sugeridos
{e[7] or 'Não informado.'}

7. Avaliação
{e[8] or 'Não informado.'}

8. Considerações finais
{e[9] or 'Não informado.'}

Assinaturas:
Professor(a) AEE: _______________________________________
Coordenação/Gestão: _____________________________________
""".strip()

    dados = dict(zip(CAMPOS_ESTUDO_CASO, e[1:]))

    def v(campo):
        valor = dados.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    return f"""
ESTUDO DE CASO E PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO - INCLUISRM

O Plano de Atendimento Educacional Especializado deverá considerar os registros avaliativos do estudante público-alvo da educação especial, partindo do estudo de caso e da identificação de barreiras, recursos de acessibilidade e estratégias necessárias à promoção da autonomia e da aprendizagem.

PARTE 1 - IDENTIFICAÇÃO SEGURA DO(A) ESTUDANTE
Código interno do estudante: {estudante[1] or 'Não informado.'}
Ano/Série cadastrado no sistema: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Turno: {estudante[6] or 'Não informado.'}
Perfil educacional: {estudante[4] or 'Não informado.'}
Ano letivo do estudo de caso: {v('ano_letivo')}
Tipo de registro: {v('tipo_registro')}

{texto_campos_sensiveis_em_branco_estudante()}

1.5 Etapa/modalidade da educação em que o(a) estudante está: {v('etapa_modalidade')}
Ano/etapa: {v('ano_etapa')}
1.6 Turma e turno: {estudante[3] or 'Não informado.'} / {estudante[6] or 'Não informado.'}
1.7 O(a) estudante apresenta laudo? {v('laudo')}
1.8 Apresenta deficiência? {v('deficiencia')} | CID: {v('cid')}
Síntese pedagógica/funcional do laudo: {v('observacoes_laudo')}
1.9 Altas habilidades/superdotação: {v('altas_habilidades')}
1.10 Usuário de BPC: {v('bpc')}
1.11 Escola do ensino comum: {v('escola_nome')}
1.12 Unidade educacional onde é atendido pelo AEE: {v('unidade_aee')}
1.13 Gestor(a) da escola do ensino comum e contato: {v('gestor_nome')} - {v('gestor_contato')}
1.14 Professor(a) do AEE e contato: {v('professor_nome')} - {v('professor_contato')}
1.15 Matrícula do(a) professor(a) do AEE: {v('matricula_professor')}
1.16 Especialidade do(a) professor(a) do AEE: {v('especialidade_professor')}
1.17 Período de elaboração do Plano/AEE - início: {v('periodo_inicio')}
1.18 Data final: {v('periodo_fim')}
1.19 Frequência de atendimento na SRM: {v('frequencia_atendimento')}
1.20 Tempo de atendimento por semana: {v('tempo_atendimento_semana')}
1.21 Formato do atendimento: {v('formato_atendimento')}

2. ESTUDO DE CASO / PERCURSO EDUCACIONAL DO(A) ESTUDANTE
Relato sobre o trajeto educacional do(a) estudante em turmas comuns e no Atendimento Educacional Especializado anterior, quando aplicável:
{v('percurso_educacional')}

2.1 Motivo pelo qual o(a) estudante foi encaminhado para o Atendimento Educacional Especializado:
{v('motivo_encaminhamento_aee')}

2.2 Precisa de transporte escolar inclusivo? {v('precisa_transporte_inclusivo')}
2.2.1 Recebe o serviço de transporte escolar inclusivo? {v('recebe_transporte_inclusivo')}

2.3 Precisa de profissional de apoio? {v('precisa_profissional_apoio')}
Justificativa:
{v('justificativa_apoio')}

2.3.1 É acompanhado por profissional de apoio na escola? {v('acompanhado_profissional_apoio')}
Nome do profissional de apoio: {v('nome_profissional_apoio')}

2.4 Recursos de tecnologia educacional e/ou assistiva utilizados:
{v('recursos_tecnologia_assistiva')}

2.5 Observações relevantes para o ambiente educacional, acompanhamento médico ou terapêutico:
{v('observacoes_ambiente_educacional')}

2.6 Habilidades observadas e desenvolvidas pelo(a) estudante:
{v('habilidades_observadas')}

2.7 Habilidades que precisam ser desenvolvidas pelo(a) estudante:
{v('habilidades_a_desenvolver')}

2.8 Indicadores de altas habilidades/superdotação observados:
{v('indicadores_altas_habilidades')}

2.9 Caso o estudante seja pessoa surda, recursos utilizados:
{v('recursos_surdez')}
Observações sobre uso de aparelho auditivo, implante coclear, Libras, comunicação e efetividade dos recursos:
{v('observacoes_surdez')}

SÍNTESE PEDAGÓGICA DO ESTUDO DE CASO
Contextualização:
{v('contextualizacao')}

Potencialidades:
{v('potencialidades')}

Dificuldades/barreiras observadas:
{v('dificuldades')}

Estratégias pedagógicas:
{v('estrategias')}

Intervenções/encaminhamentos sugeridos:
{v('intervencoes')}

Avaliação:
{v('avaliacao')}

Considerações finais:
{v('consideracoes')}

ANÁLISE COMPARATIVA GERADA COM APOIO DA IA
{v('analise_comparativa_ia')}

SUGESTÃO DE NOVO ESTUDO DE CASO GERADA COM APOIO DA IA
{v('sugestao_novo_estudo_ia')}

Assinaturas:
Professor(a) AEE: _______________________________________
Coordenação/Gestão: _____________________________________
Responsável: ____________________________________________
""".strip()


def texto_plano_aee(estudante, p):
    """Gera o texto do Plano AEE/PAEE manual com todos os campos do modelo GRE.
    Aceita registros antigos e novos para evitar erro em bancos já existentes.
    """
    campos_antigos = [
        "data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias",
        "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias",
        "avaliacao_acompanhamento", "observacoes",
    ]

    valores = list(p[1:]) if p and len(p) > 1 else []
    if len(valores) == len(CAMPOS_PLANO_AEE):
        dados = dict(zip(CAMPOS_PLANO_AEE, valores))
    else:
        dados = dict(zip(campos_antigos, valores))

    def v(campo):
        valor = dados.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    # Compatibilidade: se o banco antigo ainda tinha organização_atendimento,
    # esse conteúdo aparece como observação complementar.
    organizacao_antiga = dados.get("organizacao_atendimento")
    observacoes_extra = v("observacoes")
    if organizacao_antiga not in (None, ""):
        observacoes_extra = f"{observacoes_extra}\n\nOrganização do atendimento:\n{organizacao_antiga}"

    return f"""
PLANO AEE / PAEE - INCLUISRM

Código interno do estudante: {estudante[1]}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Perfil educacional: {estudante[4] or 'Não informado.'}
Data do registro: {v('data_registro')}

1. Habilidades específicas
1.1 Habilidades prioritárias que serão trabalhadas na SRM
{v('habilidades_prioritarias')}

1.2 Recursos de acessibilidade que serão disponibilizados ao estudante
{v('recursos_acessibilidade')}

2. Objetivos do Atendimento Educacional Especializado
2.1 Geral
{v('objetivos_gerais')}

2.2 Específicos
{v('objetivos_especificos')}

3. Metodologias e estratégias
3.1 Metodologia
{v('metodologia')}

3.2 Estratégia
{v('estrategias')}

3.3 Prazo
{v('prazo')}

4. Ações desenvolvidas no âmbito da escola
{v('acoes_escola')}

5. Barreiras identificadas na comunidade escolar
{v('barreiras_identificadas')}

6. Parcerias realizadas pelo AEE ao longo do período
{v('parcerias')}

7. Avaliação
{v('avaliacao_acompanhamento')}

8. Observações
{observacoes_extra}

Assinaturas:
Professor(a) AEE: _______________________________________
Coordenação/Gestão: _____________________________________
Responsável: ____________________________________________
""".strip()


def texto_atendimento(estudante, a):
    return f"""
REGISTRO DE ATENDIMENTO DO AEE - INCLUISRM

Código interno: {estudante[1]}
Data do atendimento: {a[1]}

Objetivo trabalhado:
{a[2] or 'Não informado.'}

Atividade realizada:
{a[3] or 'Não informado.'}

Resposta do estudante:
{a[4] or 'Não informado.'}

Avanços observados:
{a[5] or 'Não informado.'}

Dificuldades observadas:
{a[6] or 'Não informado.'}

Evolução observada:
{a[7] or 'Não informado.'}

Indicadores:
Resposta do estudante: {a[9]}/10
Avanço pedagógico: {a[10]}/10
Nível de dificuldade/barreira: {a[11]}/10
Engajamento: {a[12]}/10
Índice geral de evolução: {a[13]}/10

Encaminhamentos:
{a[14] or 'Não informado.'}

Materiais/recursos pedagógicos utilizados no atendimento:
{texto_recursos_atendimento(a[0])}
""".strip()


def texto_agenda(df):
    if df.empty:
        return "AGENDA DE ATENDIMENTOS - INCLUISRM\n\nNenhum agendamento registrado."
    return "AGENDA DE ATENDIMENTOS - INCLUISRM\n\n" + df.to_string(index=False)


# ======================================================
# PDF
# ======================================================
def gerar_pdf_documento(conteudo, codigo, tipo="documento"):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Image

    nomes = {
        "cadastro": ("Cadastro_Estudante", "CADASTRO DO ESTUDANTE"),
        "matricula_srm": ("Matricula_SRM", "MATRÍCULA PARA O ATENDIMENTO EDUCACIONAL ESPECIALIZADO - SRM"),
        "professor": ("Ficha_Professor_AEE", "FICHA DE IDENTIFICAÇÃO DO(A) PROFESSOR(A) AEE"),
        "entrevista": ("Entrevista_Familia", "ENTREVISTA COM A FAMÍLIA"),
        "avaliacao": ("Avaliacao_Pedagogica", "AVALIAÇÃO PEDAGÓGICA INICIAL"),
        "estudo": ("Estudo_Pedagogico", "ESTUDO PEDAGÓGICO DO ESTUDANTE - AEE"),
        "plano": ("Plano_AEE_PAEE", "PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO - AEE"),
        "atendimento": ("Registro_Atendimento", "REGISTRO DE ATENDIMENTO DO AEE"),
        "agenda": ("Agenda_Atendimentos", "AGENDA DE ATENDIMENTOS"),
        "relatorio": ("Relatorio_GRE", "RELATÓRIO GRE"),
        "documento": ("Documento", "DOCUMENTO"),
    }
    prefixo, titulo_doc = nomes.get(tipo, nomes["documento"])
    nome_arquivo = f"{prefixo}_{codigo}.pdf".replace("/", "-").replace("\\", "-")

    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        name="Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=15,
        leading=20,
        spaceAfter=14,
        textColor=colors.black,
    )
    secao_style = ParagraphStyle(
        name="Secao",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=9,
        spaceAfter=5,
        textColor=colors.darkblue,
    )
    normal_style = ParagraphStyle(
        name="NormalCustom",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    rodape_style = ParagraphStyle(
        name="Rodape",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceBefore=18,
    )

    elementos = []
    try:
        logo = Image(LOGO_PATH, width=160, height=80)
        logo.hAlign = "CENTER"
        elementos.append(logo)
        elementos.append(Spacer(1, 8))
    except Exception:
        elementos.append(Paragraph("<b>INCLUISRM</b>", titulo_style))

    elementos.append(Paragraph("<b>INCLUISRM<br/>Sistema de Gestão do Atendimento Educacional Especializado</b>", normal_style))
    elementos.append(Spacer(1, 8))
    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(titulo_doc, titulo_style))
    elementos.append(Spacer(1, 12))

    for linha in conteudo.split("\n"):
        linha = linha.strip()
        if not linha:
            elementos.append(Spacer(1, 6))
            continue
        linha_html = escape(linha)
        if linha.startswith("#"):
            elementos.append(Paragraph(f"<b>{escape(linha.replace('#','').strip())}</b>", secao_style))
        elif linha[:2].isdigit() and "." in linha[:4]:
            elementos.append(Paragraph(f"<b>{linha_html}</b>", secao_style))
        elif linha.startswith("-"):
            elementos.append(Paragraph(f"• {escape(linha[1:].strip())}", normal_style))
        else:
            elementos.append(Paragraph(linha_html, normal_style))

    elementos.append(Spacer(1, 18))
    elementos.append(Paragraph(f"Gerado em {agora_local().strftime('%d/%m/%Y %H:%M')} pelo INCLUISRM.", rodape_style))
    doc.build(elementos)
    return nome_arquivo


# ======================================================
# IA + BASE DE CONHECIMENTO + MODELOS 3D
# ======================================================
def obter_api_key():
    try:
        return os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return os.getenv("OPENAI_API_KEY")


def obter_cliente_openai():
    api_key = obter_api_key()
    if OpenAI is None or not api_key:
        return None
    return OpenAI(api_key=api_key)


def extrair_secao_ia(texto, marcador, padrao=""):
    """Extrai uma seção marcada no texto da IA.
    Ex.: [PERCURSO_EDUCACIONAL] ... [PROXIMA_SECAO]
    """
    try:
        padrao_regex = rf"\[{re.escape(marcador)}\](.*?)(?=\n\[[A-Z0-9_]+\]|\Z)"
        m = re.search(padrao_regex, texto or "", flags=re.DOTALL)
        if not m:
            return padrao
        return m.group(1).strip()
    except Exception:
        return padrao


def gerar_novo_estudo_caso_com_ia(estudante, estudo_anterior=None, avaliacao=None, entrevista=None, atendimentos=None, ano_novo="", avaliacoes_contexto=None):
    """Gera análise comparativa e proposta de Estudo de Caso no padrão GRE.
    A resposta é apoio pedagógico: não substitui a avaliação do professor do AEE.
    """
    client = obter_cliente_openai()
    if client is None:
        sugestao_fallback = """
[PERCURSO_EDUCACIONAL]
Preencher com relato sobre o trajeto educacional do(a) estudante, situação inicial, estratégias utilizadas e progressos alcançados em turmas comuns e no AEE, quando houver.

[MOTIVO_ENCAMINHAMENTO]
Preencher com o motivo pedagógico do encaminhamento ao Atendimento Educacional Especializado.

[HABILIDADES_OBSERVADAS]
Preencher com habilidades observadas e desenvolvidas pelo(a) estudante.

[HABILIDADES_A_DESENVOLVER]
Preencher com habilidades que precisam ser desenvolvidas ou reforçadas.

[POTENCIALIDADES]
Preencher com potencialidades observadas nas avaliações pedagógicas, atendimentos e escutas docentes.

[DIFICULDADES]
Preencher com barreiras pedagógicas, comunicacionais, curriculares, atitudinais ou de participação observadas.

[ESTRATEGIAS]
Preencher com estratégias pedagógicas recomendadas para favorecer participação, autonomia e aprendizagem.

[INTERVENCOES]
Preencher com intervenções, recursos e encaminhamentos pedagógicos sugeridos.

[AVALIACAO]
Preencher com avanços, habilidades a reforçar e efetividade das ações realizadas.

[CONSIDERACOES]
Preencher com síntese final do estudo de caso, mantendo linguagem pedagógica e institucional.

[OBSERVACOES_COMPLEMENTARES]
Registrar informações relevantes que não se encaixam nos campos anteriores.
""".strip()
        return "IA não configurada. Configure OPENAI_API_KEY para gerar automaticamente. O sistema preparou um modelo GRE para preenchimento manual.", sugestao_fallback

    texto_estudo_anterior = texto_estudo_caso(estudante, estudo_anterior) if estudo_anterior else "Nenhum estudo anterior selecionado."

    # Usa a avaliação selecionada como principal e também considera todas as demais avaliações
    # pedagógicas/documentos livres existentes para construir uma memória pedagógica mais completa.
    avaliacoes_contexto = avaliacoes_contexto or []
    textos_avaliacoes = []
    ids_avaliacoes_usadas = set()

    if avaliacao:
        try:
            textos_avaliacoes.append("AVALIAÇÃO PRINCIPAL SELECIONADA:\n" + texto_avaliacao(estudante, avaliacao))
            ids_avaliacoes_usadas.add(avaliacao[0])
        except Exception:
            textos_avaliacoes.append("AVALIAÇÃO PRINCIPAL SELECIONADA:\n" + str(avaliacao))

    for av in avaliacoes_contexto[:8]:
        if av and av[0] not in ids_avaliacoes_usadas:
            try:
                textos_avaliacoes.append("AVALIAÇÃO COMPLEMENTAR / DOCUMENTO LIVRE:\n" + texto_avaliacao(estudante, av))
            except Exception:
                textos_avaliacoes.append("AVALIAÇÃO COMPLEMENTAR / DOCUMENTO LIVRE:\n" + str(av))

    texto_avaliacao_ctx = "\n\n---\n\n".join(textos_avaliacoes) if textos_avaliacoes else "Nenhuma avaliação pedagógica selecionada ou registrada."
    texto_entrevista = str(entrevista or "Nenhuma entrevista com família localizada.")
    texto_atendimentos = "\n".join([str(a) for a in (atendimentos or [])[:12]]) or "Nenhum atendimento registrado."

    prompt = f"""
Você é um especialista em Atendimento Educacional Especializado (AEE), educação inclusiva e elaboração de Estudo de Caso no padrão usado por GRE/Secretarias de Educação.

TAREFA:
Gerar uma proposta de ESTUDO DE CASO padronizado, com base nos registros disponíveis do sistema.

REGRAS OBRIGATÓRIAS:
- Não inventar dados pessoais, nomes, diagnósticos, laudos, CPF, RG, endereço ou telefone.
- Não usar linguagem médica como conclusão diagnóstica.
- Usar linguagem pedagógica, institucional, objetiva e acolhedora.
- Se alguma informação não estiver disponível, deixar o campo com orientação de preenchimento posterior.
- Usar estudo de caso anterior, se houver.
- Se não houver estudo anterior, usar avaliações pedagógicas e demais registros como base.
- Se algo não couber nos campos padronizados, colocar em OBSERVAÇÕES_COMPLEMENTARES.
- Gerar texto para revisão do professor do AEE antes de salvar.

ESTUDANTE:
Código interno: {estudante[1]}
Ano/Série atual: {estudante[2]}
Turma: {estudante[3]}
Perfil educacional cadastrado: {estudante[4]}
Ano letivo do novo estudo: {ano_novo}

ESTUDO DE CASO ANTERIOR:
{texto_estudo_anterior}

AVALIAÇÕES PEDAGÓGICAS / DOCUMENTOS LIVRES:
{texto_avaliacao_ctx}

ENTREVISTA COM A FAMÍLIA:
{texto_entrevista}

ATENDIMENTOS REGISTRADOS:
{texto_atendimentos}

Responda exatamente com as seções abaixo, mantendo os marcadores:

[ANALISE_COMPARATIVA]
Comparar registros anteriores e atuais, destacando evolução, permanências, barreiras, avanços e pontos de atenção. Se não houver estudo anterior, explicar que a proposta foi criada a partir de avaliações pedagógicas e demais registros.

[PERCURSO_EDUCACIONAL]
Texto para o campo “Estudo de caso / percurso educacional”, relatando trajetória escolar, situação inicial, estratégias utilizadas e progressos alcançados.

[MOTIVO_ENCAMINHAMENTO]
Motivo pedagógico do encaminhamento ao AEE, sem diagnóstico clínico conclusivo.

[HABILIDADES_OBSERVADAS]
Lista ou parágrafo com habilidades observadas e desenvolvidas.

[HABILIDADES_A_DESENVOLVER]
Lista ou parágrafo com habilidades que precisam ser desenvolvidas.

[POTENCIALIDADES]
Potencialidades pedagógicas, interesses, formas de participação e respostas positivas observadas.

[DIFICULDADES]
Dificuldades e barreiras pedagógicas observadas.

[ESTRATEGIAS]
Estratégias pedagógicas recomendadas.

[INTERVENCOES]
Intervenções, recursos de acessibilidade, recursos pedagógicos e encaminhamentos sugeridos.

[AVALIACAO]
Texto avaliativo sobre avanços, habilidades a reforçar e ações para eliminação de barreiras.

[CONSIDERACOES]
Síntese pedagógica final para compor o estudo de caso.

[OBSERVACOES_COMPLEMENTARES]
Informações relevantes que não se encaixaram nos campos anteriores.
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        texto = resposta.output_text or ""
        analise = extrair_secao_ia(texto, "ANALISE_COMPARATIVA", texto)
        return analise.strip(), texto.strip()
    except Exception as e:
        return "", f"Não foi possível gerar o novo estudo de caso com IA agora. Erro: {e}"

def gerar_nova_avaliacao_pedagogica_com_ia(estudante, avaliacao_anterior=None, estudo_caso=None, entrevista=None, atendimentos=None, ano_novo=""):
    """Gera análise comparativa e sugestão de nova Avaliação Pedagógica com IA.
    A resposta é apoio pedagógico: não substitui a avaliação do professor do AEE.
    """
    client = obter_cliente_openai()
    if client is None:
        return "", "IA não configurada. Configure OPENAI_API_KEY para usar esta função."

    texto_avaliacao_anterior = texto_avaliacao(estudante, avaliacao_anterior) if avaliacao_anterior else "Nenhuma avaliação anterior selecionada."
    texto_estudo = texto_estudo_caso(estudante, estudo_caso) if estudo_caso else "Nenhum estudo de caso localizado."
    texto_entrevista = str(entrevista or "Nenhuma entrevista com família localizada.")
    texto_atendimentos = "\n".join([str(a) for a in (atendimentos or [])[:12]]) or "Nenhum atendimento registrado."

    prompt = f"""
Você é um especialista em Atendimento Educacional Especializado (AEE) e em avaliação pedagógica inclusiva.
Analise os registros abaixo e produza uma resposta institucional, pedagógica e objetiva para apoiar o professor do AEE na construção de uma nova Avaliação Pedagógica.

REGRAS IMPORTANTES:
- Não invente dados pessoais nem diagnósticos.
- Não substitua a decisão pedagógica do professor.
- Trabalhe apenas com os dados fornecidos.
- Use linguagem adequada para documento escolar.
- Foque em barreiras, potencialidades, comunicação, interação social, autonomia, aprendizagem e recomendações pedagógicas.
- Sugira recursos acessíveis, atividades pedagógicas, recursos maker/3D quando coerente e atividades plugadas/desplugadas.
- Evite termos clínicos conclusivos; mantenha foco educacional.

ESTUDANTE:
Código interno: {estudante[1]}
Ano/Série atual: {estudante[2]}
Turma: {estudante[3]}
Perfil educacional: {estudante[4]}
Ano letivo da nova avaliação: {ano_novo}

AVALIAÇÃO PEDAGÓGICA ANTERIOR:
{texto_avaliacao_anterior}

ESTUDO DE CASO DISPONÍVEL:
{texto_estudo}

ENTREVISTA COM A FAMÍLIA:
{texto_entrevista}

ATENDIMENTOS REGISTRADOS:
{texto_atendimentos}

Responda exatamente com duas seções:

[ANALISE_COMPARATIVA]
Texto comparando a avaliação anterior com os registros atuais, destacando avanços, permanências, novas barreiras, potencialidades e pontos de atenção.

[SUGESTAO_NOVA_AVALIACAO]
Proposta inicial de nova Avaliação Pedagógica, organizada nos tópicos: barreiras enfrentadas, potencialidades e habilidades, comunicação, interação social, autonomia, aprendizagem, resumo pedagógico e recomendações para intervenção no AEE.
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        texto = resposta.output_text or ""
        analise = texto
        sugestao = texto
        if "[SUGESTAO_NOVA_AVALIACAO]" in texto:
            partes = texto.split("[SUGESTAO_NOVA_AVALIACAO]", 1)
            analise = partes[0].replace("[ANALISE_COMPARATIVA]", "").strip()
            sugestao = partes[1].strip()
        return analise.strip(), sugestao.strip()
    except Exception as e:
        return "", f"Não foi possível gerar a nova avaliação pedagógica com IA agora. Erro: {e}"


# ======================================================
# BASE DE CONHECIMENTO IA - PDFs + CHROMADB
# ======================================================
def listar_pdfs_base(pasta):
    """Lista arquivos PDF de uma pasta da base de conhecimento."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    return sorted(list(pasta.glob("*.pdf")))


def extrair_texto_pdf(caminho_pdf):
    """Extrai texto de um PDF usando pypdf."""
    from pypdf import PdfReader

    partes = []
    reader = PdfReader(str(caminho_pdf))

    for i, pagina in enumerate(reader.pages):
        texto = pagina.extract_text() or ""
        if texto.strip():
            partes.append(f"\n--- Arquivo: {caminho_pdf.name} | Página {i + 1} ---\n{texto}")

    return "\n".join(partes).strip()


def quebrar_texto(texto, tamanho=1200, sobreposicao=200):
    """Divide textos longos em partes menores para busca semântica."""
    if not texto:
        return []

    partes = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho
        parte = texto[inicio:fim].strip()
        if parte:
            partes.append(parte)
        inicio = max(fim - sobreposicao, fim)
    return partes


def criar_embedding(textos):
    """Cria embeddings com OpenAI."""
    client = obter_cliente_openai()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY não configurada ou biblioteca OpenAI indisponível.")

    resposta = client.embeddings.create(
        model="text-embedding-3-small",
        input=textos,
    )
    return [item.embedding for item in resposta.data]


def obter_chroma_collection(nome_base):
    """Abre/cria uma coleção ChromaDB para a base informada."""
    import chromadb

    cliente = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return cliente.get_or_create_collection(name=f"incluisrm_{nome_base}")


def indexar_base_conhecimento(nome_base):
    """Indexa os PDFs da base científica ou pedagógica."""
    if nome_base == "cientifica":
        pasta = PASTA_CIENTIFICA
    elif nome_base == "pedagogica":
        pasta = PASTA_PEDAGOGICA
    else:
        raise ValueError("Base inválida. Use 'cientifica' ou 'pedagogica'.")

    arquivos = listar_pdfs_base(pasta)
    if not arquivos:
        return 0, f"Nenhum PDF encontrado em {pasta}."

    collection = obter_chroma_collection(nome_base)
    total_chunks = 0

    for pdf in arquivos:
        texto = extrair_texto_pdf(pdf)
        if not texto.strip():
            continue

        chunks = quebrar_texto(texto)
        if not chunks:
            continue

        ids = [f"{nome_base}_{pdf.stem}_{idx}" for idx in range(len(chunks))]
        metadados = [
            {"arquivo": pdf.name, "base": nome_base, "chunk": idx}
            for idx in range(len(chunks))
        ]
        embeddings = criar_embedding(chunks)

        collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadados,
        )
        total_chunks += len(chunks)

    return total_chunks, f"Base {nome_base} indexada com sucesso."


def buscar_na_base_conhecimento(pergunta, bases=None, limite=5):
    """Busca trechos relevantes nas bases indexadas."""
    if bases is None:
        bases = ["cientifica", "pedagogica"]

    try:
        embedding = criar_embedding([pergunta])[0]
    except Exception:
        return []

    resultados_finais = []

    for base in bases:
        try:
            collection = obter_chroma_collection(base)
            resultado = collection.query(
                query_embeddings=[embedding],
                n_results=limite,
            )

            docs = resultado.get("documents", [[]])[0]
            metas = resultado.get("metadatas", [[]])[0]

            for doc, meta in zip(docs, metas):
                resultados_finais.append(
                    {
                        "texto": doc,
                        "arquivo": meta.get("arquivo", "Arquivo não identificado"),
                        "base": meta.get("base", base),
                    }
                )
        except Exception:
            continue

    return resultados_finais


def montar_contexto_base(resultados):
    """Monta contexto textual para enviar à IA."""
    if not resultados:
        return "Nenhum trecho relevante encontrado nas bases científica e pedagógica."

    partes = []
    for i, item in enumerate(resultados, start=1):
        partes.append(
            f"""
[Fonte {i}]
Base: {item.get('base', 'não informada')}
Arquivo: {item.get('arquivo', 'não informado')}
Trecho:
{item.get('texto', '')}
""".strip()
        )
    return "\n\n".join(partes)


def arquivos_consultados_texto(resultados):
    arquivos = []
    for item in resultados or []:
        nome = item.get("arquivo")
        if nome and nome not in arquivos:
            arquivos.append(nome)
    return ", ".join(arquivos) if arquivos else "Nenhum arquivo consultado ou base ainda não indexada."


# ======================================================
# ATENDIMENTOS EM TEXTO
# ======================================================
def listar_atendimentos_texto(estudante_id):
    atendimentos = listar_atendimentos(estudante_id)
    if not atendimentos:
        return "Nenhum atendimento registrado."
    partes = []
    for a in atendimentos[:10]:
        partes.append(
            f"""
Data: {a[0]}
Objetivo: {a[1] or 'Não informado.'}
Atividade: {a[2] or 'Não informado.'}
Resposta: {a[3] or 'Não informado.'}
Avanços: {a[4] or 'Não informado.'}
Dificuldades: {a[5] or 'Não informado.'}
Evolução: {a[6] or 'Não informado.'}
Resposta: {a[8] if len(a) > 8 else 'Não informado.'}/10
Avanço: {a[9] if len(a) > 9 else 'Não informado.'}/10
Dificuldade: {a[10] if len(a) > 10 else 'Não informado.'}/10
Engajamento: {a[11] if len(a) > 11 else 'Não informado.'}/10
Índice: {a[12] if len(a) > 12 else 'Não informado.'}/10
"""
        )
    return "\n---\n".join(partes)


# ======================================================
# BUSCA DE MODELOS 3D
# ======================================================
def link_busca_thingiverse(termo):
    termo_formatado = termo.replace(" ", "%20")
    return f"https://www.thingiverse.com/search?q={termo_formatado}&type=things"


def link_busca_printables(termo):
    termo_formatado = termo.replace(" ", "%20")
    return f"https://www.printables.com/search/models?q={termo_formatado}"


def link_busca_makerworld(termo):
    termo_formatado = termo.replace(" ", "%20")
    return f"https://makerworld.com/pt/search/models?keyword={termo_formatado}"


def gerar_termos_3d_com_ia(conteudo_paee):
    """Gera exatamente 5 termos/objetos para busca de modelos 3D."""
    client = obter_cliente_openai()

    termos_padrao = [
        "braille alphabet",
        "tactile math",
        "visual schedule",
        "communication cards",
        "sensory toy",
    ]

    if client is None or not conteudo_paee:
        return termos_padrao

    prompt = f"""
Analise o PAEE abaixo e gere exatamente 5 objetos ou recursos 3D pedagógicos para busca
em sites como Thingiverse, Printables e MakerWorld.

Use termos curtos, preferencialmente em inglês, porque retornam mais modelos.
Priorize recursos inclusivos, táteis, manipuláveis, visuais, sensoriais, comunicação alternativa,
matemática concreta, alfabetização, autonomia ou organização da rotina.

Não explique.
Retorne apenas 5 linhas.
Cada linha deve conter apenas um termo de busca.

PAEE:
{conteudo_paee}
"""

    try:
        resposta = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        texto = resposta.output_text

        termos = []
        for linha in texto.split("\n"):
            termo = linha.strip().strip("-•0123456789. )(").strip()
            if termo and termo not in termos:
                termos.append(termo)

        return termos[:5] if termos else termos_padrao
    except Exception:
        return termos_padrao


# ======================================================
# PAEE SEM IA / COM IA
# ======================================================
def gerar_paee_sem_ia(estudante, avaliacao=None, entrevista=None, estudo=None):
    codigo = estudante[1]
    ano_serie = estudante[2] or "Não informado."
    turma = estudante[3] or "Não informado."
    perfil = estudante[4] or "Não informado."
    observacoes = estudante[5] or "Não informado."

    if avaliacao:
        avaliacao_txt = texto_avaliacao(estudante, ("", *avaliacao))
    else:
        avaliacao_txt = "Nenhuma avaliação pedagógica registrada."

    if entrevista:
        entrevista_txt = texto_entrevista(estudante, ("", *entrevista))
    else:
        entrevista_txt = "Nenhuma entrevista com a família registrada."

    if estudo:
        estudo_txt = texto_estudo_caso(estudante, ("", *estudo))
    else:
        estudo_txt = "Nenhum estudo de caso GRE registrado."

    historico_txt = listar_atendimentos_texto(estudante[0])

    return f"""
PLANO AEE / PAEE - SUGESTÃO PEDAGÓGICA SEM IA

1. Identificação segura do estudante
Código interno: {codigo}
Ano/Série: {ano_serie}
Turma: {turma}
Perfil educacional informado: {perfil}

Campos sensíveis para preenchimento manual no Word/PDF:
Nome completo do(a) estudante: ___________________________________________
CPF/RG do(a) estudante: _________________________________________________
Data de nascimento: ____/____/________
Nome do responsável: _________________________________________________
CPF/RG do responsável: _______________________________________________
Telefone: ___________________________________________________________
Endereço: ___________________________________________________________

2. Caracterização pedagógica inicial
{observacoes}

3. Base documental utilizada
3.1 Avaliação pedagógica
{avaliacao_txt}

3.2 Entrevista com a família
{entrevista_txt}

3.3 Estudo de caso GRE
{estudo_txt}

4. Barreiras e necessidades educacionais específicas
- Organizar as informações da entrevista, avaliação e estudo de caso para identificar barreiras de comunicação, interação, autonomia, aprendizagem, acesso curricular e participação.
- Evitar qualquer inferência diagnóstica não registrada.
- Considerar recursos de acessibilidade, tecnologia assistiva e adaptações pedagógicas conforme resposta do estudante.

5. Objetivos gerais do AEE
- Ampliar as condições de acesso, participação e aprendizagem do estudante nas atividades escolares.
- Desenvolver estratégias que favoreçam comunicação, autonomia, interação social e organização da rotina escolar.
- Utilizar recursos pedagógicos acessíveis, materiais concretos, tecnologias educacionais inclusivas e propostas maker quando pertinentes.

6. Objetivos específicos
- Fortalecer habilidades prioritárias observadas no estudo de caso.
- Reduzir barreiras identificadas na avaliação pedagógica e nos registros de atendimento.
- Apoiar o uso de recursos visuais, táteis, manipuláveis, digitais e de comunicação alternativa quando necessário.
- Acompanhar a evolução do estudante por meio de registros sistemáticos.

7. Estratégias pedagógicas sugeridas
- Utilizar rotina visual, instruções objetivas e antecipação das atividades.
- Propor atividades com materiais concretos, jogos pedagógicos, recursos visuais, recursos táteis e tecnologias digitais.
- Articular as ações do AEE com professores do ensino comum e família.
- Registrar avanços, dificuldades, engajamento, autonomia e resposta às estratégias em cada atendimento.

8. Sugestões de tecnologias educacionais inclusivas
- Impressão 3D: letras, números, mapas táteis, peças de associação, jogos de encaixe, pranchas adaptadas e recursos manipuláveis.
- Robótica educacional: sequências lógicas, comandos simples, causa e efeito, organização espacial e resolução de problemas.
- Jogos digitais: atividades de atenção, memória, comunicação, raciocínio lógico e reforço de habilidades curriculares.
- Recursos maker: construção de materiais personalizados, placas, cartões, roletas, jogos de pareamento e recursos sensoriais.
- Comunicação alternativa e aumentativa: pranchas visuais, cartões de escolha, pictogramas e rotinas estruturadas.

9. Atividades plugadas sugeridas
- Jogos digitais educativos adaptados ao perfil do estudante.
- Uso orientado de tablet/computador com recursos visuais e auditivos.
- Atividades com Scratch, Construct ou jogos simples para trabalhar sequência, escolha, atenção e resposta.
- Robótica com comandos básicos, sensores simples e atividades de causa e efeito.

10. Atividades desplugadas sugeridas
- Sequências com cartões de rotina e organização temporal.
- Pareamento de figuras, objetos, letras, números, formas e cores.
- Trilhas pedagógicas, jogos de memória, dominós adaptados e bingo de imagens/palavras.
- Atividades sensoriais com texturas, objetos 3D, encaixes, blocos, massinha, peças táteis e materiais concretos.
- Jogos de comandos corporais, lateralidade, atenção compartilhada e imitação.
- Contação de histórias com cartões visuais, personagens concretos e recontagem orientada.

11. Organização do atendimento
- Definir frequência, duração, formato e objetivos de cada ciclo de atendimento conforme necessidade pedagógica.
- Registrar cada atendimento no sistema para análise de evolução.

12. Avaliação e acompanhamento
Histórico de atendimentos registrado:
{historico_txt}

- Revisar o plano periodicamente com base nos registros reais.
- Se os registros ainda forem limitados, ampliar o acompanhamento antes de conclusões evolutivas.

13. Responsável pelo AEE
Nome: ___________________________________________
Função: Professor(a) do Atendimento Educacional Especializado (AEE)
Assinatura: _______________________________________

14. Coordenação pedagógica
Nome: ___________________________________________
Cargo: Coordenação Pedagógica
Assinatura: _______________________________________

15. Data de elaboração: ____/____/________
""".strip()




def montar_contexto_plano_aee_ia(estudante, avaliacao=None, entrevista=None, estudo=None, plano_manual=None):
    """Reúne os dados pedagógicos disponíveis para o módulo Plano AEE - IA.

    Nesta versão, o Plano AEE - IA passa a considerar também:
    - Escutas docentes salvas;
    - Histórico de escutas docentes;
    - Relatórios de Apoio ao Docente gerados e salvos.

    Observação: a finalidade continua sendo exclusivamente pedagógica e educacional.
    """
    historico_txt = listar_atendimentos_texto(estudante[0])
    escutas_docentes = listar_escutas_docentes(estudante[0])[:10]
    relatorios_docentes = listar_relatorios_docente(estudante[0])[:5]

    estudante_txt = f"""
Código interno: {estudante[1]}
Ano/Série: {estudante[2]}
Turma: {estudante[3]}
Turno: {estudante[6]}
Perfil educacional informado: {estudante[4]}
Observações pedagógicas iniciais: {estudante[5]}
Dias de atendimento preferenciais: {estudante[7]}
Horário preferencial: {estudante[8]}
""".strip()

    avaliacao_txt = texto_avaliacao(estudante, ("", *avaliacao)) if avaliacao else "Nenhuma avaliação pedagógica registrada."
    entrevista_txt = texto_entrevista(estudante, ("", *entrevista)) if entrevista else "Nenhuma entrevista com a família registrada."
    estudo_txt = texto_estudo_caso(estudante, ("", *estudo)) if estudo else "Nenhum estudo de caso GRE registrado."
    plano_txt = texto_plano_aee(estudante, ("", *plano_manual)) if plano_manual else "Nenhum plano AEE manual registrado."

    textos_escutas = []
    for esc in escutas_docentes:
        try:
            textos_escutas.append(texto_escuta_docente(estudante, esc))
        except Exception:
            textos_escutas.append(str(esc))
    escutas_txt = "\n\n---\n\n".join(textos_escutas) if textos_escutas else "Nenhuma escuta docente registrada para este estudante."

    textos_relatorios = []
    for rel in relatorios_docentes:
        try:
            textos_relatorios.append(texto_relatorio_docente(estudante, rel))
        except Exception:
            textos_relatorios.append(str(rel))
    relatorios_docente_txt = "\n\n---\n\n".join(textos_relatorios) if textos_relatorios else "Nenhum Relatório de Apoio ao Docente salvo para este estudante."

    pergunta_busca = f"""
AEE plano mensal atendimento sala de recursos multifuncionais estudante {estudante[4]} {estudante[2]}
comunicação funcional autonomia CAA tecnologia assistiva recursos visuais rotina estruturada robótica impressão 3D.
"""
    resultados_base = buscar_na_base_conhecimento(pergunta_busca, bases=["cientifica", "pedagogica"], limite=5)
    contexto_base = montar_contexto_base(resultados_base)
    arquivos_base = arquivos_consultados_texto(resultados_base)

    return {
        "estudante_txt": estudante_txt,
        "avaliacao_txt": avaliacao_txt,
        "entrevista_txt": entrevista_txt,
        "estudo_txt": estudo_txt,
        "plano_txt": plano_txt,
        "escutas_docentes_txt": escutas_txt,
        "relatorios_docente_txt": relatorios_docente_txt,
        "qtd_escutas_docentes": len(escutas_docentes),
        "qtd_relatorios_docente": len(relatorios_docentes),
        "historico_txt": historico_txt,
        "contexto_base": contexto_base,
        "arquivos_base": arquivos_base,
    }


def gerar_diagnostico_aee_ia(estudante, avaliacao=None, entrevista=None, estudo=None, plano_manual=None):
    """Gera perfil pedagógico inicial/evolutivo para apoiar o professor do AEE.
    Mantém o nome da função por compatibilidade com versões anteriores.
    """
    ctx = montar_contexto_plano_aee_ia(estudante, avaliacao, entrevista, estudo, plano_manual)
    client = obter_cliente_openai()

    fallback = f"""
PERFIL PEDAGÓGICO INICIAL - PLANO AEE IA

Código interno: {estudante[1]}
Perfil educacional informado: {estudante[4]}
Ano/Série: {estudante[2]}

Síntese inicial:
O perfil pedagógico deve considerar os registros já disponíveis no cadastro, entrevista familiar, avaliação pedagógica, estudo de caso, escuta docente, relatórios de apoio ao docente, plano AEE e atendimentos. Caso ainda existam poucos registros, recomenda-se utilizar este documento como roteiro de observação inicial, sem conclusões definitivas sobre evolução.

Focos de observação prioritários:
- Comunicação funcional e formas de expressão utilizadas pelo estudante.
- Autonomia na organização e realização das atividades.
- Atenção compartilhada e permanência nas propostas.
- Interação com professor, profissional de apoio e colegas.
- Resposta a recursos visuais, tecnológicos, concretos, sensoriais e maker.
- Barreiras comunicacionais, pedagógicas, atitudinais e de acessibilidade.

Sugestões gerais para o planejamento do AEE:
- Definir objetivos prioritários a partir das barreiras e potencialidades registradas.
- Selecionar recursos acessíveis e estratégias de mediação compatíveis com o perfil pedagógico do estudante.
- Registrar sistematicamente as respostas do estudante para ajustar o planejamento.

Encaminhamento:
Registrar os atendimentos semanalmente para que o sistema consiga gerar análises evolutivas mais consistentes.
""".strip()

    if client is None:
        return fallback

    prompt = f"""
Você é especialista em Atendimento Educacional Especializado (AEE), educação inclusiva, tecnologia assistiva, CAA, cultura maker e avaliação pedagógica funcional.

TAREFA:
Gere um PERFIL PEDAGÓGICO DO ESTUDANTE - AEE com base nos dados disponíveis. O texto deve apoiar o professor do AEE na organização dos atendimentos e não deve criar diagnóstico clínico, médico ou terapêutico.

REGRAS:
- Não usar nome real do estudante.
- Usar apenas o código interno.
- Não inventar dados.
- Se houver poucos atendimentos, informar que a análise evolutiva ainda é inicial.
- Diferenciar potencialidades, barreiras e necessidades prioritárias.
- Sugerir apenas encaminhamentos pedagógicos e funcionais.

DADOS DO ESTUDANTE:
{ctx['estudante_txt']}

ENTREVISTA FAMILIAR:
{ctx['entrevista_txt']}

AVALIAÇÃO PEDAGÓGICA:
{ctx['avaliacao_txt']}

ESTUDO DE CASO GRE:
{ctx['estudo_txt']}

PLANO AEE MANUAL:
{ctx['plano_txt']}

ESCUTA DOCENTE / HISTÓRICO DE ESCUTAS:
{ctx['escutas_docentes_txt']}

RELATÓRIOS DE APOIO AO DOCENTE SALVOS:
{ctx['relatorios_docente_txt']}

ATENDIMENTOS REGISTRADOS:
{ctx['historico_txt']}

BASES CONSULTADAS:
{ctx['contexto_base']}

ARQUIVOS CONSULTADOS:
{ctx['arquivos_base']}

ESTRUTURE EM:
1. Síntese pedagógica do estudante
2. Potencialidades observadas
3. Barreiras identificadas
4. Necessidades prioritárias para o AEE
5. Recursos com maior chance de resposta
6. Cuidados pedagógicos no atendimento
7. Indicadores a observar nos próximos atendimentos
8. Sugestões gerais para o planejamento do AEE
9. Observação sobre suficiência dos dados

Na seção 8, incluir objetivos prioritários, recursos sugeridos, estratégias de mediação, organização inicial dos atendimentos e formas de acompanhamento, sem repetir um relatório separado.
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return resposta.output_text
    except Exception as e:
        return f"{fallback}\n\nObservação técnica: não foi possível gerar com IA agora. Erro: {e}"



def gerar_perfil_pedagogico_aee_ia(estudante, avaliacao=None, entrevista=None, estudo=None, plano_manual=None):
    """Nome pedagógico atual da função de perfil. Mantém a função antiga como base por compatibilidade."""
    return gerar_diagnostico_aee_ia(estudante, avaliacao, entrevista, estudo, plano_manual)

def gerar_sugestao_geral_aee_ia(estudante, avaliacao=None, entrevista=None, estudo=None, plano_manual=None):
    """Gera uma sugestão geral de atendimento para orientar o semestre/período."""
    ctx = montar_contexto_plano_aee_ia(estudante, avaliacao, entrevista, estudo, plano_manual)
    client = obter_cliente_openai()

    fallback = f"""
SUGESTÃO GERAL DE ATENDIMENTO AEE - IA

Código interno: {estudante[1]}
Perfil educacional informado: {estudante[4]}

Objetivo geral sugerido:
Promover a participação, a autonomia, a comunicação funcional e o acesso às atividades escolares por meio de estratégias estruturadas, recursos de acessibilidade, tecnologias educacionais inclusivas e mediação pedagógica no Atendimento Educacional Especializado.

Eixos prioritários:
1. Comunicação funcional e uso progressivo de recursos visuais/CAA.
2. Organização da rotina e desenvolvimento de autonomia.
3. Atenção compartilhada e permanência nas atividades.
4. Participação social mediada.
5. Uso de recursos tecnológicos, concretos, sensoriais e maker conforme resposta do estudante.

Estratégias gerais:
- Utilizar comandos curtos, claros e objetivos.
- Trabalhar com rotina visual e previsibilidade.
- Oferecer escolhas mediadas por imagens, objetos ou recursos digitais.
- Registrar respostas, avanços, barreiras e nível de engajamento em cada atendimento.
- Iniciar com atividades de baixa complexidade e ampliar gradualmente.

Recursos possíveis:
- Pranchas de CAA, cartões visuais, tablet, Chromebook, jogos pedagógicos, materiais manipuláveis, impressão 3D, robótica educacional e atividades desplugadas.

Avaliação:
Acompanhar semanalmente a participação, comunicação, autonomia, atenção, interação e resposta aos recursos utilizados.
""".strip()

    if client is None:
        return fallback

    prompt = f"""
Você é especialista em AEE e planejamento de atendimento em Sala de Recursos Multifuncionais.

TAREFA:
Gere uma SUGESTÃO GERAL DE ATENDIMENTO AEE para orientar o professor no período letivo. Ela deve ser prática, aplicável e alimentar depois os registros de atendimento.

REGRAS:
- Não usar nome real.
- Usar código interno.
- Não inventar diagnósticos ou terapias.
- Não substituir o Plano AEE oficial; este é um apoio operacional de atendimento.
- Priorizar ações aplicáveis na SRM.

DADOS DO ESTUDANTE:
{ctx['estudante_txt']}

ENTREVISTA FAMILIAR:
{ctx['entrevista_txt']}

AVALIAÇÃO PEDAGÓGICA:
{ctx['avaliacao_txt']}

ESTUDO DE CASO GRE:
{ctx['estudo_txt']}

PLANO AEE MANUAL:
{ctx['plano_txt']}

ESCUTA DOCENTE / HISTÓRICO DE ESCUTAS:
{ctx['escutas_docentes_txt']}

RELATÓRIOS DE APOIO AO DOCENTE SALVOS:
{ctx['relatorios_docente_txt']}

ATENDIMENTOS REGISTRADOS:
{ctx['historico_txt']}

BASES CONSULTADAS:
{ctx['contexto_base']}

ESTRUTURE EM:
1. Objetivo geral de atendimento
2. Objetivos específicos
3. Eixos prioritários
4. Organização sugerida dos atendimentos
5. Recursos de acessibilidade e tecnologia educacional
6. Sugestões de atividades plugadas
7. Sugestões de atividades desplugadas
8. Sugestões com impressão 3D/robótica/cultura maker, quando aplicável
9. Como registrar evidências no módulo Atendimentos
10. Indicadores de acompanhamento
11. Cuidados para revisão do plano
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return resposta.output_text
    except Exception as e:
        return f"{fallback}\n\nObservação técnica: não foi possível gerar com IA agora. Erro: {e}"


def gerar_plano_mensal_aee_ia(estudante, mes_referencia, ano_referencia, qtd_atendimentos_semana=1, avaliacao=None, entrevista=None, estudo=None, plano_manual=None, datas_atendimentos=None):
    """Gera plano mensal aplicável às datas reais de atendimento do mês."""
    ctx = montar_contexto_plano_aee_ia(estudante, avaliacao, entrevista, estudo, plano_manual)
    client = obter_cliente_openai()
    qtd = max(1, min(5, int(qtd_atendimentos_semana or 1)))
    datas_atendimentos = datas_atendimentos or []
    datas_txt = datas_atendimentos_para_texto(datas_atendimentos)
    total_atendimentos = len(datas_atendimentos) if datas_atendimentos else qtd * 4

    fallback = f"""
PLANO MENSAL DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO (AEE)

Código interno: {estudante[1]}
Mês de referência: {mes_referencia}/{ano_referencia}
Dias/datas previstas de atendimento:
{datas_txt}

Total previsto de atendimentos no mês: {total_atendimentos}

Objetivo do mês:
Organizar uma rotina inicial/progressiva de atendimento voltada à comunicação funcional, autonomia, atenção compartilhada, interação e participação nas atividades da SRM.
""".strip()

    if datas_atendimentos:
        for idx, data_atual in enumerate(datas_atendimentos, start=1):
            semana_mes = ((data_atual.day - 1) // 7) + 1
            nome_dia = DIAS_SEMANA[data_atual.weekday()] if data_atual.weekday() < len(DIAS_SEMANA) else "Dia"
            fallback += f"""

SEMANA {semana_mes} - ATENDIMENTO {idx}
Data prevista: {data_atual.strftime('%d/%m/%Y')} ({nome_dia})
- Objetivo: desenvolver comunicação funcional, atenção, autonomia e participação de forma gradual.
- Atividade: proposta mediada com apoio visual, escolha dirigida, recurso tecnológico, material manipulável ou atividade maker conforme resposta do estudante.
- Recursos: prancha de CAA, rotina visual, tablet/Chromebook, material concreto, impressão 3D/robótica quando aplicável.
- Mediação: comandos curtos, demonstração prática, reforço positivo e tempo ampliado para resposta.
- Registro no sistema: resposta do estudante, engajamento, recurso utilizado, barreiras observadas, avanços e encaminhamentos.
"""
    else:
        for semana in range(1, 5):
            fallback += f"""

SEMANA {semana}
Atendimento 1:
- Objetivo: ampliar gradualmente comunicação, atenção e autonomia.
- Atividade: atividade estruturada com apoio visual, escolha mediada, sequência simples ou recurso tecnológico.
- Recursos: prancha de CAA, rotina visual, material manipulável, tablet/Chromebook ou jogo pedagógico.
- Registro no sistema: avanços, dificuldades, barreiras e encaminhamentos.
"""
            if qtd >= 2:
                fallback += f"""
Atendimento 2:
- Objetivo: generalizar a habilidade trabalhada em nova situação.
- Atividade: proposta prática com tecnologia, recurso maker, impressão 3D, robótica ou atividade desplugada.
- Recursos: materiais concretos, recurso visual e mediação individualizada.
- Registro no sistema: comparação com o atendimento anterior e necessidade de ajuste.
"""

    fallback += """

Avaliação do mês:
Ao final do mês, verificar evolução em comunicação funcional, autonomia, atenção compartilhada, interação e resposta aos recursos utilizados.
"""

    if client is None:
        return fallback

    prompt = f"""
Você é especialista em AEE e deve criar um PLANO MENSAL DE ATENDIMENTO aplicável na Sala de Recursos Multifuncionais.

TAREFA:
Crie um plano mensal considerando as DATAS REAIS de atendimento abaixo, para o mês de {mes_referencia}/{ano_referencia}.

DATAS REAIS DE ATENDIMENTO CALCULADAS PELO SISTEMA:
{datas_txt}

TOTAL REAL DE ATENDIMENTOS NO MÊS: {total_atendimentos}

REGRAS:
- Não usar nome real do estudante.
- Usar código interno.
- Não inventar evolução ainda não registrada.
- Gerar atividades realistas para o professor aplicar.
- Cada atendimento deve ter: objetivo, atividade, recursos, mediação, registro esperado no sistema e indicador de observação.
- Incluir progressão gradual.
- Considerar atividades plugadas e desplugadas.
- Quando fizer sentido, incluir tablet, Chromebook, CAA, recursos visuais, impressão 3D, robótica e materiais manipuláveis.
- O plano deve ser usado para alimentar o módulo Atendimentos.

DADOS DO ESTUDANTE:
{ctx['estudante_txt']}

ENTREVISTA FAMILIAR:
{ctx['entrevista_txt']}

AVALIAÇÃO PEDAGÓGICA:
{ctx['avaliacao_txt']}

ESTUDO DE CASO GRE:
{ctx['estudo_txt']}

PLANO AEE MANUAL:
{ctx['plano_txt']}

ESCUTA DOCENTE / HISTÓRICO DE ESCUTAS:
{ctx['escutas_docentes_txt']}

RELATÓRIOS DE APOIO AO DOCENTE SALVOS:
{ctx['relatorios_docente_txt']}

ATENDIMENTOS REGISTRADOS:
{ctx['historico_txt']}

BASES CONSULTADAS:
{ctx['contexto_base']}

FORMATO DE SAÍDA:
1. Identificação segura
2. Objetivo do mês
3. Habilidades prioritárias do mês
4. Recursos necessários
5. Roteiro por data real de atendimento
   - Data e dia da semana
   - Objetivo do atendimento
   - Atividade proposta
   - Recursos
   - Mediação
   - Registro esperado no sistema
6. Como registrar cada atendimento no sistema
7. Indicadores para avaliação mensal
8. Ajustes possíveis para o mês seguinte
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return resposta.output_text
    except Exception as e:
        return f"{fallback}\n\nObservação técnica: não foi possível gerar com IA agora. Erro: {e}"


def salvar_historico_plano_aee_ia(estudante_id, mes_referencia, ano_referencia, qtd_atendimentos_semana, tipo_geracao, diagnostico_ia="", sugestao_geral="", plano_mensal="", observacoes=""):
    inserir_registro(
        "plano_aee_ia",
        ["estudante_id", *CAMPOS_PLANO_AEE_IA],
        [
            estudante_id,
            hoje_str(),
            mes_referencia,
            str(ano_referencia),
            int(qtd_atendimentos_semana or 1),
            tipo_geracao,
            diagnostico_ia,
            sugestao_geral,
            "",
            "",
            "",
            plano_mensal,
            plano_mensal,
            observacoes,
        ],
    )

def gerar_paee_com_ia(estudante, avaliacao=None, entrevista=None, estudo=None):
    client = obter_cliente_openai()

    if client is None:
        return gerar_paee_sem_ia(estudante, avaliacao, entrevista, estudo)

    historico_txt = listar_atendimentos_texto(estudante[0])

    estudante_txt = f"""
Código interno: {estudante[1]}
Ano/Série: {estudante[2]}
Turma: {estudante[3]}
Turno: {estudante[6]}
Perfil educacional informado: {estudante[4]}
Observações pedagógicas iniciais: {estudante[5]}
Dias de atendimento preferenciais: {estudante[7]}
Horário preferencial: {estudante[8]}
"""

    avaliacao_txt = texto_avaliacao(estudante, ("", *avaliacao)) if avaliacao else "Nenhuma avaliação pedagógica registrada."
    entrevista_txt = texto_entrevista(estudante, ("", *entrevista)) if entrevista else "Nenhuma entrevista com a família registrada."
    estudo_txt = texto_estudo_caso(estudante, ("", *estudo)) if estudo else "Nenhum estudo de caso GRE registrado."

    pergunta_busca = f"""
Plano AEE PAEE para estudante com perfil {estudante[4]}, ano/série {estudante[2]},
barreiras, potencialidades, estratégias pedagógicas, atividades desplugadas,
tecnologia assistiva, recursos maker, robótica, impressão 3D e inclusão escolar.
"""
    resultados_base = buscar_na_base_conhecimento(pergunta_busca, bases=["cientifica", "pedagogica"], limite=5)
    contexto_base = montar_contexto_base(resultados_base)
    arquivos_base = arquivos_consultados_texto(resultados_base)

    prompt = f"""
Você é um assistente pedagógico especializado em Atendimento Educacional Especializado (AEE), Educação Inclusiva, Sala de Recursos Multifuncionais (SRM), tecnologias educacionais inclusivas e elaboração de Plano AEE/PAEE.

TAREFA:
Elabore uma sugestão de Plano AEE/PAEE com linguagem formal, técnica, objetiva e pedagógica, cruzando as informações do cadastro, entrevista com a família, avaliação pedagógica, estudo de caso GRE, escuta docente, relatórios de apoio ao docente, histórico de atendimentos e os trechos recuperados das bases científica e pedagógica.

REGRAS DE SEGURANÇA E PRIVACIDADE:
- Não usar nome real de estudante.
- Usar somente “Código interno” para identificar o estudante.
- Não solicitar CPF, RG, endereço, telefone ou dados sensíveis.
- Quando necessário, deixar campos sensíveis em branco para preenchimento manual no Word/PDF.
- Não inventar diagnóstico.
- Não criar condutas médicas.
- Não afirmar evolução não registrada.
- Não inventar citações bibliográficas.
- Quando usar a base de conhecimento, cite apenas o nome do arquivo consultado.

REGRA SOBRE TEA SEM NÍVEL:
Se o perfil educacional for TEA e o nível de suporte não estiver informado, adotar provisoriamente estratégias compatíveis com suporte moderado, sem afirmar diagnóstico clínico.

REGRA CRÍTICA SOBRE ATENDIMENTOS:
A análise da evolução deve ser baseada exclusivamente nos dados reais do histórico de atendimentos. Se os registros forem insuficientes, escrever: “Os registros de atendimento ainda são limitados para uma análise evolutiva consistente, sendo necessário ampliar o acompanhamento pedagógico.”

DADOS DO ESTUDANTE:
{estudante_txt}

ENTREVISTA COM A FAMÍLIA:
{entrevista_txt}

AVALIAÇÃO PEDAGÓGICA:
{avaliacao_txt}

ESTUDO DE CASO GRE:
{estudo_txt}

HISTÓRICO DE ATENDIMENTOS:
{historico_txt}

TRECHOS DAS BASES CIENTÍFICA E PEDAGÓGICA:
{contexto_base}

ARQUIVOS CONSULTADOS:
{arquivos_base}

ESTRUTURE O DOCUMENTO COM:
1. Identificação segura do estudante
2. Campos sensíveis para preenchimento manual no Word/PDF
3. Caracterização pedagógica
4. Síntese da entrevista com a família
5. Síntese da avaliação pedagógica
6. Síntese do estudo de caso GRE
7. Necessidades educacionais específicas
8. Barreiras identificadas
9. Potencialidades
10. Objetivos gerais do AEE
11. Objetivos específicos do AEE
12. Estratégias pedagógicas
13. Recursos de acessibilidade e tecnologias assistivas
14. Sugestões de tecnologias educacionais inclusivas
    - impressão 3D
    - robótica educacional
    - jogos digitais
    - recursos maker
    - comunicação alternativa e aumentativa
    - materiais táteis, visuais e manipuláveis
15. Atividades plugadas sugeridas
16. Atividades desplugadas sugeridas
17. Como aplicar as atividades no atendimento da SRM
18. Organização do atendimento
19. Articulação com família, professores e gestão
20. Avaliação e acompanhamento
21. Evolução do estudante com base nos atendimentos
22. Recomendações para revisão do plano
23. Fundamentação com base nos documentos consultados
24. Arquivos utilizados como referência
25. Responsável pelo AEE:
Nome: ___________________________________________
Função: Professor(a) do Atendimento Educacional Especializado (AEE)
Assinatura: _______________________________________
26. Coordenação pedagógica:
Nome: ___________________________________________
Cargo: Coordenação Pedagógica
Assinatura: _______________________________________
27. Data de elaboração: ____/____/________

Na seção de atividades desplugadas, inclua sugestões concretas e aplicáveis sem computador, como cartões de rotina, pareamento, sequência lógica, jogos de memória, materiais táteis, objetos 3D, trilhas pedagógicas, contação de histórias com apoio visual, atividades de atenção compartilhada e recursos manipuláveis.
"""

    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return resposta.output_text


def gerar_relatorio_evolucao(estudante, avaliacao=None):
    api_key = obter_api_key()

    if OpenAI is None or not api_key:
        return "IA não configurada."

    historico_txt = listar_atendimentos_texto(estudante[0])

    estudante_txt = f"""
Código interno: {estudante[1]}
Ano/Série: {estudante[2]}
Turma: {estudante[3]}
Perfil educacional: {estudante[4]}
"""

    prompt = f"""
Você é um especialista em Educação Inclusiva e AEE.

Analise o histórico de atendimentos e produza um RELATÓRIO PEDAGÓGICO ANALÍTICO.

DADOS DO ESTUDANTE:
{estudante_txt}

HISTÓRICO DE ATENDIMENTOS:
{historico_txt}

REGRAS IMPORTANTES:
- NÃO inventar informações.
- Usar somente dados reais.
- Se os dados forem fracos, dizer claramente.

ESTRUTURA DO RELATÓRIO:
1. Síntese da evolução do estudante
2. Análise dos avanços
3. Análise das dificuldades
4. Qualidade dos registros pedagógicos
Classificar como: Alta, Média ou Baixa.
5. Principais problemas identificados nos registros
6. Recomendações para melhoria dos registros
7. Recomendações pedagógicas para o AEE
8. Conclusão técnica
"""

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return resposta.output_text


# ======================================================
# DOCUMENTOS GRE - MODELOS INSTITUCIONAIS COM CAMPOS SIGILOSOS EM BRANCO
# ======================================================
def linha_preenchimento(rotulo, tamanho=60):
    return f"{rotulo}: " + "_" * tamanho


def valor_ou_linha(valor, rotulo="", tamanho=60, sigiloso=False):
    """Preenche somente dados não sigilosos já existentes no sistema."""
    if sigiloso:
        return linha_preenchimento(rotulo, tamanho) if rotulo else "_" * tamanho
    if valor not in (None, "", "Não informado"):
        return str(valor)
    return linha_preenchimento(rotulo, tamanho) if rotulo else "Não informado."


def marcar_opcao(valor, esperado):
    valor = str(valor or "").strip().lower()
    esperado = str(esperado or "").strip().lower()
    return "(X)" if valor == esperado else "( )"


def texto_campos_sensiveis_gre_estudante():
    return """
DADOS SIGILOSOS / PREENCHIMENTO MANUAL NO WORD OU IMPRESSO
Nome completo do(a) estudante: ___________________________________________
Data de nascimento: ____/____/________
CPF/RG do(a) estudante: _________________________________________________
Matrícula oficial do(a) estudante: _______________________________________
Nome do(a) responsável: _________________________________________________
CPF do(a) responsável: _________________________________________________
Contato telefônico do(a) responsável: ___________________________________
Endereço completo: ______________________________________________________
Número do NIS: __________________________________________________________
Número do Cartão SUS: __________________________________________________
Filiação: _______________________________________________________________
""".strip()


def texto_cabecalho_gre(titulo):
    return f"""
SECRETARIA DE EDUCAÇÃO E ESPORTES
GERÊNCIA METROPOLITANA NORTE DE EDUCAÇÃO
CGDE - COORDENAÇÃO GERAL DE DESENVOLVIMENTO DA EDUCAÇÃO
NÚCLEO / UNIDADE DE EDUCAÇÃO INCLUSIVA, DIREITOS HUMANOS E CIDADANIA

{titulo}
""".strip()


def texto_ficha_professor_gre(professor=None):
    if professor is None:
        professor = buscar_professor_responsavel()

    if not professor:
        return "Nenhum professor AEE cadastrado."

    return f"""
{texto_cabecalho_gre("FICHA DE IDENTIFICAÇÃO PROFESSOR(A) AEE")}

ANO LETIVO: ______________________

1. IDENTIFICAÇÃO PESSOAL
Nome: {professor[1] or 'Não informado.'}
Data de nascimento: ____/____/________
Matrícula: ___________________________________________
Endereço: ____________________________________________
Filiação: ____________________________________________
País de nacionalidade: _______________________________
CPF: _________________________________________________
UF de nascimento: ______ Município de nascimento: __________________________

Profissional escolar com deficiência, Transtorno do Espectro do Autismo e/ou Altas Habilidades/Superdotação?
( ) Não   ( ) Sim. Qual? _________________________________________________

Telefones para contato: _________________________________________________
E-mail: _________________________________________________________________

2. FORMAÇÃO ACADÊMICA
Maior nível de escolaridade concluída: {professor[4] or 'Não informado.'}

Dados sobre graduação:
Curso: _________________________________________________________________
Instituição: ____________________________________________________________
Ano de conclusão: _________________________

Dados sobre pós-graduação:
( ) Especialização   ( ) Mestrado   ( ) Doutorado   ( ) Não tem pós concluída
Curso: _________________________________________________________________
Instituição: ____________________________________________________________
Ano de conclusão: _________________________

Outras informações relevantes quanto à qualificação profissional:
{professor[7] or '________________________________________________________________________________'}

3. IDENTIFICAÇÃO PROFISSIONAL
Escola que atua na rede: {professor[2] or 'Não informado.'}
Telefone institucional: _________________________________________________
Regional: {professor[3] or 'Não informado.'}
Horário / carga horária: {professor[5] or 'Não informado.'}
Turno de atuação: {professor[6] or 'Não informado.'}
Acumulação: ___________________________________________
Trabalha em outra rede? ( ) Sim   ( ) Não
Rede que atua: _________________________________________
Horário: ____________________ Telefone: ________________________________

____________________, ____ de __________________________ de ____________

Assinatura do(a) professor(a): __________________________________________
""".strip()


def texto_matricula_srm_gre(estudante):
    return f"""
{texto_cabecalho_gre("MATRÍCULA PARA O ATENDIMENTO EDUCACIONAL ESPECIALIZADO NA SALA DE RECURSOS MULTIFUNCIONAIS - SRM")}

Escola: ________________________________________________
Estudante: _____________________________________________
Ano: {estudante[2] or 'Não informado.'}   Turma: {estudante[3] or 'Não informado.'}   Turno: {estudante[6] or 'Não informado.'}
Ano letivo: ______________________

1. IDENTIFICAÇÃO SEGURA NO SISTEMA
Código interno: {estudante[1] or 'Não informado.'}
Perfil educacional informado: {estudante[4] or 'Não informado.'}
Dias preferenciais de atendimento: {estudante[7] or 'Não informado.'}
Horário preferencial: {estudante[8] or 'Não informado.'}

{texto_campos_sensiveis_gre_estudante()}

2. REQUERIMENTO DE MATRÍCULA / TERMO DE CIÊNCIA DO SERVIÇO DE AEE
Nome da Instituição de Ensino da SRM: ___________________________________
Local e data: ______________________, ____ de __________________ de ______

Nome do(a) estudante: _________________________________________________
Data de nascimento: ____/____/________
Turma: {estudante[3] or 'Não informado.'}   Turno: {estudante[6] or 'Não informado.'}
Filiação: ______________________________________________________________
Endereço: ______________________________________________________________
Recebe auxílio? ( ) Não   ( ) Sim   Número do NIS: ______________________
Número do Cartão SUS: _________________________________________________

3. INDICAÇÃO DO PÚBLICO-ALVO DA EDUCAÇÃO ESPECIAL
( ) Deficiência Auditiva        ( ) Surdo(a)        ( ) Usa aparelho auditivo
( ) Surdocegueira
( ) Deficiência Intelectual     ( ) Síndrome de Down
( ) Altas habilidades/Superdotação
( ) Deficiência Visual          ( ) Cegueira        ( ) Baixa visão
( ) Transtorno do Espectro do Autismo - TEA
( ) Deficiência Física          ( ) Usuário(a) de cadeira de rodas
( ) Deficiência Múltipla. Quais? ________________________________________
( ) Outro: ______________________________________________________________

Perfil registrado no sistema: {estudante[4] or 'Não informado.'}

4. AUTORIZAÇÕES
Autorização para retirar o(a) estudante da escola:
( ) Deixar a escola sozinho(a)
( ) Deixar a escola apenas acompanhado(a)

Nome do acompanhante | Parentesco/relação social | Documento | Telefone
_______________________________________________________________________
_______________________________________________________________________

Permissão para uso e divulgação da imagem para fins educacionais e pedagógicos:
( ) Sim   ( ) Não

Matrícula no Atendimento Educacional Especializado - AEE, realizado na Sala de Recursos Multifuncionais desta escola,
nos dias de {estudante[7] or '_______________________'} no horário de {estudante[8] or '________ às ________'}.

5. TERMO DE CIÊNCIA
Eu, ____________________________________________, CPF nº ______________________________,
responsável pelo(a) estudante ____________________________________________, regularmente matriculado(a)
na escola ____________________________________________, no ano {estudante[2] or '_____'} turma {estudante[3] or '_____'} turno {estudante[6] or '_____'},
declaro estar ciente do Serviço do Atendimento Educacional Especializado disponibilizado pela Unidade Escolar.
Autorizo e me comprometo com a participação e frequência deste(a) estudante aos Atendimentos Educacionais
Especializados na Sala de Recursos Multifuncionais desta Unidade Educacional.

Declaro ter ciência de que o descumprimento do compromisso acima poderá resultar na perda da vaga neste serviço.

Data: ____/____/________

Assinatura do responsável: ______________________________________________
Professor(a) da SRM / AEE: ______________________________________________
Gestão / Coordenação Pedagógica: ________________________________________
""".strip()


def texto_entrevista_familia_gre(estudante, entrevista=None):
    if entrevista is None:
        entrevista = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante[0])

    dados = dict(zip(CAMPOS_ENTREVISTA_FAMILIA, entrevista or []))
    def v(campo):
        valor = dados.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    return f"""
{texto_cabecalho_gre("ENTREVISTA COM A FAMÍLIA")}

Escola: ________________________________________________
Estudante: _____________________________________________
Ano letivo: {v('ano_letivo')}
Tipo de registro: {v('tipo_registro')}
Código interno no sistema: {estudante[1] or 'Não informado.'}
Ano/Série: {estudante[2] or 'Não informado.'}   Turma: {estudante[3] or 'Não informado.'}   Turno: {estudante[6] or 'Não informado.'}

{texto_campos_sensiveis_gre_estudante()}

1. INFORMAÇÕES DIVERSAS
A família participa de algum programa de auxílio governamental? {v('auxilio_governamental')}
Qual(is): {v('auxilio_quais')}
Há histórico familiar de doenças graves, deficiência ou transtornos? {v('historico_familiar')}
Qual(is): {v('historico_quais')}
Já repetiu de ano? {v('repetiu_ano')}   Quantas vezes? {v('repetiu_qtd')}
Trocou de escola? {v('trocou_escola')}   Quantas vezes? {v('trocou_qtd')}
Motivo da troca: {v('motivo_troca')}
Situação em relação à escola: {v('situacao_escolar')}
Demonstra interesse em frequentar a escola: {v('interesse_escola')}
Cuida/organiza seus materiais: {v('organiza_materiais')}
Apresenta resistência à escola: {v('resistencia_escola')}
Relaciona-se bem com colegas: {v('relacao_colegas')}
Relaciona-se bem com professores: {v('relacao_professores')}
Leva alimentação de casa: {v('leva_alimentacao')}
Alimenta-se da merenda escolar: {v('merenda_escolar')}
Possui alergia alimentar: {v('alergia_alimentar')}   Qual(is): {v('alergia_quais')}
Outras observações: {v('obs_diversas')}

2. SOBRE A ESCOLHA DA ESCOLA
Motivo da escolha: {v('motivo_escolha')}
Outros motivos: {v('outros_motivos')}
O que conhece sobre o serviço do AEE: {v('conhecimento_aee')}

3. INFORMAÇÕES SOBRE A SAÚDE
Possui doença preexistente: {v('doenca_preexistente')}
Convulsões: {v('convulsoes')}
Acompanhamentos profissionais: {v('acompanhamentos')}
Outro acompanhamento: {v('acompanhamento_outro')}
Frequência: {v('frequencia_acompanhamento')}   Outra: {v('frequencia_outro')}
Alimentação saudável: {v('alimentacao_saudavel')}
Seletividade alimentar: {v('seletividade_alimentar')}
Dieta sensorial: {v('dieta_sensorial')}
Usa suplemento alimentar: {v('suplemento_alimentar')}   Qual: {v('suplemento_qual')}
Alimenta-se por sonda: {v('alimenta_sonda')}
Dorme bem: {v('dorme_bem')}
Faz uso de medicação: {v('medicacao')}   Qual(is): {v('medicacao_qual')}
Tempo de medicação/tratamentos realizados: {v('tempo_medicacao_tratamentos')}
Outras observações de saúde: {v('obs_saude')}

4. DESENVOLVIMENTO PSICOMOTOR
Lateralidade: {v('lateralidade')}
Estereotipias: {v('estereotipias')}   Qual(is): {v('estereotipias_quais')}
Segura objetos com as duas mãos: {v('segura_objetos_duas_maos')}
Tamanho dos objetos que segura: {v('tamanho_objetos')}
Faz a pega correta do lápis: {v('pega_lapis')}
Engatinhou: {v('engatinhou')}   Andou com que idade: {v('idade_andou')}
Usa fraldas na escola: {v('usa_fraldas')}
Usa sonda de alívio: {v('usa_sonda_alivio')}
Autonomia nas atividades: {v('autonomia_atividades')}
Outras atividades de autonomia: {v('autonomia_outros')}
Atende comandos: {v('atende_comandos')}
Gosta do toque: {v('gosta_toque')}
Outras observações psicomotoras: {v('obs_psicomotor')}

5. LINGUAGEM
Verbal: {v('verbal')}
Consegue se comunicar: {v('consegue_comunicar')}
Problemas na fala: {v('problemas_fala')}
Ecolalia: {v('ecolalia')}
Consegue dar recado: {v('da_recado')}
Usa comunicação alternativa: {v('comunicacao_alternativa')}   Qual: {v('comunicacao_alternativa_qual')}

6. SOCIALIZAÇÃO
Relação com pai: {v('relacao_pai')}
Relação com mãe: {v('relacao_mae')}
Relação com parentes: {v('relacao_parentes')}
Relação com irmãos: {v('relacao_irmaos')}
Relação com outros estudantes: {v('relacao_estudantes')}
Tem melhor amigo(a): {v('tem_melhor_amigo')}   Tipo: {v('tipo_melhor_amigo')}
Adapta-se ao ambiente: {v('adapta_ambiente')}
Flexível na rotina: {v('flexivel_rotina')}
Respeita regras: {v('respeita_regras')}
Chora com facilidade: {v('chora_facilidade')}
Brinca como: {v('brinca_como')}
Interesses e lazer: {v('interesses_lazer')}
O que a família mais gosta no(a) estudante: {v('familia_gosta')}
O que a família considera necessário melhorar: {v('familia_nao_gosta')}
Ambiente físico em casa para estudos/brincadeiras: {v('ambiente_estudo_casa')}

7. CONTEXTO FAMILIAR
Principais habilidades:
{v('habilidades')}

Principais oportunidades de melhoria:
{v('oportunidades_melhoria')}

8. OUTRAS INFORMAÇÕES
{v('outras_info_familia')}

____________________, ____ de __________________________ de ____________
Assinatura do responsável: ______________________________________________
Professor(a) AEE: ______________________________________________________
""".strip()


def texto_estudo_plano_aee_gre(estudante, estudo=None, plano=None):
    if estudo is None:
        estudo = ultima_linha("estudos_caso", CAMPOS_ESTUDO_CASO, estudante[0])
    if plano is None:
        plano = ultima_linha(
            "planos_aee",
            CAMPOS_PLANO_AEE,
            estudante[0],
        )

    dados_estudo = dict(zip(CAMPOS_ESTUDO_CASO, estudo or []))
    def e(campo):
        valor = dados_estudo.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    dados_plano = {}
    if plano:
        valores_plano = list(plano)
        if len(valores_plano) == len(CAMPOS_PLANO_AEE):
            dados_plano = dict(zip(CAMPOS_PLANO_AEE, valores_plano))
        else:
            chaves_antigas = ["data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias", "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias", "avaliacao_acompanhamento", "observacoes"]
            dados_plano = dict(zip(chaves_antigas, valores_plano))

    def p(campo):
        valor = dados_plano.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    return f"""
{texto_cabecalho_gre("ESTUDO DE CASO E PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO")}

O Plano de Atendimento Educacional Especializado deverá garantir os registros avaliativos do estudante público-alvo da educação especial, considerando as observações do professor do AEE, a eliminação de barreiras e a busca por recursos de acessibilidade necessários à promoção da autonomia e da aprendizagem.

PARTE 1 - IDENTIFICAÇÃO DO(A) ESTUDANTE
Código interno: {estudante[1] or 'Não informado.'}
Ano/Série cadastrado: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}   Turno: {estudante[6] or 'Não informado.'}
Perfil educacional: {estudante[4] or 'Não informado.'}

{texto_campos_sensiveis_gre_estudante()}

1.5 Etapa/modalidade: {e('etapa_modalidade')}
Ano/etapa: {e('ano_etapa')}
1.6 Turma e turno: {estudante[3] or 'Não informado.'} / {estudante[6] or 'Não informado.'}
1.7 Apresenta laudo? {e('laudo')}
1.8 Apresenta deficiência? {e('deficiencia')}   CID: {e('cid')}
1.9 Altas habilidades/superdotação: {e('altas_habilidades')}
1.10 Usuário de BPC? {e('bpc')}
1.11 Escola do ensino comum: {e('escola_nome')}
1.12 Unidade educacional onde é atendido pelo AEE: {e('unidade_aee')}
1.13 Gestor(a) e contato: {e('gestor_nome')} - {e('gestor_contato')}
1.14 Professor(a) AEE e contato: {e('professor_nome')} - {e('professor_contato')}
1.15 Matrícula do(a) professor(a) AEE: {e('matricula_professor')}
1.16 Especialidade do(a) professor(a) AEE: {e('especialidade_professor')}
1.17 Período de elaboração do plano - início: {e('periodo_inicio')}
1.18 Data final: {e('periodo_fim')}
1.19 Frequência de atendimento na SRM: {e('frequencia_atendimento') or estudante[7] or 'Não informado.'}
1.20 Tempo de atendimento por semana: {e('tempo_atendimento_semana')}
1.21 Formato do atendimento: {e('formato_atendimento')}

PARTE 2 - ESTUDO DE CASO / PERCURSO EDUCACIONAL
Relato sobre o trajeto educacional em turmas comuns e no AEE anterior:
{e('percurso_educacional')}

2.1 Motivo de encaminhamento ao AEE:
{e('motivo_encaminhamento_aee') or e('queixa_principal')}

2.2 Precisa de transporte escolar inclusivo? {e('precisa_transporte_inclusivo')}
2.2.1 Recebe transporte escolar inclusivo? {e('recebe_transporte_inclusivo')}
2.3 Precisa de profissional de apoio? {e('precisa_profissional_apoio')}
Justificativa: {e('justificativa_apoio')}
2.3.1 É acompanhado por profissional de apoio? {e('acompanhado_profissional_apoio')}
Nome do apoio: {e('nome_profissional_apoio')}
2.4 Recursos de tecnologia educacional e/ou assistiva utilizados:
{e('recursos_tecnologia_assistiva')}
2.5 Observações relevantes para o ambiente educacional/acompanhamento terapêutico:
{e('observacoes_ambiente_educacional')}
2.6 Habilidades observadas e desenvolvidas:
{e('habilidades_observadas') or e('potencialidades')}
2.7 Habilidades que precisam ser desenvolvidas:
{e('habilidades_a_desenvolver') or e('dificuldades')}
2.8 Indicadores de altas habilidades/superdotação:
{e('indicadores_altas_habilidades')}
2.9 Caso seja pessoa surda, recursos utilizados:
{e('recursos_surdez')}
Observações sobre surdez/audição/comunicação:
{e('observacoes_surdez')}

SÍNTESE PEDAGÓGICA DO ESTUDO DE CASO
Contextualização:
{e('contextualizacao')}

Potencialidades:
{e('potencialidades')}

Dificuldades/barreiras observadas:
{e('dificuldades')}

Estratégias pedagógicas já utilizadas:
{e('estrategias')}

Intervenções/encaminhamentos sugeridos:
{e('intervencoes')}

Avaliação:
{e('avaliacao')}

Considerações finais:
{e('consideracoes')}

PARTE 3 - PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO
1. Habilidades prioritárias que serão trabalhadas na SRM:
{p('habilidades_prioritarias')}

2. Recursos de acessibilidade que serão disponibilizados:
{p('recursos_acessibilidade')}

3. Objetivos do AEE
3.1 Objetivo geral:
{p('objetivos_gerais')}

3.2 Objetivos específicos:
{p('objetivos_especificos')}

4. Metodologias e estratégias
4.1 Metodologia:
{p('metodologia')}

4.2 Estratégia:
{p('estrategias')}

4.3 Prazo:
{p('prazo')}

5. Ações desenvolvidas no âmbito da escola:
{p('acoes_escola')}

6. Barreiras identificadas na comunidade escolar:
{p('barreiras_identificadas')}

7. Parcerias realizadas pelo AEE:
{p('parcerias')}

8. Avaliação e acompanhamento:
{p('avaliacao_acompanhamento')}

9. Observações:
{p('observacoes')}

____________________, ____ de __________________________ de ____________
Professor(a) AEE: _______________________________________
Coordenação/Gestão: _____________________________________
Responsável: ____________________________________________
""".strip()


def resumo_indicadores_atendimentos(estudante_id):
    atendimentos = listar_atendimentos(estudante_id)
    if not atendimentos:
        return "Nenhum atendimento registrado."
    total = len(atendimentos)
    def media(indice):
        valores = []
        for a in atendimentos:
            try:
                valores.append(float(a[indice]))
            except Exception:
                pass
        return round(sum(valores)/len(valores), 1) if valores else "Não informado"
    return f"""
Total de atendimentos registrados: {total}
Média da resposta do estudante: {media(8)}/10
Média do avanço pedagógico: {media(9)}/10
Média da dificuldade/barreira observada: {media(10)}/10
Média do engajamento/participação: {media(11)}/10
Média do índice geral de evolução: {media(12)}/10
""".strip()


def gerar_relatorio_gre_texto(estudante):
    avaliacao = ultima_avaliacao(estudante[0])
    entrevista = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante[0])
    estudo = ultima_linha("estudos_caso", CAMPOS_ESTUDO_CASO, estudante[0])
    plano = ultima_linha(
        "planos_aee",
        CAMPOS_PLANO_AEE,
        estudante[0],
    )

    return f"""
{texto_cabecalho_gre("RELATÓRIO CONSOLIDADO GRE - ATENDIMENTO EDUCACIONAL ESPECIALIZADO")}

1. IDENTIFICAÇÃO SEGURA DO ESTUDANTE
Código interno: {estudante[1] or 'Não informado.'}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Turno: {estudante[6] or 'Não informado.'}
Perfil educacional: {estudante[4] or 'Não informado.'}
Dias de atendimento: {estudante[7] or 'Não informado.'}
Horário preferencial: {estudante[8] or 'Não informado.'}

{texto_campos_sensiveis_gre_estudante()}

2. PROFESSOR(A) AEE RESPONSÁVEL
{texto_professores_vinculados(estudante[0])}

3. SÍNTESE DO CADASTRO PEDAGÓGICO
{estudante[5] or 'Não informado.'}

4. SÍNTESE DA ENTREVISTA COM A FAMÍLIA
{texto_entrevista_familia_gre(estudante, entrevista) if entrevista else 'Nenhuma entrevista registrada.'}

5. AVALIAÇÃO PEDAGÓGICA
{texto_avaliacao(estudante, ('', *avaliacao)) if avaliacao else 'Nenhuma avaliação registrada.'}

6. ESTUDO DE CASO E PLANO AEE
{texto_estudo_plano_aee_gre(estudante, estudo, plano) if (estudo or plano) else 'Nenhum estudo de caso ou plano registrado.'}

7. INDICADORES DOS ATENDIMENTOS
{resumo_indicadores_atendimentos(estudante[0])}

8. HISTÓRICO DOS ATENDIMENTOS
{listar_atendimentos_texto(estudante[0])}

9. ENCAMINHAMENTOS GERAIS
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________

10. CONSIDERAÇÕES FINAIS
_______________________________________________________________________
_______________________________________________________________________
_______________________________________________________________________

11. ASSINATURAS
Professor(a) AEE: _______________________________________
Coordenação/Gestão: _____________________________________
Responsável: ____________________________________________
""".strip()


def texto_pacote_gre_completo(estudante):
    return f"""
PACOTE GRE COMPLETO - INCLUISRM
Código interno do estudante: {estudante[1] or 'Não informado.'}

======================================================================
DOCUMENTO 1 - FICHA DE IDENTIFICAÇÃO PROFESSOR(A) AEE
======================================================================
{texto_ficha_professor_gre()}


======================================================================
DOCUMENTO 2 - MATRÍCULA SRM / TERMO DE CIÊNCIA
======================================================================
{texto_matricula_srm_gre(estudante)}


======================================================================
DOCUMENTO 3 - ENTREVISTA COM A FAMÍLIA
======================================================================
{texto_entrevista_familia_gre(estudante)}


======================================================================
DOCUMENTO 4 - ESTUDO DE CASO E PLANO AEE
======================================================================
{texto_estudo_plano_aee_gre(estudante)}


======================================================================
DOCUMENTO 5 - RELATÓRIO CONSOLIDADO GRE
======================================================================
{gerar_relatorio_gre_texto(estudante)}
""".strip()

# ======================================================
# DATAFRAMES / GRÁFICOS
# ======================================================
def montar_dataframe_evolucao(atendimentos):
    dados = []
    for atendimento in reversed(atendimentos):
        data_atendimento = atendimento[0]
        avancos = atendimento[4]
        dificuldades = atendimento[5]
        evolucao = atendimento[6]
        nivel_resposta = limitar_escala(atendimento[8] if len(atendimento) > 8 else 5)
        nivel_avanco = limitar_escala(atendimento[9] if len(atendimento) > 9 else 5)
        nivel_dificuldade = limitar_escala(atendimento[10] if len(atendimento) > 10 else 5)
        nivel_engajamento = limitar_escala(atendimento[11] if len(atendimento) > 11 else 5)
        indice = calcular_indice_geral(nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento)

        try:
            data_ordenacao = datetime.strptime(data_atendimento, "%d/%m/%Y")
        except Exception:
            data_ordenacao = None

        dados.append(
            {
                "Data": data_atendimento,
                "Data ordenação": data_ordenacao,
                "Resposta do estudante": nivel_resposta,
                "Avanço pedagógico": nivel_avanco,
                "Nível de dificuldade": nivel_dificuldade,
                "Engajamento": nivel_engajamento,
                "Índice geral de evolução": indice,
                "Interpretação": interpretar_indice(indice),
                "Avanços": avancos or "Não informado.",
                "Dificuldades observadas": dificuldades or "Não informado.",
                "Evolução observada": evolucao or "Não informado.",
            }
        )
    df = pd.DataFrame(dados)
    if not df.empty and "Data ordenação" in df.columns:
        df = df.sort_values(by="Data ordenação", na_position="last")
    return df


def render_grafico_evolucao(atendimentos):
    df = montar_dataframe_evolucao(atendimentos)
    if df.empty:
        st.warning("Este estudante ainda não possui atendimentos registrados.")
        return

    df = df.copy()
    df["Ordem"] = range(1, len(df) + 1)
    contagem_datas = df.groupby("Data").cumcount() + 1
    repetidas = df["Data"].duplicated(keep=False)
    df["Atendimento"] = df["Data"]
    df.loc[repetidas, "Atendimento"] = df.loc[repetidas, "Data"] + " #" + contagem_datas.loc[repetidas].astype(str)

    indicadores = [
        "Resposta do estudante",
        "Avanço pedagógico",
        "Nível de dificuldade",
        "Engajamento",
        "Índice geral de evolução",
    ]
    for col in indicadores:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(5).clip(1, 10)

    df_long = df.melt(
        id_vars=["Atendimento", "Data", "Interpretação"],
        value_vars=indicadores,
        var_name="Indicador",
        value_name="Pontuação",
    )

    grafico = (
        alt.Chart(df_long)
        .mark_bar()
        .encode(
            x=alt.X("Atendimento:N", title="Data / atendimento", sort=None),
            xOffset=alt.XOffset("Indicador:N"),
            y=alt.Y("Pontuação:Q", title="Pontuação", scale=alt.Scale(domain=[0, 10])),
            color=alt.Color("Indicador:N", title="Indicador"),
            tooltip=["Data", "Indicador", "Pontuação", "Interpretação"],
        )
        .properties(height=360)
    )
    st.altair_chart(grafico, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Atendimentos", len(df))
    col2.metric("Média do índice", f"{df['Índice geral de evolução'].mean():.1f}/10")
    col3.metric("Último índice", f"{df['Índice geral de evolução'].iloc[-1]:.1f}/10")
    col4.metric("Variação", f"{df['Índice geral de evolução'].iloc[-1] - df['Índice geral de evolução'].iloc[0]:+.1f}")

    with st.expander("Ver dados usados no gráfico"):
        st.dataframe(df, use_container_width=True, hide_index=True)


# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    try:
        st.markdown('<div class="sidebar-logo-card">', unsafe_allow_html=True)
        st.image(LOGO_PATH, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception:
        st.markdown('<div class="sidebar-title">INCLUISRM</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sidebar-subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

    st.markdown("---")

    menu = st.radio(
        "Navegação",
        [
            "Dashboard",
            "Cadastro do Estudante",
            "Cadastro do Professor AEE",
            "Entrevista com a Família",
            "Avaliação Pedagógica",
            "Articulação Pedagógica Inclusiva",
            "Estudo de Caso",
            "Plano AEE - IA",
            "Agenda de Atendimentos",
            "Atendimentos",
            "Relatórios GRE",
            "Administração",
        ],
        index=0,
        key="menu_atual"  # 🔥 ESSA LINHA É A CHAVE
    )

    st.markdown("---")
    st.caption("LabTec3DI – UFRPE")
    st.caption(APP_SUBTITLE)


render_app_header()

# ======================================================
# DASHBOARD
# ======================================================
if menu == "Dashboard":
    # Dashboard compacto para visualizar o ecossistema em uma única tela.
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.8rem !important;
            padding-bottom: 1.2rem !important;
            max-width: 1550px !important;
        }
        .app-hero {
            padding: 18px 24px !important;
            margin-bottom: 14px !important;
            border-radius: 18px !important;
        }
        .app-title {
            font-size: 30px !important;
        }
        .app-subtitle {
            font-size: 14px !important;
            margin-top: 4px !important;
        }
        .app-badge {
            font-size: 12px !important;
            padding: 4px 10px !important;
            margin-bottom: 6px !important;
        }
        .subtitulo {
            font-size: 21px !important;
            margin-bottom: 8px !important;
        }
        [data-testid="stMetric"] {
            padding: 12px 14px !important;
            min-height: 82px !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 27px !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 13px !important;
        }
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
            padding-top: 8px !important;
            padding-bottom: 8px !important;
        }
        h3 {
            font-size: 21px !important;
            margin-top: 0.15rem !important;
            margin-bottom: 0.35rem !important;
        }
        hr {
            margin-top: 0.7rem !important;
            margin-bottom: 0.7rem !important;
        }
        .stDataFrame {
            margin-top: 0.2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="subtitulo">📊 Painel inicial</div>', unsafe_allow_html=True)

    with st.spinner("Carregando painel..."):
        estudantes = listar_estudantes()
        total_estudantes = len(estudantes)
        total_avaliacoes = contar_registros_tabela("avaliacoes")
        total_atendimentos = contar_registros_tabela("atendimentos")
        total_agenda = contar_registros_tabela("agenda")
        total_escutas_docentes = contar_registros_tabela("escutas_docentes")
        total_relatorios_docente = contar_registros_tabela("relatorios_docente")

        try:
            ult_avaliacoes = carregar_tabela_dataframe("avaliacoes").sort_values("id", ascending=False).head(1)
        except Exception:
            ult_avaliacoes = pd.DataFrame()
        try:
            ult_escutas = carregar_tabela_dataframe("escutas_docentes").sort_values("id", ascending=False).head(1)
        except Exception:
            ult_escutas = pd.DataFrame()
        try:
            ult_relatorios = carregar_tabela_dataframe("relatorios_docente").sort_values("id", ascending=False).head(1)
        except Exception:
            ult_relatorios = pd.DataFrame()

    # Métricas principais em uma única linha para reduzir rolagem.
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Estudantes", total_estudantes)
    col2.metric("Avaliações", total_avaliacoes)
    col3.metric("Atendimentos", total_atendimentos)
    col4.metric("Agenda", total_agenda)
    col5.metric("Escutas", total_escutas_docentes)
    col6.metric("Relatórios", total_relatorios_docente)

    st.markdown("---")

    # Visão única do ecossistema: memória, articulação, IA e fluxo na mesma tela.
    col_esq, col_centro, col_dir = st.columns([1.15, 1.05, 1.05])

    with col_esq:
        with st.container(border=True):
            st.markdown("### 👥 Estudantes recentes")
            if estudantes:
                st.dataframe(
                    [
                        {
                            "Código": e[1],
                            "Ano/Série": e[2],
                            "Turma": e[3],
                            "Perfil": e[4],
                            "Dias": e[7],
                        }
                        for e in estudantes[:6]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    height=185,
                )
            else:
                st.info("Nenhum estudante cadastrado ainda.")

        with st.container(border=True):
            st.markdown("### 🧠 IA Pedagógica")
            if OpenAI is not None and os.getenv("OPENAI_API_KEY"):
                st.success("IA configurada para gerar sínteses pedagógicas e relatórios de apoio ao docente.")
            else:
                st.warning("IA ainda não configurada. Configure OPENAI_API_KEY para ativar a geração automática.")

    with col_centro:
        with st.container(border=True):
            st.markdown("### 🧭 Fluxo pedagógico sugerido")
            st.markdown(
                """
                1. Cadastro do estudante com código interno.  
                2. Entrevista familiar e avaliação pedagógica inicial.  
                3. Documentos históricos e avaliações extras.  
                4. Estudo de caso e Plano AEE - IA.  
                5. Escuta Docente da sala regular.  
                6. Atendimentos e evolução pedagógica.  
                7. Relatório Pedagógico de Apoio ao Docente.  
                8. Relatórios GRE quando necessário.
                """
            )

    with col_dir:
        with st.container(border=True):
            st.markdown("### 🔗 Articulação Inclusiva")
            st.write(f"Escutas docentes registradas: **{total_escutas_docentes}**")
            st.write(f"Relatórios de apoio gerados: **{total_relatorios_docente}**")
            st.write(f"Avaliações pedagógicas: **{total_avaliacoes}**")
            st.write(f"Atendimentos AEE: **{total_atendimentos}**")

        with st.container(border=True):
            st.markdown("### 🧩 Últimos registros")
            if not ult_avaliacoes.empty:
                st.write(f"**Avaliação:** {ult_avaliacoes.iloc[0].get('data_registro', 'Data não informada')}")
            else:
                st.write("**Avaliação:** nenhuma")

            if not ult_escutas.empty:
                componente = ult_escutas.iloc[0].get('componente_curricular', 'Área não informada')
                codigo_docente = ult_escutas.iloc[0].get('codigo_docente', 'Docente não informado')
                st.write(f"**Escuta:** {componente} • {codigo_docente}")
            else:
                st.write("**Escuta:** nenhuma")

            if not ult_relatorios.empty:
                st.write(f"**Relatório:** {ult_relatorios.iloc[0].get('data_geracao', 'Data não informada')}")
            else:
                st.write("**Relatório:** nenhum")

# ======================================================
# CADASTRO DO ESTUDANTE
# ======================================================
elif menu == "Cadastro do Estudante":
    st.markdown('<div class="subtitulo">👤 Cadastro do estudante</div>', unsafe_allow_html=True)

    col_form, col_lista = st.columns([1, 1.2])
    with col_form:
        with st.container(border=True):
            st.markdown("### Novo estudante")
            with st.form(get_form_key("cadastro_estudante"), clear_on_submit=True):
                codigo = st.text_input("Código interno / matrícula segura", placeholder="Ex.: AEE-2026-001")
                ano_serie = st.text_input("Ano/Série", placeholder="Ex.: 8º ano")
                turma = st.text_input("Turma", placeholder="Ex.: 8º ano A")
                turno = st.selectbox("Turno", ["Não informado", "Manhã", "Tarde", "Noite", "Integral"])
                perfil = st.selectbox("Perfil educacional informado", PERFIS)
                dias = st.multiselect("Dias preferenciais de atendimento", DIAS_SEMANA)
                horario = st.text_input("Horário preferencial", placeholder="Ex.: 08:00 às 08:50")
                observacoes = st.text_area("Observações pedagógicas iniciais")
                enviar = st.form_submit_button("Cadastrar estudante")

                if enviar:
                    if not codigo.strip():
                        st.error("Informe um código interno para o estudante.")
                    else:
                        try:
                            cadastrar_estudante(codigo.strip(), ano_serie, turma, turno, perfil, observacoes, ", ".join(dias), horario)
                            st.success("Estudante cadastrado com sucesso.")
                            resetar_form("cadastro_estudante")
                            st.rerun()

                        except INTEGRITY_ERRORS:
                            st.error("Este código já existe. Use outro código interno.")

    with col_lista:
        with st.container(border=True):
            st.markdown("### 📋 Estudantes cadastrados")
            estudantes = listar_estudantes()
            if estudantes:
                st.dataframe(
                    [
                        {
                            "ID": e[0], "Código": e[1], "Ano/Série": e[2], "Turma": e[3],
                            "Turno": e[6], "Perfil": e[4], "Dias": e[7], "Horário": e[8],
                        }
                        for e in estudantes
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Nenhum estudante cadastrado ainda.")

    with st.container(border=True):
        st.markdown("### ✏️ Editar, excluir ou exportar cadastro")
        estudantes = listar_estudantes()
        if estudantes:
            ids, mapa = opcoes_estudantes_por_id(estudantes)
            estudante_id = st.selectbox("Selecione o estudante", ids, format_func=lambda x: mapa[x], key="edit_estudante")
            estudante = buscar_estudante(estudante_id)
            with st.expander("Editar cadastro"):
                with st.form(f"form_edit_estudante_{estudante_id}"):
                    codigo_e = st.text_input("Código interno", value=estudante[1] or "")
                    ano_e = st.text_input("Ano/Série", value=estudante[2] or "")
                    turma_e = st.text_input("Turma", value=estudante[3] or "")
                    turno_e = st.selectbox("Turno", ["Não informado", "Manhã", "Tarde", "Noite", "Integral"], index=["Não informado", "Manhã", "Tarde", "Noite", "Integral"].index(estudante[6]) if estudante[6] in ["Não informado", "Manhã", "Tarde", "Noite", "Integral"] else 0)
                    perfil_e = st.selectbox("Perfil", PERFIS, index=PERFIS.index(estudante[4]) if estudante[4] in PERFIS else 0)
                    dias_e = st.text_input("Dias de atendimento", value=estudante[7] or "")
                    horario_e = st.text_input("Horário preferencial", value=estudante[8] or "")
                    obs_e = st.text_area("Observações", value=estudante[5] or "")
                    if st.form_submit_button("Salvar alterações"):
                        atualizar_estudante(estudante_id, codigo_e, ano_e, turma_e, turno_e, perfil_e, obs_e, dias_e, horario_e)
                        st.success("Cadastro atualizado.")
                        st.rerun()

            texto = texto_cadastro_estudante(estudante)
            export_buttons(texto, f"Cadastro_Estudante_{estudante[1]}", tipo_pdf="cadastro")

            confirmar = st.checkbox("Confirmar exclusão do estudante e de todos os registros vinculados", key="conf_excluir_est")
            if st.button("Excluir estudante", key="btn_excluir_est"):
                if confirmar:
                    excluir_estudante(estudante_id)
                    st.success("Estudante excluído.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de excluir.")


# ======================================================
# CADASTRO DO PROFESSOR AEE
# ======================================================
elif menu == "Cadastro do Professor AEE":
    st.markdown('<div class="subtitulo">👨‍🏫 Cadastro do Professor AEE</div>', unsafe_allow_html=True)
    st.caption("Protótipo personalizado: o sistema considera o professor cadastrado mais recente como professor responsável pelos estudantes e relatórios.")

    if "prof_form_nonce" not in st.session_state:
        st.session_state["prof_form_nonce"] = 0

    nonce = st.session_state["prof_form_nonce"]

    # ===============================
    # FORMULÁRIO DE CADASTRO
    # ===============================
    with st.container(border=True):
        st.markdown("### Novo cadastro profissional")
        st.caption("Ao salvar, a página será atualizada e o formulário aparecerá limpo.")

        with st.form(f"form_professor_{nonce}", clear_on_submit=True):
            nome_ref = st.text_input(
                "Nome de referência / nome profissional",
                key=f"prof_nome_{nonce}",
            )
            escola = st.text_input(
                "Escola",
                key=f"prof_escola_{nonce}",
            )
            regional = st.text_input(
                "Regional / GRE",
                key=f"prof_regional_{nonce}",
            )
            formacao = st.text_area(
                "Formação",
                key=f"prof_formacao_{nonce}",
            )
            carga = st.text_input(
                "Carga horária",
                key=f"prof_carga_{nonce}",
            )
            turno = st.text_input(
                "Turno de atuação",
                key=f"prof_turno_{nonce}",
            )
            obs = st.text_area(
                "Observações",
                key=f"prof_obs_{nonce}",
            )

            salvar = st.form_submit_button("Salvar cadastro do professor")

        if salvar:
            if not nome_ref.strip():
                st.error("Informe pelo menos o nome de referência do professor.")
            else:
                salvar_professor(nome_ref, escola, regional, formacao, carga, turno, obs)
                st.success("Cadastro do professor salvo com sucesso.")
                st.session_state["prof_form_nonce"] += 1
                st.rerun()

    # ===============================
    # HISTÓRICO DO PROFESSOR
    # ===============================
    with st.container(border=True):
        st.markdown("### Histórico")

        professores = listar_professores()

        if professores:
            st.dataframe(
                [
                    {
                        "ID": p[0],
                        "Nome referência": p[1],
                        "Escola": p[2],
                        "Regional": p[3],
                        "Carga horária": p[5],
                        "Turno": p[6],
                        "Responsável atual": "Sim" if i == 0 else "Não",
                    }
                    for i, p in enumerate(professores)
                ],
                use_container_width=True,
                hide_index=True,
            )

            professor_atual = professores[0]
            st.success(
                f"Professor responsável atual nos documentos: {professor_atual[1] or 'Sem nome'}"
            )

            for p in professores:
                rotulo = "responsável atual" if p[0] == professor_atual[0] else "registro anterior"
                with st.expander(f"Professor(a) #{p[0]} - {p[1] or 'Sem nome'} ({rotulo})"):
                    texto = texto_professor(p)
                    st.text(texto)
                    export_buttons(texto, f"Ficha_Professor_AEE_{p[0]}", tipo_pdf="professor")

                    st.markdown("---")
                    st.markdown("### ✏️ Editar cadastro")

                    with st.form(f"edit_professor_{p[0]}"):
                        nome_e = st.text_input("Nome referência", value=p[1] or "", key=f"edit_prof_nome_{p[0]}")
                        escola_e = st.text_input("Escola", value=p[2] or "", key=f"edit_prof_escola_{p[0]}")
                        regional_e = st.text_input("Regional/GRE", value=p[3] or "", key=f"edit_prof_regional_{p[0]}")
                        formacao_e = st.text_area("Formação", value=p[4] or "", key=f"edit_prof_formacao_{p[0]}")
                        carga_e = st.text_input("Carga horária", value=p[5] or "", key=f"edit_prof_carga_{p[0]}")
                        turno_e = st.text_input("Turno", value=p[6] or "", key=f"edit_prof_turno_{p[0]}")
                        obs_e = st.text_area("Observações", value=p[7] or "", key=f"edit_prof_obs_{p[0]}")

                        if st.form_submit_button("💾 Atualizar cadastro"):
                            atualizar_professor(
                                p[0],
                                nome_e,
                                escola_e,
                                regional_e,
                                formacao_e,
                                carga_e,
                                turno_e,
                                obs_e,
                            )
                            st.success("Cadastro atualizado com sucesso.")
                            st.rerun()

                    st.markdown("---")
                    st.markdown("### 🗑️ Excluir professor")
                    st.caption("Ao excluir o professor, o sistema passará a considerar o cadastro mais recente restante como responsável.")

                    confirmar_exclusao = st.checkbox(
                        "Confirmar exclusão deste professor",
                        key=f"confirmar_excluir_prof_{p[0]}",
                    )

                    if st.button("Excluir professor", key=f"excluir_professor_{p[0]}"):
                        if confirmar_exclusao:
                            excluir_professor(p[0])
                            st.warning("Professor excluído com sucesso.")
                            st.rerun()
                        else:
                            st.warning("Marque a confirmação antes de excluir.")
        else:
            st.info("Nenhum professor cadastrado.")
            st.warning("Cadastre seus dados profissionais para que eles apareçam nos relatórios e documentos.")


# ENTREVISTA COM A FAMÍLIA
# ======================================================
elif menu == "Entrevista com a Família":
    st.markdown('<div class="subtitulo">👪 Entrevista com a Família</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()

    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="entrevista_estudante",
        )
        estudante = buscar_estudante(estudante_id)

        with st.container(border=True):
            st.markdown("### Nova entrevista com a família")
            st.caption("Dados organizados conforme o roteiro de entrevista familiar do AEE. Campos sensíveis continuam para preenchimento manual nos documentos impressos.")

            with st.form("form_entrevista_completa"):
                ano_padrao_entrevista = str(agora_local().year)
                anos_opcoes_entrevista = [str(a) for a in range(2020, agora_local().year + 4)]
                idx_ano_entrevista = anos_opcoes_entrevista.index(ano_padrao_entrevista) if ano_padrao_entrevista in anos_opcoes_entrevista else 0

                st.markdown("### 📅 Identificação do registro")
                col_ano_ent, col_tipo_ent = st.columns(2)
                with col_ano_ent:
                    ano_letivo_entrevista = st.selectbox(
                        "Ano letivo da entrevista familiar",
                        anos_opcoes_entrevista,
                        index=idx_ano_entrevista,
                        key="entrevista_ano_letivo",
                    )
                with col_tipo_ent:
                    tipo_registro_entrevista = st.selectbox(
                        "Tipo de registro",
                        OPCOES_TIPO_ENTREVISTA_FAMILIA,
                        key="entrevista_tipo_registro",
                    )
                st.caption(
                    "Use 'Registro histórico' para lançar entrevistas de anos anteriores e 'Entrevista familiar atual' para o ano em acompanhamento."
                )

                st.markdown("### 🧾 1. Informações diversas")
                col1, col2 = st.columns(2)
                with col1:
                    auxilio_governamental = st.radio("A família participa de programa de auxílio governamental?", ["Não", "Sim"], horizontal=True)
                    auxilio_quais = st.text_input("Qual(is) programa(s)?")
                    historico_familiar = st.radio("Há histórico de doenças graves, deficiência ou transtornos na família?", ["Não", "Sim"], horizontal=True)
                    historico_quais = st.text_input("Qual(is) histórico(s)?")
                    repetiu_ano = st.radio("O estudante já repetiu de ano?", ["Não", "Sim"], horizontal=True)
                    repetiu_qtd = st.number_input("Quantas vezes repetiu?", min_value=0, max_value=20, value=0)
                with col2:
                    trocou_escola = st.radio("O estudante trocou de escola?", ["Não", "Sim"], horizontal=True)
                    trocou_qtd = st.number_input("Quantas vezes trocou de escola?", min_value=0, max_value=20, value=0)
                    motivo_troca = st.text_area("Por qual motivo trocou de escola?")
                    situacao_escolar = st.radio("Em relação à escola, o estudante é:", ["Não informado", "Novato(a)", "Veterano(a)"], horizontal=True)

                st.markdown("### 🏫 Relação com a escola")
                col1, col2, col3 = st.columns(3)
                with col1:
                    interesse_escola = st.radio("Demonstra interesse em frequentar a escola?", ["Não", "Sim", "Não informado"], horizontal=True)
                    organiza_materiais = st.radio("Cuida/organiza seus materiais?", ["Não", "Sim", "Não informado"], horizontal=True)
                    resistencia_escola = st.radio("Apresenta resistência à escola?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col2:
                    relacao_colegas = st.radio("Relaciona-se bem com colegas?", ["Não", "Sim", "Não informado"], horizontal=True)
                    relacao_professores = st.radio("Relaciona-se bem com professores?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col3:
                    leva_alimentacao = st.radio("Leva alimentação de casa?", ["Não", "Sim", "Não informado"], horizontal=True)
                    merenda_escolar = st.radio("Alimenta-se da merenda escolar?", ["Não", "Sim", "Não informado"], horizontal=True)
                    alergia_alimentar = st.radio("Possui alergia alimentar?", ["Não", "Sim", "Não informado"], horizontal=True)
                    alergia_quais = st.text_input("Qual(is) alergia(s)?")
                obs_diversas = st.text_area("Outras observações relevantes sobre escola/família")

                st.markdown("### 🏫 1.1 Sobre a escolha da escola")
                motivo_escolha_lista = st.multiselect(
                    "Motivo da escolha da escola",
                    [
                        "Proximidade de casa",
                        "Tem o serviço do AEE",
                        "Irmãos matriculados na unidade educacional",
                        "Escola com boas referências",
                        "A unidade tem EJAI / estudante fora de faixa",
                        "Outro",
                    ],
                )
                motivo_escolha = ", ".join(motivo_escolha_lista)
                outros_motivos = st.text_area("Outros motivos da escolha")
                conhecimento_aee = st.text_area("O que a família conhece sobre o serviço do AEE?")

                st.markdown("### 🩺 2. Informações sobre a saúde do estudante")
                col1, col2, col3 = st.columns(3)
                with col1:
                    doenca_preexistente = st.radio("Possui doença preexistente?", ["Não", "Sim", "Não informado"], horizontal=True)
                    convulsoes = st.radio("Apresenta convulsões?", ["Não", "Sim", "Não informado"], horizontal=True)
                    acompanhamentos_lista = st.multiselect(
                        "Possui acompanhamento de",
                        ["Fonoaudiólogo", "Terapeuta Ocupacional", "Fisioterapeuta", "Psicólogo", "Outro"],
                    )
                    acompanhamentos = ", ".join(acompanhamentos_lista)
                    acompanhamento_outro = st.text_input("Outro acompanhamento")
                with col2:
                    frequencia_acompanhamento = st.selectbox("Frequência dos acompanhamentos", ["Não informado", "1x na semana", "2x na semana", "Quinzenalmente", "Outro"])
                    frequencia_outro = st.text_input("Outra frequência")
                    alimentacao_saudavel = st.radio("Tem alimentação saudável?", ["Não", "Sim", "Não informado"], horizontal=True)
                    seletividade_alimentar = st.radio("Possui seletividade alimentar?", ["Não", "Sim", "Não informado"], horizontal=True)
                    dieta_sensorial = st.radio("Possui dieta sensorial?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col3:
                    suplemento_alimentar = st.radio("Usa suplemento alimentar?", ["Não", "Sim", "Não informado"], horizontal=True)
                    suplemento_qual = st.text_input("Qual suplemento?")
                    alimenta_sonda = st.radio("Alimenta-se por sonda?", ["Não", "Sim", "Não informado"], horizontal=True)
                    dorme_bem = st.radio("Dorme bem?", ["Não", "Sim", "Não informado"], horizontal=True)
                    medicacao = st.radio("Faz uso de medicação?", ["Não", "Sim", "Não informado"], horizontal=True)
                    medicacao_qual = st.text_input("Qual(is) medicação(ões)?")
                tempo_medicacao_tratamentos = st.text_area("Há quanto tempo usa medicação? Quais tratamentos realizados?")
                obs_saude = st.text_area("Outras observações relevantes sobre saúde")

                st.markdown("### 🧠 3. Desenvolvimento psicomotor")
                lateralidade = st.radio("Lateralidade", ["Não informado", "Destro(a)", "Canhoto(a)", "Ambidestro(a)"], horizontal=True)
                col1, col2 = st.columns(2)
                with col1:
                    estereotipias_lista = st.multiselect(
                        "Estereotipias observadas",
                        [
                            "Não apresenta",
                            "Balançar o corpo para frente e para trás",
                            "Balançar as mãos / flapping",
                            "Girar objetos ou girar em volta do próprio corpo",
                            "Fazer sons repetitivos ou repetir sílabas/palavras",
                            "Estalar os dedos",
                            "Pular",
                            "Correr indo e vindo sem destino claro",
                            "Andar na ponta dos pés",
                            "Movimentar os dedos na frente dos olhos",
                        ],
                    )
                    estereotipias = ", ".join(estereotipias_lista)
                    estereotipias_quais = st.text_area("Outras estereotipias / descrição")
                    segura_objetos_duas_maos = st.radio("Segura objetos com as duas mãos?", ["Não", "Sim", "Não informado"], horizontal=True)
                    tamanho_objetos_lista = st.multiselect("Segura objetos", ["Pequenos", "Médios", "Grandes"])
                    tamanho_objetos = ", ".join(tamanho_objetos_lista)
                    pega_lapis = st.radio("Faz a pega correta do lápis?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col2:
                    engatinhou = st.radio("Engatinhou?", ["Não", "Sim", "Não informado"], horizontal=True)
                    idade_andou = st.text_input("Andou com que idade?")
                    usa_fraldas = st.radio("Usa fraldas na escola?", ["Não", "Sim", "Não informado"], horizontal=True)
                    usa_sonda_alivio = st.radio("Usa sonda de alívio?", ["Não", "Sim", "Não informado"], horizontal=True)
                    autonomia_lista = st.multiselect("O que consegue fazer sem ajuda?", ["Tomar banho", "Escovar os dentes", "Usar o banheiro", "Se alimentar", "Se vestir", "Outros"])
                    autonomia_atividades = ", ".join(autonomia_lista)
                    autonomia_outros = st.text_input("Outras atividades de autonomia")
                    atende_comandos = st.radio("Atende comandos?", ["Não", "Sim", "Não informado"], horizontal=True)
                    gosta_toque = st.radio("Gosta do toque?", ["Não", "Sim", "Não informado"], horizontal=True)
                obs_psicomotor = st.text_area("Outras observações relevantes sobre desenvolvimento psicomotor")

                st.markdown("### 🗣️ 4. Linguagem")
                col1, col2, col3 = st.columns(3)
                with col1:
                    verbal = st.radio("É verbal?", ["Não", "Sim", "Não informado"], horizontal=True)
                    consegue_comunicar = st.radio("Consegue se comunicar?", ["Não", "Sim", "Não informado"], horizontal=True)
                    problemas_fala = st.radio("Possui problemas na fala?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col2:
                    ecolalia = st.radio("Tem ecolalia?", ["Não", "Sim", "Não informado"], horizontal=True)
                    da_recado = st.radio("Consegue dar um recado?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col3:
                    comunicacao_alternativa = st.radio("Usa comunicação alternativa?", ["Não", "Sim", "Não informado"], horizontal=True)
                    comunicacao_alternativa_qual = st.text_input("Qual comunicação alternativa?")

                st.markdown("### 🤝 5. Socialização")
                col1, col2, col3 = st.columns(3)
                with col1:
                    relacao_pai = st.radio("Relaciona-se bem com o pai?", ["Não", "Sim", "Não informado"], horizontal=True)
                    relacao_mae = st.radio("Relaciona-se bem com a mãe?", ["Não", "Sim", "Não informado"], horizontal=True)
                    relacao_parentes = st.radio("Relaciona-se bem com outros parentes?", ["Não", "Sim", "Não informado"], horizontal=True)
                    relacao_irmaos = st.radio("Relaciona-se bem com irmãos?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col2:
                    relacao_estudantes = st.radio("Relaciona-se bem com outros estudantes?", ["Não", "Sim", "Não informado"], horizontal=True)
                    tem_melhor_amigo = st.radio("Tem melhor amigo(a)?", ["Não", "Sim", "Não informado"], horizontal=True)
                    tipo_melhor_amigo = st.selectbox("Esse(a) melhor amigo(a) é", ["Não informado", "Parente", "Colega de escola", "Colega do local onde mora"])
                    adapta_ambiente = st.radio("Adapta-se facilmente ao ambiente?", ["Não", "Sim", "Não informado"], horizontal=True)
                with col3:
                    flexivel_rotina = st.radio("É flexível na rotina?", ["Não", "Sim", "Não informado"], horizontal=True)
                    respeita_regras = st.radio("Respeita regras?", ["Não", "Sim", "Não informado"], horizontal=True)
                    chora_facilidade = st.radio("Chora com facilidade?", ["Não", "Sim", "Não informado"], horizontal=True)
                    brinca_como = st.radio("Gosta de brincar", ["Não informado", "Sozinho(a)", "Com outros", "Das duas formas"], horizontal=True)
                interesses_lazer = st.text_area("Assunto ou lazer que interessa ao estudante")
                familia_gosta = st.text_area("O que a família mais gosta nesse(a) filho(a)?")
                familia_nao_gosta = st.text_area("O que a família não gosta/necesita melhorar nele(a)?")
                ambiente_estudo_casa = st.text_area("Em casa existe ambiente físico para atividades escolares e brincadeiras?")

                st.markdown("### 🏠 6. Contexto familiar")
                habilidades = st.text_area("Principais habilidades: o que faz bem")
                oportunidades_melhoria = st.text_area("Principais oportunidades de melhoria: o que podemos estimular mais")

                st.markdown("### 📝 7. Outras informações")
                outras_info_familia = st.text_area("Outras informações que a família considera importante registrar")

                salvar_entrevista = st.form_submit_button("Salvar entrevista com a família")

                if salvar_entrevista:
                    inserir_registro(
                        "entrevistas_familia",
                        ["estudante_id"] + CAMPOS_ENTREVISTA_FAMILIA,
                        [
                            estudante_id, hoje_str(), ano_letivo_entrevista, tipo_registro_entrevista,
                            auxilio_governamental, auxilio_quais, historico_familiar, historico_quais,
                            repetiu_ano, str(repetiu_qtd), trocou_escola, str(trocou_qtd), motivo_troca,
                            situacao_escolar, interesse_escola, organiza_materiais, resistencia_escola,
                            relacao_colegas, relacao_professores, leva_alimentacao, merenda_escolar,
                            alergia_alimentar, alergia_quais, obs_diversas,
                            motivo_escolha, outros_motivos, conhecimento_aee,
                            doenca_preexistente, convulsoes, acompanhamentos, acompanhamento_outro,
                            frequencia_acompanhamento, frequencia_outro, alimentacao_saudavel,
                            seletividade_alimentar, dieta_sensorial, suplemento_alimentar, suplemento_qual,
                            alimenta_sonda, dorme_bem, medicacao, medicacao_qual,
                            tempo_medicacao_tratamentos, obs_saude,
                            lateralidade, estereotipias, estereotipias_quais, segura_objetos_duas_maos,
                            tamanho_objetos, pega_lapis, engatinhou, idade_andou,
                            usa_fraldas, usa_sonda_alivio, autonomia_atividades, autonomia_outros,
                            atende_comandos, gosta_toque, obs_psicomotor,
                            verbal, consegue_comunicar, problemas_fala, ecolalia, da_recado,
                            comunicacao_alternativa, comunicacao_alternativa_qual,
                            relacao_pai, relacao_mae, relacao_parentes, relacao_irmaos, relacao_estudantes,
                            tem_melhor_amigo, tipo_melhor_amigo, adapta_ambiente, flexivel_rotina,
                            respeita_regras, chora_facilidade, brinca_como, interesses_lazer,
                            familia_gosta, familia_nao_gosta, ambiente_estudo_casa,
                            habilidades, oportunidades_melhoria, outras_info_familia,
                        ],
                    )
                    st.success("Entrevista com a família salva com sucesso.")
                    st.rerun()

        registros = listar_por_estudante("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)

        with st.container(border=True):
            st.markdown("### Histórico de entrevistas")
            if registros:
                for r in registros:
                    ano_reg = r[2] if len(r) > 2 and r[2] else "Ano não informado"
                    tipo_reg = r[3] if len(r) > 3 and r[3] else "Registro"
                    with st.expander(f"Entrevista em {r[1]} | {ano_reg} | {tipo_reg}"):
                        texto = texto_entrevista(estudante, r)
                        st.text(texto)
                        export_buttons(texto, f"Entrevista_Familia_{estudante[1]}_{r[0]}", tipo_pdf="entrevista")
                        if st.button("Excluir entrevista", key=f"exc_ent_{r[0]}"):
                            excluir_registro("entrevistas_familia", r[0])
                            st.success("Entrevista excluída.")
                            st.rerun()
            else:
                st.info("Nenhuma entrevista registrada.")


# ======================================================
# AVALIAÇÃO PEDAGÓGICA
# ======================================================
elif menu == "Avaliação Pedagógica":
    st.markdown('<div class="subtitulo">📝 Avaliação Pedagógica / Histórico por Ano Letivo</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()

    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="avaliacao_estudante",
        )
        estudante = buscar_estudante(estudante_id)
        avaliacoes = listar_avaliacoes(estudante_id)

        st.info(
            "Este módulo permite registrar avaliações pedagógicas estruturadas, avaliações anteriores, "
            "documentos livres e anexos digitalizados. Use sempre o código interno do estudante e evite "
            "inserir dados pessoais sensíveis nos textos ou arquivos."
        )

        anos_opcoes = [str(a) for a in range(2024, agora_local().year + 4)]
        ano_padrao = str(agora_local().year)
        idx_ano = anos_opcoes.index(ano_padrao) if ano_padrao in anos_opcoes else 0

        with st.container(border=True):
            st.markdown("### Configuração do registro")
            col_ano, col_tipo = st.columns(2)

            with col_ano:
                ano_letivo = st.selectbox(
                    "Ano letivo da avaliação pedagógica",
                    anos_opcoes,
                    index=idx_ano,
                    key="avaliacao_ano_letivo",
                )

            with col_tipo:
                tipo_registro = st.selectbox(
                    "Tipo de registro",
                    OPCOES_TIPO_AVALIACAO,
                    key="avaliacao_tipo_registro",
                )

            modo_extra = tipo_registro == "Avaliação Pedagógica - Extra / Documento Livre"

            opcoes_avaliacoes = {0: "Nenhuma avaliação anterior"}
            for av in avaliacoes:
                ano_av = av[2] or "Ano não informado"
                tipo_av = av[3] or "Tipo não informado"
                opcoes_avaliacoes[av[0]] = f"ID {av[0]} • {ano_av} • {tipo_av} • {av[1]}"

            avaliacao_anterior_id = st.selectbox(
                "Avaliação anterior para comparação ou vínculo",
                list(opcoes_avaliacoes.keys()),
                format_func=lambda x: opcoes_avaliacoes[x],
                key="avaliacao_anterior_id_select",
            )

            if not modo_extra:
                foco_ia = st.text_area(
                    "Orientação para a IA (opcional)",
                    placeholder="Ex.: observar avanços em autonomia, comunicação, participação nas atividades e barreiras de aprendizagem.",
                    height=80,
                    key="avaliacao_foco_ia",
                )

                if st.button("🤖 Gerar sugestão de nova Avaliação Pedagógica com IA", key="btn_ia_avaliacao"):
                    av_base = buscar_avaliacao_por_id(avaliacao_anterior_id) if avaliacao_anterior_id else None
                    estudo_atual = ultima_linha("estudos_caso", CAMPOS_ESTUDO_CASO, estudante_id)
                    estudo_atual = ("", *estudo_atual) if estudo_atual else None
                    entrevista_atual = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)
                    atendimentos_atuais = listar_atendimentos(estudante_id)
                    analise_ia, sugestao_ia = gerar_nova_avaliacao_pedagogica_com_ia(
                        estudante,
                        av_base,
                        estudo_atual,
                        entrevista_atual,
                        atendimentos_atuais,
                        ano_letivo,
                    )
                    if foco_ia.strip():
                        analise_ia = f"Orientação do professor: {foco_ia.strip()}\n\n{analise_ia}".strip()
                    st.session_state["avaliacao_analise_ia"] = analise_ia
                    st.session_state["avaliacao_sugestao_ia"] = sugestao_ia
                    st.success("Sugestão gerada. Revise e ajuste manualmente antes de salvar.")

                analise_previa = st.session_state.get("avaliacao_analise_ia", "")
                sugestao_previa = st.session_state.get("avaliacao_sugestao_ia", "")
                if analise_previa or sugestao_previa:
                    with st.expander("Prévia da análise e sugestão geradas com IA", expanded=True):
                        st.markdown("**Análise comparativa:**")
                        st.text_area("Análise comparativa IA", value=analise_previa, height=180, key="preview_analise_avaliacao_ia")
                        st.markdown("**Sugestão de nova avaliação:**")
                        st.text_area("Sugestão IA", value=sugestao_previa, height=260, key="preview_sugestao_avaliacao_ia")

        with st.container(border=True):
            if modo_extra:
                st.markdown("### Avaliação Pedagógica Extra / Documento Livre")
                st.caption(
                    "Use este espaço para registrar documentos antigos, pareceres, relatórios anteriores "
                    "ou informações pedagógicas que não cabem no formulário estruturado."
                )

                with st.form("form_avaliacao_extra"):
                    origem_documento = st.text_input(
                        "Origem do documento",
                        placeholder="Ex.: relatório antigo da escola, parecer pedagógico anterior, registro do AEE anterior...",
                    )

                    texto_documento_extra = st.text_area(
                        "Conteúdo completo do documento ou relatório",
                        height=420,
                        placeholder="Cole aqui o conteúdo do documento antigo, relatório, parecer ou histórico pedagógico anterior.",
                    )

                    arquivo_upload = st.file_uploader(
                        "Anexar documento digitalizado ou arquivo relacionado",
                        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
                        accept_multiple_files=False,
                    )

                    observacao_upload = st.text_area(
                        "Observação sobre o arquivo anexado",
                        height=90,
                        placeholder="Ex.: documento físico arquivado em pasta protegida; arquivo sem dados sensíveis; digitalização parcial...",
                    )

                    salvar_extra = st.form_submit_button("Salvar Avaliação Pedagógica Extra")

                if salvar_extra:
                    if not texto_documento_extra.strip() and arquivo_upload is None:
                        st.warning("Digite o conteúdo do documento ou anexe um arquivo antes de salvar.")
                    else:
                        salvar_avaliacao(
                            estudante_id=estudante_id,
                            ano_letivo=ano_letivo,
                            tipo_registro=tipo_registro,
                            avaliacao_anterior_id=None if avaliacao_anterior_id == 0 else avaliacao_anterior_id,
                            origem_documento=origem_documento,
                            texto_documento_extra=texto_documento_extra,
                        )

                        avaliacoes_atualizadas = listar_avaliacoes(estudante_id)
                        avaliacao_id = avaliacoes_atualizadas[0][0] if avaliacoes_atualizadas else None

                        if arquivo_upload is not None:
                            salvar_documento_avaliacao(
                                estudante_id=estudante_id,
                                avaliacao_id=avaliacao_id,
                                ano_letivo=ano_letivo,
                                tipo_documento=tipo_registro,
                                arquivo=arquivo_upload,
                                observacao=observacao_upload,
                            )

                        st.success("Avaliação Pedagógica Extra salva com sucesso.")
                        st.rerun()

            else:
                st.markdown("### Registro manual / revisão da avaliação")

                with st.form("form_avaliacao"):
                    sugestao_base = st.session_state.get("avaliacao_sugestao_ia", "")
                    barreiras = st.text_area(
                        "Barreiras enfrentadas pelo estudante",
                        value=sugestao_base if tipo_registro == "Nova avaliação com base em avaliação anterior" else "",
                        height=120,
                    )
                    potencialidades = st.text_area("Potencialidades e habilidades já desenvolvidas", height=100)
                    comunicacao = st.text_area("Comunicação", height=90)
                    interacao = st.text_area("Interação social", height=90)
                    autonomia = st.text_area("Autonomia", height=90)
                    aprendizagem = st.text_area("Aprendizagem", height=100)
                    resumo_laudo = st.text_area("Resumo pedagógico do laudo, sem identificação", height=90)

                    analise_comparativa_ia = st.text_area(
                        "Análise comparativa IA/manual",
                        value=st.session_state.get("avaliacao_analise_ia", ""),
                        height=150,
                    )
                    sugestao_nova_avaliacao_ia = st.text_area(
                        "Sugestão IA/manual para nova avaliação",
                        value=st.session_state.get("avaliacao_sugestao_ia", ""),
                        height=180,
                    )

                    arquivo_upload = st.file_uploader(
                        "Anexar documento complementar da avaliação",
                        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
                        accept_multiple_files=False,
                    )

                    observacao_upload = st.text_area(
                        "Observação sobre o arquivo anexado",
                        height=80,
                        placeholder="Ex.: documento complementar, imagem digitalizada ou parecer usado como apoio.",
                    )

                    salvar_estruturada = st.form_submit_button("Salvar avaliação pedagógica")

                if salvar_estruturada:
                    salvar_avaliacao(
                        estudante_id=estudante_id,
                        barreiras=barreiras,
                        potencialidades=potencialidades,
                        comunicacao=comunicacao,
                        interacao=interacao,
                        autonomia=autonomia,
                        aprendizagem=aprendizagem,
                        resumo_laudo=resumo_laudo,
                        ano_letivo=ano_letivo,
                        tipo_registro=tipo_registro,
                        avaliacao_anterior_id=None if avaliacao_anterior_id == 0 else avaliacao_anterior_id,
                        analise_comparativa_ia=analise_comparativa_ia,
                        sugestao_nova_avaliacao_ia=sugestao_nova_avaliacao_ia,
                    )

                    avaliacoes_atualizadas = listar_avaliacoes(estudante_id)
                    avaliacao_id = avaliacoes_atualizadas[0][0] if avaliacoes_atualizadas else None

                    if arquivo_upload is not None:
                        salvar_documento_avaliacao(
                            estudante_id=estudante_id,
                            avaliacao_id=avaliacao_id,
                            ano_letivo=ano_letivo,
                            tipo_documento=tipo_registro,
                            arquivo=arquivo_upload,
                            observacao=observacao_upload,
                        )

                    st.session_state.pop("avaliacao_analise_ia", None)
                    st.session_state.pop("avaliacao_sugestao_ia", None)

                    st.success("Avaliação pedagógica salva com sucesso.")
                    st.rerun()

        with st.container(border=True):
            st.markdown("### Histórico de avaliações pedagógicas")
            avaliacoes = listar_avaliacoes(estudante_id)

            if avaliacoes:
                for av in avaliacoes:
                    dados_av = dict(zip(["id"] + CAMPOS_AVALIACAO, av))
                    av_id = dados_av.get("id")
                    data_reg = dados_av.get("data_registro") or "Data não informada"
                    ano_reg = dados_av.get("ano_letivo") or "Ano não informado"
                    tipo_reg = dados_av.get("tipo_registro") or "Registro"

                    with st.expander(f"Avaliação em {data_reg} | {ano_reg} | {tipo_reg}"):
                        texto = texto_avaliacao(estudante, av)
                        st.text(texto)
                        export_buttons(texto, f"Avaliacao_Pedagogica_{estudante[1]}_{av_id}", tipo_pdf="avaliacao")

                        if st.button("Excluir avaliação", key=f"exc_avaliacao_{av_id}"):
                            excluir_registro("avaliacoes", av_id)
                            st.success("Avaliação excluída.")
                            st.rerun()
            else:
                st.info("Nenhuma avaliação pedagógica registrada.")

        with st.container(border=True):
            st.markdown("### Documentos anexados à Avaliação Pedagógica")
            documentos = listar_documentos_avaliacao(estudante_id)

            if documentos:
                for doc in documentos:
                    doc_id, avaliacao_id, ano_doc, tipo_doc, nome_original, caminho_arquivo, observacao, data_upload = doc

                    with st.expander(f"{nome_original} | {ano_doc or 'Ano não informado'} | {data_upload}"):
                        st.write(f"**Tipo:** {tipo_doc or 'Não informado'}")
                        st.write(f"**Avaliação vinculada:** {avaliacao_id or 'Não vinculada'}")
                        st.write(f"**Observação:** {observacao or 'Sem observação.'}")

                        if caminho_arquivo and Path(caminho_arquivo).exists():
                            with open(caminho_arquivo, "rb") as f:
                                st.download_button(
                                    "Baixar documento",
                                    data=f,
                                    file_name=nome_original,
                                    key=f"baixar_doc_avaliacao_{doc_id}",
                                )
                        else:
                            st.warning("Arquivo não encontrado na pasta de documentos do sistema.")

                        if st.button("Excluir documento anexado", key=f"excluir_doc_avaliacao_{doc_id}"):
                            excluir_documento_avaliacao(doc_id, caminho_arquivo)
                            st.success("Documento excluído.")
                            st.rerun()
            else:
                st.info("Nenhum documento anexado para este estudante.")


# ======================================================
# ARTICULAÇÃO PEDAGÓGICA INCLUSIVA - ESCUTA DOCENTE
# ======================================================
elif menu == "Articulação Pedagógica Inclusiva":
    st.markdown('<div class="subtitulo">🤝 Articulação Pedagógica Inclusiva – Escuta Docente</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()

    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="api_estudante",
        )
        estudante = buscar_estudante(estudante_id)

        st.info(
            "Este módulo registra a escuta dos professores da sala regular e gera o "
            "Relatório Pedagógico de Apoio ao Docente por IA, cruzando avaliação pedagógica, "
            "estudo de caso, atendimentos, documentos históricos e escutas docentes."
        )

        anos_opcoes = [str(a) for a in range(2024, agora_local().year + 4)]
        ano_padrao = str(agora_local().year)
        idx_ano = anos_opcoes.index(ano_padrao) if ano_padrao in anos_opcoes else 0

        aba_escuta, aba_historico, aba_relatorio, aba_relatorios_salvos = st.tabs(
            [
                "Nova Escuta Docente",
                "Histórico de Escutas",
                "Gerar Relatório de Apoio ao Docente",
                "Relatórios Salvos",
            ]
        )

        with aba_escuta:
            with st.container(border=True):
                st.markdown("### Nova Escuta Docente da Sala Regular")
                st.caption(
                    "Use este formulário para registrar a percepção pedagógica do professor da área. "
                    "Evite dados familiares, clínicos ou informações sensíveis que não sejam necessárias ao planejamento pedagógico."
                )

                with st.form("form_escuta_docente"):
                    col1, col2 = st.columns(2)

                    with col1:
                        ano_letivo = st.selectbox(
                            "Ano letivo",
                            anos_opcoes,
                            index=idx_ano,
                            key="escuta_ano_letivo",
                        )
                        codigo_docente = st.text_input(
                            "Código interno do docente / referência pedagógica",
                            placeholder="Ex.: DOC-MAT-001",
                            help="Use um código interno ou referência pedagógica. Evite registrar nomes pessoais de docentes neste campo.",
                        )
                        componente_curricular = st.selectbox(
                            "Componente curricular / área",
                            OPCOES_AREAS_CONHECIMENTO,
                        )
                        outro_componente = ""
                        if componente_curricular == "Outras":
                            outro_componente = st.text_input(
                                "Informe o componente/área",
                                placeholder="Digite a área ou componente curricular",
                            )

                    with col2:
                        turma = st.text_input(
                            "Turma",
                            value=estudante[3] or "",
                            placeholder="Ex.: 1º A",
                        )
                        tempo_acompanhamento = st.text_input(
                            "Tempo que acompanha o estudante",
                            placeholder="Ex.: desde o início do ano letivo, há dois meses...",
                        )
                        nivel_participacao = st.slider("Nível de participação em sala", 1, 10, 5)
                        nivel_autonomia = st.slider("Nível de autonomia nas atividades", 1, 10, 5)
                        nivel_engajamento = st.slider("Nível de engajamento", 1, 10, 5)

                    participacao_sala = st.text_area(
                        "Como o estudante participa das aulas?",
                        height=110,
                        placeholder="Descreva participação, atenção, realização das atividades, necessidade de mediação etc.",
                    )
                    comunicacao = st.text_area(
                        "Comunicação em sala",
                        height=90,
                        placeholder="Como o estudante expressa dúvidas, responde às solicitações, comunica necessidades ou interage verbalmente/não verbalmente?",
                    )
                    interacao_social = st.text_area(
                        "Interação social",
                        height=90,
                        placeholder="Como interage com colegas, professor e atividades em grupo?",
                    )
                    aprendizagem = st.text_area(
                        "Aprendizagem no componente curricular",
                        height=110,
                        placeholder="O que consegue acompanhar? Em quais situações demonstra melhor compreensão?",
                    )

                    estrategias_selecionadas = st.multiselect(
                        "Estratégias que parecem funcionar",
                        OPCOES_ESTRATEGIAS_INCLUSIVAS,
                    )
                    adaptacoes_selecionadas = st.multiselect(
                        "Adaptações já utilizadas pelo docente",
                        OPCOES_ESTRATEGIAS_INCLUSIVAS,
                    )

                    barreiras_percebidas = st.text_area(
                        "Barreiras percebidas",
                        height=100,
                        placeholder="Ex.: excesso de cópia, comandos longos, organização da atividade, comunicação, atenção, interação...",
                    )
                    potencialidades_observadas = st.text_area(
                        "Potencialidades observadas",
                        height=100,
                        placeholder="Ex.: criatividade, memória visual, oralidade, interesse por tecnologia, raciocínio lógico, participação em atividades práticas...",
                    )
                    recomendacoes_docente = st.text_area(
                        "Sugestões/recomendações do professor da área",
                        height=100,
                        placeholder="Registre o que o professor acredita que pode ajudar no processo de aprendizagem.",
                    )
                    observacoes = st.text_area(
                        "Observações complementares",
                        height=80,
                    )

                    salvar_escuta = st.form_submit_button("Salvar Escuta Docente")

                if salvar_escuta:
                    if not codigo_docente.strip():
                        st.warning("Informe o código interno do docente / referência pedagógica antes de salvar. Ex.: DOC-MAT-001.")
                    else:
                        salvar_escuta_docente(
                            estudante_id=estudante_id,
                            ano_letivo=ano_letivo,
                            codigo_docente=codigo_docente,
                            componente_curricular=componente_curricular,
                            outro_componente=outro_componente,
                            turma=turma,
                            tempo_acompanhamento=tempo_acompanhamento,
                            participacao_sala=participacao_sala,
                            comunicacao=comunicacao,
                            interacao_social=interacao_social,
                            aprendizagem=aprendizagem,
                            barreiras_percebidas=barreiras_percebidas,
                            potencialidades_observadas=potencialidades_observadas,
                            estrategias_funcionam=", ".join(estrategias_selecionadas),
                            adaptacoes_utilizadas=", ".join(adaptacoes_selecionadas),
                            recomendacoes_docente=recomendacoes_docente,
                            nivel_participacao=nivel_participacao,
                            nivel_autonomia=nivel_autonomia,
                            nivel_engajamento=nivel_engajamento,
                            observacoes=observacoes,
                        )
                        st.success("Escuta docente salva com sucesso. Acesse a aba Histórico de Escutas para baixar o registro em Word ou PDF.")
                        st.rerun()

        with aba_historico:
            with st.container(border=True):
                st.markdown("### Histórico de Escutas Docentes")
                st.caption("Cada escuta registrada pode ser visualizada, baixada em TXT, PDF ou Word e excluída, se necessário.")
                escutas = listar_escutas_docentes(estudante_id)

                if escutas:
                    for esc in escutas:
                        dados_esc = dict(zip(["id"] + CAMPOS_ESCUTA_DOCENTE, esc))
                        esc_id = dados_esc.get("id")
                        data_reg = dados_esc.get("data_registro") or "Data não informada"
                        area = dados_esc.get("componente_curricular") or "Área não informada"
                        codigo_doc = dados_esc.get("codigo_docente") or "Código docente não informado"

                        with st.expander(f"{data_reg} | {area} | {codigo_doc}"):
                            texto = texto_escuta_docente(estudante, esc)
                            st.text(texto)
                            export_buttons(texto, f"Escuta_Docente_{estudante[1]}_{esc_id}", tipo_pdf="escuta_docente")

                            if st.button("Excluir escuta docente", key=f"excluir_escuta_{esc_id}"):
                                excluir_escuta_docente(esc_id)
                                st.success("Escuta docente excluída.")
                                st.rerun()
                else:
                    st.info("Nenhuma escuta docente registrada para este estudante.")

        with aba_relatorio:
            with st.container(border=True):
                st.markdown("### Relatório Pedagógico de Apoio ao Docente")
                st.caption(
                    "O relatório será gerado com IA a partir dos registros já existentes: avaliação pedagógica, "
                    "estudo de caso, atendimentos, documentos históricos anexados e escutas docentes."
                )

                colr1, colr2 = st.columns(2)
                with colr1:
                    ano_relatorio = st.selectbox(
                        "Ano letivo do relatório",
                        anos_opcoes,
                        index=idx_ano,
                        key="relatorio_docente_ano",
                    )
                    componente_destino = st.selectbox(
                        "Componente/área de destino",
                        OPCOES_AREAS_CONHECIMENTO,
                        key="relatorio_docente_componente",
                    )
                    if componente_destino == "Outras":
                        componente_destino = st.text_input(
                            "Informe o componente/área de destino",
                            key="relatorio_docente_componente_outro",
                        )

                with colr2:
                    professor_destino = ""
                    st.info("O destinatário ficará em branco no relatório para preenchimento manual após impressão ou edição do Word.")
                    observacoes_relatorio = st.text_area(
                        "Observações internas do AEE",
                        height=90,
                        placeholder="Opcional. Ex.: relatório para planejamento de atividades avaliativas do bimestre.",
                        key="relatorio_docente_obs",
                    )

                foco_docente = st.text_area(
                    "Foco para a IA",
                    height=100,
                    placeholder="Ex.: orientar o professor sobre participação, adaptação das atividades e formas avaliativas sem expor dados familiares.",
                    key="relatorio_docente_foco",
                )

                contexto_previo, fontes_previas = montar_contexto_relatorio_docente(estudante_id)
                with st.expander("Ver fontes que serão cruzadas pelo sistema"):
                    st.write(fontes_previas)
                    st.text_area(
                        "Contexto reunido pelo sistema",
                        value=contexto_previo,
                        height=300,
                        disabled=True,
                    )

                if st.button("🤖 Gerar Relatório Pedagógico de Apoio ao Docente", key="btn_gerar_relatorio_docente_ia"):
                    conteudo, fontes = gerar_relatorio_apoio_docente_ia(
                        estudante_id=estudante_id,
                        ano_letivo=ano_relatorio,
                        componente_destino=componente_destino,
                        professor_destino=professor_destino,
                        foco_docente=foco_docente,
                    )
                    st.session_state["relatorio_docente_conteudo"] = conteudo
                    st.session_state["relatorio_docente_fontes"] = fontes
                    st.success("Relatório gerado. Revise antes de salvar ou entregar ao docente.")

                conteudo_gerado = st.session_state.get("relatorio_docente_conteudo", "")
                fontes_geradas = st.session_state.get("relatorio_docente_fontes", fontes_previas)

                if conteudo_gerado:
                    st.markdown("### Prévia editável do relatório")
                    conteudo_editado = st.text_area(
                        "Revise o relatório antes de salvar",
                        value=conteudo_gerado,
                        height=520,
                        key="relatorio_docente_editavel",
                    )

                    titulo_relatorio = "RELATÓRIO PEDAGÓGICO DE APOIO AO DOCENTE"
                    texto_final = f"""
{titulo_relatorio}

Código interno do estudante: {estudante[1]}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Ano letivo: {ano_relatorio}
Componente/área de destino: {componente_destino}
Destinatário: ________________________________________
Data de geração: {hoje_str()}

{conteudo_editado}

FONTES UTILIZADAS PELO SISTEMA:
{fontes_geradas}

Observação institucional:
Este relatório possui finalidade exclusivamente pedagógica e objetiva apoiar práticas educacionais inclusivas no contexto escolar, sem expor dados familiares ou informações sensíveis desnecessárias.
""".strip()

                    st.text(texto_final)
                    export_buttons(
                        texto_final,
                        f"Relatorio_Apoio_Docente_{estudante[1]}_{ano_relatorio}",
                        tipo_pdf="relatorio_docente",
                    )

                    if st.button("Salvar relatório no histórico", key="btn_salvar_relatorio_docente"):
                        salvar_relatorio_docente(
                            estudante_id=estudante_id,
                            ano_letivo=ano_relatorio,
                            componente_destino=componente_destino,
                            professor_destino=professor_destino,
                            titulo=titulo_relatorio,
                            conteudo=conteudo_editado,
                            fontes_utilizadas=fontes_geradas,
                            observacoes=observacoes_relatorio,
                        )
                        st.session_state.pop("relatorio_docente_conteudo", None)
                        st.session_state.pop("relatorio_docente_fontes", None)
                        st.success("Relatório salvo no histórico.")
                        st.rerun()

        with aba_relatorios_salvos:
            with st.container(border=True):
                st.markdown("### Relatórios Pedagógicos de Apoio ao Docente salvos")
                relatorios = listar_relatorios_docente(estudante_id)

                if relatorios:
                    for rel in relatorios:
                        dados_rel = dict(zip(["id"] + CAMPOS_RELATORIO_DOCENTE, rel))
                        rel_id = dados_rel.get("id")
                        data_rel = dados_rel.get("data_geracao") or "Data não informada"
                        area_rel = dados_rel.get("componente_destino") or "Área não informada"

                        with st.expander(f"{data_rel} | {area_rel}"):
                            texto = texto_relatorio_docente(estudante, rel)
                            st.text(texto)
                            export_buttons(
                                texto,
                                f"Relatorio_Apoio_Docente_{estudante[1]}_{rel_id}",
                                tipo_pdf="relatorio_docente_salvo",
                            )

                            if st.button("Excluir relatório salvo", key=f"excluir_relatorio_docente_{rel_id}"):
                                excluir_relatorio_docente(rel_id)
                                st.success("Relatório excluído.")
                                st.rerun()
                else:
                    st.info("Nenhum relatório pedagógico de apoio ao docente salvo para este estudante.")


elif menu == "Estudo de Caso":
    st.markdown('<div class="subtitulo">📚 Estudo de Caso / Documento GRE</div>', unsafe_allow_html=True)
    st.caption("Os campos sensíveis como CPF, RG, endereço e nome completo ficam fora do banco. Eles aparecem em branco no Word/PDF para preenchimento manual antes da entrega à GRE.")

    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox("Selecione o estudante", ids, format_func=lambda x: mapa[x], key="estudo_estudante")
        estudante = buscar_estudante(estudante_id)
        professor_resp = buscar_professor_responsavel()
        estudos_anteriores = listar_por_estudante("estudos_caso", CAMPOS_ESTUDO_CASO, estudante_id)
        avaliacoes_pedagogicas = listar_avaliacoes(estudante_id)

        with st.container(border=True):
            st.markdown("### Novo Estudo de Caso - Campos obrigatórios GRE")
            st.info("Agora o Estudo de Caso pode ser registrado por ano letivo. Você pode lançar estudos anteriores como histórico e gerar um novo estudo com apoio da IA, comparando registros antigos com dados atuais.")
            st.caption("✅ V13 GRE ativo: a IA gera o Estudo de Caso em estrutura padronizada GRE, usando estudo anterior e/ou todas as avaliações pedagógicas disponíveis como base.")

            with st.expander("🤖 Criar novo estudo de caso com apoio da IA", expanded=True):
                if estudos_anteriores or avaliacoes_pedagogicas:
                    st.caption(
                        "A IA pode gerar um novo Estudo de Caso a partir de estudo anterior e/ou avaliações pedagógicas. "
                        "Quando não houver estudo anterior, o sistema usa as avaliações pedagógicas e demais registros como base."
                    )

                    if estudos_anteriores:
                        opcoes_estudos = {0: "Nenhum estudo anterior - gerar com base nas avaliações pedagógicas e demais registros"}
                        opcoes_estudos.update({
                            e[0]: f"ID {e[0]} | Ano: {e[2] or 'não informado'} | Tipo: {e[3] or 'não informado'} | Registro: {e[1]}"
                            for e in estudos_anteriores
                        })
                        estudo_base_id_ia = st.selectbox(
                            "Estudo anterior para comparação (opcional)",
                            list(opcoes_estudos.keys()),
                            format_func=lambda x: opcoes_estudos[x],
                            key=f"estudo_base_ia_{estudante_id}",
                        )
                    else:
                        estudo_base_id_ia = 0
                        st.info("Não há estudo de caso anterior. A IA criará uma primeira versão com base nas avaliações pedagógicas e demais registros disponíveis.")

                    if avaliacoes_pedagogicas:
                        opcoes_avaliacoes_ia = {
                            a[0]: f"ID {a[0]} | Ano: {a[2] or 'não informado'} | Tipo: {a[3] or 'não informado'} | Registro: {a[1]}"
                            for a in avaliacoes_pedagogicas
                        }
                        avaliacao_base_id_ia = st.selectbox(
                            "Avaliação pedagógica principal para compor o Estudo de Caso",
                            list(opcoes_avaliacoes_ia.keys()),
                            format_func=lambda x: opcoes_avaliacoes_ia[x],
                            key=f"avaliacao_base_estudo_ia_{estudante_id}",
                        )
                        st.caption("A avaliação escolhida será a principal, mas a IA também considerará as demais avaliações pedagógicas/documentos livres registrados para este estudante.")
                    else:
                        avaliacao_base_id_ia = 0
                        st.warning("Nenhuma avaliação pedagógica localizada. A IA usará apenas o estudo anterior e demais registros disponíveis.")

                    ano_novo_ia = st.text_input("Ano letivo do novo estudo", value=str(agora_local().year), key=f"ano_novo_ia_{estudante_id}")

                    fontes_ia = []
                    if estudos_anteriores and estudo_base_id_ia != 0:
                        fontes_ia.append("estudo de caso anterior")
                    if avaliacoes_pedagogicas:
                        fontes_ia.append("avaliação pedagógica")
                    fontes_ia.extend(["entrevista familiar", "atendimentos AEE", "registros disponíveis"])
                    st.caption("Fontes previstas para a IA: " + ", ".join(fontes_ia) + ".")

                    if st.button("Gerar análise e sugestão de novo estudo", key=f"gerar_estudo_ia_{estudante_id}"):
                        estudo_base = next((e for e in estudos_anteriores if e[0] == estudo_base_id_ia), None)
                        avaliacao_atual = next((a for a in avaliacoes_pedagogicas if a[0] == avaliacao_base_id_ia), None) if avaliacao_base_id_ia else None
                        entrevista_atual = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)
                        atendimentos_atuais = listar_atendimentos(estudante_id)
                        analise_ia, sugestao_ia = gerar_novo_estudo_caso_com_ia(
                            estudante,
                            estudo_base,
                            avaliacao_atual,
                            entrevista_atual,
                            atendimentos_atuais,
                            ano_novo_ia,
                            avaliacoes_contexto=avaliacoes_pedagogicas,
                        )
                        st.session_state[f"analise_estudo_ia_{estudante_id}"] = analise_ia
                        st.session_state[f"sugestao_estudo_ia_{estudante_id}"] = sugestao_ia
                        st.session_state[f"ano_estudo_ia_{estudante_id}"] = ano_novo_ia
                        st.session_state[f"estudo_anterior_id_{estudante_id}"] = None if estudo_base_id_ia == 0 else estudo_base_id_ia
                        st.session_state[f"avaliacao_base_id_estudo_ia_{estudante_id}"] = avaliacao_base_id_ia
                        st.session_state[f"fontes_estudo_ia_{estudante_id}"] = ", ".join(fontes_ia)

                        # Campos estruturados do Estudo de Caso GRE gerados pela IA.
                        st.session_state[f"ia_percurso_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "PERCURSO_EDUCACIONAL")
                        st.session_state[f"ia_motivo_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "MOTIVO_ENCAMINHAMENTO")
                        st.session_state[f"ia_hab_obs_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "HABILIDADES_OBSERVADAS")
                        st.session_state[f"ia_hab_des_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "HABILIDADES_A_DESENVOLVER")
                        st.session_state[f"ia_potencialidades_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "POTENCIALIDADES")
                        st.session_state[f"ia_dificuldades_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "DIFICULDADES")
                        st.session_state[f"ia_estrategias_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "ESTRATEGIAS")
                        st.session_state[f"ia_intervencoes_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "INTERVENCOES")
                        st.session_state[f"ia_avaliacao_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "AVALIACAO")
                        st.session_state[f"ia_consideracoes_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "CONSIDERACOES")
                        st.session_state[f"ia_observacoes_complementares_{estudante_id}"] = extrair_secao_ia(sugestao_ia, "OBSERVACOES_COMPLEMENTARES")

                        st.success("Sugestão GRE gerada. Os campos do formulário foram preparados para revisão e edição antes de salvar.")

                    if st.session_state.get(f"sugestao_estudo_ia_{estudante_id}"):
                        st.markdown("#### Análise IA")
                        analise_preview = st.text_area(
                            "Resultado da análise",
                            value=st.session_state.get(f"analise_estudo_ia_{estudante_id}", ""),
                            height=180,
                            key=f"preview_analise_{estudante_id}",
                        )
                        st.markdown("#### Sugestão GRE estruturada")
                        sugestao_preview = st.text_area(
                            "Sugestão gerada",
                            value=st.session_state.get(f"sugestao_estudo_ia_{estudante_id}", ""),
                            height=260,
                            key=f"preview_sugestao_{estudante_id}",
                        )

                        texto_previa_estudo = f"""
ESTUDO PEDAGÓGICO DO ESTUDANTE - AEE
Sugestão gerada por IA para revisão do professor do AEE

Código interno do estudante: {estudante[1]}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Ano letivo: {st.session_state.get(f'ano_estudo_ia_{estudante_id}', str(agora_local().year))}

ANÁLISE PEDAGÓGICA DA IA:
{analise_preview}

SUGESTÃO ESTRUTURADA PADRÃO GRE:
{sugestao_preview}

Observação institucional:
Documento preliminar para revisão do professor do AEE antes do salvamento definitivo e/ou envio à GRE.
""".strip()

                        st.markdown("#### Download da sugestão gerada")
                        export_buttons(
                            texto_previa_estudo,
                            f"Estudo_Caso_GRE_IA_{estudante[1]}_{st.session_state.get(f'ano_estudo_ia_{estudante_id}', str(agora_local().year))}",
                            tipo_pdf="estudo_ia_previa",
                        )

                        st.markdown("#### Salvar no histórico")
                        st.caption("Esta opção salva imediatamente a sugestão gerada no histórico do estudante, mantendo a estrutura GRE. Depois você ainda pode abrir o registro salvo, baixar em Word/PDF e complementar manualmente.")
                        if st.button("💾 Salvar sugestão gerada no histórico", key=f"salvar_sugestao_estudo_ia_{estudante_id}"):
                            ano_salvar = st.session_state.get(f"ano_estudo_ia_{estudante_id}", str(agora_local().year))
                            estudo_ant_salvar = st.session_state.get(f"estudo_anterior_id_{estudante_id}")
                            analise_salvar = st.session_state.get(f"analise_estudo_ia_{estudante_id}", "")
                            sugestao_salvar = st.session_state.get(f"sugestao_estudo_ia_{estudante_id}", "")

                            dados_estudo_ia = {
                                "data_registro": hoje_str(),
                                "ano_letivo": ano_salvar,
                                "tipo_registro": "Novo estudo com base em estudo anterior ou avaliação pedagógica",
                                "estudo_anterior_id": estudo_ant_salvar,
                                "analise_comparativa_ia": analise_salvar,
                                "sugestao_novo_estudo_ia": sugestao_salvar,
                                "contextualizacao": extrair_secao_ia(sugestao_salvar, "PERCURSO_EDUCACIONAL"),
                                "queixa_principal": extrair_secao_ia(sugestao_salvar, "MOTIVO_ENCAMINHAMENTO"),
                                "potencialidades": extrair_secao_ia(sugestao_salvar, "POTENCIALIDADES") or extrair_secao_ia(sugestao_salvar, "HABILIDADES_OBSERVADAS"),
                                "dificuldades": extrair_secao_ia(sugestao_salvar, "DIFICULDADES") or extrair_secao_ia(sugestao_salvar, "HABILIDADES_A_DESENVOLVER"),
                                "estrategias": extrair_secao_ia(sugestao_salvar, "ESTRATEGIAS"),
                                "intervencoes": extrair_secao_ia(sugestao_salvar, "INTERVENCOES"),
                                "avaliacao": extrair_secao_ia(sugestao_salvar, "AVALIACAO"),
                                "consideracoes": extrair_secao_ia(sugestao_salvar, "CONSIDERACOES"),
                                "etapa_modalidade": "",
                                "ano_etapa": estudante[2] or "",
                                "laudo": "",
                                "deficiencia": estudante[4] or "",
                                "cid": "",
                                "observacoes_laudo": "",
                                "altas_habilidades": "",
                                "bpc": "",
                                "escola_nome": "",
                                "unidade_aee": "",
                                "gestor_nome": "",
                                "gestor_contato": "",
                                "professor_nome": "",
                                "professor_contato": "",
                                "matricula_professor": "",
                                "especialidade_professor": "",
                                "periodo_inicio": "",
                                "periodo_fim": "",
                                "frequencia_atendimento": "",
                                "tempo_atendimento_semana": "",
                                "formato_atendimento": "",
                                "percurso_educacional": extrair_secao_ia(sugestao_salvar, "PERCURSO_EDUCACIONAL"),
                                "motivo_encaminhamento_aee": extrair_secao_ia(sugestao_salvar, "MOTIVO_ENCAMINHAMENTO"),
                                "precisa_transporte_inclusivo": "",
                                "recebe_transporte_inclusivo": "",
                                "precisa_profissional_apoio": "",
                                "justificativa_apoio": "",
                                "acompanhado_profissional_apoio": "",
                                "nome_profissional_apoio": "",
                                "recursos_tecnologia_assistiva": extrair_secao_ia(sugestao_salvar, "INTERVENCOES"),
                                "observacoes_ambiente_educacional": extrair_secao_ia(sugestao_salvar, "OBSERVACOES_COMPLEMENTARES"),
                                "habilidades_observadas": extrair_secao_ia(sugestao_salvar, "HABILIDADES_OBSERVADAS"),
                                "habilidades_a_desenvolver": extrair_secao_ia(sugestao_salvar, "HABILIDADES_A_DESENVOLVER"),
                                "indicadores_altas_habilidades": "",
                                "recursos_surdez": "",
                                "observacoes_surdez": "",
                            }
                            inserir_registro(
                                "estudos_caso",
                                ["estudante_id"] + CAMPOS_ESTUDO_CASO,
                                [estudante_id] + [dados_estudo_ia.get(campo, "") for campo in CAMPOS_ESTUDO_CASO],
                            )
                            st.success("Estudo de caso GRE salvo no histórico do estudante.")
                            st.rerun()

                        st.info("Você também pode revisar os campos nas abas abaixo e clicar em **Salvar estudo de caso GRE** para gravar uma versão editada manualmente.")
                else:
                    st.info(
                        "Ainda não há estudo anterior ou avaliações pedagógicas registradas para este estudante. "
                        "Primeiro cadastre avaliação pedagógica e/ou o estudo histórico ou atual."
                    )

            with st.form("form_estudo_gre"):
                aba1, aba2, aba3, aba4 = st.tabs([
                    "1. Identificação",
                    "2. Percurso educacional",
                    "3. Habilidades",
                    "4. Síntese pedagógica",
                ])

                with aba1:
                    st.markdown("#### Identificação educacional")
                    col_ano_hist, col_tipo_hist = st.columns(2)
                    with col_ano_hist:
                        ano_letivo = st.text_input("Ano letivo do estudo de caso", value=st.session_state.get(f"ano_estudo_ia_{estudante_id}", str(agora_local().year)))
                    with col_tipo_hist:
                        tipo_registro = st.selectbox(
                            "Tipo de registro",
                            ["Estudo de caso atual", "Registro histórico", "Novo estudo com base em estudo anterior ou avaliação pedagógica"],
                            index=2 if st.session_state.get(f"sugestao_estudo_ia_{estudante_id}") else 0,
                        )
                    estudo_anterior_id = st.session_state.get(f"estudo_anterior_id_{estudante_id}")
                    analise_comparativa_ia = st.session_state.get(f"analise_estudo_ia_{estudante_id}", "")
                    sugestao_novo_estudo_ia = st.session_state.get(f"sugestao_estudo_ia_{estudante_id}", "")

                    etapa_modalidade = st.selectbox(
                        "Etapa/modalidade",
                        ["Ensino Fundamental", "Ensino Médio", "EJA", "Outro / não informado"],
                    )
                    ano_etapa = st.selectbox("Ano/etapa", OPCOES_ANO_ETAPA)
                    turma_turno_info = f"{estudante[3] or 'Turma não informada'} / {estudante[6] or 'Turno não informado'}"
                    st.info(f"Turma e turno cadastrados: {turma_turno_info}")

                    col_l1, col_l2, col_l3 = st.columns(3)
                    with col_l1:
                        laudo = st.radio("Possui laudo?", ["Não", "Sim"], horizontal=True)
                    with col_l2:
                        deficiencia = st.radio("Apresenta deficiência?", ["Não", "Sim"], horizontal=True)
                    with col_l3:
                        altas_habilidades = st.radio("Altas habilidades/superdotação?", ["Não", "Sim"], horizontal=True)

                    cid = st.text_input(
                        "CID, se houver",
                        placeholder="Ex.: F84.0",
                        help="Informe apenas o CID indicado no laudo, quando disponível. Não anexe laudos ou exames no sistema."
                    )
                    observacoes_laudo = st.text_area(
                        "Síntese pedagógica/funcional do laudo",
                        placeholder=(
                            "Registre apenas informações relevantes para o contexto educacional, como comunicação, "
                            "autonomia, interação social, atenção, comportamento, necessidades de apoio, "
                            "organização pedagógica e acessibilidade. Não inserir laudo completo, exames ou dados clínicos excessivamente sensíveis."
                        ),
                        height=140,
                        help="Este campo deve transformar a informação do laudo em orientação pedagógica/funcional para o AEE."
                    )
                    bpc = st.radio("Usuário de BPC?", ["Não", "Sim", "Não informado"], horizontal=True)

                    st.markdown("#### Dados institucionais")
                    escola_nome = st.text_input("Nome da escola em que o(a) estudante está matriculado no ensino comum", value="")
                    unidade_aee = st.text_input("Unidade educacional onde o(a) estudante é atendido pelo AEE", value="")
                    gestor_nome = st.text_input("Nome do(a) gestor(a) da escola do ensino comum", value="")
                    gestor_contato = st.text_input("Contato institucional do(a) gestor(a)", value="")

                    professor_nome_padrao = professor_resp[1] if professor_resp else ""
                    professor_nome = st.text_input("Nome do(a) professor(a) AEE", value=professor_nome_padrao or "")
                    professor_contato = st.text_input("Contato institucional do(a) professor(a) AEE", value="")
                    matricula_professor = st.text_input("Matrícula do(a) professor(a) AEE", value="")
                    especialidade_professor = st.multiselect("Especialidade do(a) professor(a) AEE", OPCOES_ESPECIALIDADE_AEE, default=["Professor(a) do AEE"])

                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        periodo_inicio = st.text_input("Período de elaboração/início do atendimento", placeholder="Ex.: 01/02/2026")
                    with col_p2:
                        periodo_fim = st.text_input("Data final", placeholder="Ex.: 30/06/2026")

                    frequencia_atendimento = st.multiselect("Frequência de atendimento na SRM", DIAS_SEMANA, default=[])
                    tempo_atendimento_semana = st.text_input("Tempo de atendimento por semana", placeholder="Ex.: 2h semanais")
                    formato_atendimento = st.multiselect("Formato do atendimento", OPCOES_FORMATO_ATENDIMENTO, default=["Individual"])

                with aba2:
                    st.markdown("#### Estudo de caso / percurso educacional")
                    percurso_educacional = st.text_area(
                        "Relato sobre o trajeto educacional do(a) estudante",
                        value=st.session_state.get(f"ia_percurso_{estudante_id}", ""),
                        placeholder="Descreva situação inicial, estratégias já utilizadas e progressos alcançados em turmas comuns e/ou AEE anterior.",
                        height=180,
                    )
                    motivo_encaminhamento_aee = st.text_area(
                        "Motivo pelo qual foi encaminhado ao AEE",
                        value=st.session_state.get(f"ia_motivo_{estudante_id}", ""),
                        height=120,
                    )

                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        precisa_transporte_inclusivo = st.radio("Precisa de transporte escolar inclusivo?", ["Não", "Sim", "Não informado"], horizontal=True)
                    with col_t2:
                        recebe_transporte_inclusivo = st.radio("Recebe transporte escolar inclusivo?", ["Não", "Sim", "Não informado"], horizontal=True)

                    precisa_profissional_apoio = st.radio("Precisa de profissional de apoio?", ["Não", "Sim", "Não informado"], horizontal=True)
                    justificativa_apoio = st.text_area("Justificativa para profissional de apoio, se necessário", height=100)
                    acompanhado_profissional_apoio = st.radio("É acompanhado por profissional de apoio na escola?", ["Não", "Sim", "Não informado"], horizontal=True)
                    nome_profissional_apoio = st.text_input("Nome do profissional de apoio, se houver")

                    recursos_tecnologia_assistiva = st.multiselect("Recursos de tecnologia educacional e/ou assistiva utilizados", OPCOES_RECURSOS_TA)
                    observacoes_ambiente_educacional = st.text_area(
                        "Observações relevantes para o ambiente educacional / acompanhamento médico ou terapêutico",
                        value=st.session_state.get(f"ia_observacoes_complementares_{estudante_id}", ""),
                        placeholder="Ex.: acompanhamento terapêutico, recomendações pedagógicas, cuidados no ambiente escolar.",
                        height=140,
                    )

                with aba3:
                    st.markdown("#### Habilidades e indicadores")
                    habilidades_observadas = st.multiselect("Habilidades observadas e desenvolvidas", OPCOES_HABILIDADES_PEDAGOGICAS)
                    habilidades_observadas_ia = st.text_area(
                        "Habilidades observadas sugeridas pela IA / complementação manual",
                        value=st.session_state.get(f"ia_hab_obs_{estudante_id}", ""),
                        height=90,
                    )
                    habilidades_a_desenvolver = st.multiselect("Habilidades que precisam ser desenvolvidas", OPCOES_HABILIDADES_A_DESENVOLVER)
                    habilidades_a_desenvolver_ia = st.text_area(
                        "Habilidades a desenvolver sugeridas pela IA / complementação manual",
                        value=st.session_state.get(f"ia_hab_des_{estudante_id}", ""),
                        height=90,
                    )
                    indicadores_altas_habilidades = st.multiselect("Indicadores de altas habilidades/superdotação", OPCOES_INDICADORES_AHSD)
                    recursos_surdez = st.multiselect("Caso seja pessoa surda, marque recursos utilizados", OPCOES_RECURSOS_SURDEZ, default=["Não se aplica"])
                    observacoes_surdez = st.text_area(
                        "Observações sobre aparelho auditivo, implante coclear, Libras, uso diário, efetividade ou incômodos",
                        height=120,
                    )

                with aba4:
                    st.markdown("#### Síntese pedagógica")
                    contextualizacao = st.text_area(
                        "Contextualização",
                        value=st.session_state.get(f"ia_percurso_{estudante_id}", ""),
                        height=130,
                    )
                    potencialidades = st.text_area("Potencialidades", value=st.session_state.get(f"ia_potencialidades_{estudante_id}", ""), height=100)
                    dificuldades = st.text_area("Dificuldades/barreiras observadas", value=st.session_state.get(f"ia_dificuldades_{estudante_id}", ""), height=100)
                    estrategias = st.text_area("Estratégias pedagógicas", value=st.session_state.get(f"ia_estrategias_{estudante_id}", ""), height=120)
                    intervencoes = st.text_area("Intervenções / encaminhamentos sugeridos", value=st.session_state.get(f"ia_intervencoes_{estudante_id}", ""), height=120)
                    avaliacao_estudo = st.text_area("Avaliação", value=st.session_state.get(f"ia_avaliacao_{estudante_id}", ""), height=100)
                    consideracoes = st.text_area("Considerações finais", value=st.session_state.get(f"ia_consideracoes_{estudante_id}", ""), height=100)

                salvar_estudo = st.form_submit_button("Salvar estudo de caso GRE")

                if salvar_estudo:
                    campos = ["estudante_id"] + CAMPOS_ESTUDO_CASO
                    valores = [
                        estudante_id,
                        hoje_str(),
                        ano_letivo,
                        tipo_registro,
                        estudo_anterior_id,
                        analise_comparativa_ia,
                        sugestao_novo_estudo_ia,
                        contextualizacao,
                        motivo_encaminhamento_aee,
                        "; ".join([x for x in [", ".join(habilidades_observadas), habilidades_observadas_ia] if x]),
                        "; ".join([x for x in [", ".join(habilidades_a_desenvolver), habilidades_a_desenvolver_ia] if x]),
                        estrategias,
                        intervencoes,
                        avaliacao_estudo,
                        consideracoes,
                        etapa_modalidade,
                        ano_etapa,
                        laudo,
                        deficiencia,
                        cid,
                        observacoes_laudo,
                        altas_habilidades,
                        bpc,
                        escola_nome,
                        unidade_aee,
                        gestor_nome,
                        gestor_contato,
                        professor_nome,
                        professor_contato,
                        matricula_professor,
                        ", ".join(especialidade_professor),
                        periodo_inicio,
                        periodo_fim,
                        ", ".join(frequencia_atendimento),
                        tempo_atendimento_semana,
                        ", ".join(formato_atendimento),
                        percurso_educacional,
                        motivo_encaminhamento_aee,
                        precisa_transporte_inclusivo,
                        recebe_transporte_inclusivo,
                        precisa_profissional_apoio,
                        justificativa_apoio,
                        acompanhado_profissional_apoio,
                        nome_profissional_apoio,
                        ", ".join(recursos_tecnologia_assistiva),
                        observacoes_ambiente_educacional,
                        "; ".join([x for x in [", ".join(habilidades_observadas), habilidades_observadas_ia] if x]),
                        "; ".join([x for x in [", ".join(habilidades_a_desenvolver), habilidades_a_desenvolver_ia] if x]),
                        ", ".join(indicadores_altas_habilidades),
                        ", ".join(recursos_surdez),
                        observacoes_surdez,
                    ]
                    inserir_registro("estudos_caso", campos, valores)
                    st.success("Estudo de caso GRE salvo.")
                    st.rerun()

        estudos = listar_por_estudante(
            "estudos_caso",
            CAMPOS_ESTUDO_CASO,
            estudante_id,
        )
        with st.container(border=True):
            st.markdown("### Histórico de estudos de caso")
            if estudos:
                for e in estudos:
                    with st.expander(f"Estudo em {e[1]} | Ano letivo: {e[2] if len(e) > 2 else 'não informado'}"):
                        texto = texto_estudo_caso(estudante, e)
                        st.text(texto)
                        export_buttons(texto, f"Estudo_Caso_GRE_{estudante[1]}_{e[0]}", tipo_pdf="estudo")
                        if st.button("Excluir estudo de caso", key=f"exc_estudo_{e[0]}"):
                            excluir_registro("estudos_caso", e[0])
                            st.success("Estudo excluído.")
                            st.rerun()
            else:
                st.info("Nenhum estudo de caso registrado.")


# ======================================================
# PLANO AEE - INTELIGÊNCIA
# ======================================================
elif menu == "Plano AEE - IA":
    st.markdown('<div class="subtitulo">🧠 Plano AEE - IA</div>', unsafe_allow_html=True)
    st.caption(
        "Módulo de planejamento pedagógico inteligente para perfil pedagógico, plano mensal, evolução e histórico do AEE."
    )

    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="plano_ia_estudante_v19",
        )
        estudante = buscar_estudante(estudante_id)

        avaliacao_ia = ultima_avaliacao(estudante_id)
        entrevista_ia = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)
        estudo_ia = ultima_linha("estudos_caso", CAMPOS_ESTUDO_CASO, estudante_id)
        plano_manual_ia = ultima_linha("planos_aee", CAMPOS_PLANO_AEE, estudante_id)

        pendencias = []
        if not entrevista_ia:
            pendencias.append("Entrevista com a família")
        if not avaliacao_ia:
            pendencias.append("Avaliação pedagógica")
        if not estudo_ia:
            pendencias.append("Estudo de caso GRE")

        escutas_docentes_ia = listar_escutas_docentes(estudante_id)
        relatorios_docente_ia = listar_relatorios_docente(estudante_id)

        with st.container(border=True):
            st.markdown("### ✅ Dados usados pela IA")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Entrevista familiar", "OK" if entrevista_ia else "Pendente")
            c2.metric("Avaliação pedagógica", "OK" if avaliacao_ia else "Pendente")
            c3.metric("Estudo de caso GRE", "OK" if estudo_ia else "Pendente")
            c4.metric("Escuta docente", f"{len(escutas_docentes_ia)} registro(s)" if escutas_docentes_ia else "Pendente")
            c5.metric("Relatórios docentes", f"{len(relatorios_docente_ia)} salvo(s)" if relatorios_docente_ia else "Opcional")
            c6.metric("Plano AEE manual", "OK" if plano_manual_ia else "Opcional")

            fontes_ativas = []
            if entrevista_ia:
                fontes_ativas.append("entrevista familiar")
            if avaliacao_ia:
                fontes_ativas.append("avaliação pedagógica")
            if estudo_ia:
                fontes_ativas.append("estudo de caso GRE")
            if escutas_docentes_ia:
                fontes_ativas.append("escuta docente/histórico de escutas")
            if relatorios_docente_ia:
                fontes_ativas.append("relatórios de apoio ao docente")
            if plano_manual_ia:
                fontes_ativas.append("plano AEE manual")

            if pendencias:
                st.warning(
                    "Ainda faltam dados para uma sugestão mais personalizada: " + ", ".join(pendencias) + ". "
                    "Mesmo assim, é possível gerar um roteiro inicial de observação e planejamento sem presumir informações não registradas."
                )
            else:
                st.success("Dados mínimos encontrados. A IA pode gerar sugestões mais personalizadas para o estudante.")

            if fontes_ativas:
                st.caption("Fontes pedagógicas consideradas neste estudante: " + ", ".join(fontes_ativas) + ".")

        escolha_plano_ia = st.radio(
            "Escolha o que deseja fazer",
            [
                "🧩 Perfil Pedagógico Inteligente",
                "📅 Plano Mensal IA",
                "📈 Evolução IA",
                "📚 Bases de Conhecimento",
                "📝 Plano AEE Manual",
                "🗂️ Histórico IA",
            ],
            horizontal=True,
            key=f"radio_plano_ia_v22_{estudante_id}",
        )

        st.divider()

        if escolha_plano_ia == "🧩 Perfil Pedagógico Inteligente":
            st.markdown("### 🧩 Perfil Pedagógico Inteligente")
            st.info(
                "Organiza informações pedagógicas, funcionais e educacionais registradas no sistema para apoiar o planejamento do AEE, considerando comunicação, autonomia, participação escolar, acessibilidade, interação social e estratégias pedagógicas."
            )
            st.caption(
                "Este recurso possui finalidade exclusivamente pedagógica e educacional, não realizando diagnóstico clínico, médico ou terapêutico."
            )
            if st.button("🧩 Gerar Perfil Pedagógico Inteligente", key=f"gerar_perfil_pedagogico_v22_{estudante_id}"):
                with st.spinner("Gerando Perfil Pedagógico Inteligente com IA..."):
                    st.session_state[f"perfil_pedagogico_ia_v30_{estudante_id}"] = gerar_perfil_pedagogico_aee_ia(
                        estudante, avaliacao_ia, entrevista_ia, estudo_ia, plano_manual_ia
                    )

            if f"perfil_pedagogico_ia_v30_{estudante_id}" in st.session_state:
                perfil_pedagogico_txt = st.text_area(
                    "Perfil pedagógico gerado",
                    st.session_state[f"perfil_pedagogico_ia_v30_{estudante_id}"],
                    height=520,
                    key=f"perfil_pedagogico_txt_v30_{estudante_id}",
                )
                col_d1, col_d2 = st.columns([1, 1])
                with col_d1:
                    export_buttons(perfil_pedagogico_txt, f"Perfil_Pedagogico_Inteligente_{estudante[1]}", tipo_pdf="perfil_pedagogico")
                with col_d2:
                    if st.button("💾 Salvar perfil pedagógico no histórico", key=f"salvar_perfil_pedagogico_v22_{estudante_id}"):
                        salvar_historico_plano_aee_ia(
                            estudante_id=estudante_id,
                            mes_referencia="",
                            ano_referencia=agora_local().year,
                            qtd_atendimentos_semana=1,
                            tipo_geracao="Perfil Pedagógico Inteligente",
                            diagnostico_ia=perfil_pedagogico_txt,
                            observacoes="Perfil Pedagógico Inteligente gerado no módulo Plano AEE - IA.",
                        )
                        st.success("Perfil pedagógico salvo no histórico IA.")
                        st.rerun()

        # A opção "Sugestão Geral AEE" foi incorporada ao Perfil Pedagógico Inteligente.
        # A função gerar_sugestao_geral_aee_ia permanece no código apenas para compatibilidade
        # com históricos antigos, mas não aparece mais como botão separado na interface.

        elif escolha_plano_ia == "📅 Plano Mensal IA":
            st.markdown("### 📅 Plano mensal inteligente")
            st.info(
                "Organiza os atendimentos do mês por semana. Para cada atendimento, a IA sugere objetivo, atividade, recursos e registro esperado."
            )
            meses = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
            ]
            dias_cadastrados_txt = ""
            try:
                dias_cadastrados_txt = estudante[7] or ""
            except Exception:
                dias_cadastrados_txt = ""
            dias_padrao = [d for d in DIAS_SEMANA if d in dias_cadastrados_txt]
            if not dias_padrao:
                dias_padrao = ["Segunda-feira", "Quarta-feira"]

            col_m1, col_m2, col_m3 = st.columns([1, 1, 2])
            with col_m1:
                mes_ref = st.selectbox("Mês de referência", meses, index=agora_local().month - 1, key=f"mes_plano_ia_v19_{estudante_id}")
            with col_m2:
                ano_ref = st.text_input("Ano de referência", value=str(agora_local().year), key=f"ano_plano_ia_v19_{estudante_id}")
            with col_m3:
                dias_atendimento_ref = st.multiselect(
                    "Dias de atendimento na SRM",
                    DIAS_SEMANA,
                    default=dias_padrao,
                    key=f"dias_atendimento_plano_ia_v23_{estudante_id}",
                    help="O sistema calcula automaticamente quantos atendimentos existirão no mês com base nos dias selecionados.",
                )

            datas_calculadas = gerar_datas_atendimentos_mes(ano_ref, mes_ref, dias_atendimento_ref)
            qtd_semana = max(1, len(dias_atendimento_ref))
            total_atendimentos_calculado = len(datas_calculadas)

            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.metric("Atendimentos calculados no mês", total_atendimentos_calculado)
            with col_info2:
                st.metric("Dias por semana", qtd_semana)

            with st.expander("📆 Ver datas previstas de atendimento", expanded=True):
                st.text(datas_atendimentos_para_texto(datas_calculadas))

            st.caption(
                "O roteiro gerado usa as datas reais do mês. Após cada encontro, registre o atendimento no módulo Atendimentos para alimentar a evolução da IA."
            )

            if st.button("📅 Gerar Plano Mensal AEE - IA", key=f"gerar_plano_mensal_v19_{estudante_id}"):
                with st.spinner("Gerando plano mensal por semanas e atendimentos..."):
                    plano_base = gerar_plano_mensal_aee_ia(
                        estudante,
                        mes_ref,
                        ano_ref,
                        qtd_semana,
                        avaliacao_ia,
                        entrevista_ia,
                        estudo_ia,
                        plano_manual_ia,
                        datas_calculadas,
                    )
                    complemento = f"""

ORGANIZAÇÃO OPERACIONAL PARA REGISTRO NO SISTEMA
Mês de referência: {mes_ref}/{ano_ref}
Dias de atendimento selecionados: {", ".join(dias_atendimento_ref) if dias_atendimento_ref else "Não informado"}
Total real de atendimentos no mês: {total_atendimentos_calculado}

Datas previstas:
{datas_atendimentos_para_texto(datas_calculadas)}

Modelo obrigatório para cada atendimento:
- Objetivo do atendimento:
- Atividade proposta:
- Recursos utilizados:
- Mediação necessária:
- Resposta esperada do estudante:
- Como registrar depois no módulo Atendimentos:
""".strip()
                    st.session_state[f"plano_mensal_ia_v19_{estudante_id}"] = plano_base + "\n\n" + complemento

            if f"plano_mensal_ia_v19_{estudante_id}" in st.session_state:
                plano_mensal_txt = st.text_area(
                    "Plano mensal gerado",
                    st.session_state[f"plano_mensal_ia_v19_{estudante_id}"],
                    height=680,
                    key=f"plano_mensal_txt_v19_{estudante_id}",
                )
                col_pm1, col_pm2 = st.columns([1, 1])
                with col_pm1:
                    export_buttons(plano_mensal_txt, f"Plano_Mensal_AEE_IA_{estudante[1]}_{mes_ref}_{ano_ref}", tipo_pdf="plano_ia_visual")
                with col_pm2:
                    if st.button("💾 Salvar plano mensal no histórico", key=f"salvar_plano_mensal_v19_{estudante_id}"):
                        salvar_historico_plano_aee_ia(
                            estudante_id=estudante_id,
                            mes_referencia=mes_ref,
                            ano_referencia=ano_ref,
                            qtd_atendimentos_semana=int(qtd_semana),
                            tipo_geracao="Plano Mensal IA",
                            plano_mensal=plano_mensal_txt,
                            observacoes=f"Plano mensal calculado automaticamente com {total_atendimentos_calculado} atendimento(s) no mês, considerando os dias: {', '.join(dias_atendimento_ref)}.",
                        )
                        st.success("Plano mensal salvo no histórico IA.")
                        st.rerun()

        elif escolha_plano_ia == "📈 Evolução IA":
            st.markdown("### 📈 Evolução inteligente")
            st.info(
                "Usa os registros de atendimento para apoiar a análise de avanços, barreiras persistentes, recursos mais efetivos e ajustes para o próximo mês."
            )
            if st.button("📈 Gerar análise evolutiva IA", key=f"gerar_evolucao_ia_v19_{estudante_id}"):
                historico_txt = listar_atendimentos_texto(estudante_id)
                if "Nenhum atendimento registrado" in historico_txt:
                    st.warning("Ainda não há atendimentos registrados. Registre os atendimentos para gerar uma análise evolutiva consistente.")
                    st.session_state[f"evolucao_ia_v19_{estudante_id}"] = (
                        "Ainda não há atendimentos suficientes para análise evolutiva. "
                        "Registre objetivo, atividade, resposta do estudante, avanços, dificuldades, engajamento e encaminhamentos após cada atendimento."
                    )
                else:
                    with st.spinner("Gerando análise evolutiva com base nos atendimentos..."):
                        st.session_state[f"evolucao_ia_v19_{estudante_id}"] = gerar_perfil_pedagogico_aee_ia(
                            estudante, avaliacao_ia, entrevista_ia, estudo_ia, plano_manual_ia
                        )

            if f"evolucao_ia_v19_{estudante_id}" in st.session_state:
                evolucao_txt = st.text_area(
                    "Análise evolutiva gerada",
                    st.session_state[f"evolucao_ia_v19_{estudante_id}"],
                    height=540,
                    key=f"evolucao_txt_v19_{estudante_id}",
                )
                col_e1, col_e2 = st.columns([1, 1])
                with col_e1:
                    export_buttons(evolucao_txt, f"Evolucao_AEE_IA_{estudante[1]}", tipo_pdf="relatorio")
                with col_e2:
                    if st.button("💾 Salvar evolução no histórico", key=f"salvar_evolucao_ia_v19_{estudante_id}"):
                        salvar_historico_plano_aee_ia(
                            estudante_id=estudante_id,
                            mes_referencia="",
                            ano_referencia=agora_local().year,
                            qtd_atendimentos_semana=1,
                            tipo_geracao="Evolução IA",
                            diagnostico_ia=evolucao_txt,
                            observacoes="Análise evolutiva com base nos registros de atendimento.",
                        )
                        st.success("Evolução salva no histórico IA.")
                        st.rerun()

        elif escolha_plano_ia == "📚 Bases de Conhecimento":
            st.markdown("### 📚 Bases de Conhecimento IA")
            st.caption("Confira e indexe os PDFs colocados nas pastas base_conhecimento/cientifica e base_conhecimento/pedagogica.")
            col_base1, col_base2 = st.columns(2)
            with col_base1:
                st.markdown("#### Base Científica Inclusiva")
                pdfs_cientificos = listar_pdfs_base(PASTA_CIENTIFICA)
                st.metric("PDFs científicos", len(pdfs_cientificos))
                if pdfs_cientificos:
                    with st.expander("Ver PDFs científicos"):
                        for pdf in pdfs_cientificos:
                            st.write(f"• {pdf.name}")
                else:
                    st.info("Nenhum PDF encontrado em base_conhecimento/cientifica")
                if st.button("Indexar Base Científica", key="indexar_base_cientifica_plano_ia_v19"):
                    try:
                        with st.spinner("Indexando base científica..."):
                            total, msg = indexar_base_conhecimento("cientifica")
                        st.success(f"{msg} Total de trechos indexados: {total}")
                    except Exception as e:
                        st.error(f"Erro ao indexar base científica: {e}")
            with col_base2:
                st.markdown("#### Base Pedagógica AEE")
                pdfs_pedagogicos = listar_pdfs_base(PASTA_PEDAGOGICA)
                st.metric("PDFs pedagógicos", len(pdfs_pedagogicos))
                if pdfs_pedagogicos:
                    with st.expander("Ver PDFs pedagógicos"):
                        for pdf in pdfs_pedagogicos:
                            st.write(f"• {pdf.name}")
                else:
                    st.info("Nenhum PDF encontrado em base_conhecimento/pedagogica")
                if st.button("Indexar Base Pedagógica", key="indexar_base_pedagogica_plano_ia_v19"):
                    try:
                        with st.spinner("Indexando base pedagógica..."):
                            total, msg = indexar_base_conhecimento("pedagogica")
                        st.success(f"{msg} Total de trechos indexados: {total}")
                    except Exception as e:
                        st.error(f"Erro ao indexar base pedagógica: {e}")

            st.markdown("#### Consultar manualmente as bases")
            pergunta_base = st.text_area(
                "Digite uma pergunta para consultar os documentos",
                placeholder="Ex: Que estratégias usar para estudante com TEA no AEE?",
                key=f"pergunta_base_conhecimento_ia_v19_{estudante_id}",
            )
            bases_escolhidas = st.multiselect(
                "Bases para consulta",
                ["cientifica", "pedagogica"],
                default=["cientifica", "pedagogica"],
                key=f"bases_consulta_manual_v19_{estudante_id}",
            )
            if st.button("Consultar bases", key=f"consultar_bases_ia_v19_{estudante_id}"):
                if not pergunta_base.strip():
                    st.warning("Digite uma pergunta primeiro.")
                else:
                    with st.spinner("Buscando trechos nas bases..."):
                        resultados = buscar_na_base_conhecimento(pergunta_base, bases=bases_escolhidas, limite=6)
                        contexto = montar_contexto_base(resultados)
                        st.session_state[f"consulta_base_resultado_v19_{estudante_id}"] = contexto
            if f"consulta_base_resultado_v19_{estudante_id}" in st.session_state:
                st.text_area("Trechos encontrados", st.session_state[f"consulta_base_resultado_v19_{estudante_id}"], height=320)

        elif escolha_plano_ia == "📝 Plano AEE Manual":
            st.markdown("### 📝 Novo Plano AEE / PAEE manual")
            with st.form("form_plano_manual_ia_v19"):
                habilidades_lista = st.multiselect("1.1 Habilidades prioritárias que serão trabalhadas na SRM", OPCOES_HABILIDADES_PRIORITARIAS_SRM)
                habilidades_outros = st.text_area("Complemento de habilidades prioritárias, se necessário")
                recursos_lista = st.multiselect("1.2 Recursos de acessibilidade que serão disponibilizados ao estudante", OPCOES_RECURSOS_ACESSIBILIDADE)
                recursos_outros = st.text_area("Complemento de recursos de acessibilidade, se necessário")
                objetivos_gerais = st.text_area("2.1 Objetivo geral")
                objetivos_especificos = st.text_area("2.2 Objetivos específicos")
                metodologia = st.text_area("3.1 Metodologia")
                estrategias = st.text_area("3.2 Estratégia")
                prazo = st.text_area("3.3 Prazo")
                acoes_lista = st.multiselect("4. Ações desenvolvidas no âmbito da escola", OPCOES_ACOES_ESCOLA)
                acoes_outros = st.text_area("Descrição/complemento das ações desenvolvidas")
                barreiras_lista = st.multiselect("5. Barreiras identificadas na comunidade escolar", OPCOES_BARREIRAS)
                barreiras_outros = st.text_area("Descrição/complemento das barreiras identificadas")
                parcerias = st.text_area("6. Parcerias realizadas pelo AEE ao longo do período")
                avaliacao = st.text_area("7. Avaliação")
                observacoes = st.text_area("Observações complementares")
                if st.form_submit_button("Salvar Plano AEE / PAEE manual"):
                    habilidades = "; ".join([x for x in [", ".join(habilidades_lista), habilidades_outros] if x])
                    recursos = "; ".join([x for x in [", ".join(recursos_lista), recursos_outros] if x])
                    acoes_escola = "; ".join([x for x in [", ".join(acoes_lista), acoes_outros] if x])
                    barreiras = "; ".join([x for x in [", ".join(barreiras_lista), barreiras_outros] if x])
                    inserir_registro(
                        "planos_aee",
                        ["estudante_id", *CAMPOS_PLANO_AEE],
                        [
                            estudante_id, hoje_str(), habilidades, recursos, objetivos_gerais, objetivos_especificos,
                            metodologia, estrategias, prazo, acoes_escola, barreiras, parcerias, avaliacao, observacoes,
                        ],
                    )
                    st.success("Plano manual salvo.")
                    st.rerun()

            st.markdown("### Histórico de planos manuais")
            planos = listar_por_estudante("planos_aee", CAMPOS_PLANO_AEE, estudante_id)
            if planos:
                for p in planos:
                    with st.expander(f"Plano em {p[1]}"):
                        texto = texto_plano_aee(estudante, p)
                        st.text(texto)
                        export_buttons(texto, f"Plano_AEE_PAEE_{estudante[1]}_{p[0]}", tipo_pdf="plano")
                        if st.button("Excluir plano", key=f"exc_plano_v19_{p[0]}"):
                            excluir_registro("planos_aee", p[0])
                            st.success("Plano excluído.")
                            st.rerun()
            else:
                st.info("Nenhum plano manual registrado.")

        elif escolha_plano_ia == "🗂️ Histórico IA":
            st.markdown("### 🗂️ Histórico do Plano AEE - IA")
            campos_hist_ia = CAMPOS_PLANO_AEE_IA
            historico_ia = listar_por_estudante("plano_aee_ia", campos_hist_ia, estudante_id)
            if historico_ia:
                for item in historico_ia:
                    item_id = item[0]
                    data_geracao = item[1]
                    mes_hist = item[2]
                    ano_hist = item[3]
                    tipo_hist = item[5] or "Registro IA"
                    diagnostico_hist = item[6] or ""
                    sugestao_hist = item[7] or ""
                    plano_hist = item[11] or item[12] or ""
                    conteudo_hist = diagnostico_hist or sugestao_hist or plano_hist or item[13] or ""
                    titulo_hist = f"{tipo_hist} - {normalizar_data_historico(data_geracao)}"
                    if mes_hist or ano_hist:
                        titulo_hist += f" - {mes_hist or ''}/{ano_hist or ''}"
                    with st.expander(titulo_hist):
                        st.text_area("Conteúdo", conteudo_hist, height=440, key=f"hist_plano_ia_v19_{item_id}")
                        export_buttons(conteudo_hist, f"Plano_AEE_IA_{estudante[1]}_{item_id}", tipo_pdf=("plano_ia_visual" if "Plano Mensal" in str(tipo_hist) else "plano"))
                        if st.button("Excluir registro IA", key=f"exc_plano_ia_v19_{item_id}"):
                            excluir_registro("plano_aee_ia", item_id)
                            st.success("Registro IA excluído.")
                            st.rerun()
            else:
                st.info("Nenhum registro IA salvo ainda.")

elif menu == "Atendimentos":
    st.markdown('<div class="subtitulo">📌 Registro dos atendimentos</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox("Selecione o estudante", ids, format_func=lambda x: mapa[x], key="atendimento_estudante")
        estudante = buscar_estudante(estudante_id)

        with st.container(border=True):
            st.markdown("### Novo atendimento")
            with st.form("form_atendimento"):
                data_atendimento = st.date_input("Data do atendimento")
                objetivo = st.text_area("Objetivo trabalhado")
                atividade = st.text_area("Atividade realizada")
                resposta = st.text_area("Resposta do estudante")
                nivel_resposta = st.slider("Escala da resposta do estudante", 1, 10, 5)
                avancos = st.text_area("Avanços observados")
                nivel_avanco = st.slider("Escala do avanço pedagógico", 1, 10, 5)
                dificuldades = st.text_area("Dificuldades observadas")
                nivel_dificuldade = st.slider("Escala de dificuldade/barreira observada", 1, 10, 5)
                evolucao = st.text_area("Evolução observada")
                nivel_engajamento = st.slider("Escala de engajamento/participação", 1, 10, 5)
                indice = calcular_indice_geral(nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento)
                st.info(f"Índice geral calculado automaticamente: {indice}/10")
                encaminhamentos = st.text_area("Encaminhamentos")

                st.markdown("#### 🧩 Recursos pedagógicos utilizados")
                st.caption(
                    "Registre apenas o material criado ou utilizado no atendimento. "
                    "Não insira fotos do estudante; use links do Drive, Canva, Wordwall, modelos 3D, jogos ou documentos pedagógicos."
                )

                qtd_recursos = st.number_input(
                    "Quantidade de recursos/materiais utilizados",
                    min_value=0,
                    max_value=10,
                    value=0,
                    step=1,
                    help="Use quando houver mais de um material pedagógico vinculado ao atendimento.",
                )

                categorias_recursos = [
                    "CAA / Comunicação alternativa",
                    "Rotina visual",
                    "Jogo pedagógico",
                    "Atividade digital",
                    "Wordwall",
                    "Canva",
                    "Impressão 3D",
                    "Robótica educacional",
                    "Material concreto/manipulável",
                    "Tecnologia assistiva",
                    "Outro",
                ]

                recursos_registrados = []
                for i in range(int(qtd_recursos)):
                    st.markdown(f"**Recurso {i + 1}**")
                    c1, c2 = st.columns([1.2, 1])
                    with c1:
                        nome_recurso = st.text_input(
                            "Nome do recurso/material",
                            key=f"recurso_nome_{i}",
                            placeholder="Ex.: Prancha CAA alimentar, atividade Wordwall, modelo 3D...",
                        )
                    with c2:
                        categoria_recurso = st.selectbox(
                            "Categoria",
                            categorias_recursos,
                            key=f"recurso_categoria_{i}",
                        )
                    link_recurso = st.text_input(
                        "Link do material",
                        key=f"recurso_link_{i}",
                        placeholder="Cole aqui o link do Drive, Canva, Wordwall, arquivo 3D, vídeo ou documento.",
                    )
                    observacao_uso = st.text_area(
                        "Observação sobre o uso do recurso",
                        key=f"recurso_obs_{i}",
                        placeholder="Ex.: apresentou maior engajamento; precisou de mediação; facilitou a escolha visual...",
                        height=80,
                    )
                    recursos_registrados.append((nome_recurso, categoria_recurso, link_recurso, observacao_uso))

                if st.form_submit_button("Salvar atendimento"):
                    atendimento_id = salvar_atendimento(
                        estudante_id, data_atendimento.strftime("%d/%m/%Y"), objetivo, atividade, resposta,
                        avancos, dificuldades, evolucao, 1, nivel_resposta, nivel_avanco,
                        nivel_dificuldade, nivel_engajamento, indice, encaminhamentos,
                    )

                    for nome_recurso, categoria_recurso, link_recurso, observacao_uso in recursos_registrados:
                        if nome_recurso.strip() or link_recurso.strip() or observacao_uso.strip():
                            salvar_recurso_atendimento(
                                atendimento_id,
                                estudante_id,
                                nome_recurso.strip(),
                                categoria_recurso,
                                link_recurso.strip(),
                                observacao_uso.strip(),
                            )

                    st.success("Atendimento registrado com recursos pedagógicos vinculados.")
                    st.rerun()

        atendimentos = listar_atendimentos_com_id(estudante_id)

        with st.container(border=True):
            st.markdown("### 📊 Indicadores por atendimento")
            render_grafico_evolucao(listar_atendimentos(estudante_id))

        with st.container(border=True):
            st.markdown("### Histórico de atendimentos")
            if atendimentos:
                for a in atendimentos:
                    with st.expander(f"Atendimento em {a[1]}"):
                        texto = texto_atendimento(estudante, a)
                        st.text(texto)

                        recursos_do_atendimento = listar_recursos_atendimento(a[0])
                        if recursos_do_atendimento:
                            st.markdown("#### 🧩 Recursos pedagógicos vinculados")
                            dados_recursos = []
                            for r in recursos_do_atendimento:
                                _, nome, categoria, link, observacao, criado_em = r
                                dados_recursos.append({
                                    "Recurso/material": nome or "Não informado",
                                    "Categoria": categoria or "Não informada",
                                    "Link": link or "",
                                    "Observação": observacao or "",
                                })
                            st.dataframe(pd.DataFrame(dados_recursos), use_container_width=True)
                            for r in recursos_do_atendimento:
                                _, nome, categoria, link, observacao, criado_em = r
                                if link:
                                    st.markdown(f"🔗 [{nome or 'Abrir recurso pedagógico'}]({link})")

                        export_buttons(texto, f"Registro_Atendimento_{estudante[1]}_{a[0]}", tipo_pdf="atendimento")
                        if st.button("Excluir atendimento", key=f"exc_at_{a[0]}"):
                            excluir_atendimento(a[0])
                            st.success("Atendimento excluído.")
                            st.rerun()
            else:
                st.info("Nenhum atendimento registrado.")


# ======================================================
# AGENDA DE ATENDIMENTOS
# ======================================================
elif menu == "Agenda de Atendimentos":
    st.markdown('<div class="subtitulo">📅 Agenda de Atendimentos</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        with st.container(border=True):
            st.markdown("### Novo agendamento")
            with st.form("form_agenda"):
                estudante_id = st.selectbox("Estudante", ids, format_func=lambda x: mapa[x])
                data_ag = st.date_input("Data do atendimento")
                dia_semana = st.selectbox("Dia da semana", DIAS_SEMANA)
                hora_inicio = st.time_input("Hora início", value=time(8, 0))
                hora_fim = st.time_input("Hora fim", value=time(8, 50))
                tipo = st.selectbox("Tipo de atendimento", ["Individual", "Grupo", "Acompanhamento", "Observação", "Outro"])
                obs = st.text_area("Observações")
                if st.form_submit_button("Salvar agendamento"):
                    salvar_agendamento(
                        estudante_id,
                        data_ag.strftime("%d/%m/%Y"),
                        dia_semana,
                        hora_inicio.strftime("%H:%M"),
                        hora_fim.strftime("%H:%M"),
                        tipo,
                        obs,
                    )
                    st.success("Agendamento salvo.")
                    st.rerun()

    agenda = listar_agenda()
    with st.container(border=True):
        st.markdown("### 📆 Agenda semanal")
        if agenda:
            df = pd.DataFrame(
                agenda,
                columns=["ID", "Código", "Ano/Série", "Perfil", "Data", "Dia", "Início", "Fim", "Tipo", "Observações"],
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            col_csv, col_txt, col_pdf = st.columns(3)
            with col_csv:
                st.download_button("Baixar agenda em CSV", csv, "Agenda_INCLUISRM.csv", "text/csv")
            with col_txt:
                texto = texto_agenda(df)
                st.download_button("Baixar agenda em TXT", texto, "Agenda_INCLUISRM.txt", "text/plain")
            with col_pdf:
                if st.button("Gerar PDF da agenda"):
                    arquivo = gerar_pdf_documento(texto_agenda(df), "Agenda_INCLUISRM", tipo="agenda")
                    st.session_state["pdf_agenda"] = arquivo
                if "pdf_agenda" in st.session_state:
                    with open(st.session_state["pdf_agenda"], "rb") as f:
                        st.download_button("Baixar PDF da agenda", f, "Agenda_INCLUISRM.pdf", "application/pdf")

            for _, row in df.iterrows():
                with st.expander(f"{row['Data']} - {row['Início']} - {row['Código']}"):
                    st.write(row.to_dict())
                    col_status1, col_status2, col_status3 = st.columns(3)
                    with col_status1:
                        if st.button("Marcar Compareceu", key=f"cmp_ag_{row['ID']}"):
                            atualizar_status_agenda(int(row["ID"]), "Compareceu")
                            st.success("Presença marcada como compareceu.")
                            st.rerun()
                    with col_status2:
                        if st.button("Marcar Faltou", key=f"falt_ag_{row['ID']}"):
                            atualizar_status_agenda(int(row["ID"]), "Faltou")
                            st.success("Presença marcada como falta.")
                            st.rerun()
                    with col_status3:
                        if st.button("Marcar Justificado", key=f"just_ag_{row['ID']}"):
                            atualizar_status_agenda(int(row["ID"]), "Justificado")
                            st.success("Presença marcada como justificada.")
                            st.rerun()
                    if st.button("Excluir agendamento", key=f"exc_ag_{row['ID']}"):
                        excluir_agendamento(int(row["ID"]))
                        st.success("Agendamento excluído.")
                        st.rerun()
        else:
            st.info("Nenhum agendamento registrado.")


# ======================================================
# RELATÓRIOS GRE
# ======================================================
elif menu == "Relatórios GRE":
    st.markdown('<div class="subtitulo">📄 Relatórios GRE</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="descricao">
        Gere os documentos solicitados pela GRE sob demanda, a partir dos dados já cadastrados no sistema.
        Os arquivos não ficam armazenados no banco; apenas a data e o tipo de documento gerado entram no histórico.
        Os campos sigilosos permanecem em branco para preenchimento manual no Word ou após impressão.
        </div>
        """,
        unsafe_allow_html=True,
    )

    estudantes = listar_estudantes()
    professores = listar_professores()

    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox("Selecione o estudante", ids, format_func=lambda x: mapa[x], key="gre_estudante")
        estudante = buscar_estudante(estudante_id)

        with st.container(border=True):
            st.markdown("### 📌 Documentos GRE disponíveis")
            tipo = st.selectbox(
                "Escolha o documento que deseja gerar",
                [
                    "Ficha de Identificação Professor(a) AEE",
                    "Matrícula SRM / Termo de Ciência",
                    "Relatório Comparativo das Entrevistas Familiares",
                    "Registro da Entrevista Familiar (última registrada)",
                    "Estudo de Caso e Plano AEE",
                    "Relatório Consolidado GRE",
                    "Quadro Semanal - Ações/Práticas do Professor AEE",
                    "Pacote GRE Completo",
                ],
            )

            st.info(
                "Os campos como nome completo, CPF, endereço, telefone pessoal, NIS, Cartão SUS e dados familiares sensíveis ficarão em branco para preenchimento manual."
            )
            if tipo == "Relatório Comparativo das Entrevistas Familiares":
                st.success("Este relatório será gerado a partir das entrevistas familiares já registradas no sistema, comparando uma entrevista anterior com uma entrevista atual. A IA atua apenas na análise comparativa, sem criar ou alterar respostas da família.")
            elif tipo == "Registro da Entrevista Familiar (última registrada)":
                st.warning("Este documento apenas imprime a última entrevista familiar registrada. Para analisar mudanças entre anos, escolha 'Relatório Comparativo das Entrevistas Familiares'.")

            # Configurações específicas do Quadro Semanal GRE
            data_inicio_qs = None
            data_fim_qs = None
            escola_qs = ""
            regional_qs = ""
            mes_qs = agora_local().strftime("%m")
            ano_qs = agora_local().strftime("%Y")
            df_quadro_qs = pd.DataFrame()

            entrevista_comp_anterior_id = None
            entrevista_comp_atual_id = None

            if tipo == "Relatório Comparativo das Entrevistas Familiares":
                st.markdown("### 👪 Configuração do relatório comparativo familiar")
                entrevistas_familia = listar_por_estudante("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)
                if len(entrevistas_familia) < 2:
                    st.warning("Registre pelo menos duas entrevistas familiares para gerar o relatório comparativo.")
                else:
                    mapa_entrevistas = {
                        e[0]: f"#{e[0]} | Data: {e[1] or 'Não informada'} | Ano: {(e[2] if len(e) > 2 else '') or 'Não informado'} | Tipo: {(e[3] if len(e) > 3 else '') or 'Não informado'}"
                        for e in entrevistas_familia
                    }
                    ids_entrevistas = [e[0] for e in entrevistas_familia]
                    col_ent_ant, col_ent_atu = st.columns(2)
                    with col_ent_ant:
                        entrevista_comp_anterior_id = st.selectbox(
                            "Entrevista anterior/base",
                            ids_entrevistas,
                            index=1 if len(ids_entrevistas) > 1 else 0,
                            format_func=lambda x: mapa_entrevistas[x],
                            key="gre_entrevista_comparativa_anterior",
                        )
                    with col_ent_atu:
                        entrevista_comp_atual_id = st.selectbox(
                            "Entrevista atual/comparada",
                            ids_entrevistas,
                            index=0,
                            format_func=lambda x: mapa_entrevistas[x],
                            key="gre_entrevista_comparativa_atual",
                        )
                    if entrevista_comp_anterior_id == entrevista_comp_atual_id:
                        st.info("Selecione duas entrevistas diferentes para uma comparação mais útil.")
                    st.caption("A entrevista familiar continua manual. A IA pode ser usada apenas para analisar a comparação entre duas entrevistas, sem criar ou alterar respostas da família.")

                    observacao_ia_entrevista = st.text_area(
                        "Orientação para a análise com IA (opcional)",
                        placeholder="Ex: observar possível impacto de luto, mudança de responsável, alteração na rotina ou sinais de desregulação.",
                        key="gre_entrevista_observacao_ia",
                    )

                    if st.button("🤖 Gerar análise comparativa das entrevistas com IA", key="gre_entrevista_comparativa_ia"):
                        entrevista_anterior_ia = buscar_entrevista_familia_por_id(entrevista_comp_anterior_id) if entrevista_comp_anterior_id else None
                        entrevista_atual_ia = buscar_entrevista_familia_por_id(entrevista_comp_atual_id) if entrevista_comp_atual_id else None
                        with st.spinner("Analisando comparação das entrevistas familiares com IA..."):
                            st.session_state["analise_ia_entrevistas_familia"] = gerar_analise_ia_comparativo_entrevistas_familia(
                                estudante,
                                entrevista_anterior=entrevista_anterior_ia,
                                entrevista_atual=entrevista_atual_ia,
                                observacao_professor=observacao_ia_entrevista,
                            )

                    if "analise_ia_entrevistas_familia" in st.session_state:
                        st.markdown("### 🤖 Análise comparativa com IA")
                        st.text_area(
                            "Análise editável antes de usar no relatório",
                            st.session_state["analise_ia_entrevistas_familia"],
                            height=360,
                            key="gre_entrevista_analise_ia_texto",
                        )

            if tipo == "Quadro Semanal - Ações/Práticas do Professor AEE":
                st.markdown("### 📋 Configuração do Quadro Semanal")
                col_periodo1, col_periodo2, col_periodo3, col_periodo4 = st.columns(4)
                with col_periodo1:
                    data_inicio_qs = st.date_input("Data inicial", value=agora_local().date().replace(day=1), key="qs_inicio")
                with col_periodo2:
                    data_fim_qs = st.date_input("Data final", value=agora_local().date(), key="qs_fim")
                with col_periodo3:
                    mes_qs = st.text_input("Mês", value=agora_local().strftime("%m"), key="qs_mes")
                with col_periodo4:
                    ano_qs = st.text_input("Ano", value=agora_local().strftime("%Y"), key="qs_ano")

                col_escola, col_regional = st.columns(2)
                with col_escola:
                    escola_qs = st.text_input("Escola", value="", placeholder="Preencha ou deixe para puxar do professor cadastrado", key="qs_escola")
                with col_regional:
                    regional_qs = st.text_input("Regional", value="", placeholder="Ex: Metropolitana Norte", key="qs_regional")

                df_quadro_qs = montar_dataframe_quadro_semanal(
                    estudante_id=estudante_id,
                    data_inicio=data_inicio_qs,
                    data_fim=data_fim_qs,
                )

                st.markdown("### ✅ Presença automática e registros do período")
                if df_quadro_qs.empty:
                    st.info("Nenhum agendamento/atendimento encontrado no período selecionado.")
                else:
                    st.dataframe(df_quadro_qs, use_container_width=True, hide_index=True)

                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        st.markdown("#### 📈 Atendimentos por status")
                        status_df = df_quadro_qs.groupby("Presença").size().reset_index(name="Quantidade")
                        graf_status = (
                            alt.Chart(status_df)
                            .mark_bar()
                            .encode(
                                x=alt.X("Presença:N", title="Status"),
                                y=alt.Y("Quantidade:Q", title="Quantidade"),
                                tooltip=["Presença", "Quantidade"],
                            )
                            .properties(height=260)
                        )
                        st.altair_chart(graf_status, use_container_width=True)
                    with col_g2:
                        st.markdown("#### 📈 Atendimentos por data")
                        data_df = df_quadro_qs.groupby("Data").size().reset_index(name="Quantidade")
                        graf_data = (
                            alt.Chart(data_df)
                            .mark_bar()
                            .encode(
                                x=alt.X("Data:N", title="Data", sort=None),
                                y=alt.Y("Quantidade:Q", title="Quantidade"),
                                tooltip=["Data", "Quantidade"],
                            )
                            .properties(height=260)
                        )
                        st.altair_chart(graf_data, use_container_width=True)

                    foco_ia_qs = st.text_area(
                        "Orientação para a IA sugerir o preenchimento do quadro",
                        placeholder="Ex: sintetizar os recursos utilizados e as observações pedagógicas com linguagem institucional.",
                        key="qs_foco_ia",
                    )
                    if st.button("🤖 Sugerir preenchimento do Quadro Semanal com IA", key="qs_ia"):
                        with st.spinner("Gerando sugestão pedagógica para o quadro..."):
                            st.session_state["qs_sugestao_ia"] = gerar_sugestao_ia_quadro_semanal(df_quadro_qs, foco=foco_ia_qs)

                    if "qs_sugestao_ia" in st.session_state:
                        st.markdown("### 🤖 Sugestão da IA para preenchimento")
                        st.text_area("Sugestão editável", st.session_state["qs_sugestao_ia"], height=260, key="qs_sugestao_ia_texto")

            if st.button("Gerar documento GRE", key="gerar_documento_gre"):
                if tipo == "Ficha de Identificação Professor(a) AEE":
                    texto = texto_ficha_professor_gre()
                    tipo_pdf = "professor"
                    nome = "Ficha_Professor_AEE_GRE"

                elif tipo == "Matrícula SRM / Termo de Ciência":
                    texto = texto_matricula_srm_gre(estudante)
                    tipo_pdf = "matricula_srm"
                    nome = f"Matricula_SRM_Termo_Ciencia_{estudante[1]}"

                elif tipo == "Registro da Entrevista Familiar (última registrada)":
                    entrevista = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)
                    texto = texto_entrevista_familia_gre(estudante, entrevista)
                    tipo_pdf = "entrevista"
                    nome = f"Registro_Entrevista_Familiar_GRE_{estudante[1]}"

                elif tipo == "Relatório Comparativo das Entrevistas Familiares":
                    entrevista_anterior = buscar_entrevista_familia_por_id(entrevista_comp_anterior_id) if entrevista_comp_anterior_id else None
                    entrevista_atual = buscar_entrevista_familia_por_id(entrevista_comp_atual_id) if entrevista_comp_atual_id else None
                    texto = gerar_relatorio_comparativo_entrevistas_familia(
                        estudante,
                        entrevista_anterior=entrevista_anterior,
                        entrevista_atual=entrevista_atual,
                    )
                    analise_ia = st.session_state.get("analise_ia_entrevistas_familia", "")
                    if analise_ia:
                        texto = texto + "\n\n7. ANÁLISE COMPARATIVA COM APOIO DE IA\n" + analise_ia + "\n\nObservação: a análise com IA é apoio à leitura pedagógica. A entrevista familiar permanece como registro manual e a decisão final cabe ao professor do AEE."
                    tipo_pdf = "relatorio"
                    nome = f"Relatorio_Comparativo_Entrevistas_Familiares_{estudante[1]}"

                elif tipo == "Estudo de Caso e Plano AEE":
                    estudo = ultima_linha("estudos_caso", CAMPOS_ESTUDO_CASO, estudante_id)
                    plano = ultima_linha(
                        "planos_aee",
                        CAMPOS_PLANO_AEE,
                        estudante_id,
                    )
                    texto = texto_estudo_plano_aee_gre(estudante, estudo, plano)
                    tipo_pdf = "estudo"
                    nome = f"Estudo_Caso_Plano_AEE_GRE_{estudante[1]}"

                elif tipo == "Relatório Consolidado GRE":
                    texto = gerar_relatorio_gre_texto(estudante)
                    tipo_pdf = "relatorio"
                    nome = f"Relatorio_Consolidado_GRE_{estudante[1]}"

                elif tipo == "Quadro Semanal - Ações/Práticas do Professor AEE":
                    professor = buscar_professor_responsavel()
                    df_quadro_qs = montar_dataframe_quadro_semanal(
                        estudante_id=estudante_id,
                        data_inicio=data_inicio_qs,
                        data_fim=data_fim_qs,
                    )
                    texto = gerar_texto_quadro_semanal_gre(
                        professor=professor,
                        df_quadro=df_quadro_qs,
                        mes=mes_qs,
                        ano=ano_qs,
                        escola_manual=escola_qs,
                        regional_manual=regional_qs,
                    )
                    tipo_pdf = "relatorio"
                    nome = f"Quadro_Semanal_GRE_{estudante[1]}_{mes_qs}_{ano_qs}"
                    try:
                        arquivo_docx_qs = gerar_docx_quadro_semanal_gre(
                            professor=professor,
                            df_quadro=df_quadro_qs,
                            nome_base=f"{estudante[1]}_{mes_qs}_{ano_qs}",
                            mes=mes_qs,
                            ano=ano_qs,
                            escola_manual=escola_qs,
                            regional_manual=regional_qs,
                        )
                        st.session_state["gre_docx_quadro"] = arquivo_docx_qs
                    except Exception as e:
                        st.warning(f"Não foi possível gerar o Word em tabela do Quadro Semanal: {e}")

                else:
                    texto = texto_pacote_gre_completo(estudante)
                    tipo_pdf = "relatorio"
                    nome = f"Pacote_GRE_Completo_{estudante[1]}"

                st.session_state["gre_texto"] = texto
                st.session_state["gre_nome"] = nome
                st.session_state["gre_tipo_pdf"] = tipo_pdf
                st.session_state["gre_tipo"] = tipo

                registrar_documento_gre(
                    estudante_id=estudante_id,
                    tipo_documento=tipo,
                    nome_arquivo=nome,
                    observacao="Documento gerado sob demanda. PDF/Word não armazenado no banco.",
                )
                st.success("Documento GRE gerado sob demanda. Apenas o registro da geração foi salvo no histórico.")

        if "gre_texto" in st.session_state:
            with st.container(border=True):
                titulo_preview = st.session_state.get('gre_tipo', '')
                if titulo_preview == "Relatório Comparativo das Entrevistas Familiares":
                    st.markdown("### Documento gerado: Relatório Comparativo das Entrevistas Familiares")
                    st.caption("Este documento é produzido a partir de entrevistas já registradas no sistema e tem como objetivo analisar possíveis mudanças familiares, emocionais, comportamentais e pedagógicas ao longo do tempo.")
                else:
                    st.markdown(f"### Documento gerado: {titulo_preview}")
                st.text_area("Pré-visualização", st.session_state["gre_texto"], height=560)
                export_buttons(st.session_state["gre_texto"], st.session_state["gre_nome"], tipo_pdf=st.session_state["gre_tipo_pdf"])
                if st.session_state.get("gre_tipo") == "Quadro Semanal - Ações/Práticas do Professor AEE" and "gre_docx_quadro" in st.session_state:
                    try:
                        with open(st.session_state["gre_docx_quadro"], "rb") as f:
                            st.download_button(
                                "Baixar Quadro Semanal em Word com tabela",
                                data=f,
                                file_name=Path(st.session_state["gre_docx_quadro"]).name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="download_quadro_semanal_docx_tabela",
                            )
                    except Exception:
                        st.info("Gere novamente o Quadro Semanal para baixar o Word em tabela.")

        with st.container(border=True):
            st.markdown("### 🗂️ Histórico de geração GRE")
            st.caption("Este histórico guarda somente data, tipo e nome-base do documento. O arquivo e o conteúdo não ficam armazenados no banco.")
            historico_gre = listar_documentos_gre_gerados(estudante_id)
            if historico_gre:
                df_hist_gre = pd.DataFrame(
                    historico_gre,
                    columns=["ID", "Código", "Tipo de documento", "Nome-base", "Data de geração", "Observação"],
                )
                st.dataframe(df_hist_gre.drop(columns=["ID"]), use_container_width=True)

                excluir_hist = st.selectbox(
                    "Excluir item do histórico, se necessário",
                    [0] + [h[0] for h in historico_gre],
                    format_func=lambda x: "Não excluir" if x == 0 else f"Registro #{x}",
                    key="excluir_historico_gre",
                )
                if excluir_hist and st.button("Excluir registro do histórico GRE"):
                    excluir_historico_documento_gre(excluir_hist)
                    st.success("Registro removido do histórico.")
                    st.rerun()
            else:
                st.info("Nenhum documento GRE gerado para este estudante nesta base de dados.")

        with st.container(border=True):
            st.markdown("### 🧾 Conferência dos dados usados")
            st.write(f"**Código interno:** {estudante[1]}")
            st.write(f"**Ano/Série:** {estudante[2] or 'Não informado'}")
            st.write(f"**Turma:** {estudante[3] or 'Não informado'}")
            st.write(f"**Turno:** {estudante[6] or 'Não informado'}")
            st.write(f"**Perfil educacional:** {estudante[4] or 'Não informado'}")
            st.write(f"**Professor(a) AEE:** {texto_professores_vinculados(estudante_id)}")
            st.write("**Campos sigilosos:** permanecerão em branco no documento gerado.")


# ======================================================
# ADMINISTRAÇÃO
# ======================================================
elif menu == "Administração":
    st.markdown('<div class="subtitulo">⚙️ Administração e backup</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### Backup geral do banco")
        tabelas = listar_tabelas_banco()
        backup = {}
        for tabela in tabelas:
            backup[tabela] = carregar_tabela_dataframe(tabela)

        st.write("Tabelas encontradas:", ", ".join(tabelas))

        for tabela, df in backup.items():
            with st.expander(f"Tabela: {tabela} ({len(df)} registros)"):
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.download_button(
                    f"Baixar {tabela}.csv",
                    df.to_csv(index=False).encode("utf-8"),
                    f"{tabela}_incluisrm.csv",
                    "text/csv",
                    key=f"backup_{tabela}",
                )

        # Backup único em JSON
        json_texto = "{\n" + ",\n".join(
            [f'"{tabela}": {df.to_json(orient="records", force_ascii=False)}' for tabela, df in backup.items()]
        ) + "\n}"
        st.download_button(
            "Baixar backup completo em JSON",
            json_texto,
            f"backup_completo_incluisrm_{agora_local().strftime('%Y%m%d_%H%M')}.json",
            "application/json",
        )
