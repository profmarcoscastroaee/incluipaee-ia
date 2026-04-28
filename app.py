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

======================================================
# CONFIGURAÇÃO DA API KEY
======================================================
def obter_api_key():
"""Busca a chave da OpenAI no ambiente local ou nos Secrets do Streamlit Cloud."""
try:
return os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
except Exception:
return os.getenv("OPENAI_API_KEY")

======================================================
BANCO DE DADOS
======================================================
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
        evolucao TEXT,
        encaminhamentos TEXT,
        FOREIGN KEY(estudante_id) REFERENCES estudantes(id)
    )
    """
)

# Migração simples: se o banco já existia sem a coluna evolucao, adiciona.
cursor.execute("PRAGMA table_info(atendimentos)")
colunas = [col[1] for col in cursor.fetchall()]
if "evolucao" not in colunas:
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
cursor.execute("DELETE FROM paees WHERE estudante_id=?", (estudante_id,))
cursor.execute("DELETE FROM avaliacoes WHERE estudante_id=?", (estudante_id,))
cursor.execute("DELETE FROM estudantes WHERE id=?", (estudante_id,))
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

def salvar_atendimento(
estudante_id,
data_atendimento,
objetivo,
atividade,
resposta_estudante,
avancos,
dificuldades,
evolucao,
encaminhamentos,
):
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
"""
return texto

======================================================
IA
======================================================
def gerar_paee_sem_ia(estudante, avaliacao):
codigo, ano_serie, turma, perfil, observacoes = estudante[1], estudante[2], estudante[3], estudante[4], estudante[5]
data_registro, barreiras, potencialidades, comunicacao, interacao, autonomia, aprendizagem, resumo_laudo = avaliacao

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

Recursos específicos devem ser definidos conforme observação pedagógica e resposta do estudante.

13. Avaliação e acompanhamento
Registrar avanços, dificuldades, participação, autonomia e resposta às estratégias utilizadas.

Revisar o PAEE periodicamente, considerando a evolução do estudante.

Data da avaliação utilizada: {data_registro}
"""

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

Utilizar exclusivamente a expressão “Código interno” para identificação do estudante.

Usar “Data de elaboração” como referência temporal do documento.

Evitar termos imprecisos, ambiguidades de gênero e repetições desnecessárias.

Não incluir título principal do documento.

REGRA SOBRE TEA SEM NÍVEL:
Se o perfil educacional for TEA e o nível de suporte não estiver informado, adotar provisoriamente abordagem equivalente ao nível II (suporte moderado), sem afirmar diagnóstico clínico.

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

Identificação do estudante

Caracterização pedagógica

Necessidades educacionais específicas

Barreiras identificadas

Potencialidades

Objetivos gerais e específicos do AEE

Estratégias pedagógicas

Recursos de acessibilidade e tecnologias assistivas

Sugestões de tecnologias educacionais inclusivas

impressão 3D

robótica educacional

jogos digitais

recursos maker

comunicação alternativa e aumentativa

materiais táteis, visuais e manipuláveis

atividades plugadas e desplugadas

Como aplicar essas tecnologias no atendimento

Organização do atendimento

Articulação com família e professores

Avaliação e acompanhamento

Recomendações para revisão do plano

Adaptação automática conforme o perfil educacional

Evolução do estudante com base nos atendimentos

Responsável pelo AEE:
Nome: ___________________________________________
Função: Professor(a) do Atendimento Educacional Especializado (AEE)
Assinatura: _______________________________________

Coordenação pedagógica:
Nome: ___________________________________________
Cargo: Coordenação Pedagógica
Assinatura: _______________________________________

Data de elaboração: dd/mm/aaaa

Na seção 16, descrever:

principais avanços observados;

dificuldades que permanecem;

estratégias que funcionaram melhor;

tecnologias que tiveram melhor resposta;

ajustes recomendados para os próximos atendimentos;

indicativos de autonomia, comunicação, interação e aprendizagem.

Não inventar evolução. Usar apenas os dados registrados nos atendimentos.
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

NÃO inventar informações.

Usar somente dados reais.

Se os dados forem fracos, dizer claramente.

ESTRUTURA DO RELATÓRIO:

Síntese da evolução do estudante

Análise dos avanços

Análise das dificuldades

Qualidade dos registros pedagógicos
Classificar como: Alta, Média ou Baixa.

Principais problemas identificados nos registros

Recomendações para melhoria dos registros

Recomendações pedagógicas para o AEE

Conclusão técnica

IMPORTANTE:
Se os registros forem fracos, dizer explicitamente isso.
"""

client = OpenAI(api_key=api_key)
resposta = client.responses.create(
    model="gpt-4.1-mini",
    input=prompt,
)
return resposta.output_text
======================================================
PDF
======================================================
def gerar_pdf_paee(conteudo, codigo):
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

caminho = f"PAEE_{codigo}.pdf"

doc = SimpleDocTemplate(
    caminho,
    pagesize=A4,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40
)

styles = getSampleStyleSheet()

titulo_style = ParagraphStyle(
    name="Titulo",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=16,
    spaceAfter=16,
    textColor=colors.black
)

secao_style = ParagraphStyle(
    name="Secao",
    parent=styles["Heading2"],
    fontSize=13,
    spaceBefore=10,
    spaceAfter=6,
    textColor=colors.darkblue
)

normal_style = ParagraphStyle(
    name="NormalCustom",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    spaceAfter=6
)

rodape_style = ParagraphStyle(
    name="Rodape",
    parent=styles["Normal"],
    fontSize=9,
    alignment=TA_CENTER,
    textColor=colors.grey,
    spaceBefore=20
)

elementos = []

elementos.append(Paragraph(
    "<b>Universidade Federal Rural de Pernambuco<br/>"
    "LabTec3DI – Laboratório de Tecnologias 3D e Inclusivas</b>",
    normal_style
))
elementos.append(Spacer(1, 8))
elementos.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
elementos.append(Spacer(1, 12))
elementos.append(Paragraph("PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO (PAEE)", titulo_style))
#🔥 título dinâmico
    if "Relatorio" in codigo or "relatorio" in codigo:
    titulo_doc = "RELATÓRIO DE EVOLUÇÃO E QUALIDADE DO ATENDIMENTO"
else:
    titulo_doc = "PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO (PAEE)"

    elementos.append(Paragraph(titulo_doc, titulo_style))

for linha in conteudo.split("\n"):
    linha = linha.strip()

    if "plano de atendimento educacional especializado" in linha.lower() or "(paee)" in linha.lower():
        continue

    if linha in ["--", "• --", "---"]:
        continue

    if not linha:
        elementos.append(Spacer(1, 6))
    elif linha.startswith("#"):
        elementos.append(Paragraph(f"<b>{linha.replace('#','').strip()}</b>", secao_style))
    elif linha.startswith("**") and linha.endswith("**"):
        elementos.append(Paragraph(f"<b>{linha.replace('**','')}</b>", normal_style))
    elif linha.startswith("-"):
        elementos.append(Paragraph(f"• {linha[1:].strip()}", normal_style))
    else:
        elementos.append(Paragraph(linha, normal_style))

elementos.append(Spacer(1, 20))
elementos.append(Paragraph("Elaborado com apoio do LabTec3DI – UFRPE", rodape_style))
doc.build(elementos)

return caminho
======================================================
INTERFACE STREAMLIT
======================================================
st.set_page_config(
page_title="IncluiPAEE IA",
page_icon="🧠",
layout="wide"
)

criar_tabelas()

st.markdown("""

st.markdown("""

tab1, tab2, tab3, tab4, tab5 = st.tabs([
"1. Cadastro",
"2. Avaliação Pedagógica",
"3. Gerar PAEE",
"4. Atendimentos",
"5. Relatório IA"
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

st.markdown("---")
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
    )
else:
    st.info("Nenhum estudante cadastrado ainda.")

st.markdown("---")
st.markdown("### ✏️ Editar cadastro do estudante")

estudantes = listar_estudantes()

if estudantes:
    opcoes_editar = {f"{e[1]} - {e[2]} - {e[4]}": e[0] for e in estudantes}
    selecionado_editar = st.selectbox(
        "Selecione o estudante para editar",
        list(opcoes_editar.keys()),
        key="editar_estudante"
    )

    estudante_id_editar = opcoes_editar[selecionado_editar]
    estudante_editar = buscar_estudante(estudante_id_editar)

    perfil_atual = estudante_editar[4] if estudante_editar[4] in PERFIS else "Não informado"

    with st.form("form_editar_estudante"):
        col1, col2 = st.columns(2)

        with col1:
            codigo_edit = st.text_input(
                "Código interno",
                value=estudante_editar[1],
                key="edit_codigo"
            )
            ano_edit = st.text_input(
                "Ano/Série",
                value=estudante_editar[2],
                key="edit_ano"
            )

        with col2:
            turma_edit = st.text_input(
                "Turma",
                value=estudante_editar[3],
                key="edit_turma"
            )
            perfil_edit = st.selectbox(
                "Perfil educacional",
                PERFIS,
                index=PERFIS.index(perfil_atual),
                key="edit_perfil"
            )

        observacoes_edit = st.text_area(
            "Observações pedagógicas iniciais",
            value=estudante_editar[5] or "",
            key="edit_observacoes"
        )

        atualizar = st.form_submit_button("💾 Atualizar cadastro")

        if atualizar:
            try:
                atualizar_estudante(
                    estudante_id_editar,
                    codigo_edit.strip(),
                    ano_edit,
                    turma_edit,
                    perfil_edit,
                    observacoes_edit
                )
                st.success("Cadastro atualizado com sucesso.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Este código interno já está sendo usado por outro estudante.")

    st.markdown("---")
    st.markdown("### 🗑️ Excluir estudante")

    confirmar = st.checkbox(
        "Confirmar exclusão do estudante selecionado",
        key="confirmar_exclusao_estudante"
    )

    if st.button("Excluir estudante", key="btn_excluir_estudante"):
        if confirmar:
            excluir_estudante(estudante_id_editar)
            st.success("Estudante excluído com sucesso.")
            st.rerun()
        else:
            st.warning("Marque a confirmação antes de excluir.")
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
        barreiras = st.text_area("Barreiras enfrentadas pelo estudante", key="av_barreiras")
        potencialidades = st.text_area("Potencialidades e habilidades já desenvolvidas", key="av_potencialidades")
        comunicacao = st.text_area("Comunicação", key="av_comunicacao")
        interacao = st.text_area("Interação social", key="av_interacao")
        autonomia = st.text_area("Autonomia", key="av_autonomia")
        aprendizagem = st.text_area("Aprendizagem", key="av_aprendizagem")
        resumo_laudo = st.text_area(
            "Resumo pedagógico do laudo, sem identificação",
            placeholder="Ex.: O laudo informa TEA e aponta necessidade de previsibilidade, apoio visual e mediação nas interações.",
            key="av_resumo"
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

        if st.button("Gerar sugestão de PAEE", key="btn_gerar_paee"):
            with st.spinner("Gerando PAEE..."):
                try:
                    paee = gerar_paee_com_ia(estudante, avaliacao)
                    st.session_state["paee_gerado"] = paee
                    salvar_paee(estudante_id, paee)
                    st.success("PAEE gerado e salvo no histórico.")
                except Exception as erro:
                    st.error(f"Erro ao gerar PAEE: {erro}")

        if "paee_gerado" in st.session_state:
            st.subheader("PAEE gerado")
            st.text_area("Conteúdo", st.session_state["paee_gerado"], height=600, key="txt_paee_gerado")

            st.download_button(
                "Baixar PAEE em .txt",
                data=st.session_state["paee_gerado"],
                file_name=f"PAEE_{estudante[1]}.txt",
                mime="text/plain",
                key="download_txt_paee"
            )

            if st.button("Gerar PDF", key="btn_gerar_pdf"):
                arquivo = gerar_pdf_paee(st.session_state["paee_gerado"], estudante[1])

                with open(arquivo, "rb") as f:
                    st.download_button(
                        "Baixar PAEE em PDF",
                        f,
                        file_name=f"PAEE_{estudante[1]}.pdf",
                        mime="application/pdf",
                        key="download_pdf_paee"
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
        data_atendimento = st.date_input("Data do atendimento", key="at_data")
        objetivo = st.text_area("Objetivo trabalhado", key="at_objetivo")
        atividade = st.text_area("Atividade realizada", key="at_atividade")
        resposta_estudante = st.text_area("Resposta do estudante", key="at_resposta")
        avancos = st.text_area("Avanços observados", key="at_avancos")
        dificuldades = st.text_area("Dificuldades observadas", key="at_dificuldades")
        evolucao = st.text_area("Evolução observada", key="at_evolucao")
        encaminhamentos = st.text_area("Encaminhamentos", key="at_encaminhamentos")
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
            st.rerun()

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
with tab5:
st.header("Relatório de evolução e qualidade do atendimento")

   estudantes = listar_estudantes()

      if not estudantes:
       st.info("Cadastre um estudante primeiro.")
    else:
        opcoes = {f"{e[1]} - {e[2]} - {e[4]}": e[0] for e in estudantes}

    selecionado = st.selectbox(
        "Selecione o estudante",
        list(opcoes.keys()),
        key="relatorio_estudante"
    )

    estudante_id = opcoes[selecionado]
    estudante = buscar_estudante(estudante_id)
    avaliacao = ultima_avaliacao(estudante_id)

    if st.button("Gerar relatório de evolução", key="btn_relatorio"):
        with st.spinner("Analisando atendimentos..."):
            relatorio = gerar_relatorio_evolucao(estudante, avaliacao)
            st.session_state["relatorio_evolucao"] = relatorio

    # 🔥 AQUI ESTAVA O ERRO DE INDENTAÇÃO
    if "relatorio_evolucao" in st.session_state:
        relatorio = st.session_state["relatorio_evolucao"]

        st.text_area("Relatório", relatorio, height=500)

        # TXT
        st.download_button(
            "Baixar relatório em .txt",
            data=relatorio,
            file_name=f"Relatorio_{estudante[1]}.txt",
            mime="text/plain",
        )

        # PDF
        if st.button("Gerar PDF do relatório"):
            arquivo = gerar_pdf_paee(relatorio, f"Relatorio_{estudante[1]}")

            with open(arquivo, "rb") as f:
                st.download_button(
                    "Baixar relatório em PDF",
                    f,
                    file_name=f"Relatorio_{estudante[1]}.pdf",
                    mime="application/pdf",
                )
