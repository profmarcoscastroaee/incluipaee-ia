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
            codigo_edit = st.text_input("Código interno", value=estudante_editar[1])
            ano_edit = st.text_input("Ano/Série", value=estudante_editar[2])

        with col2:
            turma_edit = st.text_input("Turma", value=estudante_editar[3])
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
                index=0
            )

        observacoes_edit = st.text_area(
            "Observações pedagógicas iniciais",
            value=estudante_editar[5] or ""
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