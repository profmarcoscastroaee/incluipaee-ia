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

# ======================================================
# 🔐 API KEY (CORREÇÃO PRINCIPAL)
# ======================================================

def obter_api_key():
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
        conteudo TEXT
    )
    """)

    conn.commit()
    conn.close()

def cadastrar_estudante(codigo, ano_serie, turma, perfil, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO estudantes (codigo, ano_serie, turma, perfil, observacoes)
    VALUES (?, ?, ?, ?, ?)
    """, (codigo, ano_serie, turma, perfil, observacoes))
    conn.commit()
    conn.close()

def listar_estudantes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, ano_serie, turma, perfil FROM estudantes")
    dados = cursor.fetchall()
    conn.close()
    return dados

def buscar_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM estudantes WHERE id=?", (estudante_id,))
    dado = cursor.fetchone()
    conn.close()
    return dado

def salvar_avaliacao(estudante_id, barreiras, potencialidades, comunicacao, interacao, autonomia, aprendizagem, resumo_laudo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO avaliacoes VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (estudante_id, barreiras, potencialidades, comunicacao, interacao, autonomia, aprendizagem, resumo_laudo))
    conn.commit()
    conn.close()

def ultima_avaliacao(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM avaliacoes WHERE estudante_id=? ORDER BY id DESC LIMIT 1
    """, (estudante_id,))
    dado = cursor.fetchone()
    conn.close()
    return dado

def salvar_paee(estudante_id, conteudo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO paees VALUES (NULL, ?, ?)", (estudante_id, conteudo))
    conn.commit()
    conn.close()


# ======================================================
# 🤖 IA
# ======================================================

def gerar_paee_sem_ia(estudante, avaliacao):
    return "PAEE básico gerado (sem IA)."

def gerar_paee_com_ia(estudante, avaliacao):
    api_key = obter_api_key()

    if OpenAI is None or not api_key:
        return gerar_paee_sem_ia(estudante, avaliacao)

    prompt = f"""
Crie um PAEE profissional com base nesses dados:

Estudante: {estudante}
Avaliação: {avaliacao}

Estruture com:
- objetivos
- estratégias pedagógicas
- acessibilidade
- acompanhamento
"""

    client = OpenAI(api_key=api_key)

    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return resposta.output_text


# ======================================================
# INTERFACE
# ======================================================

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
        st.success("Cadastrado!")

# AVALIAÇÃO
with tab2:
    estudantes = listar_estudantes()
    if estudantes:
        opcoes = {e[1]: e[0] for e in estudantes}
        selecionado = st.selectbox("Aluno", list(opcoes.keys()))
        id_est = opcoes[selecionado]

        barreiras = st.text_area("Barreiras")
        pot = st.text_area("Potencialidades")

        if st.button("Salvar avaliação"):
            salvar_avaliacao(id_est, barreiras, pot, "", "", "", "", "")
            st.success("Salvo!")

# GERAR PAEE
with tab3:
    estudantes = listar_estudantes()
    if estudantes:
        opcoes = {e[1]: e[0] for e in estudantes}
        selecionado = st.selectbox("Aluno", list(opcoes.keys()), key="paee")

        estudante = buscar_estudante(opcoes[selecionado])
        avaliacao = ultima_avaliacao(opcoes[selecionado])

        usar_ia = OpenAI is not None and bool(obter_api_key())

        if usar_ia:
            st.success("IA ativada")
        else:
            st.warning("IA não configurada")

        if st.button("Gerar PAEE"):
            paee = gerar_paee_com_ia(estudante, avaliacao)
            st.write(paee)
