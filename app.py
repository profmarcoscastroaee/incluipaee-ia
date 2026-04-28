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
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudante_id INTEGER NOT NULL,
            data_atendimento TEXT,
            objetivo TEXT,
            atividade TEXT,
            resposta_estudante TEXT,
            avancos TEXT,
            dificuldades TEXT,
            encaminhamentos TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

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
        (codigo, ano_serie, turma, perfil, observacoes, datetime.now().strftime("%d/%m/%Y %H:%M")),
    )
    conn.commit()
    conn.close()


def listar_estudantes():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, ano_serie, turma, perfil FROM estudantes ORDER BY codigo")
    dados = cursor.fetchall()
    conn.close()
    return dados


def buscar_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo, ano_serie, turma, perfil, observacoes FROM estudantes WHERE id = ?", (estudante_id,))
    dado = cursor.fetchone()
    conn.close()
    return dado


def salvar_avaliacao(estudante_id, barreiras, potencialidades, comunicacao, interacao, autonomia, aprendizagem, resumo_laudo):
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


def salvar_paee(estudante_id, conteudo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO paees (estudante_id, data_geracao, conteudo) VALUES (?, ?, ?)",
        (estudante_id, datetime.now().strftime("%d/%m/%Y %H:%M"), conteudo),
    )
    conn.commit()
    conn.close()


def salvar_atendimento(estudante_id, data_atendimento, objetivo, atividade, resposta_estudante, avancos, dificuldades, encaminhamentos):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO atendimentos (
            estudante_id, data_atendimento, objetivo, atividade,
            resposta_estudante, avancos, dificuldades, encaminhamentos
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (estudante_id, data_atendimento, objetivo, atividade, resposta_estudante, avancos, dificuldades, encaminhamentos),
    )
    conn.commit()
    conn.close()


def listar_atendimentos(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT data_atendimento, objetivo, atividade, resposta_estudante, avancos, dificuldades, encaminhamentos
        FROM atendimentos
        WHERE estudante_id = ?
        ORDER BY data_atendimento DESC
        """,
        (estudante_id,),
    )
    dados = cursor.fetchall()
    conn.close()
    return dados


# ======================================================
# IA
# ======================================================

def gerar_paee_sem_ia(estudante, avaliacao):
    codigo, ano_serie, turma, perfil, observacoes = estudante[1], estudante[2], estudante[3], estudante[4], estudante[5]
    data_registro, barreiras, potencialidades, comunicacao, interacao, autonomia, aprendizagem, resumo_laudo = avaliacao

    return f"""
# PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO - PAEE

## 1. Identificação do estudante
- Código interno: {codigo}
- Ano/Série: {ano_serie}
- Turma: {turma}
- Perfil educacional informado: {perfil}

> Observação: este documento utiliza código interno para preservar a identidade do estudante.

## 2. Caracterização pedagógica inicial
{observacoes or 'Não informado.'}

## 3. Síntese pedagógica do laudo ou informações complementares
{resumo_laudo or 'Não informado.'}

## 4. Barreiras identificadas
{barreiras or 'Não informado.'}

## 5. Potencialidades do estudante
{potencialidades or 'Não informado.'}

## 6. Comunicação
{comunicacao or 'Não informado.'}

## 7. Interação social
{interacao or 'Não informado.'}

## 8. Autonomia
{autonomia or 'Não informado.'}

## 9. Aprendizagem
{aprendizagem or 'Não informado.'}

## 10. Objetivos do AEE
- Ampliar as condições de acesso, participação e aprendizagem do estudante nas atividades escolares.
- Desenvolver estratégias que favoreçam comunicação, autonomia, interação e organização da rotina escolar.
- Utilizar recursos pedagógicos acessíveis, materiais concretos e tecnologias educacionais inclusivas conforme as necessidades observadas.

## 11. Estratégias pedagógicas sugeridas
- Utilizar rotina visual, instruções objetivas e organização antecipada das atividades.
- Propor atividades com materiais concretos, jogos pedagógicos, recursos visuais e tecnologias digitais.
- Articular as ações do AEE com os professores do ensino comum.
- Registrar os avanços e dificuldades após cada atendimento.

## 12. Recursos de acessibilidade e tecnologia assistiva
- Pranchas visuais, cartões de comunicação, materiais táteis, objetos 3D, jogos adaptados e recursos digitais.
- Recursos específicos devem ser definidos conforme observação pedagógica e resposta do estudante.

## 13. Organização do atendimento
- Modalidade: individual ou em pequeno grupo, conforme necessidade.
- Periodicidade: definir conforme carga horária do AEE e planejamento escolar.
- Registro: acompanhamento contínuo em diário de atendimento.

## 14. Articulação com família e professores
- Realizar escuta da família para compreender rotina, interesses e necessidades.
- Dialogar com professores do ensino comum para alinhar estratégias e adaptações.

## 15. Avaliação e acompanhamento
- Registrar avanços, dificuldades, participação, autonomia e resposta às estratégias utilizadas.
- Revisar o PAEE periodicamente, considerando a evolução do estudante.

Data da avaliação utilizada: {data_registro}
"""


def gerar_paee_com_ia(estudante, avaliacao):
    if OpenAI is None or not os.getenv("OPENAI_API_KEY"):
        return gerar_paee_sem_ia(estudante, avaliacao)

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

Elabore uma sugestão de PAEE com linguagem técnica, objetiva e pedagógica.
Não invente diagnóstico. Não use nome de estudante. Use apenas o código interno.
Não apresente condutas médicas. Foque em barreiras, potencialidades, objetivos, estratégias pedagógicas, acessibilidade, tecnologia assistiva e acompanhamento.

DADOS DO ESTUDANTE:
{estudante_txt}

AVALIAÇÃO PEDAGÓGICA:
{avaliacao_txt}

Estruture o documento com:
1. Identificação do estudante
2. Caracterização pedagógica
3. Necessidades educacionais específicas
4. Barreiras identificadas
5. Potencialidades
6. Objetivos gerais e específicos do AEE
7. Estratégias pedagógicas
8. Recursos de acessibilidade e tecnologias assistivas
9. Organização do atendimento
10. Articulação com família e professores
11. Avaliação e acompanhamento
12. Recomendações para revisão do plano
"""

    client = OpenAI()
    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return resposta.output_text


# ======================================================
# INTERFACE STREAMLIT
# ======================================================

st.set_page_config(page_title="IncluiPAEE IA", page_icon="🧩", layout="wide")
criar_tabelas()

st.title("IncluiPAEE IA")
st.caption("Sistema inicial para elaboração, organização e acompanhamento do PAEE no AEE")

st.warning(
    "Use apenas código interno do estudante. Não insira nome completo, CPF, endereço, telefone, documentos pessoais ou dados que identifiquem diretamente o aluno."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Cadastro",
    "2. Avaliação Pedagógica",
    "3. Gerar PAEE",
    "4. Atendimentos"
])

with tab1:
    st.header("Cadastro do estudante")
    with st.form("form_cadastro"):
        codigo = st.text_input("Código interno do estudante", placeholder="Ex.: AEE-001")
        ano_serie = st.text_input("Ano/Série", placeholder="Ex.: 4º ano")
        turma = st.text_input("Turma", placeholder="Ex.: 4º ano B")
        perfil = st.selectbox(
            "Perfil educacional informado",
            [
                "Não informado",
                "Deficiência intelectual",
                "Deficiência visual",
                "Deficiência auditiva/surdez",
                "Deficiência física",
                "TEA",
                "Altas habilidades/superdotação",
                "Deficiência múltipla",
                "Outro",
            ],
        )
        observacoes = st.text_area("Observações pedagógicas iniciais")
        enviar = st.form_submit_button("Cadastrar estudante")

        if enviar:
            if not codigo.strip():
                st.error("Informe um código interno para o estudante.")
            else:
                try:
                    cadastrar_estudante(codigo.strip(), ano_serie, turma, perfil, observacoes)
                    st.success("Estudante cadastrado com sucesso.")
                except sqlite3.IntegrityError:
                    st.error("Este código já existe. Use outro código interno.")

    st.subheader("Estudantes cadastrados")
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
                }
                for e in estudantes
            ],
            use_container_width=True,
        )
    else:
        st.info("Nenhum estudante cadastrado ainda.")

with tab2:
    st.header("Avaliação pedagógica inicial")
    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        opcoes = {f"{e[1]} - {e[2]} - {e[4]}": e[0] for e in estudantes}
        selecionado = st.selectbox("Selecione o estudante", list(opcoes.keys()), key="avaliacao_estudante")
        estudante_id = opcoes[selecionado]

        with st.form("form_avaliacao"):
            barreiras = st.text_area("Barreiras enfrentadas pelo estudante")
            potencialidades = st.text_area("Potencialidades e habilidades já desenvolvidas")
            comunicacao = st.text_area("Comunicação")
            interacao = st.text_area("Interação social")
            autonomia = st.text_area("Autonomia")
            aprendizagem = st.text_area("Aprendizagem")
            resumo_laudo = st.text_area(
                "Resumo pedagógico do laudo, sem identificação",
                placeholder="Ex.: O laudo informa TEA e aponta necessidade de previsibilidade, apoio visual e mediação nas interações.",
            )
            enviar = st.form_submit_button("Salvar avaliação")

            if enviar:
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
                st.success("Avaliação pedagógica salva com sucesso.")

with tab3:
    st.header("Gerar PAEE com IA")
    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        opcoes = {f"{e[1]} - {e[2]} - {e[4]}": e[0] for e in estudantes}
        selecionado = st.selectbox("Selecione o estudante", list(opcoes.keys()), key="paee_estudante")
        estudante_id = opcoes[selecionado]
        estudante = buscar_estudante(estudante_id)
        avaliacao = ultima_avaliacao(estudante_id)

        if not avaliacao:
            st.warning("Este estudante ainda não possui avaliação pedagógica registrada.")
        else:
            usar_ia = OpenAI is not None and bool(os.getenv("OPENAI_API_KEY"))
            if usar_ia:
                st.success("IA ativada: a variável OPENAI_API_KEY foi encontrada.")
            else:
                st.info("IA não configurada. O sistema irá gerar um PAEE-base automático sem conexão com IA.")

            if st.button("Gerar sugestão de PAEE"):
                with st.spinner("Gerando PAEE..."):
                    paee = gerar_paee_com_ia(estudante, avaliacao)
                    st.session_state["paee_gerado"] = paee
                    salvar_paee(estudante_id, paee)
                    st.success("PAEE gerado e salvo no histórico.")

            if "paee_gerado" in st.session_state:
                st.subheader("PAEE gerado")
                st.text_area("Conteúdo", st.session_state["paee_gerado"], height=600)
                st.download_button(
                    "Baixar PAEE em .txt",
                    data=st.session_state["paee_gerado"],
                    file_name=f"PAEE_{estudante[1]}.txt",
                    mime="text/plain",
                )

with tab4:
    st.header("Registro dos atendimentos")
    estudantes = listar_estudantes()
    if not estudantes:
        st.info("Cadastre um estudante primeiro.")
    else:
        opcoes = {f"{e[1]} - {e[2]} - {e[4]}": e[0] for e in estudantes}
        selecionado = st.selectbox("Selecione o estudante", list(opcoes.keys()), key="atendimento_estudante")
        estudante_id = opcoes[selecionado]

        with st.form("form_atendimento"):
            data_atendimento = st.date_input("Data do atendimento")
            objetivo = st.text_area("Objetivo trabalhado")
            atividade = st.text_area("Atividade realizada")
            resposta_estudante = st.text_area("Resposta do estudante")
            avancos = st.text_area("Avanços observados")
            dificuldades = st.text_area("Dificuldades observadas")
            encaminhamentos = st.text_area("Encaminhamentos")
            enviar = st.form_submit_button("Salvar atendimento")

            if enviar:
                salvar_atendimento(
                    estudante_id,
                    data_atendimento.strftime("%d/%m/%Y"),
                    objetivo,
                    atividade,
                    resposta_estudante,
                    avancos,
                    dificuldades,
                    encaminhamentos,
                )
                st.success("Atendimento registrado com sucesso.")

        st.subheader("Histórico de atendimentos")
        atendimentos = listar_atendimentos(estudante_id)
        if atendimentos:
            for item in atendimentos:
                with st.expander(f"Atendimento em {item[0]}"):
                    st.markdown(f"**Objetivo:** {item[1]}")
                    st.markdown(f"**Atividade:** {item[2]}")
                    st.markdown(f"**Resposta do estudante:** {item[3]}")
                    st.markdown(f"**Avanços:** {item[4]}")
                    st.markdown(f"**Dificuldades:** {item[5]}")
                    st.markdown(f"**Encaminhamentos:** {item[6]}")
        else:
            st.info("Nenhum atendimento registrado para este estudante.")
