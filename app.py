import os
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

DB_PATH = Path("inclui_paee.db")

# =========================
# API KEY
# =========================
def obter_api_key():
    try:
        return os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
    except Exception:
        return os.getenv("OPENAI_API_KEY")


# =========================
# BANCO
# =========================
def conectar():
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estudantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        ano_serie TEXT,
        turma TEXT,
        perfil TEXT,
        observacoes TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS avaliacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estudante_id INTEGER,
        data_registro TEXT,
        barreiras TEXT,
        potencialidades TEXT,
        comunicacao TEXT,
        interacao TEXT,
        autonomia TEXT,
        aprendizagem TEXT,
        resumo_laudo TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estudante_id INTEGER,
        data_geracao TEXT,
        conteudo TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================
# CRUD
# =========================
def cadastrar_estudante(codigo, ano, turma, perfil, obs):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO estudantes VALUES (NULL, ?, ?, ?, ?, ?)
    """, (codigo, ano, turma, perfil, obs))
    conn.commit()
    conn.close()

def listar_estudantes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, ano_serie, turma, perfil FROM estudantes")
    dados = cursor.fetchall()
    conn.close()
    return dados

def buscar_estudante(id_est):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estudantes WHERE id=?", (id_est,))
    dado = cursor.fetchone()
    conn.close()
    return dado

def salvar_avaliacao(id_est, barreiras, pot, com, inter, auto, apr, resumo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO avaliacoes (
        estudante_id, data_registro, barreiras, potencialidades,
        comunicacao, interacao, autonomia, aprendizagem, resumo_laudo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        id_est,
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        barreiras, pot, com, inter, auto, apr, resumo
    ))
    conn.commit()
    conn.close()

def ultima_avaliacao(id_est):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM avaliacoes WHERE estudante_id=? ORDER BY id DESC LIMIT 1
    """, (id_est,))
    dado = cursor.fetchone()
    conn.close()
    return dado

def salvar_paee(id_est, conteudo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO paees VALUES (NULL, ?, ?, ?)
    """, (id_est, datetime.now().strftime("%d/%m/%Y %H:%M"), conteudo))
    conn.commit()
    conn.close()


# =========================
# IA
# =========================
def gerar_paee_com_ia(estudante, avaliacao):
    api_key = obter_api_key()

    if OpenAI is None or not api_key:
        return "IA não configurada."

    prompt = f"""
Você é especialista em AEE. Gere um PAEE profissional.

Dados do estudante:
{estudante}

Avaliação:
{avaliacao}

Estruture com:
- objetivos
- estratégias
- acessibilidade
- acompanhamento
"""

    client = OpenAI(api_key=api_key)

    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return resposta.output_text


# =========================
# INTERFACE
# =========================
st.set_page_config(page_title="IncluiPAEE IA")

criar_tabelas()

st.title("IncluiPAEE IA")

tab1, tab2, tab3 = st.tabs(["Cadastro", "Avaliação", "Gerar PAEE"])

# CADASTRO
with tab1:
    codigo = st.text_input("Código")
    ano = st.text_input("Ano")
    turma = st.text_input("Turma")
    perfil = st.text_input("Perfil")
    obs = st.text_area("Observações")

    if st.button("Cadastrar"):
        cadastrar_estudante(codigo, ano, turma, perfil, obs)
        st.success("Cadastrado")

# AVALIAÇÃO
with tab2:
    estudantes = listar_estudantes()
    if estudantes:
        op = {e[1]: e[0] for e in estudantes}
        sel = st.selectbox("Aluno", list(op.keys()))
        id_est = op[sel]

        barreiras = st.text_area("Barreiras")
        pot = st.text_area("Potencialidades")

        if st.button("Salvar avaliação"):
            salvar_avaliacao(id_est, barreiras, pot, "", "", "", "", "")
            st.success("Salvo")

# PAEE
with tab3:
    estudantes = listar_estudantes()
    if estudantes:
        op = {e[1]: e[0] for e in estudantes}
        sel = st.selectbox("Aluno", list(op.keys()), key="paee")

        est = buscar_estudante(op[sel])
        av = ultima_avaliacao(op[sel])

        if OpenAI is not None and obter_api_key():
            st.success("IA ativada")
        else:
            st.warning("IA não configurada")

        if st.button("Gerar PAEE"):
            texto = gerar_paee_com_ia(est, av)
            st.write(texto)
