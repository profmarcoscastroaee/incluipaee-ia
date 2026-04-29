import os
import requests
import sqlite3
from datetime import datetime
from pathlib import Path
from html import escape

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="IncluiPAEE IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Fundo geral */
.stApp {
    background-color: #f5f7fb;
}

/* Espaçamento geral */
.block-container {
    padding-top: 3rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* Corrige topo e centraliza melhor conteúdo */
main > div {
    padding-top: 1rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0f172a;
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Títulos */
.titulo {
    font-size: 30px;
    font-weight: 800;
    color: #0f172a;
    margin-bottom: 0px;
}

.subtitulo {
    font-size: 19px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
}

.descricao {
    color: #64748b;
    font-size: 15px;
    margin-bottom: 18px;
}

/* Botões */
.stButton > button,
.stDownloadButton > button {
    border-radius: 10px;
    font-weight: 600;
}

/* Inputs */
div[data-baseweb="input"],
div[data-baseweb="select"] {
    border-radius: 10px;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Métricas */
[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e5e7eb;
    padding: 16px;
    border-radius: 14px;
}

/* Linha divisória suave */
hr {
    margin-top: 0.8rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


DB_PATH = Path("inclui_paee.db")


# ======================================================
# CONFIGURAÇÃO DA API KEY
# ======================================================
def obter_api_key():
    """Busca a chave da OpenAI no ambiente local ou nos Secrets do Streamlit Cloud."""
    try:
        return os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return os.getenv("OPENAI_API_KEY")


# ======================================================
# BANCO DE DADOS
# ======================================================
def conectar():
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS estudantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            ano_serie TEXT,
            turma TEXT,
            perfil TEXT,
            observacoes TEXT,
            criado_em TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS paees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    cursor.execute("PRAGMA table_info(atendimentos)")
    colunas = [col[1] for col in cursor.fetchall()]
    if "evolucao" not in colunas:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN evolucao TEXT")
    if "qtd_atividades" not in colunas:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN qtd_atividades INTEGER DEFAULT 1")
    if "nivel_resposta" not in colunas:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN nivel_resposta INTEGER DEFAULT 5")
    if "nivel_avanco" not in colunas:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN nivel_avanco INTEGER DEFAULT 5")
    if "nivel_dificuldade" not in colunas:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN nivel_dificuldade INTEGER DEFAULT 5")
    if "nivel_engajamento" not in colunas:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN nivel_engajamento INTEGER DEFAULT 5")
    if "nivel_evolucao" not in colunas:
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN nivel_evolucao REAL DEFAULT 5")

    conn.commit()
    conn.close()


def cadastrar_estudante(codigo, ano_serie, turma, perfil, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO estudantes (codigo, ano_serie, turma, perfil, observacoes, criado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            codigo,
            ano_serie,
            turma,
            perfil,
            observacoes,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
        ),
    )
    conn.commit()
    conn.close()


def listar_estudantes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, codigo, ano_serie, turma, perfil, observacoes
        FROM estudantes
        ORDER BY codigo
        """
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def buscar_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, codigo, ano_serie, turma, perfil, observacoes
        FROM estudantes
        WHERE id = ?
        """,
        (estudante_id,),
    )
    dado = cursor.fetchone()
    conn.close()
    return dado


def atualizar_estudante(estudante_id, codigo, ano_serie, turma, perfil, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE estudantes
        SET codigo=?, ano_serie=?, turma=?, perfil=?, observacoes=?
        WHERE id=?
        """,
        (codigo, ano_serie, turma, perfil, observacoes, estudante_id),
    )
    conn.commit()
    conn.close()


def excluir_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM atendimentos WHERE estudante_id=?", (estudante_id,))
    cursor.execute("DELETE FROM relatorios WHERE estudante_id=?", (estudante_id,))
    cursor.execute("DELETE FROM paees WHERE estudante_id=?", (estudante_id,))
    cursor.execute("DELETE FROM avaliacoes WHERE estudante_id=?", (estudante_id,))
    cursor.execute("DELETE FROM estudantes WHERE id=?", (estudante_id,))
    conn.commit()
    conn.close()


def salvar_avaliacao(
    estudante_id,
    barreiras,
    potencialidades,
    comunicacao,
    interacao,
    autonomia,
    aprendizagem,
    resumo_laudo,
):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO avaliacoes (
            estudante_id, data_registro, barreiras, potencialidades, comunicacao,
            interacao, autonomia, aprendizagem, resumo_laudo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            estudante_id,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            barreiras,
            potencialidades,
            comunicacao,
            interacao,
            autonomia,
            aprendizagem,
            resumo_laudo,
        ),
    )
    conn.commit()
    conn.close()


def ultima_avaliacao(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT data_registro, barreiras, potencialidades, comunicacao, interacao,
               autonomia, aprendizagem, resumo_laudo
        FROM avaliacoes
        WHERE estudante_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (estudante_id,),
    )
    dado = cursor.fetchone()
    conn.close()
    return dado


def listar_avaliacoes(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, data_registro, barreiras, potencialidades, comunicacao, interacao,
               autonomia, aprendizagem, resumo_laudo
        FROM avaliacoes
        WHERE estudante_id = ?
        ORDER BY id DESC
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def salvar_paee(estudante_id, conteudo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO paees (estudante_id, data_geracao, conteudo) VALUES (?, ?, ?)",
        (estudante_id, datetime.now().strftime("%d/%m/%Y %H:%M"), conteudo),
    )
    conn.commit()
    conn.close()


def salvar_relatorio(estudante_id, titulo, conteudo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO relatorios (estudante_id, data_geracao, titulo, conteudo)
        VALUES (?, ?, ?, ?)
        """,
        (
            estudante_id,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            titulo,
            conteudo,
        ),
    )
    relatorio_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return relatorio_id


def listar_relatorios(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, data_geracao, titulo, conteudo
        FROM relatorios
        WHERE estudante_id = ?
        ORDER BY id DESC
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


def atualizar_relatorio(relatorio_id, titulo, conteudo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE relatorios
        SET titulo = ?, conteudo = ?
        WHERE id = ?
        """,
        (titulo, conteudo, relatorio_id),
    )
    conn.commit()
    conn.close()


def excluir_relatorio(relatorio_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM relatorios WHERE id = ?", (relatorio_id,))
    conn.commit()
    conn.close()


def salvar_atendimento(
    estudante_id,
    data_atendimento,
    objetivo,
    atividade,
    resposta_estudante,
    avancos,
    dificuldades,
    evolucao,
    qtd_atividades,
    nivel_resposta,
    nivel_avanco,
    nivel_dificuldade,
    nivel_engajamento,
    nivel_evolucao,
    encaminhamentos,
):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO atendimentos (
            estudante_id, data_atendimento, objetivo, atividade,
            resposta_estudante, avancos, dificuldades, evolucao,
            qtd_atividades, nivel_resposta, nivel_avanco, nivel_dificuldade,
            nivel_engajamento, nivel_evolucao, encaminhamentos
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            estudante_id,
            data_atendimento,
            objetivo,
            atividade,
            resposta_estudante,
            avancos,
            dificuldades,
            evolucao,
            qtd_atividades,
            nivel_resposta,
            nivel_avanco,
            nivel_dificuldade,
            nivel_engajamento,
            nivel_evolucao,
            encaminhamentos,
        ),
    )
    conn.commit()
    conn.close()




def atualizar_atendimento(
    atendimento_id,
    data_atendimento,
    objetivo,
    atividade,
    resposta_estudante,
    avancos,
    dificuldades,
    evolucao,
    qtd_atividades,
    nivel_resposta,
    nivel_avanco,
    nivel_dificuldade,
    nivel_engajamento,
    nivel_evolucao,
    encaminhamentos,
):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE atendimentos
        SET data_atendimento = ?,
            objetivo = ?,
            atividade = ?,
            resposta_estudante = ?,
            avancos = ?,
            dificuldades = ?,
            evolucao = ?,
            qtd_atividades = ?,
            nivel_resposta = ?,
            nivel_avanco = ?,
            nivel_dificuldade = ?,
            nivel_engajamento = ?,
            nivel_evolucao = ?,
            encaminhamentos = ?
        WHERE id = ?
        """,
        (
            data_atendimento, objetivo, atividade, resposta_estudante, avancos, dificuldades, evolucao,
            qtd_atividades, nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento,
            nivel_evolucao, encaminhamentos, atendimento_id,
        ),
    )
    conn.commit()
    conn.close()


def excluir_atendimento(atendimento_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM atendimentos WHERE id = ?", (atendimento_id,))
    conn.commit()
    conn.close()


def data_para_date(data_texto):
    try:
        return datetime.strptime(data_texto, "%d/%m/%Y").date()
    except Exception:
        return datetime.now().date()

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




def calcular_nivel_evolucao(texto_evolucao, avancos, dificuldades):
    """Compatibilidade com atendimentos antigos sem escala numérica."""
    texto_positivo = f"{texto_evolucao or ''} {avancos or ''}".lower()
    texto_dificuldades = f"{dificuldades or ''}".lower()
    pontos = 0

    palavras_positivas = [
        "melhorou", "avançou", "evoluiu", "participou", "realizou",
        "conseguiu", "interagiu", "compreendeu", "autonomia",
        "progresso", "positivo", "bom desempenho", "maior interesse",
        "engajamento", "atenção", "comunicação", "iniciativa",
        "independência", "colaborou", "respondeu bem"
    ]

    palavras_dificuldade = [
        "dificuldade", "não conseguiu", "resistência", "recusou",
        "limitação", "necessita apoio", "necessitou apoio", "dependência",
        "desatenção", "não realizou", "não participou", "crise",
        "agitação", "dispersão", "baixa interação"
    ]

    for palavra in palavras_positivas:
        if palavra in texto_positivo:
            pontos += 1

    for palavra in palavras_dificuldade:
        if palavra in texto_dificuldades:
            pontos -= 1

    if pontos <= 0:
        return 1
    elif pontos == 1:
        return 2
    elif pontos == 2:
        return 3
    elif pontos == 3:
        return 4
    else:
        return 5


def limitar_escala(valor, padrao=5):
    try:
        valor = int(valor)
    except Exception:
        valor = padrao
    return max(1, min(10, valor))


def calcular_indice_geral(nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento):
    """Calcula índice geral em escala 1 a 10. A dificuldade entra invertida."""
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
    elif indice <= 6:
        return "Evolução parcial / acompanhamento em desenvolvimento"
    elif indice <= 8:
        return "Boa evolução / resposta positiva"
    return "Evolução elevada / maior autonomia e participação"


def montar_dataframe_evolucao(atendimentos):
    dados_grafico = []
    for atendimento in reversed(atendimentos):
        data_atendimento = atendimento[0]
        avancos = atendimento[4]
        dificuldades = atendimento[5]
        evolucao = atendimento[6]
        qtd_atividades = atendimento[7] if len(atendimento) > 7 else 1
        nivel_resposta = atendimento[8] if len(atendimento) > 8 else None
        nivel_avanco = atendimento[9] if len(atendimento) > 9 else None
        nivel_dificuldade = atendimento[10] if len(atendimento) > 10 else None
        nivel_engajamento = atendimento[11] if len(atendimento) > 11 else None
        nivel_evolucao_antigo = atendimento[12] if len(atendimento) > 12 else None

        base_antiga = nivel_evolucao_antigo if nivel_evolucao_antigo is not None else calcular_nivel_evolucao(evolucao, avancos, dificuldades)
        nivel_resposta = nivel_resposta if nivel_resposta is not None else base_antiga
        nivel_avanco = nivel_avanco if nivel_avanco is not None else base_antiga
        nivel_dificuldade = nivel_dificuldade if nivel_dificuldade is not None else 5
        nivel_engajamento = nivel_engajamento if nivel_engajamento is not None else base_antiga

        nivel_resposta = limitar_escala(nivel_resposta)
        nivel_avanco = limitar_escala(nivel_avanco)
        nivel_dificuldade = limitar_escala(nivel_dificuldade)
        nivel_engajamento = limitar_escala(nivel_engajamento)
        indice_geral = calcular_indice_geral(nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento)

        try:
            qtd_atividades = int(qtd_atividades)
        except Exception:
            qtd_atividades = 1
        try:
            data_ordenacao = datetime.strptime(data_atendimento, "%d/%m/%Y")
        except Exception:
            data_ordenacao = None

        dados_grafico.append({
            "Data": data_atendimento,
            "Data ordenação": data_ordenacao,
            "Quantidade de atividades": qtd_atividades,
            "Resposta do estudante": nivel_resposta,
            "Avanço pedagógico": nivel_avanco,
            "Nível de dificuldade": nivel_dificuldade,
            "Dificuldade invertida": 11 - nivel_dificuldade,
            "Engajamento": nivel_engajamento,
            "Índice geral de evolução": indice_geral,
            "Interpretação": interpretar_indice(indice_geral),
            "Avanços": avancos or "Não informado.",
            "Dificuldades observadas": dificuldades or "Não informado.",
            "Evolução observada": evolucao or "Não informado.",
        })
    df = pd.DataFrame(dados_grafico)
    if not df.empty and "Data ordenação" in df.columns:
        df = df.sort_values(by="Data ordenação", na_position="last")
    return df

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


def listar_atendimentos_texto(estudante_id):
    atendimentos = listar_atendimentos(estudante_id)

    if not atendimentos:
        return "Nenhum atendimento registrado."

    texto = ""
    for a in atendimentos[:10]:
        texto += f"""
Data do atendimento: {a[0]}
Objetivo trabalhado: {a[1] or 'Não informado.'}
Atividade realizada: {a[2] or 'Não informado.'}
Resposta do estudante: {a[3] or 'Não informado.'}
Avanços observados: {a[4] or 'Não informado.'}
Dificuldades observadas: {a[5] or 'Não informado.'}
Evolução observada: {a[6] or 'Não informado.'}
Resposta do estudante: {a[8] if len(a) > 8 and a[8] is not None else 'Não informado.'}/10
Avanço pedagógico: {a[9] if len(a) > 9 and a[9] is not None else 'Não informado.'}/10
Nível de dificuldade: {a[10] if len(a) > 10 and a[10] is not None else 'Não informado.'}/10
Engajamento: {a[11] if len(a) > 11 and a[11] is not None else 'Não informado.'}/10
Índice geral de evolução: {a[12] if len(a) > 12 and a[12] is not None else 'Não informado.'}/10
Encaminhamentos: {a[13] if len(a) > 13 and a[13] else 'Não informado.'}
---
"""
    return texto.strip()


def montar_texto_avaliacao(estudante, data_registro, barreiras, potencialidades, comunicacao, interacao, autonomia, aprendizagem, resumo_laudo):
    """Monta um texto simples para download após salvar a avaliação pedagógica."""
    return f"""
AVALIAÇÃO PEDAGÓGICA INICIAL

Data do registro: {data_registro}

1. Identificação do estudante
Código interno: {estudante[1] or 'Não informado.'}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Perfil educacional informado: {estudante[4] or 'Não informado.'}
Observações pedagógicas iniciais: {estudante[5] or 'Não informado.'}

2. Informações lançadas na avaliação
Barreiras enfrentadas pelo estudante:
{barreiras or 'Não informado.'}

Potencialidades e habilidades já desenvolvidas:
{potencialidades or 'Não informado.'}

Comunicação:
{comunicacao or 'Não informado.'}

Interação social:
{interacao or 'Não informado.'}

Autonomia:
{autonomia or 'Não informado.'}

Aprendizagem:
{aprendizagem or 'Não informado.'}

Resumo pedagógico do laudo, sem identificação:
{resumo_laudo or 'Não informado.'}
""".strip()


def montar_texto_atendimento(
    estudante,
    data_atendimento,
    objetivo,
    atividade,
    resposta_estudante,
    avancos,
    dificuldades,
    evolucao,
    qtd_atividades,
    nivel_resposta,
    nivel_avanco,
    nivel_dificuldade,
    nivel_engajamento,
    nivel_evolucao,
    encaminhamentos,
):
    """Monta um texto simples para download de um registro de atendimento."""
    return f"""
REGISTRO DE ATENDIMENTO DO AEE

1. Identificação do estudante
Código interno: {estudante[1] or 'Não informado.'}
Ano/Série: {estudante[2] or 'Não informado.'}
Turma: {estudante[3] or 'Não informado.'}
Perfil educacional informado: {estudante[4] or 'Não informado.'}

2. Dados do atendimento
Data do atendimento: {data_atendimento or 'Não informado.'}

Objetivo trabalhado:
{objetivo or 'Não informado.'}

Atividade realizada:
{atividade or 'Não informado.'}

Resposta do estudante:
{resposta_estudante or 'Não informado.'}

Avanços observados:
{avancos or 'Não informado.'}

Dificuldades observadas:
{dificuldades or 'Não informado.'}

Evolução observada:
{evolucao or 'Não informado.'}

Resposta do estudante:
{nivel_resposta if nivel_resposta is not None else 'Não informado.'}/10

Avanço pedagógico:
{nivel_avanco if nivel_avanco is not None else 'Não informado.'}/10

Nível de dificuldade:
{nivel_dificuldade if nivel_dificuldade is not None else 'Não informado.'}/10

Engajamento:
{nivel_engajamento if nivel_engajamento is not None else 'Não informado.'}/10

Índice geral de evolução:
{nivel_evolucao if nivel_evolucao is not None else 'Não informado.'}/10

Encaminhamentos:
{encaminhamentos or 'Não informado.'}
""".strip()


# ======================================================
# BUSCA DE MODELOS 3D
# ======================================================
def link_busca_thingiverse(termo):
    """Gera link de busca no Thingiverse sem depender da API."""
    termo_formatado = termo.replace(" ", "%20")
    return f"https://www.thingiverse.com/search?q={termo_formatado}&type=things"

def link_busca_printables(termo):
    termo_formatado = termo.replace(" ", "%20")
    return f"https://www.printables.com/search/models?q={termo_formatado}"


def link_busca_makerworld(termo):
    """Gera link de busca no MakerWorld sem depender de API."""
    termo_formatado = termo.replace(" ", "%20")
    return f"https://makerworld.com/pt/search/models?keyword={termo_formatado}"


def gerar_termos_3d_com_ia(conteudo_paee):
    """Gera termos curtos para busca de modelos 3D a partir do PAEE."""
    api_key = obter_api_key()

    termos_padrao = [
        "braille",
        "tactile math",
        "visual schedule",
        "communication cards",
        "sensory toys",
    ]

    if OpenAI is None or not api_key or not conteudo_paee:
        return termos_padrao

    prompt = f"""
Analise o PAEE abaixo e gere exatamente 5 termos curtos para busca de modelos 3D pedagógicos
em sites como Thingiverse, Printables e MakerWorld.

Use termos preferencialmente em inglês, pois retornam mais modelos.
Priorize recursos inclusivos, táteis, manipuláveis, visuais, sensoriais ou de comunicação alternativa.
Não explique. Retorne apenas uma lista, um termo por linha.

PAEE:
{conteudo_paee}
"""

    try:
        client = OpenAI(api_key=api_key)
        resposta = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )

        termos = []
        for linha in resposta.output_text.split("\n"):
            termo = linha.strip().strip("-•0123456789. )(").strip()
            if termo and termo not in termos:
                termos.append(termo)

        return termos[:5] if termos else termos_padrao

    except Exception:
        return termos_padrao

# ======================================================
# IA
# ======================================================
def gerar_paee_sem_ia(estudante, avaliacao):
    codigo = estudante[1]
    ano_serie = estudante[2]
    turma = estudante[3]
    perfil = estudante[4]
    observacoes = estudante[5]

    (
        data_registro,
        barreiras,
        potencialidades,
        comunicacao,
        interacao,
        autonomia,
        aprendizagem,
        resumo_laudo,
    ) = avaliacao

    return f"""
1. Identificação do estudante
Código interno: {codigo}
Ano/Série: {ano_serie}
Turma: {turma}
Perfil educacional informado: {perfil}

2. Caracterização pedagógica inicial
{observacoes or 'Não informado.'}

3. Síntese pedagógica do laudo ou informações complementares
{resumo_laudo or 'Não informado.'}

4. Barreiras identificadas
{barreiras or 'Não informado.'}

5. Potencialidades do estudante
{potencialidades or 'Não informado.'}

6. Comunicação
{comunicacao or 'Não informado.'}

7. Interação social
{interacao or 'Não informado.'}

8. Autonomia
{autonomia or 'Não informado.'}

9. Aprendizagem
{aprendizagem or 'Não informado.'}

10. Objetivos do AEE
Ampliar as condições de acesso, participação e aprendizagem do estudante nas atividades escolares.
Desenvolver estratégias que favoreçam comunicação, autonomia, interação e organização da rotina escolar.
Utilizar recursos pedagógicos acessíveis, materiais concretos e tecnologias educacionais inclusivas.

11. Estratégias pedagógicas sugeridas
Utilizar rotina visual, instruções objetivas e organização antecipada das atividades.
Propor atividades com materiais concretos, jogos pedagógicos, recursos visuais e tecnologias digitais.
Articular as ações do AEE com os professores do ensino comum.
Registrar os avanços e dificuldades após cada atendimento.

12. Recursos de acessibilidade e tecnologia assistiva
Pranchas visuais, cartões de comunicação, materiais táteis, objetos 3D, jogos adaptados e recursos digitais.

13. Avaliação e acompanhamento
Registrar avanços, dificuldades, participação, autonomia e resposta às estratégias utilizadas.
Revisar o PAEE periodicamente, considerando a evolução do estudante.

Data da avaliação utilizada: {data_registro}
""".strip()


def gerar_paee_com_ia(estudante, avaliacao):
    api_key = obter_api_key()

    if OpenAI is None or not api_key:
        return gerar_paee_sem_ia(estudante, avaliacao)

    historico_txt = listar_atendimentos_texto(estudante[0])

    estudante_txt = f"""
Código interno: {estudante[1]}
Ano/Série: {estudante[2]}
Turma: {estudante[3]}
Perfil educacional informado: {estudante[4]}
Observações pedagógicas: {estudante[5]}
"""

    avaliacao_txt = f"""
Data do registro: {avaliacao[0]}
Barreiras: {avaliacao[1]}
Potencialidades: {avaliacao[2]}
Comunicação: {avaliacao[3]}
Interação: {avaliacao[4]}
Autonomia: {avaliacao[5]}
Aprendizagem: {avaliacao[6]}
Resumo pedagógico do laudo: {avaliacao[7]}
"""

    prompt = f"""
Você é um assistente pedagógico especializado em Atendimento Educacional Especializado (AEE), Educação Inclusiva e elaboração de PAEE.

Elabore uma sugestão de PAEE com linguagem formal, técnica, objetiva e pedagógica.
Não invente diagnóstico. Não use nome de estudante. Use apenas o código interno.
Não apresente condutas médicas. Foque em barreiras, potencialidades, objetivos, estratégias pedagógicas, acessibilidade, tecnologia assistiva, acompanhamento e evolução.

PADRÕES DE LINGUAGEM:
- Utilizar exclusivamente a expressão “Código interno” para identificação do estudante.
- Usar “Data de elaboração” como referência temporal do documento.
- Evitar termos imprecisos, ambiguidades de gênero e repetições desnecessárias.
- Não incluir título principal do documento.

REGRA SOBRE TEA SEM NÍVEL:
Se o perfil educacional for TEA e o nível de suporte não estiver informado, adotar provisoriamente abordagem equivalente ao nível II, sem afirmar diagnóstico clínico.

REGRA CRÍTICA SOBRE O USO DOS ATENDIMENTOS:
A análise da evolução deve ser baseada EXCLUSIVAMENTE nos dados reais do histórico de atendimentos.
É proibido inventar avanços, inferir melhorias não registradas ou criar evolução genérica.
A IA deve citar os avanços, dificuldades e evolução observada exatamente como foram registrados.
Se os dados forem insuficientes, escrever claramente:
“Os registros de atendimento ainda são limitados para uma análise evolutiva consistente, sendo necessário ampliar o acompanhamento pedagógico.”

DADOS DO ESTUDANTE:
{estudante_txt}

AVALIAÇÃO PEDAGÓGICA:
{avaliacao_txt}

HISTÓRICO DE ATENDIMENTOS:
{historico_txt}

Estruture o documento com:
1. Identificação do estudante
2. Caracterização pedagógica
3. Necessidades educacionais específicas
4. Barreiras identificadas
5. Potencialidades
6. Objetivos gerais e específicos do AEE
7. Estratégias pedagógicas
8. Recursos de acessibilidade e tecnologias assistivas
9. Sugestões de tecnologias educacionais inclusivas
10. Como aplicar essas tecnologias no atendimento
11. Organização do atendimento
12. Articulação com família e professores
13. Avaliação e acompanhamento
14. Recomendações para revisão do plano
15. Adaptação automática conforme o perfil educacional
16. Evolução do estudante com base nos atendimentos
17. Assinaturas

Na seção de tecnologias educacionais inclusivas, considere:
- impressão 3D;
- robótica educacional;
- jogos digitais;
- recursos maker;
- comunicação alternativa e aumentativa;
- materiais táteis, visuais e manipuláveis;
- atividades plugadas e desplugadas.

Na seção 16, descrever:
- principais avanços observados;
- dificuldades que permanecem;
- estratégias que funcionaram melhor;
- tecnologias que tiveram melhor resposta;
- ajustes recomendados para os próximos atendimentos;
- indicativos de autonomia, comunicação, interação e aprendizagem.

Não inventar evolução. Usar apenas os dados registrados nos atendimentos.

Responsável pelo AEE:
Nome: ___________________________________________
Função: Professor(a) do Atendimento Educacional Especializado (AEE)
Assinatura: _______________________________________

Coordenação pedagógica:
Nome: ___________________________________________
Cargo: Coordenação Pedagógica
Assinatura: _______________________________________

Data de elaboração: {datetime.now().strftime("%d/%m/%Y")}
"""

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return resposta.output_text


def gerar_relatorio_evolucao(estudante, avaliacao):
    api_key = obter_api_key()

    if OpenAI is None or not api_key:
        return """
Relatório de evolução e qualidade do atendimento

IA não configurada.

Para gerar o relatório analítico com IA, configure a variável OPENAI_API_KEY nos Secrets do Streamlit Cloud.
""".strip()

    historico_txt = listar_atendimentos_texto(estudante[0])

    estudante_txt = f"""
Código interno: {estudante[1]}
Ano/Série: {estudante[2]}
Turma: {estudante[3]}
Perfil educacional: {estudante[4]}
"""

    avaliacao_txt = "Avaliação pedagógica não localizada."
    if avaliacao:
        avaliacao_txt = f"""
Data do registro: {avaliacao[0]}
Barreiras: {avaliacao[1]}
Potencialidades: {avaliacao[2]}
Comunicação: {avaliacao[3]}
Interação: {avaliacao[4]}
Autonomia: {avaliacao[5]}
Aprendizagem: {avaliacao[6]}
Resumo pedagógico do laudo: {avaliacao[7]}
"""

    prompt = f"""
Você é um especialista em Educação Inclusiva e Atendimento Educacional Especializado (AEE).

Analise o histórico de atendimentos e produza um documento com o seguinte título:
Relatório de evolução e qualidade do atendimento

DADOS DO ESTUDANTE:
{estudante_txt}

AVALIAÇÃO PEDAGÓGICA:
{avaliacao_txt}

HISTÓRICO DE ATENDIMENTOS:
{historico_txt}

REGRAS IMPORTANTES:
- Não inventar informações.
- Usar somente dados reais registrados.
- Se os dados forem insuficientes, dizer claramente.
- Não usar nome real de estudante.
- Usar somente “Código interno” como identificação.

ESTRUTURA DO RELATÓRIO:
1. Identificação
2. Síntese da evolução do estudante
3. Análise dos avanços
4. Análise das dificuldades
5. Qualidade dos registros pedagógicos
6. Classificação da qualidade dos registros: Alta, Média ou Baixa
7. Principais problemas identificados nos registros
8. Recomendações para melhoria dos registros
9. Recomendações pedagógicas para o AEE
10. Conclusão técnica

IMPORTANTE:
Se os registros forem fracos, dizer explicitamente isso.
"""

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return resposta.output_text


# ======================================================
# PDF
# ======================================================
def gerar_pdf_documento(conteudo, codigo, tipo="paee"):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Image,
    )

    if tipo == "relatorio":
        nome_arquivo = f"Relatorio_{codigo}.pdf"
        titulo_doc = "RELATÓRIO DE EVOLUÇÃO E QUALIDADE DO ATENDIMENTO"
    elif tipo == "avaliacao":
        nome_arquivo = f"Avaliacao_Pedagogica_{codigo}.pdf"
        titulo_doc = "AVALIAÇÃO PEDAGÓGICA INICIAL"
    elif tipo == "atendimento":
        nome_arquivo = f"Registro_Atendimento_{codigo}.pdf"
        titulo_doc = "REGISTRO DE ATENDIMENTO DO AEE"
    else:
        nome_arquivo = f"PAEE_{codigo}.pdf"
        titulo_doc = "PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO (PAEE)"

    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        name="Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=16,
        leading=20,
        spaceAfter=16,
        textColor=colors.black,
    )

    secao_style = ParagraphStyle(
        name="Secao",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
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
        spaceBefore=20,
    )

    elementos = []

    # LOGO
    try:
        logo = Image("logo.png", width=140, height=70)
        logo.hAlign = "CENTER"
        elementos.append(logo)
        elementos.append(Spacer(1, 8))
    except Exception:
        pass

    # NOME INSTITUCIONAL
    elementos.append(
        Paragraph(
            "<b>Universidade Federal Rural de Pernambuco<br/>"
            "LabTec3DI – Laboratório de Tecnologias 3D e Inclusivas</b>",
            normal_style,
        )
    )

    elementos.append(Spacer(1, 8))
    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elementos.append(Spacer(1, 12))

    # TÍTULO
    elementos.append(Paragraph(titulo_doc, titulo_style))
    elementos.append(Spacer(1, 12))

    # CONTEÚDO
    for linha in conteudo.split("\n"):
        linha = linha.strip()

        if not linha:
            elementos.append(Spacer(1, 6))
            continue

        linha_lower = linha.lower()

        if "plano de atendimento educacional especializado" in linha_lower:
            continue
        if "relatório de evolução e qualidade do atendimento" in linha_lower:
            continue
        if "avaliação pedagógica inicial" in linha_lower:
            continue
        if "registro de atendimento do aee" in linha_lower:
            continue
        if linha in ["--", "• --", "---"]:
            continue

        linha_html = escape(linha)

        if linha.startswith("#"):
            texto = escape(linha.replace("#", "").strip())
            elementos.append(Paragraph(f"<b>{texto}</b>", secao_style))

        elif linha.startswith("**") and linha.endswith("**"):
            texto = escape(linha.replace("**", "").strip())
            elementos.append(Paragraph(f"<b>{texto}</b>", secao_style))

        elif linha[:2].isdigit() and "." in linha[:4]:
            elementos.append(Paragraph(f"<b>{linha_html}</b>", secao_style))

        elif linha.startswith("-"):
            elementos.append(Paragraph(f"• {escape(linha[1:].strip())}", normal_style))

        else:
            elementos.append(Paragraph(linha_html, normal_style))

    elementos.append(Spacer(1, 20))
    elementos.append(
        Paragraph(
            "Elaborado com apoio do LabTec3DI – UFRPE",
            rodape_style,
        )
    )

    doc.build(elementos)
    return nome_arquivo

def gerar_pdf_paee(conteudo, codigo):
    return gerar_pdf_documento(conteudo, codigo, tipo="paee")


def gerar_pdf_avaliacao(conteudo, codigo):
    return gerar_pdf_documento(conteudo, codigo, tipo="avaliacao")


def gerar_pdf_atendimento(conteudo, codigo):
    return gerar_pdf_documento(conteudo, codigo, tipo="atendimento")


def gerar_pdf_relatorio(conteudo, codigo):
    return gerar_pdf_documento(conteudo, codigo, tipo="relatorio")


criar_tabelas()

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


def opcoes_estudantes_por_id(estudantes):
    """Retorna lista de IDs e mapa para exibir estudante no selectbox."""
    ids = [e[0] for e in estudantes]
    mapa = {e[0]: f"{e[1]} - {e[2] or 'Ano/Série não informado'} - {e[4] or 'Perfil não informado'}" for e in estudantes}
    return ids, mapa


# ======================================================
# SIDEBAR PROFISSIONAL
# ======================================================
with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        st.markdown("## IncluiPAEE IA")

    st.markdown("---")

    menu = st.radio(
        "Navegação",
        [
            "Dashboard",
            "Cadastro",
            "Avaliação Pedagógica",
            "Gerar PAEE",
            "Atendimentos",
            "Relatório IA",
            "Administração",
        ],
        index=0,
    )

    st.markdown("---")
    st.caption("LabTec3DI – UFRPE")
    st.caption("Sistema inteligente de apoio ao AEE")


st.markdown('<div class="titulo">IncluiPAEE IA</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="descricao">Sistema inteligente de apoio à elaboração de PAEE, registros pedagógicos e relatórios de evolução.</div>',
    unsafe_allow_html=True,
)


# ======================================================
# DASHBOARD
# ======================================================
if menu == "Dashboard":
    st.markdown('<div class="subtitulo">📊 Painel inicial</div>', unsafe_allow_html=True)

    estudantes = listar_estudantes()
    total_estudantes = len(estudantes)

    total_avaliacoes = 0
    total_atendimentos = 0

    for estudante in estudantes:
        total_avaliacoes += len(listar_avaliacoes(estudante[0]))
        total_atendimentos += len(listar_atendimentos(estudante[0]))

    col1, col2, col3 = st.columns(3)
    col1.metric("Estudantes cadastrados", total_estudantes)
    col2.metric("Avaliações registradas", total_avaliacoes)
    col3.metric("Atendimentos registrados", total_atendimentos)

    st.markdown("---")

    col_esq, col_dir = st.columns([1.2, 1])

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
                2. Registre a avaliação pedagógica inicial.
                3. Gere a sugestão de PAEE.
                4. Registre os atendimentos.
                5. Gere o relatório de evolução.
                """
            )


# ======================================================
# CADASTRO
# ======================================================
elif menu == "Cadastro":
    st.markdown('<div class="subtitulo">👤 Cadastro do estudante</div>', unsafe_allow_html=True)

    col_form, col_lista = st.columns([1, 1.2])

    with col_form:
        with st.container(border=True):
            st.markdown("### Novo estudante")

            with st.form("form_cadastro"):
                codigo = st.text_input("Código interno do estudante", placeholder="Ex.: AEE-001", key="cad_codigo")
                ano_serie = st.text_input("Ano/Série", placeholder="Ex.: 4º ano", key="cad_ano")
                turma = st.text_input("Turma", placeholder="Ex.: 4º ano B", key="cad_turma")
                perfil = st.selectbox("Perfil educacional informado", PERFIS, key="cad_perfil")
                observacoes = st.text_area("Observações pedagógicas iniciais", key="cad_observacoes")
                enviar = st.form_submit_button("Cadastrar estudante")

                if enviar:
                    if not codigo.strip():
                        st.error("Informe um código interno para o estudante.")
                    else:
                        try:
                            cadastrar_estudante(codigo.strip(), ano_serie, turma, perfil, observacoes)
                            st.success("Estudante cadastrado com sucesso.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Este código já existe. Use outro código interno.")

    with col_lista:
        with st.container(border=True):
            st.markdown("### 📋 Estudantes cadastrados")

            estudantes = listar_estudantes()

            if estudantes:
                st.dataframe(
                    [
                        {
                            "ID": e[0],
                            "Código": e[1],
                            "Ano/Série": e[2],
                            "Turma": e[3],
                            "Perfil": e[4],
                            "Observações": e[5],
                        }
                        for e in estudantes
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Nenhum estudante cadastrado ainda.")


# ======================================================
# AVALIAÇÃO PEDAGÓGICA
# ======================================================
elif menu == "Avaliação Pedagógica":
    st.markdown('<div class="subtitulo">📝 Avaliação pedagógica inicial</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()

    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="avaliacao_estudante_id",
        )
        estudante_info = buscar_estudante(estudante_id)

        with st.container(border=True):
            st.markdown("### Registro da avaliação")

            with st.form("form_avaliacao"):
                barreiras = st.text_area("Barreiras enfrentadas pelo estudante", key="av_barreiras")
                potencialidades = st.text_area("Potencialidades e habilidades já desenvolvidas", key="av_potencialidades")
                comunicacao = st.text_area("Comunicação", key="av_comunicacao")
                interacao = st.text_area("Interação social", key="av_interacao")
                autonomia = st.text_area("Autonomia", key="av_autonomia")
                aprendizagem = st.text_area("Aprendizagem", key="av_aprendizagem")
                resumo_laudo = st.text_area(
                    "Resumo pedagógico do laudo, sem identificação",
                    placeholder="Ex.: O laudo informa TEA e aponta necessidade de previsibilidade, apoio visual e mediação nas interações.",
                    key="av_resumo",
                )
                enviar = st.form_submit_button("Salvar avaliação")

                if enviar:
                    data_registro_avaliacao = datetime.now().strftime("%d/%m/%Y %H:%M")

                    salvar_avaliacao(
                        estudante_id,
                        barreiras,
                        potencialidades,
                        comunicacao,
                        interacao,
                        autonomia,
                        aprendizagem,
                        resumo_laudo,
                    )

                    texto_avaliacao = montar_texto_avaliacao(
                        estudante_info,
                        data_registro_avaliacao,
                        barreiras,
                        potencialidades,
                        comunicacao,
                        interacao,
                        autonomia,
                        aprendizagem,
                        resumo_laudo,
                    )

                    st.session_state["avaliacao_salva_texto"] = texto_avaliacao
                    st.session_state["avaliacao_salva_codigo"] = estudante_info[1]
                    st.success("Avaliação pedagógica salva com sucesso.")

        if "avaliacao_salva_texto" in st.session_state:
            with st.container(border=True):
                texto_avaliacao = st.session_state["avaliacao_salva_texto"]
                codigo_avaliacao = st.session_state.get("avaliacao_salva_codigo", estudante_info[1])

                st.markdown("### Avaliação salva para download")

                col_txt, col_pdf = st.columns(2)

                with col_txt:
                    st.download_button(
                        "Baixar avaliação em .txt",
                        data=texto_avaliacao,
                        file_name=f"Avaliacao_Pedagogica_{codigo_avaliacao}.txt",
                        mime="text/plain",
                        key="download_txt_avaliacao",
                    )

                with col_pdf:
                    if st.button("Gerar PDF da avaliação", key="btn_pdf_avaliacao"):
                        arquivo = gerar_pdf_avaliacao(texto_avaliacao, codigo_avaliacao)
                        st.session_state["arquivo_pdf_avaliacao"] = arquivo

                    if "arquivo_pdf_avaliacao" in st.session_state:
                        with open(st.session_state["arquivo_pdf_avaliacao"], "rb") as f:
                            st.download_button(
                                "Baixar avaliação em PDF",
                                data=f,
                                file_name=f"Avaliacao_Pedagogica_{codigo_avaliacao}.pdf",
                                mime="application/pdf",
                                key="download_pdf_avaliacao",
                            )

        with st.container(border=True):
            st.markdown("### Histórico de avaliações pedagógicas")
            avaliacoes = listar_avaliacoes(estudante_id)

            if avaliacoes:
                for avaliacao_item in avaliacoes:
                    avaliacao_id = avaliacao_item[0]
                    data_registro = avaliacao_item[1]
                    barreiras_hist = avaliacao_item[2]
                    potencialidades_hist = avaliacao_item[3]
                    comunicacao_hist = avaliacao_item[4]
                    interacao_hist = avaliacao_item[5]
                    autonomia_hist = avaliacao_item[6]
                    aprendizagem_hist = avaliacao_item[7]
                    resumo_laudo_hist = avaliacao_item[8]

                    with st.expander(f"Avaliação em {data_registro}"):
                        st.markdown(f"**Barreiras:** {barreiras_hist or 'Não informado.'}")
                        st.markdown(f"**Potencialidades:** {potencialidades_hist or 'Não informado.'}")
                        st.markdown(f"**Comunicação:** {comunicacao_hist or 'Não informado.'}")
                        st.markdown(f"**Interação social:** {interacao_hist or 'Não informado.'}")
                        st.markdown(f"**Autonomia:** {autonomia_hist or 'Não informado.'}")
                        st.markdown(f"**Aprendizagem:** {aprendizagem_hist or 'Não informado.'}")
                        st.markdown(f"**Resumo pedagógico do laudo:** {resumo_laudo_hist or 'Não informado.'}")

                        texto_historico = montar_texto_avaliacao(
                            estudante_info,
                            data_registro,
                            barreiras_hist,
                            potencialidades_hist,
                            comunicacao_hist,
                            interacao_hist,
                            autonomia_hist,
                            aprendizagem_hist,
                            resumo_laudo_hist,
                        )

                        st.download_button(
                            "Baixar esta avaliação em .txt",
                            data=texto_historico,
                            file_name=f"Avaliacao_Pedagogica_{estudante_info[1]}_{avaliacao_id}.txt",
                            mime="text/plain",
                            key=f"download_txt_avaliacao_hist_{avaliacao_id}",
                        )

                        if st.button("Gerar PDF desta avaliação", key=f"btn_pdf_avaliacao_hist_{avaliacao_id}"):
                            arquivo = gerar_pdf_avaliacao(texto_historico, f"{estudante_info[1]}_{avaliacao_id}")
                            st.session_state[f"arquivo_pdf_avaliacao_hist_{avaliacao_id}"] = arquivo

                        if f"arquivo_pdf_avaliacao_hist_{avaliacao_id}" in st.session_state:
                            with open(st.session_state[f"arquivo_pdf_avaliacao_hist_{avaliacao_id}"], "rb") as f:
                                st.download_button(
                                    "Baixar esta avaliação em PDF",
                                    data=f,
                                    file_name=f"Avaliacao_Pedagogica_{estudante_info[1]}_{avaliacao_id}.pdf",
                                    mime="application/pdf",
                                    key=f"download_pdf_avaliacao_hist_{avaliacao_id}",
                                )
            else:
                st.info("Nenhuma avaliação pedagógica registrada para este estudante.")


# ======================================================
# GERAR PAEE
# ======================================================
elif menu == "Gerar PAEE":
    st.markdown('<div class="subtitulo">🧠 Gerar PAEE com IA</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()

    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="paee_estudante_id",
        )

        estudante = buscar_estudante(estudante_id)
        avaliacao = ultima_avaliacao(estudante_id)

        with st.container(border=True):
            if not avaliacao:
                st.warning("Este estudante ainda não possui avaliação pedagógica registrada.")
            else:
                usar_ia = OpenAI is not None and bool(obter_api_key())

                if usar_ia:
                    st.success("IA pronta para gerar sugestões pedagógicas.")
                else:
                    st.info("IA não configurada. O sistema irá gerar um PAEE-base automático sem conexão com IA.")

                if st.button("Gerar sugestão de PAEE", key="btn_gerar_paee"):
                    with st.spinner("Gerando PAEE..."):
                        try:
                            paee = gerar_paee_com_ia(estudante, avaliacao)
                            st.session_state["paee_gerado"] = paee
                            st.session_state["paee_codigo"] = estudante[1]
                            salvar_paee(estudante_id, paee)
                            st.success("PAEE gerado e salvo no histórico.")
                        except Exception as erro:
                            st.error(f"Erro ao gerar PAEE: {erro}")

        if "paee_gerado" in st.session_state:
            with st.container(border=True):
                st.markdown("### PAEE gerado")
                st.text_area(
                    "Conteúdo",
                    st.session_state["paee_gerado"],
                    height=600,
                    key="txt_paee_gerado",
                )

                codigo_download = st.session_state.get("paee_codigo", estudante[1])

                col_txt, col_pdf = st.columns(2)

                with col_txt:
                    st.download_button(
                        "Baixar PAEE em .txt",
                        data=st.session_state["paee_gerado"],
                        file_name=f"PAEE_{codigo_download}.txt",
                        mime="text/plain",
                        key="download_txt_paee",
                    )

                with col_pdf:
                    if st.button("Gerar PDF do PAEE", key="btn_gerar_pdf_paee"):
                        arquivo = gerar_pdf_paee(st.session_state["paee_gerado"], codigo_download)
                        st.session_state["arquivo_pdf_paee"] = arquivo

                    if "arquivo_pdf_paee" in st.session_state:
                        with open(st.session_state["arquivo_pdf_paee"], "rb") as f:
                            st.download_button(
                                "Baixar PAEE em PDF",
                                data=f,
                                file_name=f"PAEE_{codigo_download}.pdf",
                                mime="application/pdf",
                                key="download_pdf_paee",
                            )

            with st.container(border=True):
                st.markdown("### 🔎 Modelos 3D sugeridos para apoio pedagógico")
                st.caption(
                    "A IA analisa o PAEE e sugere termos de busca. Depois, o professor escolhe onde pesquisar os modelos."
                )

                if st.button("Gerar sugestões de busca com IA", key="btn_gerar_termos_3d"):
                    with st.spinner("Gerando termos de busca a partir do PAEE..."):
                        termos_sugeridos = gerar_termos_3d_com_ia(
                            st.session_state["paee_gerado"]
                        )
                        st.session_state["termos_3d_sugeridos"] = termos_sugeridos
                        st.success("Sugestões geradas com sucesso.")

                if "termos_3d_sugeridos" in st.session_state:
                    st.markdown("#### Sugestões geradas a partir do PAEE")

                    for termo in st.session_state["termos_3d_sugeridos"]:
                        col_termo, col_thingiverse, col_printables, col_makerworld = st.columns(
                            [2.5, 1.4, 1.4, 1.4]
                        )

                        with col_termo:
                            st.markdown(f"**{termo}**")

                        with col_thingiverse:
                            st.link_button("Thingiverse", link_busca_thingiverse(termo))

                        with col_printables:
                            st.link_button("Printables", link_busca_printables(termo))

                        with col_makerworld:
                            st.link_button("MakerWorld", link_busca_makerworld(termo))

                st.markdown("#### Busca manual")
                termo_3d = st.text_input(
                    "Digite outro termo, se desejar",
                    placeholder="Ex.: braille, tactile math, visual schedule",
                    key="termo_3d_paee",
                )

                col_thingiverse_manual, col_printables_manual, col_makerworld_manual = st.columns(3)

                with col_thingiverse_manual:
                    if termo_3d.strip():
                        st.link_button("Thingiverse", link_busca_thingiverse(termo_3d.strip()))
                    else:
                        st.caption("Digite um termo para buscar no Thingiverse.")

                with col_printables_manual:
                    if termo_3d.strip():
                        st.link_button("Printables", link_busca_printables(termo_3d.strip()))
                    else:
                        st.caption("Digite um termo para buscar no Printables.")

                with col_makerworld_manual:
                    if termo_3d.strip():
                        st.link_button("MakerWorld", link_busca_makerworld(termo_3d.strip()))
                    else:
                        st.caption("Digite um termo para buscar no MakerWorld.")


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
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="atendimento_estudante_id",
        )
        estudante_info = buscar_estudante(estudante_id)

        with st.container(border=True):
            st.markdown("### Novo atendimento")

            with st.form("form_atendimento"):
                data_atendimento = st.date_input("Data do atendimento", key="at_data")

                st.markdown("#### Registro pedagógico e indicadores")
                st.caption(
                    "Preencha o texto pedagógico e, logo abaixo de cada dimensão, informe a escala correspondente. "
                    "O gráfico será alimentado pelos indicadores numéricos e o relatório pela descrição pedagógica."
                )

                objetivo = st.text_area("Objetivo trabalhado", key="at_objetivo")
                atividade = st.text_area("Atividade realizada", key="at_atividade")

                resposta_estudante = st.text_area("Resposta do estudante", key="at_resposta")
                nivel_resposta = st.slider(
                    "Escala da resposta do estudante",
                    min_value=1, max_value=10, value=5,
                    help="1 a 3: pouca resposta; 4 a 6: resposta parcial; 7 a 8: boa resposta; 9 a 10: resposta excelente.",
                    key="at_nivel_resposta",
                )

                avancos = st.text_area("Avanços observados", key="at_avancos")
                nivel_avanco = st.slider(
                    "Escala do avanço pedagógico",
                    min_value=1, max_value=10, value=5,
                    help="Avalia avanço em aprendizagem, participação, comunicação, autonomia ou objetivo trabalhado.",
                    key="at_nivel_avanco",
                )

                dificuldades = st.text_area("Dificuldades observadas", key="at_dificuldades")
                nivel_dificuldade = st.slider(
                    "Escala de dificuldade/barreira observada",
                    min_value=1, max_value=10, value=5,
                    help="1 representa pouca dificuldade; 10 representa muita dificuldade/barreira observada.",
                    key="at_nivel_dificuldade",
                )

                evolucao = st.text_area("Evolução observada", key="at_evolucao")
                nivel_engajamento = st.slider(
                    "Escala de engajamento/participação",
                    min_value=1, max_value=10, value=5,
                    help="Avalia interesse, participação, permanência na atividade e envolvimento durante o atendimento.",
                    key="at_nivel_engajamento",
                )

                nivel_evolucao = calcular_indice_geral(nivel_resposta, nivel_avanco, nivel_dificuldade, nivel_engajamento)
                st.info(
                    f"Índice geral calculado automaticamente: {nivel_evolucao}/10. "
                    "Esse índice considera resposta, avanço, engajamento e o impacto invertido da dificuldade."
                )

                encaminhamentos = st.text_area("Encaminhamentos", key="at_encaminhamentos")
                enviar = st.form_submit_button("Salvar atendimento")

                if enviar:
                    salvar_atendimento(
                        estudante_id, data_atendimento.strftime("%d/%m/%Y"), objetivo, atividade,
                        resposta_estudante, avancos, dificuldades, evolucao, 1, nivel_resposta, nivel_avanco,
                        nivel_dificuldade, nivel_engajamento, nivel_evolucao, encaminhamentos,
                    )
                    st.success("Atendimento registrado com sucesso.")
                    st.rerun()

        with st.container(border=True):
            st.markdown("### Histórico de atendimentos")
            atendimentos = listar_atendimentos_com_id(estudante_id)

            if atendimentos:
                for item in atendimentos:
                    atendimento_id = item[0]
                    data_hist = item[1]
                    objetivo_hist = item[2]
                    atividade_hist = item[3]
                    resposta_hist = item[4]
                    avancos_hist = item[5]
                    dificuldades_hist = item[6]
                    evolucao_hist = item[7]
                    qtd_atividades_hist = item[8] if len(item) > 8 and item[8] is not None else 1
                    nivel_resposta_hist = limitar_escala(item[9] if len(item) > 9 else 5)
                    nivel_avanco_hist = limitar_escala(item[10] if len(item) > 10 else 5)
                    nivel_dificuldade_hist = limitar_escala(item[11] if len(item) > 11 else 5)
                    nivel_engajamento_hist = limitar_escala(item[12] if len(item) > 12 else 5)
                    nivel_evolucao_hist = item[13] if len(item) > 13 and item[13] is not None else calcular_indice_geral(nivel_resposta_hist, nivel_avanco_hist, nivel_dificuldade_hist, nivel_engajamento_hist)
                    encaminhamentos_hist = item[14] if len(item) > 14 else None

                    with st.expander(f"Atendimento em {data_hist}"):
                        st.markdown("#### Visualização do atendimento")
                        st.markdown(f"**Objetivo:** {objetivo_hist or 'Não informado.'}")
                        st.markdown(f"**Atividade:** {atividade_hist or 'Não informado.'}")
                        st.markdown(f"**Resposta do estudante:** {resposta_hist or 'Não informado.'}")
                        st.markdown(f"**Avanços:** {avancos_hist or 'Não informado.'}")
                        st.markdown(f"**Dificuldades:** {dificuldades_hist or 'Não informado.'}")
                        st.markdown(f"**Evolução observada:** {evolucao_hist or 'Não informado.'}")
                        st.markdown(f"**Resposta do estudante:** {nivel_resposta_hist}/10")
                        st.markdown(f"**Avanço pedagógico:** {nivel_avanco_hist}/10")
                        st.markdown(f"**Nível de dificuldade:** {nivel_dificuldade_hist}/10")
                        st.markdown(f"**Engajamento:** {nivel_engajamento_hist}/10")
                        st.markdown(f"**Índice geral de evolução:** {nivel_evolucao_hist}/10")
                        st.markdown(f"**Encaminhamentos:** {encaminhamentos_hist or 'Não informado.'}")

                        texto_atendimento = montar_texto_atendimento(
                            estudante_info, data_hist, objetivo_hist, atividade_hist, resposta_hist, avancos_hist,
                            dificuldades_hist, evolucao_hist, qtd_atividades_hist, nivel_resposta_hist, nivel_avanco_hist,
                            nivel_dificuldade_hist, nivel_engajamento_hist, nivel_evolucao_hist, encaminhamentos_hist,
                        )

                        col_txt_at, col_pdf_at = st.columns(2)
                        with col_txt_at:
                            st.download_button(
                                "Baixar este atendimento em .txt", data=texto_atendimento,
                                file_name=f"Registro_Atendimento_{estudante_info[1]}_{atendimento_id}.txt",
                                mime="text/plain", key=f"download_txt_atendimento_{atendimento_id}",
                            )
                        with col_pdf_at:
                            if st.button("Gerar PDF deste atendimento", key=f"btn_pdf_atendimento_{atendimento_id}"):
                                arquivo = gerar_pdf_atendimento(texto_atendimento, f"{estudante_info[1]}_{atendimento_id}")
                                st.session_state[f"arquivo_pdf_atendimento_{atendimento_id}"] = arquivo
                            if f"arquivo_pdf_atendimento_{atendimento_id}" in st.session_state:
                                with open(st.session_state[f"arquivo_pdf_atendimento_{atendimento_id}"], "rb") as f:
                                    st.download_button(
                                        "Baixar este atendimento em PDF", data=f,
                                        file_name=f"Registro_Atendimento_{estudante_info[1]}_{atendimento_id}.pdf",
                                        mime="application/pdf", key=f"download_pdf_atendimento_{atendimento_id}",
                                    )

                        st.markdown("---")
                        st.markdown("#### ✏️ Editar atendimento")
                        with st.form(f"form_editar_atendimento_{atendimento_id}"):
                            data_edit = st.date_input("Data do atendimento", value=data_para_date(data_hist), key=f"edit_at_data_{atendimento_id}")
                            objetivo_edit = st.text_area("Objetivo trabalhado", value=objetivo_hist or "", key=f"edit_at_objetivo_{atendimento_id}")
                            atividade_edit = st.text_area("Atividade realizada", value=atividade_hist or "", key=f"edit_at_atividade_{atendimento_id}")
                            resposta_edit = st.text_area("Resposta do estudante", value=resposta_hist or "", key=f"edit_at_resposta_{atendimento_id}")
                            nivel_resposta_edit = st.slider("Escala da resposta do estudante", 1, 10, int(nivel_resposta_hist), key=f"edit_at_nivel_resposta_{atendimento_id}")
                            avancos_edit = st.text_area("Avanços observados", value=avancos_hist or "", key=f"edit_at_avancos_{atendimento_id}")
                            nivel_avanco_edit = st.slider("Escala do avanço pedagógico", 1, 10, int(nivel_avanco_hist), key=f"edit_at_nivel_avanco_{atendimento_id}")
                            dificuldades_edit = st.text_area("Dificuldades observadas", value=dificuldades_hist or "", key=f"edit_at_dificuldades_{atendimento_id}")
                            nivel_dificuldade_edit = st.slider("Escala de dificuldade/barreira observada", 1, 10, int(nivel_dificuldade_hist), key=f"edit_at_nivel_dificuldade_{atendimento_id}")
                            evolucao_edit = st.text_area("Evolução observada", value=evolucao_hist or "", key=f"edit_at_evolucao_{atendimento_id}")
                            nivel_engajamento_edit = st.slider("Escala de engajamento/participação", 1, 10, int(nivel_engajamento_hist), key=f"edit_at_nivel_engajamento_{atendimento_id}")
                            nivel_evolucao_edit = calcular_indice_geral(nivel_resposta_edit, nivel_avanco_edit, nivel_dificuldade_edit, nivel_engajamento_edit)
                            st.info(f"Índice geral recalculado: {nivel_evolucao_edit}/10")
                            encaminhamentos_edit = st.text_area("Encaminhamentos", value=encaminhamentos_hist or "", key=f"edit_at_encaminhamentos_{atendimento_id}")
                            salvar_edicao = st.form_submit_button("Salvar atualização do atendimento")
                            if salvar_edicao:
                                atualizar_atendimento(
                                    atendimento_id, data_edit.strftime("%d/%m/%Y"), objetivo_edit, atividade_edit, resposta_edit,
                                    avancos_edit, dificuldades_edit, evolucao_edit, qtd_atividades_hist, nivel_resposta_edit,
                                    nivel_avanco_edit, nivel_dificuldade_edit, nivel_engajamento_edit, nivel_evolucao_edit,
                                    encaminhamentos_edit,
                                )
                                st.success("Atendimento atualizado com sucesso.")
                                st.rerun()

                        st.markdown("#### 🗑️ Excluir atendimento")
                        confirmar_exclusao_atendimento = st.checkbox("Confirmar exclusão deste atendimento", key=f"confirmar_exclusao_atendimento_{atendimento_id}")
                        if st.button("Excluir este atendimento", key=f"btn_excluir_atendimento_{atendimento_id}"):
                            if confirmar_exclusao_atendimento:
                                excluir_atendimento(atendimento_id)
                                st.success("Atendimento excluído com sucesso.")
                                st.rerun()
                            else:
                                st.warning("Marque a confirmação antes de excluir.")
            else:
                st.info("Nenhum atendimento registrado para este estudante.")


# ======================================================
# RELATÓRIO IA
# ======================================================
elif menu == "Relatório IA":
    st.markdown('<div class="subtitulo">📄 Relatório de evolução e qualidade do atendimento</div>', unsafe_allow_html=True)
    estudantes = listar_estudantes()

    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        ids, mapa = opcoes_estudantes_por_id(estudantes)
        estudante_id = st.selectbox(
            "Selecione o estudante",
            ids,
            format_func=lambda x: mapa[x],
            key="relatorio_estudante_id",
        )

        estudante = buscar_estudante(estudante_id)
        avaliacao = ultima_avaliacao(estudante_id)
        atendimentos = listar_atendimentos(estudante_id)

        if atendimentos:
            df_evolucao = montar_dataframe_evolucao(atendimentos)

            with st.container(border=True):
                st.markdown("### 📊 Indicadores por atendimento")
                st.caption(
                    "Cada data apresenta barras agrupadas com os indicadores registrados no atendimento. "
                    "A escala vai de 1 a 10. A dificuldade é exibida para identificar barreiras, mas não deve ser lida como evolução positiva."
                )

                media_resposta = df_evolucao["Resposta do estudante"].mean()
                media_avanco = df_evolucao["Avanço pedagógico"].mean()
                media_dificuldade = df_evolucao["Nível de dificuldade"].mean()
                media_engajamento = df_evolucao["Engajamento"].mean()

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Atendimentos", len(df_evolucao))
                col2.metric("Média resposta", f"{media_resposta:.1f}/10")
                col3.metric("Média avanço", f"{media_avanco:.1f}/10")
                col4.metric("Média dificuldade", f"{media_dificuldade:.1f}/10")
                col5.metric("Média engajamento", f"{media_engajamento:.1f}/10")

                indicadores = [
                    "Resposta do estudante",
                    "Avanço pedagógico",
                    "Nível de dificuldade",
                    "Engajamento",
                ]

                # Inclui a evolução geral apenas se existir na base de dados.
                if "Índice geral de evolução" in df_evolucao.columns:
                    df_evolucao = df_evolucao.rename(columns={"Índice geral de evolução": "Evolução geral"})
                    indicadores.append("Evolução geral")

                df_indicadores = df_evolucao[["Data"] + indicadores].melt(
                    id_vars="Data",
                    value_vars=indicadores,
                    var_name="Indicador",
                    value_name="Pontuação",
                )

                grafico_indicadores = (
                    alt.Chart(df_indicadores)
                    .mark_bar()
                    .encode(
                        x=alt.X("Data:N", title="Data do atendimento", sort=None),
                        xOffset=alt.XOffset("Indicador:N"),
                        y=alt.Y("Pontuação:Q", title="Pontuação", scale=alt.Scale(domain=[0, 10])),
                        color=alt.Color("Indicador:N", title="Indicador"),
                        tooltip=["Data:N", "Indicador:N", alt.Tooltip("Pontuação:Q", format=".1f")],
                    )
                    .properties(height=420)
                )
                st.altair_chart(grafico_indicadores, use_container_width=True)

                with st.expander("Ver dados usados no gráfico"):
                    colunas_tabela = [
                        "Data",
                        "Resposta do estudante",
                        "Avanço pedagógico",
                        "Nível de dificuldade",
                        "Engajamento",
                    ]
                    if "Evolução geral" in df_evolucao.columns:
                        colunas_tabela.append("Evolução geral")
                    colunas_tabela += [
                        "Interpretação",
                        "Avanços",
                        "Dificuldades observadas",
                        "Evolução observada",
                    ]
                    colunas_tabela = [c for c in colunas_tabela if c in df_evolucao.columns]
                    st.dataframe(
                        df_evolucao[colunas_tabela],
                        use_container_width=True,
                        hide_index=True,
                    )
        else:
            with st.container(border=True):
                st.markdown("### 📊 Indicadores por atendimento")
                st.warning(
                    "Este estudante ainda não possui atendimentos registrados. "
                    "Registre pelo menos um atendimento para gerar o gráfico."
                )

        with st.container(border=True):
            st.markdown("### 🤖 Gerar novo relatório")
            if not atendimentos:
                st.warning("Este estudante ainda não possui atendimentos registrados. O relatório poderá ficar limitado.")

            if st.button("Gerar relatório de evolução", key="btn_relatorio"):
                with st.spinner("Analisando atendimentos..."):
                    try:
                        relatorio = gerar_relatorio_evolucao(estudante, avaliacao)
                        titulo_relatorio = "Relatório de evolução e qualidade do atendimento"
                        relatorio_id = salvar_relatorio(estudante_id, titulo_relatorio, relatorio)
                        st.session_state["relatorio_evolucao"] = relatorio
                        st.session_state["relatorio_evolucao_editavel"] = relatorio
                        st.session_state["relatorio_codigo"] = estudante[1]
                        st.session_state["relatorio_id"] = relatorio_id
                        st.success("Relatório gerado e salvo no histórico.")
                    except Exception as erro:
                        st.error(f"Erro ao gerar relatório: {erro}")

        if "relatorio_evolucao" in st.session_state:
            with st.container(border=True):
                codigo_relatorio = st.session_state.get("relatorio_codigo", estudante[1])
                relatorio_id_atual = st.session_state.get("relatorio_id")

                st.markdown("### ✏️ Relatório gerado para revisão")
                st.caption("Você pode editar, salvar, excluir ou baixar o relatório gerado.")

                if "relatorio_evolucao_editavel" not in st.session_state:
                    st.session_state["relatorio_evolucao_editavel"] = st.session_state["relatorio_evolucao"]

                relatorio_editado = st.text_area(
                    "Relatório",
                    height=500,
                    key="relatorio_evolucao_editavel",
                )

                col_salvar, col_excluir, col_txt, col_pdf = st.columns(4)

                with col_salvar:
                    if st.button("Salvar alterações", key="btn_salvar_relatorio_editado"):
                        if relatorio_id_atual:
                            atualizar_relatorio(
                                relatorio_id_atual,
                                "Relatório de evolução e qualidade do atendimento",
                                relatorio_editado,
                            )
                            st.session_state["relatorio_evolucao"] = relatorio_editado
                            st.success("Relatório atualizado com sucesso.")
                        else:
                            novo_id = salvar_relatorio(
                                estudante_id,
                                "Relatório de evolução e qualidade do atendimento",
                                relatorio_editado,
                            )
                            st.session_state["relatorio_id"] = novo_id
                            st.session_state["relatorio_evolucao"] = relatorio_editado
                            st.success("Relatório salvo com sucesso.")

                with col_excluir:
                    if st.button("Excluir relatório", key="btn_excluir_relatorio_atual"):
                        if relatorio_id_atual:
                            excluir_relatorio(relatorio_id_atual)
                        for chave in [
                            "relatorio_evolucao",
                            "relatorio_evolucao_editavel",
                            "relatorio_codigo",
                            "relatorio_id",
                            "arquivo_pdf_relatorio",
                        ]:
                            st.session_state.pop(chave, None)
                        st.success("Relatório excluído com sucesso.")
                        st.rerun()

                with col_txt:
                    st.download_button(
                        "Baixar .txt",
                        data=relatorio_editado,
                        file_name=f"Relatorio_{codigo_relatorio}.txt",
                        mime="text/plain",
                        key="download_txt_relatorio",
                    )

                with col_pdf:
                    if st.button("Gerar PDF", key="btn_pdf_relatorio"):
                        arquivo = gerar_pdf_relatorio(relatorio_editado, codigo_relatorio)
                        st.session_state["arquivo_pdf_relatorio"] = arquivo

                    if "arquivo_pdf_relatorio" in st.session_state:
                        with open(st.session_state["arquivo_pdf_relatorio"], "rb") as f:
                            st.download_button(
                                "Baixar PDF",
                                data=f,
                                file_name=f"Relatorio_{codigo_relatorio}.pdf",
                                mime="application/pdf",
                                key="download_pdf_relatorio",
                            )

        with st.container(border=True):
            st.markdown("### 📚 Histórico de relatórios salvos")
            st.caption("Abra um relatório salvo para editar, baixar ou excluir.")
            relatorios_salvos = listar_relatorios(estudante_id)

            if relatorios_salvos:
                for rel_item in relatorios_salvos:
                    relatorio_id_hist = rel_item[0]
                    data_geracao_hist = rel_item[1]
                    titulo_hist = rel_item[2] or "Relatório de evolução e qualidade do atendimento"
                    conteudo_hist = rel_item[3] or ""

                    with st.expander(f"{titulo_hist} — {data_geracao_hist}"):
                        titulo_editado = st.text_input(
                            "Título do relatório",
                            value=titulo_hist,
                            key=f"titulo_relatorio_hist_{relatorio_id_hist}",
                        )
                        conteudo_editado = st.text_area(
                            "Conteúdo do relatório",
                            value=conteudo_hist,
                            height=420,
                            key=f"conteudo_relatorio_hist_{relatorio_id_hist}",
                        )

                        col_hist_salvar, col_hist_excluir, col_hist_txt, col_hist_pdf = st.columns(4)

                        with col_hist_salvar:
                            if st.button("Salvar edição", key=f"btn_salvar_relatorio_hist_{relatorio_id_hist}"):
                                atualizar_relatorio(relatorio_id_hist, titulo_editado, conteudo_editado)
                                st.success("Relatório atualizado com sucesso.")
                                st.rerun()

                        with col_hist_excluir:
                            confirmar_exclusao_relatorio = st.checkbox(
                                "Confirmar exclusão",
                                key=f"check_excluir_relatorio_hist_{relatorio_id_hist}",
                            )
                            if st.button("Excluir relatório salvo", key=f"btn_excluir_relatorio_hist_{relatorio_id_hist}"):
                                if confirmar_exclusao_relatorio:
                                    excluir_relatorio(relatorio_id_hist)
                                    st.success("Relatório excluído com sucesso.")
                                    st.rerun()
                                else:
                                    st.warning("Marque a confirmação antes de excluir.")

                        with col_hist_txt:
                            st.download_button(
                                "Baixar .txt",
                                data=conteudo_editado,
                                file_name=f"Relatorio_{estudante[1]}_{relatorio_id_hist}.txt",
                                mime="text/plain",
                                key=f"download_txt_relatorio_hist_{relatorio_id_hist}",
                            )

                        with col_hist_pdf:
                            if st.button("Gerar PDF", key=f"btn_pdf_relatorio_hist_{relatorio_id_hist}"):
                                arquivo = gerar_pdf_relatorio(
                                    conteudo_editado,
                                    f"{estudante[1]}_{relatorio_id_hist}",
                                )
                                st.session_state[f"arquivo_pdf_relatorio_hist_{relatorio_id_hist}"] = arquivo

                            if f"arquivo_pdf_relatorio_hist_{relatorio_id_hist}" in st.session_state:
                                with open(st.session_state[f"arquivo_pdf_relatorio_hist_{relatorio_id_hist}"], "rb") as f:
                                    st.download_button(
                                        "Baixar PDF",
                                        data=f,
                                        file_name=f"Relatorio_{estudante[1]}_{relatorio_id_hist}.pdf",
                                        mime="application/pdf",
                                        key=f"download_pdf_relatorio_hist_{relatorio_id_hist}",
                                    )
            else:
                st.info("Nenhum relatório salvo para este estudante.")

# ======================================================
# ADMINISTRAÇÃO
# ======================================================
elif menu == "Administração":
    st.markdown('<div class="subtitulo">⚙️ Administração</div>', unsafe_allow_html=True)

    estudantes = listar_estudantes()

    if estudantes:
        ids, mapa = opcoes_estudantes_por_id(estudantes)

        estudante_id_editar = st.selectbox(
            "Selecione o estudante para editar",
            ids,
            format_func=lambda x: mapa[x],
            key="editar_estudante_id",
        )

        estudante_editar = buscar_estudante(estudante_id_editar)

        if estudante_editar:
            perfil_atual = estudante_editar[4] if estudante_editar[4] in PERFIS else "Não informado"

            col_edit, col_delete = st.columns([1.4, 0.8])

            with col_edit:
                with st.container(border=True):
                    st.markdown("### ✏️ Editar cadastro do estudante")

                    with st.form(f"form_editar_estudante_{estudante_id_editar}"):
                        col1, col2 = st.columns(2)

                        with col1:
                            codigo_edit = st.text_input(
                                "Código interno",
                                value=estudante_editar[1] or "",
                                key=f"edit_codigo_{estudante_id_editar}",
                            )
                            ano_edit = st.text_input(
                                "Ano/Série",
                                value=estudante_editar[2] or "",
                                key=f"edit_ano_{estudante_id_editar}",
                            )

                        with col2:
                            turma_edit = st.text_input(
                                "Turma",
                                value=estudante_editar[3] or "",
                                key=f"edit_turma_{estudante_id_editar}",
                            )
                            perfil_edit = st.selectbox(
                                "Perfil educacional",
                                PERFIS,
                                index=PERFIS.index(perfil_atual),
                                key=f"edit_perfil_{estudante_id_editar}",
                            )

                        observacoes_edit = st.text_area(
                            "Observações pedagógicas iniciais",
                            value=estudante_editar[5] or "",
                            key=f"edit_observacoes_{estudante_id_editar}",
                        )

                        atualizar = st.form_submit_button("💾 Atualizar cadastro")

                        if atualizar:
                            if not codigo_edit.strip():
                                st.error("O código interno não pode ficar vazio.")
                            else:
                                try:
                                    atualizar_estudante(
                                        estudante_id_editar,
                                        codigo_edit.strip(),
                                        ano_edit,
                                        turma_edit,
                                        perfil_edit,
                                        observacoes_edit,
                                    )
                                    st.success("Cadastro atualizado com sucesso.")
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("Este código interno já está sendo usado por outro estudante.")

            with col_delete:
                with st.container(border=True):
                    st.markdown("### 🗑️ Excluir estudante")
                    st.warning("A exclusão remove cadastro, avaliações, PAEE e atendimentos vinculados ao estudante.")

                    confirmar = st.checkbox(
                        "Confirmar exclusão do estudante selecionado",
                        key=f"confirmar_exclusao_estudante_{estudante_id_editar}",
                    )

                    if st.button("Excluir estudante", key=f"btn_excluir_estudante_{estudante_id_editar}"):
                        if confirmar:
                            excluir_estudante(estudante_id_editar)
                            st.success("Estudante excluído com sucesso.")
                            st.rerun()
                        else:
                            st.warning("Marque a confirmação antes de excluir.")

    else:
        st.info("Nenhum estudante cadastrado ainda.")
