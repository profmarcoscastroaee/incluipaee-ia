import os
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

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

def atualizar_estudante(estudante_id, codigo, ano_serie, turma, perfil, observacoes):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE estudantes
        SET codigo=?, ano_serie=?, turma=?, perfil=?, observacoes=?
        WHERE id=?
    """, (codigo, ano_serie, turma, perfil, observacoes, estudante_id))
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
    for a in atendimentos[:5]:  # últimos 5
        texto += f"""
Data: {a[0]}
Objetivo: {a[1]}
Atividade: {a[2]}
Resposta: {a[3]}
Avanços: {a[4]}
Dificuldades: {a[5]}
Encaminhamentos: {a[6]}
--------------------
"""
    return texto
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

Observação: este documento utiliza código interno para preservar a identidade do estudante.

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

## 16. Adaptação automática conforme o perfil educacional

Evite respostas genéricas. Todas as recomendações devem estar diretamente relacionadas aos dados do estudante.

Quando o nível de suporte do TEA não estiver informado, indicar que está sendo adotada uma abordagem pedagógica intermediária, equivalente ao nível II, de forma provisória, justificando essa escolha com base nas barreiras e necessidades observadas.

A IA deve evitar repetir o mesmo padrão de texto entre diferentes estudantes, variando a escrita conforme os dados analisados.

A IA deve analisar o perfil educacional informado e elaborar um texto descritivo explicando como o plano foi adaptado especificamente para esse estudante.

- Para TEA (nível I, II ou III), descrever o nível de suporte necessário e como isso impacta as estratégias, organização do ambiente, comunicação e uso de tecnologias.
- Para Altas habilidades/superdotação, descrever como o plano promove enriquecimento curricular, desafios cognitivos, criatividade e autonomia.
- Para deficiência visual, descrever adaptações com recursos táteis, audiodescrição, acessibilidade digital e uso de impressão 3D.
- Para deficiência intelectual, descrever adaptações com atividades concretas, linguagem simplificada, repetição estruturada e uso de materiais manipuláveis.

A seção deve:
- Ser escrita em formato de texto corrido (não apenas lista).
- Explicar o "porquê" das escolhas pedagógicas.
- Relacionar as adaptações com as tecnologias sugeridas (impressão 3D, robótica, jogos, etc.).
- Utilizar linguagem pedagógica adequada, evitando termos genéricos ou imprecisos. Preferir expressões como “materiais concretos e manipuláveis” em vez de termos informais.
- Considerar as barreiras e potencialidades do estudante.

Quando houver mais de um perfil ou dúvidas no perfil informado, a IA deve indicar a necessidade de avaliação complementar e sugerir estratégias flexíveis.

Data da avaliação utilizada: {data_registro}
"""
def gerar_paee_com_ia(estudante, avaliacao):
    api_key = obter_api_key()

    if OpenAI is None or not api_key:
        return gerar_paee_sem_ia(estudante, avaliacao)

    historico_txt = listar_atendimentos_texto(estudante[0])


    # resto da IA...
    # prompt, chamada API, return resposta

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

Utilizar linguagem pedagógica formal, clara e tecnicamente correta.

Evitar:
- termos imprecisos (ex: "materiais duros", "habilidades sensores");
- ambiguidades de gênero (utilizar linguagem neutra, como "o estudante");
- repetições desnecessárias.

Garantir coerência gramatical e terminológica em todo o documento.

Elabore uma sugestão de PAEE com linguagem técnica, objetiva e pedagógica.
Não invente diagnóstico. Não use nome de estudante. Use apenas o código interno.
Não apresente condutas médicas. Foque em barreiras, potencialidades, objetivos, estratégias pedagógicas, acessibilidade, tecnologia assistiva e acompanhamento.

Se o perfil educacional for TEA e o nível de suporte (I, II ou III) não estiver explicitamente informado, a IA deve:
- Considerar provisoriamente características de nível II (suporte moderado), por ser um ponto intermediário seguro.
- Informar claramente no texto que o nível de suporte não foi especificado e que a proposta está baseada em uma hipótese pedagógica inicial.
- Recomendar avaliação complementar para definição mais precisa do nível de suporte.
- Adaptar o grau de mediação pedagógica, a estruturação das atividades, o uso de tecnologias e a intensidade do apoio necessário.
- Não afirmar diagnóstico clínico; tratar essa definição como interpretação pedagógica provisória.

Para garantir consistência, clareza e qualidade institucional do documento, o texto gerado deve seguir os seguintes padrões:

- Utilizar exclusivamente a expressão “Código interno” para identificação do estudante, evitando variações como “Código do estudante”.
- Empregar a forma “Data de elaboração” como referência temporal do documento, mantendo uniformidade terminológica.
- Padronizar títulos e subtítulos com uso de letras minúsculas após a primeira palavra, conforme norma de textos técnicos, por exemplo:
“Objetivo geral” (em vez de “Objetivo Geral”)
- Manter linguagem formal, técnica e pedagógica, evitando variações informais ou redundantes.
- Garantir uniformidade na estrutura das seções ao longo de todo o documento.

Esses critérios visam assegurar que o PAEE apresente padrão profissional, adequado para uso em contextos escolares, institucionais e acadêmicos.

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
   - impressão 3D
   - robótica educacional
   - jogos digitais
   - recursos maker
   - comunicação alternativa e aumentativa
   - materiais táteis, visuais e manipuláveis
   - atividades plugadas e desplugadas
10. Como aplicar essas tecnologias no atendimento
11. Organização do atendimento
12. Articulação com família e professores
13. EVOLUÇÃO DO ESTUDANTE COM BASE NOS ATENDIMENTOS:

É obrigatório analisar o histórico de atendimentos registrados para identificar evolução pedagógica do estudante.

A IA deve considerar:
- avanços observados;
- dificuldades persistentes;
- mudanças na comunicação;
- mudanças na autonomia;
- mudanças na interação social;
- respostas às estratégias pedagógicas;
- resposta ao uso de tecnologias educacionais;
- encaminhamentos recorrentes;
- necessidade de ajuste no PAEE.

A seção “13. Avaliação e acompanhamento” deve mencionar explicitamente os atendimentos registrados, usando expressões como:
- “Com base nos atendimentos recentes...”
- “Observa-se avanço...”
- “Persistem dificuldades...”
- “Os registros indicam...”
- “A evolução observada aponta...”

Criar também uma seção específica:

19. Evolução do estudante com base nos atendimentos

Nessa seção, descrever:
- principais avanços observados;
- dificuldades que permanecem;
- estratégias que funcionaram melhor;
- tecnologias que tiveram melhor resposta;
- ajustes recomendados para os próximos atendimentos;
- indicativos de autonomia, comunicação, interação e aprendizagem.

Caso não existam atendimentos registrados, informar:
“Até o momento, não há registros de atendimentos suficientes para análise evolutiva. Recomenda-se iniciar registros sistemáticos para acompanhar a evolução do estudante.”

Não inventar evolução. Usar apenas os dados registrados nos atendimentos.

14. Recomendações para revisão do plano
Apresentar orientações para atualização do PAEE, incluindo necessidade de avaliações complementares, revisão periódica das estratégias pedagógicas, adequação do nível de suporte e incorporação de novos recursos conforme a evolução do estudante.
15. Adaptação automática conforme o perfil educacional
Descrever de forma técnica como o plano foi ajustado ao perfil do estudante.
No caso de TEA sem definição de nível, indicar a adoção provisória do nível II (suporte moderado), com justificativa pedagógica baseada nas barreiras, potencialidades e necessidades identificadas, ressaltando a necessidade de avaliação complementar.

16. evolução do estudante


17. Responsável pelo AEE:

Nome: ___________________________________________

Função: Professor(a) do Atendimento Educacional Especializado (AEE)

Assinatura: _______________________________________

18. Coordenação pedagógica:

Nome: ___________________________________________

Cargo: Coordenação Pedagógica

Assinatura: _______________________________________

19. Indicar a data de elaboração do documento no formato padrão: dd/mm/aaaa.
Evite respostas genéricas. Todas as recomendações devem estar diretamente relacionadas aos dados do estudante.

Não incluir título principal do documento.

Quando o nível de suporte do TEA não estiver informado, indicar que está sendo adotada uma abordagem pedagógica intermediária, equivalente ao nível II, de forma provisória, justificando essa escolha com base nas barreiras e necessidades observadas.

A IA deve analisar o perfil educacional informado e elaborar um texto descritivo explicando como o plano foi adaptado especificamente para esse estudante.

- Para TEA (nível I, II ou III), descrever o nível de suporte necessário e como isso impacta as estratégias, organização do ambiente, comunicação e uso de tecnologias.
- Para Altas habilidades/superdotação, descrever como o plano promove enriquecimento curricular, desafios cognitivos, criatividade e autonomia.
- Para deficiência visual, descrever adaptações com recursos táteis, audiodescrição, acessibilidade digital e uso de impressão 3D.
- Para deficiência intelectual, descrever adaptações com atividades concretas, linguagem simplificada, repetição estruturada e uso de materiais manipuláveis.

Na seção de tecnologias educacionais inclusivas, analise o perfil do estudante e indique somente recursos coerentes com suas necessidades, potencialidades, barreiras e interesses. Para cada tecnologia sugerida, explique:
- objetivo pedagógico;
- forma de aplicação no AEE;
- material necessário;
- cuidado de acessibilidade;
- como avaliar se funcionou.
"""

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return resposta.output_text

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

    elementos.append(Paragraph(
        "PLANO DE ATENDIMENTO EDUCACIONAL ESPECIALIZADO (PAEE)",
        titulo_style
    ))

    for linha in conteudo.split("\n"):
        linha = linha.strip()

        # 🔥 remove título duplicado da IA
        if "plano de atendimento educacional especializado" in linha.lower() or "(paee)" in linha.lower():
            continue

        # 🔥 remove lixo
        if linha in ["--", "• --", "---"]:
            continue

        if not linha:
            elementos.append(Spacer(1, 6))

        elif linha.startswith("#"):
            elementos.append(Paragraph(
                f"<b>{linha.replace('#','').strip()}</b>",
                secao_style
            ))

        elif linha.startswith("**") and linha.endswith("**"):
            elementos.append(Paragraph(
                f"<b>{linha.replace('**','')}</b>",
                normal_style
            ))

        elif linha.startswith("-"):
            elementos.append(Paragraph(
                f"• {linha[1:].strip()}",
                normal_style
            ))

        else:
            elementos.append(Paragraph(linha, normal_style))

    # 🔥 FORA DO FOR (mesmo nível)
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph(
        "Elaborado com apoio do LabTec3DI – UFRPE",
        rodape_style
    ))

    doc.build(elementos)

    return caminho
# ======================================================
# INTERFACE STREAMLIT
# ======================================================

st.set_page_config(
    page_title="IncluiPAEE IA",
    page_icon="🧠",
    layout="wide"
)

criar_tabelas()

# 🔥 Cabeçalho moderno
st.markdown("""
<h1 style='margin-bottom:0;'>🧠 IncluiPAEE IA</h1>
<p style='color:gray; margin-top:0; font-size:16px;'>
Sistema inteligente para elaboração, organização e acompanhamento do PAEE no AEE
</p>
<hr>
""", unsafe_allow_html=True)

# ⚠️ Alerta estilizado
st.markdown("""
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
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Cadastro",
    "2. Avaliação Pedagógica",
    "3. Gerar PAEE",
    "4. Atendimentos"
])

with tab1:
    st.markdown("### 👤 Cadastro do estudante")
    st.markdown("""
    <div style="
    background-color:#F8F9FA;
    padding:20px;
    border-radius:12px;
    border:1px solid #DDD;
    ">
    """, unsafe_allow_html=True)
    
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
                    [
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
                    ],
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
        selecionado = st.selectbox(
            "Selecione o estudante",
            list(opcoes.keys()),
            key="paee_estudante"
        )

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
                        salvar_paee(estudante_id, paee)
                        st.success("PAEE gerado e salvo no histórico.")
                    except Exception as erro:
                        st.error(f"Erro ao gerar PAEE: {erro}")

            if "paee_gerado" in st.session_state:
                st.subheader("PAEE gerado")
                st.text_area("Conteúdo", st.session_state["paee_gerado"], height=600)

                st.download_button(
                    "Baixar PAEE em .txt",
                    data=st.session_state["paee_gerado"],
                    file_name=f"PAEE_{estudante[1]}.txt",
                    mime="text/plain",
                )

                if st.button("Gerar PDF"):
                    arquivo = gerar_pdf_paee(
                        st.session_state["paee_gerado"],
                        estudante[1]
                    )

                    with open(arquivo, "rb") as f:
                        st.download_button(
                            "Baixar PAEE em PDF",
                            f,
                            file_name=f"PAEE_{estudante[1]}.pdf",
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
