
import os
import sqlite3
from datetime import datetime, date, time
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
APP_SUBTITLE = "Sistema de Gestão do Atendimento Educacional Especializado"


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
    # Não armazenamos CPF, RG, endereço ou dados sensíveis do estudante; esses campos ficam em branco nos documentos finais.
    for coluna, definicao in [
        ("etapa_modalidade", "TEXT"),
        ("ano_etapa", "TEXT"),
        ("laudo", "TEXT"),
        ("deficiencia", "TEXT"),
        ("cid", "TEXT"),
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
            objetivos_gerais TEXT,
            objetivos_especificos TEXT,
            habilidades_prioritarias TEXT,
            recursos_acessibilidade TEXT,
            estrategias TEXT,
            organizacao_atendimento TEXT,
            parcerias TEXT,
            avaliacao_acompanhamento TEXT,
            observacoes TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

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

CAMPOS_ESTUDO_CASO = [
    "data_registro",
    "ano_letivo", "tipo_registro", "estudo_anterior_id", "analise_comparativa_ia", "sugestao_novo_estudo_ia",
    "contextualizacao", "queixa_principal", "potencialidades", "dificuldades", "estrategias", "intervencoes", "avaliacao", "consideracoes",
    "etapa_modalidade", "ano_etapa", "laudo", "deficiencia", "cid", "altas_habilidades", "bpc",
    "escola_nome", "unidade_aee", "gestor_nome", "gestor_contato",
    "professor_nome", "professor_contato", "matricula_professor", "especialidade_professor",
    "periodo_inicio", "periodo_fim", "frequencia_atendimento", "tempo_atendimento_semana", "formato_atendimento",
    "percurso_educacional", "motivo_encaminhamento_aee", "precisa_transporte_inclusivo", "recebe_transporte_inclusivo",
    "precisa_profissional_apoio", "justificativa_apoio", "acompanhado_profissional_apoio", "nome_profissional_apoio",
    "recursos_tecnologia_assistiva", "observacoes_ambiente_educacional",
    "habilidades_observadas", "habilidades_a_desenvolver", "indicadores_altas_habilidades",
    "recursos_surdez", "observacoes_surdez",
]

OPCOES_ANO_ETAPA = [
    "1º ano do EF", "2º ano do EF", "3º ano do EF", "4º ano do EF", "5º ano do EF",
    "6º ano do EF", "7º ano do EF", "8º ano do EF", "9º ano do EF",
    "1º ano do EM", "2º ano do EM", "3º ano do EM",
    "EJA - Módulo 1", "EJA - Módulo 2", "EJA - Módulo 3", "EJA - Módulo 5", "EJA - Módulo 6", "EJA - Módulo 7", "EJA - Módulo 8",
    "Outro / não informado",
]

OPCOES_ESPECIALIDADE_AEE = [
    "Professor(a) do AEE",
    "Professor(a) Brailista",
    "Professor(a) Instrutor(a) de LIBRAS",
    "Professor(a) Intérprete de LIBRAS",
    "Outra",
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
    "Inteligência interpessoal",
    "Interesse/habilidade em atividades sensoriais",
    "Raciocínio lógico-matemático",
    "Realiza as quatro operações",
    "Resolve situações-problema com autonomia",
    "Interesse em temas científicos",
    "Compreende explicações e cumpre comandos",
    "Demonstra criatividade",
    "Acompanha as atividades propostas do grupo/classe",
    "Usa recursos tecnológicos com autonomia",
    "Fluência na leitura",
    "Escreve textos com autonomia",
    "Apropriação do sistema de escrita alfabética",
    "Habilidades artísticas",
    "Comunica desejos e necessidades",
    "Apresenta atenção compartilhada",
    "Interesse por leitura",
    "Domina Libras",
    "Domina Braille",
    "Possui identidade surda",
    "Usa comunicação aumentativa e alternativa com autonomia",
    "Outro",
]

OPCOES_INDICADORES_AHSD = [
    "Aprende fácil e rapidamente",
    "Original, imaginativo(a), criativo(a), não convencional",
    "Pensa de forma incomum para resolver problemas",
    "Persistente, independente, autodirecionado(a)",
    "Persuasivo(a), capaz de influenciar os outros",
    "Inquisitivo(a), cético(a), curioso(a)",
    "Adapta-se a diferentes situações e novos ambientes",
    "Criativo(a) ao construir com materiais incomuns",
    "Habilidade nas artes (música, desenho, dança etc.)",
    "Entende a importância da natureza",
    "Vocabulário excepcional, verbalmente fluente",
    "Aprende facilmente novas línguas",
    "Trabalha independente e mostra iniciativa",
    "Bom julgamento e lógica",
    "Usa recursos tecnológicos com autonomia",
    "Versátil, muitos interesses e interesse além da idade cronológica",
    "Mostra insights e percepções incomuns",
    "Demonstra sensibilidade e empatia",
    "Apresenta excelente senso de humor",
    "Expressa ideias e reações de forma argumentativa",
    "Outro",
]

OPCOES_RECURSOS_TA = [
    "Recursos de comunicação alternativa/aumentativa",
    "Pranchas de comunicação",
    "Tablet/celular/computador com recurso acessível",
    "Materiais concretos/manipuláveis",
    "Recursos táteis/sensoriais",
    "Recursos em Libras",
    "Recursos em Braille",
    "Leitor de tela/ampliação",
    "Órteses/adaptações de acesso",
    "Jogos pedagógicos acessíveis",
    "Impressão 3D/recurso maker inclusivo",
    "Outro",
]

OPCOES_RECURSOS_SURDEZ = [
    "Implante coclear",
    "Aparelho auditivo",
    "Libras",
    "Leitura labial",
    "Intérprete de Libras",
    "Não se aplica",
]


def hoje_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def formatar_data(data_obj):
    if isinstance(data_obj, (datetime, date)):
        return data_obj.strftime("%d/%m/%Y")
    return str(data_obj)


def data_para_date(data_texto):
    try:
        return datetime.strptime(data_texto, "%d/%m/%Y").date()
    except Exception:
        return datetime.now().date()


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
        """
        <div class="app-hero">
            <span class="app-badge">Gestão do AEE • SRM • Relatórios • Agenda</span>
            <h1 class="app-title">INCLUISRM</h1>
            <p class="app-subtitle">Sistema de Gestão do Atendimento Educacional Especializado</p>
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
    run = titulo.add_run("INCLUISRM\nSistema de Gestão do Atendimento Educacional Especializado")
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
    rodape = doc.add_paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} pelo INCLUISRM.")
    rodape.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in rodape.runs:
        r.font.size = Pt(9)

    doc.save(nome_arquivo)
    return nome_arquivo


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
        "agenda", "atendimentos", "relatorios", "paees", "planos_aee",
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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
# CRUD - ATENDIMENTOS
# ======================================================
def salvar_atendimento(
    estudante_id, data_atendimento, objetivo, atividade, resposta_estudante,
    avancos, dificuldades, evolucao, qtd_atividades, nivel_resposta,
    nivel_avanco, nivel_dificuldade, nivel_engajamento, nivel_evolucao,
    encaminhamentos,
):
    inserir_registro(
        "atendimentos",
        [
            "estudante_id", "data_atendimento", "objetivo", "atividade", "resposta_estudante",
            "avancos", "dificuldades", "evolucao", "qtd_atividades", "nivel_resposta",
            "nivel_avanco", "nivel_dificuldade", "nivel_engajamento", "nivel_evolucao",
            "encaminhamentos",
        ],
        [
            estudante_id, data_atendimento, objetivo, atividade, resposta_estudante,
            avancos, dificuldades, evolucao, qtd_atividades, nivel_resposta,
            nivel_avanco, nivel_dificuldade, nivel_engajamento, nivel_evolucao,
            encaminhamentos,
        ],
    )


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
    excluir_registro("atendimentos", atendimento_id)


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

    hoje = datetime.now().date()
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
    return f"""
PLANO AEE / PAEE - INCLUISRM

Código interno do estudante: {estudante[1]}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Perfil educacional: {estudante[4] or 'Não informado.'}
Data do registro: {p[1]}

1. Objetivos gerais
{p[2] or 'Não informado.'}

2. Objetivos específicos
{p[3] or 'Não informado.'}

3. Habilidades prioritárias
{p[4] or 'Não informado.'}

4. Recursos de acessibilidade
{p[5] or 'Não informado.'}

5. Estratégias pedagógicas
{p[6] or 'Não informado.'}

6. Organização do atendimento
{p[7] or 'Não informado.'}

7. Parcerias
{p[8] or 'Não informado.'}

8. Avaliação e acompanhamento
{p[9] or 'Não informado.'}

9. Observações
{p[10] or 'Não informado.'}

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
        "estudo": ("Estudo_Caso", "ESTUDO DE CASO"),
        "plano": ("Plano_AEE_PAEE", "PLANO AEE / PAEE"),
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
    elementos.append(Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} pelo INCLUISRM.", rodape_style))
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


def gerar_novo_estudo_caso_com_ia(estudante, estudo_anterior=None, avaliacao=None, entrevista=None, atendimentos=None, ano_novo=""):
    """Gera análise comparativa e proposta de novo Estudo de Caso com IA.
    A resposta é apoio pedagógico: não substitui a avaliação do professor do AEE.
    """
    client = obter_cliente_openai()
    if client is None:
        return "", "IA não configurada. Configure OPENAI_API_KEY para usar esta função."

    texto_estudo_anterior = texto_estudo_caso(estudante, estudo_anterior) if estudo_anterior else "Nenhum estudo anterior selecionado."
    texto_avaliacao = str(avaliacao or "Nenhuma avaliação pedagógica atual localizada.")
    texto_entrevista = str(entrevista or "Nenhuma entrevista com família localizada.")
    texto_atendimentos = "\n".join([str(a) for a in (atendimentos or [])[:12]]) or "Nenhum atendimento registrado."

    prompt = f"""
Você é um especialista em Atendimento Educacional Especializado (AEE) e em elaboração de Estudo de Caso.
Analise os registros abaixo e produza uma resposta institucional, pedagógica e objetiva para apoiar o professor do AEE.

REGRAS IMPORTANTES:
- Não invente dados pessoais nem diagnósticos.
- Não substitua a decisão pedagógica do professor.
- Trabalhe apenas com os dados fornecidos.
- Use linguagem adequada para documento escolar.
- Aponte avanços, permanências, novas barreiras, potencialidades e sugestões pedagógicas.
- Sugira atividades pedagógicas, recursos acessíveis, recursos maker/3D quando coerente, atividades plugadas e desplugadas.
- Evite termos clínicos conclusivos; mantenha foco educacional.

ESTUDANTE:
Código interno: {estudante[1]}
Ano/Série atual: {estudante[2]}
Turma: {estudante[3]}
Perfil educacional: {estudante[4]}
Ano letivo do novo estudo: {ano_novo}

ESTUDO DE CASO ANTERIOR:
{texto_estudo_anterior}

AVALIAÇÃO PEDAGÓGICA ATUAL:
{texto_avaliacao}

ENTREVISTA COM A FAMÍLIA:
{texto_entrevista}

ATENDIMENTOS REGISTRADOS:
{texto_atendimentos}

Responda exatamente com duas seções:

[ANALISE_COMPARATIVA]
Texto comparando o estudo anterior com os registros atuais, destacando evolução, permanências, barreiras e pontos de atenção.

[SUGESTAO_NOVO_ESTUDO]
Proposta inicial de novo Estudo de Caso, com contextualização, potencialidades, dificuldades/barreiras, estratégias pedagógicas, intervenções/encaminhamentos, avaliação e considerações finais.
"""
    try:
        resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
        texto = resposta.output_text or ""
        analise = texto
        sugestao = texto
        if "[SUGESTAO_NOVO_ESTUDO]" in texto:
            partes = texto.split("[SUGESTAO_NOVO_ESTUDO]", 1)
            analise = partes[0].replace("[ANALISE_COMPARATIVA]", "").strip()
            sugestao = partes[1].strip()
        return analise.strip(), sugestao.strip()
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
Elabore uma sugestão de Plano AEE/PAEE com linguagem formal, técnica, objetiva e pedagógica, cruzando as informações do cadastro, entrevista com a família, avaliação pedagógica, estudo de caso GRE, histórico de atendimentos e os trechos recuperados das bases científica e pedagógica.

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
            ["data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias", "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias", "avaliacao_acompanhamento", "observacoes"],
            estudante[0],
        )

    dados_estudo = dict(zip(CAMPOS_ESTUDO_CASO, estudo or []))
    def e(campo):
        valor = dados_estudo.get(campo)
        return valor if valor not in (None, "") else "Não informado."

    dados_plano = {}
    if plano:
        chaves = ["data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias", "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias", "avaliacao_acompanhamento", "observacoes"]
        dados_plano = dict(zip(chaves, plano))

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
Metodologia / estratégias:
{p('estrategias')}

Organização do atendimento:
{p('organizacao_atendimento')}

5. Ações no âmbito da escola / gestão / educador de apoio:
( ) Implemento de tecnologia assistiva
( ) Solicitação de Profissional de Apoio
( ) Solicitação de Professor do AEE
( ) Formação continuada com temática da educação inclusiva
( ) Parcerias com saúde, UBS, USF, Conselho Tutelar, CREAS e CRAS
( ) Articulação sobre PDDE equidade
( ) Articulação de horários entre professor AEE, sala comum e apoio
( ) Solicitação de transporte escolar inclusivo
( ) Outros: ______________________________________________________________

6. Barreiras identificadas na comunidade escolar:
( ) Barreiras atitudinais
( ) Barreiras arquitetônicas
( ) Barreiras comunicacionais
( ) Barreiras curriculares
( ) Outros: ______________________________________________________________

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
        ["data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias", "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias", "avaliacao_acompanhamento", "observacoes"],
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
    st.markdown('<div class="subtitulo">📊 Painel inicial</div>', unsafe_allow_html=True)

# if USAR_POSTGRES:
#     st.success("🟢 Banco conectado: PostgreSQL (Render)")
# else:
#     st.warning("🟡 Banco conectado: SQLite local")

    with st.spinner("Carregando painel..."):
        estudantes = listar_estudantes()
        total_estudantes = len(estudantes)
        total_avaliacoes = contar_registros_tabela("avaliacoes")
        total_atendimentos = contar_registros_tabela("atendimentos")
        total_agenda = contar_registros_tabela("agenda")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Estudantes", total_estudantes)
    col2.metric("Avaliações", total_avaliacoes)
    col3.metric("Atendimentos", total_atendimentos)
    col4.metric("Agendamentos", total_agenda)

    st.markdown("---")

    col_esq, col_dir = st.columns([1.25, 1])

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
                        for e in estudantes
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Nenhum estudante cadastrado ainda.")

    with col_dir:
        with st.container(border=True):
            st.markdown("### 🧭 Fluxo sugerido")
            st.markdown(
                """
                1. Cadastre o estudante com código interno.
                2. Registre entrevista, avaliação e estudo de caso.
                3. Crie o Plano AEE - IA.
                4. Organize a agenda semanal.
                5. Lance os atendimentos e acompanhe os gráficos.
                6. Gere os relatórios GRE para impressão e pasta física.
                """
            )
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
                ano_padrao_entrevista = str(datetime.now().year)
                anos_opcoes_entrevista = [str(a) for a in range(2020, datetime.now().year + 4)]
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

        anos_opcoes = [str(a) for a in range(2024, datetime.now().year + 4)]
        ano_padrao = str(datetime.now().year)
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

        with st.container(border=True):
            st.markdown("### Novo Estudo de Caso - Campos obrigatórios GRE")
            st.info("Agora o Estudo de Caso pode ser registrado por ano letivo. Você pode lançar estudos anteriores como histórico e gerar um novo estudo com apoio da IA, comparando registros antigos com dados atuais.")

            with st.expander("🤖 Criar novo estudo de caso com apoio da IA", expanded=False):
                if estudos_anteriores:
                    opcoes_estudos = {e[0]: f"ID {e[0]} | Ano: {e[2] or 'não informado'} | Tipo: {e[3] or 'não informado'} | Registro: {e[1]}" for e in estudos_anteriores}
                    estudo_base_id_ia = st.selectbox(
                        "Selecione o estudo anterior para comparação",
                        list(opcoes_estudos.keys()),
                        format_func=lambda x: opcoes_estudos[x],
                        key=f"estudo_base_ia_{estudante_id}",
                    )
                    ano_novo_ia = st.text_input("Ano letivo do novo estudo", value=str(datetime.now().year), key=f"ano_novo_ia_{estudante_id}")
                    st.caption("A IA cruzará o estudo anterior com avaliação pedagógica, entrevista familiar e atendimentos registrados.")
                    if st.button("Gerar análise comparativa e sugestão de novo estudo", key=f"gerar_estudo_ia_{estudante_id}"):
                        estudo_base = next((e for e in estudos_anteriores if e[0] == estudo_base_id_ia), None)
                        avaliacao_atual = ultima_avaliacao(estudante_id)
                        entrevista_atual = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)
                        atendimentos_atuais = listar_atendimentos(estudante_id)
                        analise_ia, sugestao_ia = gerar_novo_estudo_caso_com_ia(
                            estudante, estudo_base, avaliacao_atual, entrevista_atual, atendimentos_atuais, ano_novo_ia
                        )
                        st.session_state[f"analise_estudo_ia_{estudante_id}"] = analise_ia
                        st.session_state[f"sugestao_estudo_ia_{estudante_id}"] = sugestao_ia
                        st.session_state[f"ano_estudo_ia_{estudante_id}"] = ano_novo_ia
                        st.session_state[f"estudo_anterior_id_{estudante_id}"] = estudo_base_id_ia
                        st.success("Sugestão gerada. Revise e ajuste os campos antes de salvar.")
                    if st.session_state.get(f"sugestao_estudo_ia_{estudante_id}"):
                        st.markdown("#### Análise comparativa IA")
                        st.text_area("Resultado da análise comparativa", value=st.session_state.get(f"analise_estudo_ia_{estudante_id}", ""), height=180, key=f"preview_analise_{estudante_id}")
                        st.markdown("#### Sugestão de novo estudo")
                        st.text_area("Sugestão gerada", value=st.session_state.get(f"sugestao_estudo_ia_{estudante_id}", ""), height=260, key=f"preview_sugestao_{estudante_id}")
                else:
                    st.info("Ainda não há estudo anterior registrado para este estudante. Primeiro cadastre o estudo histórico ou atual.")

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
                        ano_letivo = st.text_input("Ano letivo do estudo de caso", value=st.session_state.get(f"ano_estudo_ia_{estudante_id}", str(datetime.now().year)))
                    with col_tipo_hist:
                        tipo_registro = st.selectbox(
                            "Tipo de registro",
                            ["Estudo de caso atual", "Registro histórico", "Novo estudo com base em estudo anterior"],
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

                    cid = st.text_input("CID, se houver", placeholder="Ex.: F84.0. Não armazene laudos ou documentos sensíveis aqui.")
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
                        placeholder="Descreva situação inicial, estratégias já utilizadas e progressos alcançados em turmas comuns e/ou AEE anterior.",
                        height=180,
                    )
                    motivo_encaminhamento_aee = st.text_area("Motivo pelo qual foi encaminhado ao AEE", height=120)

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
                        placeholder="Ex.: acompanhamento terapêutico, recomendações pedagógicas, cuidados no ambiente escolar.",
                        height=140,
                    )

                with aba3:
                    st.markdown("#### Habilidades e indicadores")
                    habilidades_observadas = st.multiselect("Habilidades observadas e desenvolvidas", OPCOES_HABILIDADES_PEDAGOGICAS)
                    habilidades_a_desenvolver = st.multiselect("Habilidades que precisam ser desenvolvidas", OPCOES_HABILIDADES_PEDAGOGICAS)
                    indicadores_altas_habilidades = st.multiselect("Indicadores de altas habilidades/superdotação", OPCOES_INDICADORES_AHSD)
                    recursos_surdez = st.multiselect("Caso seja pessoa surda, marque recursos utilizados", OPCOES_RECURSOS_SURDEZ, default=["Não se aplica"])
                    observacoes_surdez = st.text_area(
                        "Observações sobre aparelho auditivo, implante coclear, Libras, uso diário, efetividade ou incômodos",
                        height=120,
                    )

                with aba4:
                    st.markdown("#### Síntese pedagógica")
                    contextualizacao = st.text_area("Contextualização", value=sugestao_novo_estudo_ia if tipo_registro == "Novo estudo com base em estudo anterior" else "", height=130)
                    potencialidades = st.text_area("Potencialidades", height=100)
                    dificuldades = st.text_area("Dificuldades/barreiras observadas", height=100)
                    estrategias = st.text_area("Estratégias pedagógicas", height=120)
                    intervencoes = st.text_area("Intervenções / encaminhamentos sugeridos", height=120)
                    avaliacao_estudo = st.text_area("Avaliação", height=100)
                    consideracoes = st.text_area("Considerações finais", height=100)

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
                        ", ".join(habilidades_observadas),
                        ", ".join(habilidades_a_desenvolver),
                        estrategias,
                        intervencoes,
                        avaliacao_estudo,
                        consideracoes,
                        etapa_modalidade,
                        ano_etapa,
                        laudo,
                        deficiencia,
                        cid,
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
                        ", ".join(habilidades_observadas),
                        ", ".join(habilidades_a_desenvolver),
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
    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox("Selecione o estudante", ids, format_func=lambda x: mapa[x], key="plano_estudante")
        estudante = buscar_estudante(estudante_id)

        with st.container(border=True):
            st.markdown("### 🤖 Gerar sugestão inteligente do Plano AEE")
            st.caption(
                "A IA cruza cadastro, entrevista com a família, avaliação pedagógica, estudo de caso GRE, "
                "atendimentos e as bases científica e pedagógica. Para segurança pedagógica, o sistema só gera "
                "Plano AEE completo quando houver dados mínimos registrados."
            )

            col_ia1, col_ia2 = st.columns([1, 1])
            with col_ia1:
                gerar_ai = st.button("Gerar sugestão AEE IA", key=f"btn_aee_ia_{estudante_id}")
            with col_ia2:
                limpar_ai = st.button("Limpar sugestão", key=f"btn_limpar_aee_ia_{estudante_id}")

            if limpar_ai:
                st.session_state.pop(f"paee_ia_texto_{estudante_id}", None)
                st.session_state.pop(f"paee_modo_{estudante_id}", None)
                st.session_state.pop(f"termos_3d_{estudante_id}", None)
                st.rerun()

            if gerar_ai:
                avaliacao_ia = ultima_avaliacao(estudante_id)
                entrevista_ia = ultima_linha("entrevistas_familia", CAMPOS_ENTREVISTA_FAMILIA, estudante_id)
                estudo_ia = ultima_linha("estudos_caso", CAMPOS_ESTUDO_CASO, estudante_id)

                pendencias = []
                if not entrevista_ia:
                    pendencias.append("Entrevista com a família")
                if not avaliacao_ia:
                    pendencias.append("Avaliação pedagógica")
                if not estudo_ia:
                    pendencias.append("Estudo de caso")

                if pendencias:
                    st.warning("⚠️ Ainda não há dados suficientes para gerar um Plano AEE personalizado.")
                    st.info(
                        "Será gerado apenas um roteiro diagnóstico inicial, sem sugestões de recursos específicos, "
                        "tecnologias, atividades plugadas, atividades desplugadas ou materiais maker."
                    )

                    texto_pendencias = "\n".join([f"- {p}" for p in pendencias])
                    st.session_state[f"paee_modo_{estudante_id}"] = "roteiro"
                    st.session_state.pop(f"termos_3d_{estudante_id}", None)
                    st.session_state[f"paee_ia_texto_{estudante_id}"] = f"""
ROTEIRO DIAGNÓSTICO INICIAL - INCLUISRM

Código interno do estudante: {estudante[1]}

O sistema identificou que ainda faltam informações essenciais para a elaboração de um Plano AEE personalizado.

Pendências identificadas:
{texto_pendencias}

ORIENTAÇÃO PEDAGÓGICA:
Antes de gerar sugestões individualizadas de recursos, tecnologias assistivas, atividades plugadas, atividades desplugadas, materiais maker ou objetos 3D, recomenda-se completar o fluxo pedagógico inicial:

1. Realizar a entrevista com a família.
2. Registrar a avaliação pedagógica.
3. Elaborar o estudo de caso.
4. Somente após essas etapas, retornar ao módulo Plano AEE - IA para gerar o plano completo.

O QUE O SISTEMA NÃO IRÁ FAZER NESTA ETAPA:
- Não irá indicar materiais específicos.
- Não irá sugerir tecnologias assistivas individualizadas.
- Não irá sugerir atividades plugadas ou desplugadas personalizadas.
- Não irá recomendar objetos 3D ou recursos maker específicos.
- Não irá presumir barreiras, potencialidades ou necessidades sem registros.

JUSTIFICATIVA:
Sem entrevista, avaliação pedagógica e estudo de caso, qualquer recomendação individualizada poderia ser inadequada, genérica ou sem base suficiente nas necessidades reais do estudante.

ENCAMINHAMENTO:
Preencher as informações pendentes no sistema e retornar ao módulo Plano AEE - IA para geração do Plano AEE completo.
""".strip()

                else:
                    st.success("✅ Dados mínimos encontrados. Gerando Plano AEE personalizado com IA.")
                    st.session_state[f"paee_modo_{estudante_id}"] = "completo"

                    with st.spinner("Gerando Plano AEE com Inteligência e consultando as bases de conhecimento..."):
                        st.session_state[f"paee_ia_texto_{estudante_id}"] = gerar_paee_com_ia(
                            estudante,
                            avaliacao_ia,
                            entrevista_ia,
                            estudo_ia,
                        )

            if f"paee_ia_texto_{estudante_id}" in st.session_state:
                modo_paee = st.session_state.get(f"paee_modo_{estudante_id}", "completo")
                titulo_area = "Roteiro diagnóstico inicial" if modo_paee == "roteiro" else "Plano AEE gerado pela IA"

                texto_ia = st.text_area(
                    titulo_area,
                    st.session_state[f"paee_ia_texto_{estudante_id}"],
                    height=520,
                    key=f"texto_paee_ia_{estudante_id}",
                )

                col_exp1, col_exp2 = st.columns([1, 1])
                with col_exp1:
                    export_buttons(texto_ia, f"PAEE_AEE_IA_{estudante[1]}", tipo_pdf="plano")
                with col_exp2:
                    if st.button("Salvar documento gerado no histórico", key=f"salvar_paee_ia_{estudante_id}"):
                        inserir_registro(
                            "paees",
                            ["estudante_id", "data_geracao", "conteudo"],
                            [estudante_id, hoje_str(), texto_ia],
                        )
                        st.success("Documento salvo no histórico de PAEE.")
                        st.rerun()

                if modo_paee == "roteiro":
                    st.info(
                        "🔒 A busca de modelos 3D e sugestões de recursos maker ficará disponível somente após "
                        "a geração do Plano AEE completo, com entrevista, avaliação pedagógica e estudo de caso registrados."
                    )
                else:
                    st.markdown("---")
                    st.markdown("### 🧩 Busca de modelos 3D para recursos pedagógicos")
                    st.write(
                        "A IA analisa o Plano AEE gerado, sugere 5 objetos 3D pedagógicos e também permite busca manual em bancos de modelos."
                    )

                    col_auto, col_manual = st.columns(2)

                    with col_auto:
                        st.markdown("#### 🤖 Sugestões automáticas da IA")

                        if st.button("Gerar 5 sugestões de objetos 3D", key=f"btn_3d_auto_{estudante_id}"):
                            with st.spinner("Analisando o Plano AEE e gerando sugestões de objetos 3D..."):
                                termos_3d = gerar_termos_3d_com_ia(texto_ia)
                                st.session_state[f"termos_3d_{estudante_id}"] = termos_3d

                        if f"termos_3d_{estudante_id}" in st.session_state:
                            for termo in st.session_state[f"termos_3d_{estudante_id}"]:
                                st.markdown(f"##### 🔎 {termo}")

                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    st.link_button("MakerWorld", link_busca_makerworld(termo))
                                with c2:
                                    st.link_button("Printables", link_busca_printables(termo))
                                with c3:
                                    st.link_button("Thingiverse", link_busca_thingiverse(termo))

                    with col_manual:
                        st.markdown("#### 🔍 Busca manual de modelos 3D")

                        termo_manual = st.text_input(
                            "Digite o termo para buscar",
                            placeholder="Ex: braille alphabet, tactile map, sensory toy...",
                            key=f"busca_manual_3d_{estudante_id}",
                        )

                        if termo_manual.strip():
                            st.markdown(f"##### Resultado para: {termo_manual}")

                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.link_button("Buscar no MakerWorld", link_busca_makerworld(termo_manual))
                            with c2:
                                st.link_button("Buscar no Printables", link_busca_printables(termo_manual))
                            with c3:
                                st.link_button("Buscar no Thingiverse", link_busca_thingiverse(termo_manual))
        with st.container(border=True):
            st.markdown("### 📚 Base de Conhecimento IA")
            st.caption("Use esta seção para conferir e indexar os PDFs colocados nas pastas base_conhecimento/cientifica e base_conhecimento/pedagogica.")

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

                if st.button("Indexar Base Científica", key="indexar_base_cientifica"):
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

                if st.button("Indexar Base Pedagógica", key="indexar_base_pedagogica"):
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
                key="pergunta_base_conhecimento_ia",
            )
            bases_escolhidas = st.multiselect(
                "Bases para consulta",
                ["cientifica", "pedagogica"],
                default=["cientifica", "pedagogica"],
                key="bases_consulta_manual",
            )
            if st.button("Consultar bases", key="consultar_bases_ia"):
                if not pergunta_base.strip():
                    st.warning("Digite uma pergunta primeiro.")
                else:
                    with st.spinner("Buscando trechos nas bases..."):
                        resultados = buscar_na_base_conhecimento(pergunta_base, bases=bases_escolhidas, limite=6)
                        contexto = montar_contexto_base(resultados)
                        st.session_state["consulta_base_resultado"] = contexto

            if "consulta_base_resultado" in st.session_state:
                st.text_area("Trechos encontrados", st.session_state["consulta_base_resultado"], height=320)

        with st.container(border=True):
            st.markdown("### Novo plano manual")
            with st.form("form_plano"):
                objetivos_gerais = st.text_area("Objetivos gerais")
                objetivos_especificos = st.text_area("Objetivos específicos")
                habilidades = st.text_area("Habilidades prioritárias")
                recursos = st.text_area("Recursos de acessibilidade")
                estrategias = st.text_area("Estratégias pedagógicas")
                organizacao = st.text_area("Organização do atendimento")
                parcerias = st.text_area("Parcerias")
                avaliacao = st.text_area("Avaliação e acompanhamento")
                observacoes = st.text_area("Observações")
                if st.form_submit_button("Salvar Plano AEE / PAEE"):
                    inserir_registro(
                        "planos_aee",
                        ["estudante_id", "data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias", "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias", "avaliacao_acompanhamento", "observacoes"],
                        [estudante_id, hoje_str(), objetivos_gerais, objetivos_especificos, habilidades, recursos, estrategias, organizacao, parcerias, avaliacao, observacoes],
                    )
                    st.success("Plano salvo.")
                    st.rerun()

        planos = listar_por_estudante(
            "planos_aee",
            ["data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias", "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias", "avaliacao_acompanhamento", "observacoes"],
            estudante_id,
        )
        with st.container(border=True):
            st.markdown("### Histórico de planos manuais")
            if planos:
                for p in planos:
                    with st.expander(f"Plano em {p[1]}"):
                        texto = texto_plano_aee(estudante, p)
                        st.text(texto)
                        export_buttons(texto, f"Plano_AEE_PAEE_{estudante[1]}_{p[0]}", tipo_pdf="plano")
                        if st.button("Excluir plano", key=f"exc_plano_{p[0]}"):
                            excluir_registro("planos_aee", p[0])
                            st.success("Plano excluído.")
                            st.rerun()
            else:
                st.info("Nenhum plano manual registrado.")

        paees_ia = listar_por_estudante("paees", ["data_geracao", "conteudo"], estudante_id)
        with st.container(border=True):
            st.markdown("### Histórico de sugestões AEE IA")
            if paees_ia:
                for paee in paees_ia:
                    with st.expander(f"Sugestão AEE IA em {paee[1]}"):
                        texto_paee = paee[2] or ""
                        st.text_area("Conteúdo salvo", texto_paee, height=420, key=f"paee_ia_hist_{paee[0]}")
                        export_buttons(texto_paee, f"PAEE_AEE_IA_{estudante[1]}_{paee[0]}", tipo_pdf="plano")
                        if st.button("Excluir sugestão AEE IA", key=f"exc_paee_ia_{paee[0]}"):
                            excluir_registro("paees", paee[0])
                            st.success("Sugestão AEE IA excluída.")
                            st.rerun()
            else:
                st.info("Nenhuma sugestão AEE IA salva.")


# ======================================================
# ATENDIMENTOS
# ======================================================
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
                if st.form_submit_button("Salvar atendimento"):
                    salvar_atendimento(
                        estudante_id, data_atendimento.strftime("%d/%m/%Y"), objetivo, atividade, resposta,
                        avancos, dificuldades, evolucao, 1, nivel_resposta, nivel_avanco,
                        nivel_dificuldade, nivel_engajamento, indice, encaminhamentos,
                    )
                    st.success("Atendimento registrado.")
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
            mes_qs = datetime.now().strftime("%m")
            ano_qs = datetime.now().strftime("%Y")
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
                    data_inicio_qs = st.date_input("Data inicial", value=datetime.now().date().replace(day=1), key="qs_inicio")
                with col_periodo2:
                    data_fim_qs = st.date_input("Data final", value=datetime.now().date(), key="qs_fim")
                with col_periodo3:
                    mes_qs = st.text_input("Mês", value=datetime.now().strftime("%m"), key="qs_mes")
                with col_periodo4:
                    ano_qs = st.text_input("Ano", value=datetime.now().strftime("%Y"), key="qs_ano")

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
                        ["data_registro", "objetivos_gerais", "objetivos_especificos", "habilidades_prioritarias", "recursos_acessibilidade", "estrategias", "organizacao_atendimento", "parcerias", "avaliacao_acompanhamento", "observacoes"],
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
            f"backup_completo_incluisrm_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            "application/json",
        )
