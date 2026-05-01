import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import altair as alt

# ================= CONFIG =================
st.set_page_config(
    page_title="INCLUISRM",
    page_icon="📊",
    layout="wide"
)

DB_PATH = "inclui_paee.db"

# ================= BANCO =================
def conectar():
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()

    # ESTUDANTES
    c.execute("""
    CREATE TABLE IF NOT EXISTS estudantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        ano TEXT,
        turma TEXT,
        perfil TEXT
    )
    """)

    # ATENDIMENTOS
    c.execute("""
    CREATE TABLE IF NOT EXISTS atendimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estudante_id INTEGER,
        data TEXT,
        resposta INTEGER,
        avanco INTEGER,
        dificuldade INTEGER,
        engajamento INTEGER
    )
    """)

    # AGENDA
    c.execute("""
    CREATE TABLE IF NOT EXISTS agenda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estudante_id INTEGER,
        data TEXT,
        hora TEXT,
        observacao TEXT
    )
    """)

    conn.commit()
    conn.close()

criar_tabelas()

# ================= FUNÇÕES =================

def listar_estudantes():
    conn = conectar()
    dados = conn.execute("SELECT * FROM estudantes").fetchall()
    conn.close()
    return dados

def salvar_estudante(codigo, ano, turma, perfil):
    conn = conectar()
    conn.execute(
        "INSERT INTO estudantes (codigo, ano, turma, perfil) VALUES (?, ?, ?, ?)",
        (codigo, ano, turma, perfil)
    )
    conn.commit()
    conn.close()

def salvar_atendimento(estudante_id, data, r, a, d, e):
    conn = conectar()
    conn.execute(
        "INSERT INTO atendimentos (estudante_id, data, resposta, avanco, dificuldade, engajamento) VALUES (?, ?, ?, ?, ?, ?)",
        (estudante_id, data, r, a, d, e)
    )
    conn.commit()
    conn.close()

def listar_atendimentos(estudante_id):
    conn = conectar()
    dados = conn.execute(
        "SELECT data, resposta, avanco, dificuldade, engajamento FROM atendimentos WHERE estudante_id=?",
        (estudante_id,)
    ).fetchall()
    conn.close()
    return dados

def salvar_agenda(estudante_id, data, hora, obs):
    conn = conectar()
    conn.execute(
        "INSERT INTO agenda (estudante_id, data, hora, observacao) VALUES (?, ?, ?, ?)",
        (estudante_id, data, hora, obs)
    )
    conn.commit()
    conn.close()

def listar_agenda():
    conn = conectar()
    dados = conn.execute("SELECT * FROM agenda").fetchall()
    conn.close()
    return dados

# ================= MENU =================

menu = st.sidebar.radio("Navegação", [
    "Dashboard",
    "Cadastro do Estudante",
    "Cadastro do Professor AEE",
    "Entrevista com a Família",
    "Avaliação Pedagógica",
    "Estudo de Caso",
    "Plano AEE / PAEE",
    "Atendimentos",
    "Agenda de Atendimentos",
    "Relatórios GRE",
    "Administração"
])

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.markdown("# 📊 INCLUISRM")
    st.caption("Sistema de Gestão do Atendimento Educacional Especializado")

    estudantes = listar_estudantes()

    col1, col2, col3 = st.columns(3)

    col1.metric("👥 Estudantes", len(estudantes))
    col2.metric("📅 Atendimentos", 0)
    col3.metric("📈 Evolução média", "—")

    st.markdown("---")

    st.info("Bem-vindo ao sistema INCLUISRM. Utilize o menu ao lado para iniciar.")
# ================= CADASTRO =================
elif menu == "Cadastro do Estudante":
    st.title("👤 Cadastro do Estudante")

    with st.form("cadastro"):
        codigo = st.text_input("Código do estudante (Ex: AEE-001)")
        ano = st.text_input("Ano")
        turma = st.text_input("Turma")
        perfil = st.text_input("Perfil")

        if st.form_submit_button("Salvar"):
            salvar_estudante(codigo, ano, turma, perfil)
            st.success("Estudante cadastrado")

    dados = listar_estudantes()
    if dados:
        df = pd.DataFrame(dados, columns=["ID","Código","Ano","Turma","Perfil"])
        st.dataframe(df, use_container_width=True)

# ================= ATENDIMENTOS =================
elif menu == "Atendimentos":
    st.title("📌 Atendimentos")

    estudantes = listar_estudantes()

    if estudantes:
        nomes = {e[0]: e[1] for e in estudantes}

        est_id = st.selectbox("Aluno", list(nomes.keys()), format_func=lambda x: nomes[x])

        with st.form("atendimento"):
            data = st.date_input("Data")
            r = st.slider("Resposta", 1, 10, 5)
            a = st.slider("Avanço", 1, 10, 5)
            d = st.slider("Dificuldade", 1, 10, 5)
            e = st.slider("Engajamento", 1, 10, 5)

            if st.form_submit_button("Salvar"):
                salvar_atendimento(est_id, data.strftime("%d/%m/%Y"), r, a, d, e)
                st.success("Atendimento salvo")

        dados = listar_atendimentos(est_id)

        if dados:
            df = pd.DataFrame(dados, columns=["Data","Resposta","Avanço","Dificuldade","Engajamento"])

            df["Dificuldade invertida"] = 11 - df["Dificuldade"]

            df_melt = df.melt(
                id_vars=["Data"],
                value_vars=["Resposta","Avanço","Engajamento","Dificuldade invertida"],
                var_name="Indicador",
                value_name="Valor"
            )

            grafico = alt.Chart(df_melt).mark_bar().encode(
                x="Data:N",
                y=alt.Y("Valor:Q", scale=alt.Scale(domain=[0,10])),
                color="Indicador:N",
                tooltip=["Data","Indicador","Valor"]
            )

            st.altair_chart(grafico, use_container_width=True)

# ================= AGENDA =================
elif menu == "Agenda de Atendimentos":
    st.title("📅 Agenda Semanal")

    estudantes = listar_estudantes()

    if estudantes:
        nomes = {e[0]: e[1] for e in estudantes}

        with st.form("agenda"):
            est_id = st.selectbox("Aluno", list(nomes.keys()), format_func=lambda x: nomes[x])
            data = st.date_input("Data")
            hora = st.time_input("Hora")
            obs = st.text_input("Observação")

            if st.form_submit_button("Agendar"):
                salvar_agenda(est_id, data.strftime("%d/%m/%Y"), str(hora), obs)
                st.success("Agendamento salvo")

    agenda = listar_agenda()

    if agenda:
        df = pd.DataFrame(agenda, columns=["ID","Aluno","Data","Hora","Observação"])
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Baixar Agenda",
            csv,
            "agenda.csv",
            "text/csv"
        )

# ================= RELATÓRIOS =================
elif menu == "Relatórios GRE":
    st.title("📄 Relatórios GRE")

    st.info("Base pronta. Próximo passo: geração automática de documentos.")

# ================= ADMIN =================
elif menu == "Administração":
    st.title("⚙️ Administração")

    if st.button("Backup geral"):
        conn = conectar()
        df = pd.read_sql_query("SELECT * FROM estudantes", conn)
        conn.close()

        st.download_button(
            "Baixar backup",
            df.to_csv(index=False),
            "backup.csv"
        )