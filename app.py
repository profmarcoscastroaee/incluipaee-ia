import os
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

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


def coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return coluna in [linha[1] for linha in cursor.fetchall()]


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
            evolucao TEXT,
            encaminhamentos TEXT,
            FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
        )
        """
    )

    # Migração simples para bancos antigos que foram criados sem a coluna evolucao.
    if not coluna_existe(cursor, "atendimentos", "evolucao"):
        cursor.execute("ALTER TABLE atendimentos ADD COLUMN evolucao TEXT")

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
    cursor.execute(
        "SELECT id, codigo, ano_serie, turma, perfil, observacoes FROM estudantes WHERE id = ?",
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
        SET codigo = ?, ano_serie = ?, turma = ?, perfil = ?, observacoes = ?
        WHERE id = ?
        """,
        (codigo, ano_serie, turma, perfil, observacoes, estudante_id),
    )
    conn.commit()
    conn.close()


def excluir_estudante(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM atendimentos WHERE estudante_id = ?", (estudante_id,))
    cursor.execute("DELETE FROM avaliacoes WHERE estudante_id = ?", (estudante_id,))
    cursor.execute("DELETE FROM paees WHERE estudante_id = ?", (estudante_id,))
    cursor.execute("DELETE FROM estudantes WHERE id = ?", (estudante_id,))
    conn.commit()
    conn.close()


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


def salvar_atendimento(estudante_id, data_atendimento, objetivo, atividade, resposta_estudante, avancos, dificuldades, evolucao, encaminhamentos):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO atendimentos (
            estudante_id, data_atendimento, objetivo, atividade,
            resposta_estudante, avancos, dificuldades, evolucao, encaminhamentos
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            encaminhamentos,
        ),
    )
    conn.commit()
    conn.close()


def listar_atendimentos(estudante_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT data_atendimento, objetivo, atividade, resposta_estudante,
               avancos, dificuldades, evolucao, encaminhamentos
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
    for a in atendimentos[:5]:
        texto += f"""
Data: {a[0]}
Objetivo: {a[1]}
Atividade: {a[2]}
Resposta: {a[3]}
Avanços: {a[4]}
Dificuldades: {a[5]}
Evolução observada: {a[6]}
Encaminhamentos: {a[7]}
--------------------
"""
    return texto


# ======================================================
# IA E GERAÇÃO DO PAEE
# ======================================================

def gerar_paee_sem_ia(estudante, avaliacao):
    codigo = estudante[1]
    ano_serie = estudante[2]
    turma = estudante[3]
    perfil = estudante[4]
    observacoes = estudante[5]

    data_registro = avaliacao[0]
    barreiras = avaliacao[1]
    potencialidades = avaliacao[2]
    comunicacao = avaliacao[3]
    interacao = avaliacao[4]
    autonomia = avaliacao[5]
    aprendizagem = avaliacao[6]
    resumo_laudo = avaliacao[7]

    historico = listar_atendimentos_texto(estudante[0])

    return f"""
1. Identificação do estudante
Código interno: {codigo}
Ano/Série: {ano_serie or 'Não informado.'}
Turma: {turma or 'Não informado.'}
Perfil educacional informado: {perfil or 'Não informado.'}
Data de elaboração: {datetime.now().strftime('%d/%m/%Y')}

2. Caracterização pedagógica
{observacoes or 'Não informado.'}

3. Síntese pedagógica do laudo ou informações complementares
{resumo_laudo or 'Não informado.'}

4. Barreiras identificadas
{barreiras or 'Não informado.'}

5. Potencialidades
{potencialidades or 'Não informado.'}

6. Comunicação
{comunicacao or 'Não informado.'}

7. Interação social
{interacao or 'Não informado.'}

8. Autonomia
{autonomia or 'Não informado.'}

9. Aprendizagem
{aprendizagem or 'Não informado.'}

10. Objetivo geral
Ampliar as condições de acesso, participação, comunicação, autonomia e aprendizagem do estudante no contexto escolar, considerando as barreiras e potencialidades registradas.

11. Objetivos específicos
- Favorecer a participação do estudante nas atividades escolares.
- Desenvolver estratégias de comunicação, organização e autonomia.
- Utilizar materiais concretos, recursos acessíveis e tecnologias educacionais inclusivas.
- Registrar sistematicamente avanços, dificuldades e encaminhamentos.

12. Estratégias pedagógicas
- Utilizar linguagem objetiva, rotina estruturada e mediação pedagógica conforme a necessidade observada.
- Propor atividades com materiais concretos, manipuláveis, visuais, táteis ou digitais.
- Articular as ações do AEE com os professores do ensino comum.
- Revisar as estratégias conforme a resposta do estudante aos atendimentos.

13. Recursos de acessibilidade e tecnologias assistivas
- Materiais concretos e manipuláveis.
- Recursos visuais, táteis e digitais acessíveis.
- Jogos pedagógicos e atividades plugadas e desplugadas.
- Impressão 3D, robótica educacional e recursos maker quando estiverem diretamente relacionados aos objetivos pedagógicos.

14. Histórico de atendimentos registrado
{historico}

15. Avaliação e acompanhamento
A avaliação deverá ocorrer de forma contínua, com registros após cada atendimento. Os registros devem indicar objetivo, atividade realizada, resposta do estudante, avanços, dificuldades, evolução observada e encaminhamentos.

16. Recomendações para revisão do plano
Recomenda-se revisar este PAEE periodicamente, considerando novas avaliações pedagógicas, evolução do estudante, necessidades observadas e articulação com família, professores e equipe pedagógica.

17. Responsável pelo AEE
Nome: ___________________________________________
Função: Professor(a) do Atendimento Educacional Especializado (AEE)
Assinatura: _______________________________________

18. Coordenação pedagógica
Nome: ___________________________________________
Cargo: Coordenação Pedagógica
Assinatura: _______________________________________

Data da avaliação utilizada: {data_registro}
"""


def gerar_relatorio_evolucao(estudante, avaliacao):
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
5. Principais problemas identificados nos registros
6. Recomendações para melhoria dos registros
7. Recomendações pedagógicas para o AEE
8. Conclusão técnica
"""

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return resposta.output_text


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

Utilize linguagem pedagógica formal, clara e tecnicamente correta.
Não invente diagnóstico. Não use nome de estudante. Use apenas o código interno.
Não apresente condutas médicas. Foque em barreiras, potencialidades, objetivos, estratégias pedagógicas, acessibilidade, tecnologia assistiva e acompanhamento.

REGRAS DE PADRONIZAÇÃO:
- Utilizar exclusivamente a expressão “Código interno”.
- Empregar “Data de elaboração”.
- Padronizar títulos com letras minúsculas após a primeira palavra.
- Evitar termos imprecisos, ambiguidades de gênero e repetições.
- Não incluir título principal do documento.

REGRA CRÍTICA SOBRE ATENDIMENTOS:
A análise da evolução deve usar exclusivamente os dados reais do histórico de atendimentos.
É proibido inventar avanços, inferir melhorias não registradas ou criar evolução genérica.
Se os dados forem insuficientes, escreva claramente:
“Os registros de atendimento ainda são limitados para uma análise evolutiva consistente, sendo necessário ampliar o acompanhamento pedagógico.”

DADOS DO ESTUDANTE:
{estudante_txt}

AVALIAÇÃO PEDAGÓGICA:
{avaliacao_txt}

HISTÓRICO DE ATENDIMENTOS:
{historico_txt}

Estruture o documento com as seguintes seções:
1. Identificação do estudante
2. Caracterização pedagógica
3. Necessidades educacionais específicas
4. Barreiras identificadas
5. Potencialidades
6. Objetivo geral
7. Objetivos específicos
8. Estratégias pedagógicas
9. Recursos de acessibilidade e tecnologias assistivas
10. Sugestões de tecnologias educacionais inclusivas
11. Como aplicar essas tecnologias no atendimento
12. Organização do atendimento
13. Articulação com família e professores
14. Avaliação e acompanhamento
15. Evolução do estudante com base nos atendimentos
16. Recomendações para revisão do plano
17. Adaptação automática conforme o perfil educacional
18. Responsável pelo AEE
19. Coordenação pedagógica
20. Data de elaboração

Na seção de tecnologias educacionais inclusivas, indique somente recursos coerentes com as necessidades, potencialidades, barreiras e interesses do estudante. Para cada tecnologia sugerida, explique objetivo pedagógico, forma de aplicação no AEE, material necessário, cuidado de acessibilidade e como avaliar se funcionou.

Para TEA sem nível informado, indique abordagem pedagógica provisória equivalente ao nível II, com justificativa pedagógica e necessidade de avaliação complementar.
Para altas habilidades/superdotação, abordar enriquecimento curricular, desafios cognitivos, criatividade e autonomia.
Para deficiência visual, abordar recursos táteis, audiodescrição, acessibilidade digital e impressão 3D.
Para deficiência intelectual, abordar atividades concretas, linguagem simplificada, repetição estruturada e materiais manipuláveis.
"""

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return resposta.output_text


# ======================================================
# PDF
# ======================================================

def gerar_pdf_paee(conteudo, codigo):
    caminho = f"PAEE_{codigo}.pdf"

    doc = SimpleDocTemplate(
        caminho,
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
        spaceAfter=16,
        textColor=colors.black,
    )

    secao_style = ParagraphStyle(
        name="Secao",
        parent=styles["Heading2"],
        fontSize=13,
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
    elementos.append(Paragraph("PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO (PAEE)", titulo_style))

    for linha in conteudo.split("\n"):
        linha = linha.strip()

        if not linha:
            elementos.append(Spacer(1, 6))
            continue

        linha_lower = linha.lower()
        if "plano de atendimento educacional especializado" in linha_lower or linha_lower == "paee":
            continue

        if linha in ["--", "• --", "---"]:
            continue

        # Trata títulos numerados: 1. Identificação do estudante
        if linha[:2].replace(".", "").isdigit() and "." in linha[:4]:
            elementos.append(Paragraph(f"<b>{linha}</b>", secao_style))
        elif linha.startswith("#"):
            elementos.append(Paragraph(f"<b>{linha.replace('#', '').strip()}</b>", secao_style))
        elif linha.startswith("**") and linha.endswith("**"):
            elementos.append(Paragraph(f"<b>{linha.replace('**', '')}</b>", normal_style))
        elif linha.startswith("-"):
            elementos.append(Paragraph(f"• {linha[1:].strip()}", normal_style))
        else:
            elementos.append(Paragraph(linha, normal_style))

    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Elaborado com apoio do LabTec3DI – UFRPE", rodape_style))

    doc.build(elementos)
    return caminho


# ======================================================
# INTERFACE STREAMLIT
# ======================================================

st.set_page_config(page_title="IncluiPAEE IA", page_icon="🧠", layout="wide")

criar_tabelas()

st.markdown(
    """
<h1 style='margin-bottom:0;'>🧠 IncluiPAEE IA</h1>
<p style='color:gray; margin-top:0; font-size:16px;'>
Sistema inteligente para elaboração, organização e acompanhamento do PAEE no AEE
</p>
<hr>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="
padding:15px;
border-radius:10px;
background-color:#FFF3CD;
border:1px solid #FFEEBA;
color:#856404;
font-size:14px;
">
<b>⚠️ Atenção:</b> Utilize apenas código interno do estudante.
Não insira nome completo, CPF, endereço, telefone, documentos pessoais ou dados que identifiquem diretamente o aluno.
</div>
""",
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Cadastro",
    "2. Avaliação Pedagógica",
    "3. Gerar PAEE",
    "4. Atendimentos",
])

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

with tab1:
    st.markdown("### 👤 Cadastro do estudante")

    with st.form("form_cadastro"):
        codigo = st.text_input("Código interno do estudante", placeholder="Ex.: AEE-001")
        ano_serie = st.text_input("Ano/Série", placeholder="Ex.: 4º ano")
        turma = st.text_input("Turma", placeholder="Ex.: 4º ano B")
        perfil = st.selectbox("Perfil educacional informado", PERFIS)
        observacoes = st.text_area("Observações pedagógicas iniciais")
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

    st.markdown("---")
    st.markdown("### ✏️ Editar cadastro do estudante")

    estudantes = listar_estudantes()

    if estudantes:
        opcoes_editar = {f"{e[1]} - {e[2]} - {e[4]}": e[0] for e in estudantes}
        selecionado_editar = st.selectbox(
            "Selecione o estudante para editar",
            list(opcoes_editar.keys()),
            key="editar_estudante",
        )

        estudante_id_editar = opcoes_editar[selecionado_editar]
        estudante_editar = buscar_estudante(estudante_id_editar)

        if estudante_editar:
            perfil_atual = estudante_editar[4] if estudante_editar[4] in PERFIS else "Outro"
            indice_perfil = PERFIS.index(perfil_atual)

            with st.form("form_editar_estudante"):
                col1, col2 = st.columns(2)

                with col1:
                    codigo_edit = st.text_input(
                        "Código interno",
                        value=estudante_editar[1] or "",
                        key="edit_codigo",
                    )
                    ano_edit = st.text_input(
                        "Ano/Série",
                        value=estudante_editar[2] or "",
                        key="edit_ano",
                    )

                with col2:
                    turma_edit = st.text_input(
                        "Turma",
                        value=estudante_editar[3] or "",
                        key="edit_turma",
                    )
                    perfil_edit = st.selectbox(
                        "Perfil educacional",
                        PERFIS,
                        index=indice_perfil,
                        key="edit_perfil",
                    )

                observacoes_edit = st.text_area(
                    "Observações pedagógicas iniciais",
                    value=estudante_editar[5] or "",
                    key="edit_observacoes",
                )

                atualizar = st.form_submit_button("💾 Atualizar cadastro")

                if atualizar:
                    if not codigo_edit.strip():
                        st.error("Informe um código interno para o estudante.")
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

            st.markdown("---")
            st.markdown("### 🗑️ Excluir estudante")
            st.warning("A exclusão removerá o cadastro, avaliações, atendimentos e PAEE gerados para este estudante.")

            confirmar = st.checkbox(
                f"Confirmo que desejo excluir o estudante {estudante_editar[1]}",
                key="confirmar_exclusao",
            )

            if st.button("Excluir estudante", key="btn_excluir_estudante"):
                if confirmar:
                    excluir_estudante(estudante_id_editar)
                    st.success("Estudante excluído com sucesso.")
                    st.rerun()
                else:
                    st.warning("Marque a confirmação antes de excluir.")

        st.markdown("---")
        st.markdown("### 📋 Estudantes cadastrados")
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
            usar_ia = OpenAI is not None and bool(obter_api_key())

            if usar_ia:
                st.success("IA ativada: a variável OPENAI_API_KEY foi encontrada.")
            else:
                st.info("IA não configurada. O sistema irá gerar um PAEE-base automático sem conexão com IA.")

            if st.button("Gerar sugestão de PAEE"):
                with st.spinner("Gerando PAEE..."):
                    try:
                        paee = gerar_paee_com_ia(estudante, avaliacao)
                        st.session_state["paee_gerado"] = paee
                        st.session_state["paee_estudante_codigo"] = estudante[1]
                        salvar_paee(estudante_id, paee)
                        st.success("PAEE gerado e salvo no histórico.")
                    except Exception as erro:
                        st.error(f"Erro ao gerar PAEE: {erro}")

            if "paee_gerado" in st.session_state:
                codigo_arquivo = st.session_state.get("paee_estudante_codigo", estudante[1])
                st.subheader("PAEE gerado")
                st.text_area("Conteúdo", st.session_state["paee_gerado"], height=600)

                st.download_button(
                    "Baixar PAEE em .txt",
                    data=st.session_state["paee_gerado"],
                    file_name=f"PAEE_{codigo_arquivo}.txt",
                    mime="text/plain",
                )

                if st.button("Gerar PDF"):
                    arquivo = gerar_pdf_paee(st.session_state["paee_gerado"], codigo_arquivo)
                    with open(arquivo, "rb") as f:
                        st.download_button(
                            "Baixar PAEE em PDF",
                            f,
                            file_name=f"PAEE_{codigo_arquivo}.pdf",
                            mime="application/pdf",
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
            evolucao = st.text_area("Evolução observada")
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
                    evolucao,
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
                    st.markdown(f"**Evolução observada:** {item[6]}")
                    st.markdown(f"**Encaminhamentos:** {item[7]}")
        else:
            st.info("Nenhum atendimento registrado para este estudante.")
