
"""
Tribunal IA Portugal — Interface Web (Streamlit) V2.1
Wizard de 4 passos — evita problemas com tabs.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from src.utils import ConfigError, get_config
from src.pipeline.case_processor import CaseProcessor
from src.pipeline.instancias import (
    INSTANCIAS, listar_instancias_menu, detectar_instancia_por_keywords
)
from src.cache import get_cache, limpar_cache

st.set_page_config(
    page_title="Tribunal IA Portugal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f4e79; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
    .disclaimer-box {
        background-color: #fff3cd; border: 1px solid #ffc107;
        border-radius: 8px; padding: 1rem; margin: 1rem 0;
    }
    .sentenca-box {
        background-color: #f8f9fa; border-left: 4px solid #1f4e79;
        border-radius: 4px; padding: 1rem; margin: 0.5rem 0;
    }
    .sentenca-rigoroso { border-left-color: #dc3545; }
    .sentenca-garantista { border-left-color: #28a745; }
    .sentenca-equilibrado { border-left-color: #007bff; }
    .cost-badge {
        background-color: #e9ecef; border-radius: 12px;
        padding: 0.3rem 0.8rem; font-size: 0.85rem; display: inline-block;
    }
    .rag-box {
        background-color: #e7f3ff; border: 1px solid #b3d9ff;
        border-radius: 6px; padding: 0.8rem; font-size: 0.85rem;
    }
    .step-active {
        background-color: #1f4e79; color: white;
        padding: 0.5rem 1rem; border-radius: 20px;
        font-weight: bold; text-align: center;
    }
    .step-inactive {
        background-color: #e9ecef; color: #666;
        padding: 0.5rem 1rem; border-radius: 20px;
        text-align: center;
    }
    .step-done {
        background-color: #28a745; color: white;
        padding: 0.5rem 1rem; border-radius: 20px;
        font-weight: bold; text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ── Inicialização do state ──
def init_session():
    defaults = {
        "case_description": "",
        "instancia_selecionada": None,
        "perguntas_instrucao": None,
        "respostas_instrucao": {},
        "materiais_instrucao": [],
        "resultado": None,
        "step": 1,
        "modo_economico": False,
        "erro": None,
        "auto_detect": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()


# ── Sidebar ──
with st.sidebar:
    st.markdown("### ⚖️ Tribunal IA Portugal")
    st.markdown("Simulador jurídico de alta fidelidade")
    st.divider()
    st.markdown("#### 🔧 Configurações")
    st.session_state.modo_economico = st.toggle(
        "💰 Modo Económico",
        value=st.session_state.modo_economico,
        help="Usa menos agentes e modelos mais baratos. Reduz custos em ~60%.",
    )
    st.session_state["paralelismo"] = st.toggle(
        "⚡ Paralelismo nas sentenças", value=True,
        help="Executa as 3 sentenças em paralelo (mais rápido)",
    )
    st.divider()
    try:
        cache = get_cache()
        stats = cache.estatisticas()
        st.markdown("#### 📊 Cache")
        st.markdown(f"Entradas: **{stats['entradas']}**")
        st.markdown(f"Poupança: **${stats['poupanca_estimada_usd']}**")
        if st.button("🗑️ Limpar cache antigo (>30 dias)"):
            rem = limpar_cache(30)
            st.success(f"{rem} entradas removidas")
            st.rerun()
    except Exception:
        pass
    st.divider()
    st.markdown("#### 📚 Instâncias")
    for cod, inst in INSTANCIAS.items():
        st.markdown(f"**{cod}**: {inst.nome}")
    st.divider()
    st.markdown("""
    <div style="font-size:0.75rem;color:#999;">
    ⚠️ Fins educativos apenas.<br>
    Não substitui parecer jurídico.<br>
    <a href="https://www.oa.pt" target="_blank">Ordem dos Advogados</a>
    </div>
    """, unsafe_allow_html=True)


# ── Header ──
st.markdown('<div class="main-header">🏛️ Tribunal IA Portugal</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Simulador judicial de alta fidelidade — Direito Português 🇵🇹</div>', unsafe_allow_html=True)
st.markdown("""
<div class="disclaimer-box">
<strong>⚠️ Aviso Legal:</strong> Este simulador é uma ferramenta educativa e de simulação.
Não constitui parecer jurídico, decisão judicial ou documento oficial.
Para situações reais, consulte sempre um Advogado inscrito na
<a href="https://www.oa.pt" target="_blank">Ordem dos Advogados de Portugal</a>.
</div>
""", unsafe_allow_html=True)


# ── Verificar configuração ──
try:
    cfg = get_config()
except ConfigError as e:
    st.error(f"❌ Erro de configuração: {e}")
    st.info("Cria um ficheiro `.env` na raiz com: `OPENROUTER_API_KEY=sua_chave`")
    st.stop()


# ── Barra de progresso visual ──
step = st.session_state.step
step_labels = ["1. Descrição", "2. Instrução", "3. Processo", "4. Resultado"]
cols = st.columns(4)
for i, label in enumerate(step_labels):
    with cols[i]:
        if i + 1 < step:
            st.markdown(f'<div class="step-done">✅ {label}</div>', unsafe_allow_html=True)
        elif i + 1 == step:
            st.markdown(f'<div class="step-active">▶️ {label}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="step-inactive">{label}</div>', unsafe_allow_html=True)

st.divider()


# ── Funções auxiliares ──
def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_session()
    st.rerun()


def extrair_disp(texto):
    import re
    m = re.search(r"(?:CONDENA|ABSOLVE|JULGA\s+(?:PROCEDENTE|IMPROCEDENTE)|ARQUIVA)[^.]*\.",
                  texto or "", re.IGNORECASE)
    return m.group(0).strip() if m else (texto or "")[:150] + "..."


# ═══════════════════════════════════════════════════════════════════════
# PASSO 1: DESCRIÇÃO DO CASO
# ═══════════════════════════════════════════════════════════════════════
if step == 1:
    st.markdown("### 📝 Passo 1: Descrição do Caso")
    st.info("Usa linguagem comum. Não precisas de saber termos jurídicos. Quanto mais detalhe, melhor.")

    case_input = st.text_area(
        "Descreve o caso jurídico",
        value=st.session_state.case_description,
        height=200,
        placeholder="Ex: O meu vizinho construiu um muro que invade o meu terreno em 30cm...",
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        st.session_state.auto_detect = st.checkbox(
            "Detectar tribunal automaticamente", value=st.session_state.auto_detect
        )
    with col2:
        if not st.session_state.auto_detect:
            inst_opcoes = {f"{k} — {v.nome}": k for k, v in INSTANCIAS.items()}
            inst_selecionada = st.selectbox("Escolhe o tribunal", list(inst_opcoes.keys()))
            st.session_state.instancia_selecionada = inst_opcoes[inst_selecionada]

    if st.button("▶️ Avançar para Instrução", type="primary", disabled=not case_input.strip()):
        st.session_state.case_description = case_input
        if st.session_state.auto_detect:
            st.session_state.instancia_selecionada = detectar_instancia_por_keywords(case_input)
        st.session_state.step = 2
        st.session_state.perguntas_instrucao = None
        st.session_state.respostas_instrucao = {}
        st.session_state.materiais_instrucao = []
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════
# PASSO 2: INSTRUÇÃO
# ═══════════════════════════════════════════════════════════════════════
elif step == 2:
    st.markdown("### 🔍 Passo 2: Fase de Instrução")
    inst = INSTANCIAS[st.session_state.instancia_selecionada]
    st.markdown(f"**Tribunal:** {inst.nome} | **Matéria:** {inst.materia}")

    # Gerar perguntas se ainda não existirem
    if st.session_state.perguntas_instrucao is None:
        with st.spinner("A gerar perguntas de instrução... (pode demorar com modelos free)"):
            try:
                processor = CaseProcessor()
                perguntas = processor.gerar_perguntas_instrucao(
                    st.session_state.case_description,
                    st.session_state.instancia_selecionada,
                )
                st.session_state.perguntas_instrucao = perguntas
            except Exception as e:
                st.error(f"Erro ao gerar perguntas: {e}")
                st.session_state.perguntas_instrucao = {"perguntas": [], "introducao": ""}
        st.rerun()

    perguntas = st.session_state.perguntas_instrucao
    st.markdown(f"*{perguntas.get('introducao', '')}*")

    for p in perguntas.get("perguntas", []):
        with st.container():
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**[{p['categoria']}]** {p['texto']}")
                st.caption(f"Importância: {p['importancia']}")
            with cols[1]:
                key = f"resp_{p['id']}"
                st.session_state.respostas_instrucao[p["id"]] = st.text_area(
                    "Resposta", key=key, height=80,
                    value=st.session_state.respostas_instrucao.get(p["id"], ""),
                    placeholder="Escreve a tua resposta ou deixa em branco...",
                )

    st.markdown("---")
    st.markdown("##### 📎 Materiais/Documentos adicionais")
    mat_input = st.text_area(
        "Descreve documentos ou provas que queiras anexar (opcional):",
        height=80,
    )
    if mat_input.strip():
        st.session_state.materiais_instrucao = [{"descricao": mat_input, "tipo": "material"}]

    col_voltar, col_skip, col_go = st.columns(3)
    with col_voltar:
        if st.button("⬅️ Voltar"):
            st.session_state.step = 1
            st.rerun()
    with col_skip:
        if st.button("⏭️ Ignorar instrução"):
            st.session_state.step = 3
            st.rerun()
    with col_go:
        if st.button("▶️ Iniciar Processo Judicial", type="primary"):
            st.session_state.step = 3
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════
# PASSO 3: PROCESSO (processamento)
# ═══════════════════════════════════════════════════════════════════════
elif step == 3:
    st.markdown("### ⚖️ Passo 3: Processo Judicial")

    if st.session_state.erro:
        st.error(f"❌ Erro no processamento: {st.session_state.erro}")
        st.info("💡 Dica: Se estás a usar um modelo FREE, pode ter atingido o rate limit. Tenta novamente dentro de 1 minuto.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Tentar novamente"):
                st.session_state.erro = None
                st.rerun()
        with col2:
            if st.button("⬅️ Voltar à instrução"):
                st.session_state.step = 2
                st.session_state.erro = None
                st.rerun()
        st.stop()

    if st.session_state.resultado is not None:
        st.success("✅ Processo já concluído!")
        if st.button("▶️ Ver Resultado"):
            st.session_state.step = 4
            st.rerun()
        st.stop()

    # Processar
    with st.spinner("⚖️ O tribunal está a deliberar... (pode demorar 1-5 minutos com modelos free)"):
        try:
            old_modo = cfg.__dict__.get("modo_economico", False)
            old_para = cfg.__dict__.get("paralelismo", True)
            cfg.__dict__["modo_economico"] = st.session_state.modo_economico
            cfg.__dict__["paralelismo"] = st.session_state.get("paralelismo", True)

            processor = CaseProcessor()
            dados_instrucao = None
            if st.session_state.respostas_instrucao:
                respostas_filtradas = {
                    k: {"pergunta": "", "categoria": "", "resposta": v}
                    for k, v in st.session_state.respostas_instrucao.items() if v.strip()
                }
                if respostas_filtradas:
                    dados_instrucao = {
                        "respostas": respostas_filtradas,
                        "materiais": st.session_state.materiais_instrucao,
                    }

            result = processor.process(
                case_description=st.session_state.case_description,
                instancia_codigo=st.session_state.instancia_selecionada,
                dados_instrucao=dados_instrucao,
            )
            st.session_state.resultado = result
            st.session_state.erro = None

            cfg.__dict__["modo_economico"] = old_modo
            cfg.__dict__["paralelismo"] = old_para

        except Exception as e:
            st.session_state.erro = str(e)
            cfg.__dict__["modo_economico"] = old_modo
            cfg.__dict__["paralelismo"] = old_para

    # Avançar automaticamente para o resultado
    if st.session_state.resultado is not None:
        st.session_state.step = 4
        st.rerun()
    elif st.session_state.erro:
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════
# PASSO 4: RESULTADO
# ═══════════════════════════════════════════════════════════════════════
elif step == 4:
    st.markdown("### 📄 Passo 4: Resultado")

    if st.session_state.resultado is None:
        st.warning("⚠️ Não há resultado disponível. Volta ao passo 3.")
        if st.button("⬅️ Voltar ao processo"):
            st.session_state.step = 3
            st.rerun()
        st.stop()

    result = st.session_state.resultado

    cols = st.columns([2, 1, 1, 1])
    with cols[0]:
        st.markdown(f"**{result.instancia_nome}**")
    with cols[1]:
        st.markdown(f'<span class="cost-badge">💰 ${result.custo_total_usd:.4f}</span>',
                    unsafe_allow_html=True)
    with cols[2]:
        st.markdown(f'<span class="cost-badge">🆔 {result.case_id}</span>',
                    unsafe_allow_html=True)
    with cols[3]:
        if st.button("🔄 Novo caso"):
            reset_all()

    if result.contexto_rag:
        with st.expander("📚 Contexto Jurídico Consultado (RAG)", expanded=False):
            st.markdown(f'<div class="rag-box">{result.contexto_rag.replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True)

    sub_tabs = st.tabs(["📋 Relatório", "⚖️ Sentenças", "📊 Comparação", "📝 Ata Completa"])

    with sub_tabs[0]:
        st.markdown("#### 🔍 Relatório de Instrução")
        st.markdown(result.detetive_report or "*Não disponível*")
        st.markdown("---")
        col_a, col_d = st.columns(2)
        with col_a:
            st.markdown("#### ⚔️ Acusação")
            st.markdown(result.acusacao or "*Não disponível*")
        with col_d:
            st.markdown("#### 🛡️ Defesa")
            st.markdown(result.defesa or "*Não disponível*")

    with sub_tabs[1]:
        for titulo, texto, classe in [
            ("🔴 Perfil Rigoroso", result.sentenca_rigorosa, "sentenca-rigoroso"),
            ("🟢 Perfil Garantista", result.sentenca_garantista, "sentenca-garantista"),
            ("🔵 Perfil Equilibrado", result.sentenca_equilibrada, "sentenca-equilibrado"),
        ]:
            st.markdown(f'<div class="sentenca-box {classe}">', unsafe_allow_html=True)
            st.markdown(f"**{titulo}**")
            st.markdown(texto or "*Não disponível*")
            st.markdown("</div>", unsafe_allow_html=True)

    with sub_tabs[2]:
        st.markdown("#### 📊 Comparação dos Perfis")
        comp_data = {
            "Rigoroso": extrair_disp(result.sentenca_rigorosa),
            "Garantista": extrair_disp(result.sentenca_garantista),
            "Equilibrado": extrair_disp(result.sentenca_equilibrada),
        }
        for perfil, disp in comp_data.items():
            st.markdown(f"**{perfil}:** {disp}")
        st.markdown("---")
        st.info("""
        **Nota:** As três decisões partem dos mesmos factos e provas.
        A diferença reflecte ponderações distintas do *in dubio pro reo*
        e da prevenção geral, legítimas no sistema jurídico português.
        """)

    with sub_tabs[3]:
        st.markdown("#### 📄 Ata Completa")
        st.text_area("Conteúdo da ata", value=result.ata_final or "", height=600, disabled=True)
        st.download_button(
            "⬇️ Download da Ata (.txt)",
            data=result.ata_final or "",
            file_name=f"{result.case_id}.txt",
            mime="text/plain",
        )
        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:0.8rem;color:#666;">
        <strong>Metadados:</strong><br>
        Case ID: {result.case_id} | Trace: {result.trace_id}<br>
        Timestamp: {result.timestamp}<br>
        Custo: ${result.custo_total_usd:.4f} USD<br>
        Entidades anonimizadas: {len(result.entities_found)}<br>
        </div>
        """, unsafe_allow_html=True)
