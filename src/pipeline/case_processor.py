"""
Pipeline principal — RAG integrado nos prompts + paralelismo nas sentenças.
"""

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..utils import get_config, get_logger, get_brain, anonymize_text
from .instancias import INSTANCIAS, InstanciaJudicial, detectar_instancia_por_keywords
from ..rag import MotorRAG, ValidadorCitacoes


@dataclass
class CaseResult:
    case_id: str
    trace_id: str
    original_description: str
    anonymized_description: str
    entities_found: List[Dict]
    instancia_codigo: str = ""
    instancia_nome: str = ""
    dados_instrucao: Optional[Dict] = None
    detetive_report: Optional[str] = None
    acusacao: Optional[str] = None
    defesa: Optional[str] = None
    sentenca_rigorosa: Optional[str] = None
    sentenca_garantista: Optional[str] = None
    sentenca_equilibrada: Optional[str] = None
    ata_final: Optional[str] = None
    contexto_rag: Optional[str] = None
    custo_total_usd: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CaseProcessor:
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.brain = get_brain()
        from pathlib import Path
        self.rag = MotorRAG(Path("."))
        n_frags = self.rag.indexar()
        if n_frags > 0:
            self.logger.info(f"RAG indexado: {n_frags} fragmentos")
        self.validador = ValidadorCitacoes(Path("data/leis"))

    def gerar_perguntas_instrucao(self, case_description: str,
                                   instancia_codigo: str = "TIC") -> Dict:
        inst = INSTANCIAS.get(instancia_codigo, INSTANCIAS["TIC"])

        # RAG para contexto jurídico na instrução
        ctx_rag = self._get_rag_context(case_description, n=3)

        system_prompt = f"""És o Juiz de Instrução do {inst.nome}, Portugal.
Matéria: {inst.materia}
Diploma principal: {inst.diploma_principal}

{ctx_rag}

Analisa o caso e identifica lacunas factuais, probatórias e circunstanciais.

REGRAS:
- Gera 4 a 6 perguntas específicas ao caso (não genéricas)
- Usa terminologia própria desta instância: {inst.termo_acusado}, {inst.termo_vitima}
- Responde APENAS em JSON, sem markdown, sem texto adicional

JSON:
{{"introducao":"abertura formal 2-3 frases","perguntas":[{{"id":"q1","texto":"pergunta concreta e específica ao caso","categoria":"FACTOS","importancia":"critica","aceita_documentos":false}}]}}

Categorias: FACTOS, PROVAS, TESTEMUNHAS, CIRCUNSTÂNCIAS, TEMPORAL, DIREITO
Importâncias: critica, relevante, complementar"""

        try:
            response = self.brain.call(
                messages=[{"role": "user", "content": f"Caso:\n\n{case_description}"}],
                system_prompt=system_prompt,
                temperature=0.1, max_tokens=1200,
            )
            result = self._json_robusto(response.content)
            if result and "perguntas" in result:
                return result
        except Exception as e:
            self.logger.error(f"Instrução API: {e}")

        return self._fallback_perguntas(inst)

    def _json_robusto(self, content: str) -> Optional[Dict]:
        t = content.strip()
        t = re.sub(r"```(?:json)?\s*", "", t)
        t = re.sub(r"```", "", t).strip()
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            pass
        i, f = t.find("{"), t.rfind("}")
        if i != -1 and f > i:
            try:
                return json.loads(t[i:f+1])
            except json.JSONDecodeError:
                pass
        return None

    def _fallback_perguntas(self, inst: InstanciaJudicial) -> Dict:
        return {
            "introducao": (
                f"O Juiz de Instrução do {inst.nome}, após análise preliminar, "
                "solicita esclarecimentos adicionais para fundamentar o processo."
            ),
            "perguntas": [
                {"id": "q1", "texto": "Quando e onde ocorreram exactamente os factos?",
                 "categoria": "TEMPORAL", "importancia": "critica", "aceita_documentos": False},
                {"id": "q2", "texto": f"Existem testemunhas? Em que qualidade ({inst.termo_vitima}, terceiros, etc.)?",
                 "categoria": "TESTEMUNHAS", "importancia": "relevante", "aceita_documentos": False},
                {"id": "q3", "texto": "Que provas materiais, documentais ou digitais existem?",
                 "categoria": "PROVAS", "importancia": "relevante", "aceita_documentos": True},
                {"id": "q4", "texto": "Já foi apresentada queixa ou participação a alguma autoridade? Com que resultado?",
                 "categoria": "CONTEXTO", "importancia": "relevante", "aceita_documentos": True},
                {"id": "q5", "texto": "Há outros envolvidos ou co-arguidos/co-réus além dos já mencionados?",
                 "categoria": "FACTOS", "importancia": "complementar", "aceita_documentos": False},
            ]
        }

    def _get_rag_context(self, query: str, n: int = 5) -> str:
        """Recupera contexto jurídico relevante do RAG."""
        if not self.rag.tem_dados():
            return ""
        frags = self.rag.pesquisar(query, n_resultados=n)
        return self.rag.formatar_contexto(frags, max_chars=2500)

    def process(self, case_description: str,
                instancia_codigo: str = None,
                dados_instrucao: Optional[Dict] = None) -> CaseResult:

        if not instancia_codigo:
            instancia_codigo = detectar_instancia_por_keywords(case_description)
        inst = INSTANCIAS.get(instancia_codigo, INSTANCIAS["TIC"])

        trace_id = self.logger.start_case(case_description)
        case_id = f"case_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"Caso {case_id} | {inst.nome}")

        # Anonimizar
        self.logger.set_agent("anonimizador")
        anon_text, entities = anonymize_text(case_description)
        self.logger.log_anonymization(len(entities), list(set(e.label for e in entities)))

        ctx_instrucao = self._fmt_instrucao(dados_instrucao)
        ctx_rag = self._get_rag_context(anon_text + " " + ctx_instrucao)

        def _chamar(nome: str, fn, *args) -> str:
            self.logger.set_agent(nome)
            try:
                resultado = fn(*args)
                if not resultado or not str(resultado).strip():
                    self.logger.warning(f"Agente {nome} devolveu resposta vazia")
                    return (
                        f"[{nome.upper()}: o modelo não gerou resposta.\n"
                        f"Sugestão: muda MODELO= no .env para um modelo mais capaz.\n"
                        f"Ver opções: python verificar.py --modelos]"
                    )
                return str(resultado)
            except Exception as e:
                self.logger.error(f"Agente {nome} falhou: {e}")
                return f"[{nome.upper()}: erro — {str(e)[:300]}]"

        # Agentes sequenciais (dependências)
        detetive = _chamar("detetive", self._detetive, anon_text, ctx_instrucao, ctx_rag, inst)
        acusacao = _chamar("acusacao", self._acusacao, anon_text, detetive, ctx_rag, inst)
        defesa = _chamar("defesa", self._defesa, anon_text, detetive, acusacao, ctx_rag, inst)

        # Sentenças em paralelo (async)
        if self.config.paralelismo and not self.config.modo_economico:
            s_rigorosa, s_garantista, s_equilibrada = self._sentencas_paralelo(
                anon_text, detetive, acusacao, defesa, inst
            )
        else:
            s_rigorosa = _chamar("juiz_rigoroso", self._juiz, anon_text, detetive, acusacao, defesa, "rigoroso", inst, ctx_rag)
            s_garantista = _chamar("juiz_garantista", self._juiz, anon_text, detetive, acusacao, defesa, "garantista", inst, ctx_rag)
            s_equilibrada = _chamar("juiz_equilibrado", self._juiz, anon_text, detetive, acusacao, defesa, "equilibrado", inst, ctx_rag)

        # Montar ata
        self.logger.set_agent("escrivao")
        ata = self._montar_ata(
            case_id, trace_id, anon_text, inst,
            detetive, acusacao, defesa,
            s_rigorosa, s_garantista, s_equilibrada,
            dados_instrucao, ctx_rag
        )

        hash_doc = hashlib.sha256(ata.encode()).hexdigest()[:16]
        ata_final = self._disclaimer(hash_doc, case_id) + ata + self._watermark(hash_doc, case_id, trace_id)

        if self.config.guardar_atas:
            fp = self.config.pasta_atas / f"{case_id}.txt"
            fp.write_text(ata_final, encoding="utf-8")
            self.logger.info(f"Ata guardada: {fp}")

        # Custos
        cost_stats = self.brain.get_cost_stats()

        self.logger.info(f"Caso {case_id} concluído")
        return CaseResult(
            case_id=case_id, trace_id=trace_id,
            original_description=case_description,
            anonymized_description=anon_text,
            entities_found=[{"text": e.text, "type": e.label, "score": e.score} for e in entities],
            instancia_codigo=instancia_codigo,
            instancia_nome=inst.nome,
            dados_instrucao=dados_instrucao,
            detetive_report=detetive, acusacao=acusacao, defesa=defesa,
            sentenca_rigorosa=s_rigorosa, sentenca_garantista=s_garantista,
            sentenca_equilibrada=s_equilibrada, ata_final=ata_final,
            contexto_rag=ctx_rag,
            custo_total_usd=cost_stats["total_cost_usd"],
        )

    def _sentencas_paralelo(self, case_text, detetive, acusacao, defesa, inst):
        """Executa as 3 sentenças em paralelo com asyncio."""
        import asyncio

        async def _chamar_async(perfil: str):
            return self._juiz(case_text, detetive, acusacao, defesa, perfil, inst, self._get_rag_context(case_text))

        async def _executar():
            tasks = [
                _chamar_async("rigoroso"),
                _chamar_async("garantista"),
                _chamar_async("equilibrado"),
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        resultados = loop.run_until_complete(_executar())

        # Tratar exceções
        final = []
        for i, perfil in enumerate(["rigoroso", "garantista", "equilibrado"]):
            r = resultados[i]
            if isinstance(r, Exception):
                self.logger.error(f"Sentença {perfil} falhou: {r}")
                final.append(f"[SENTENÇA {perfil.upper()}: erro — {str(r)[:300]}]")
            else:
                final.append(r)

        return final[0], final[1], final[2]

    def _fmt_instrucao(self, dados: Optional[Dict]) -> str:
        if not dados or not dados.get("respostas"):
            return ""
        linhas = ["\n\n═══ ESCLARECIMENTOS DA INSTRUÇÃO ═══\n"]
        for item in dados["respostas"].values():
            if item["resposta"] != "Sem resposta":
                linhas.append(f"[{item['categoria']}] {item['pergunta']}")
                linhas.append(f"→ {item['resposta']}\n")
        for m in dados.get("materiais", []):
            linhas.append(f"📎 {m['descricao']}")
        linhas.append("═══════════════════════════════════\n")
        return "\n".join(linhas)

    def _detetive(self, case_text: str, ctx_instrucao: str, ctx_rag: str, inst: InstanciaJudicial) -> str:
        sp = f"""És o Investigador/Detetive de Instrução do {inst.nome}, Portugal.
Diploma: {inst.diploma_principal}
Partes: {inst.termo_acusado} vs {inst.termo_vitima}

{ctx_rag}

Produz RELATÓRIO DE INSTRUÇÃO FACTUAL com estas secções:

## FACTOS ALEGADOS
(lista numerada — o que o {inst.termo_vitima} relata)

## FACTOS PROVADOS
(cada um com: 🔴 Evidência Fraca / 🟡 Média / 🟢 Forte)

## FACTOS NÃO PROVADOS / INCERTOS
(lista e razão da incerteza)

## PROVAS DISPONÍVEIS
- Testemunhal: (quem e em que qualidade)
- Documental: (o que existe)
- Pericial: (o que seria necessário)

## DILIGÊNCIAS RECOMENDADAS
(perícias, inquirições, buscas necessárias)

## PRAZOS DE PRESCRIÇÃO
(indicação dos prazos relevantes ao abrigo do {inst.diploma_principal})

Usa linguagem técnica portuguesa. Sê preciso e factual."""

        return self.brain.call(
            messages=[{"role": "user", "content": f"CASO:\n{case_text}{ctx_instrucao}"}],
            system_prompt=sp, temperature=0.1, max_tokens=1200,
        ).content

    def _acusacao(self, case_text: str, detetive: str, ctx_rag: str, inst: InstanciaJudicial) -> str:
        sp = f"""És o {inst.termo_mp} do {inst.nome}, Portugal.
Diploma: {inst.diploma_principal}

{ctx_rag}

Rediges as ALEGAÇÕES DA ACUSAÇÃO / PETIÇÃO INICIAL com:

## FACTOS IMPUTADOS AO {inst.termo_acusado.upper()}
(lista numerada e datada)

## QUALIFICAÇÃO JURÍDICA
(artigos concretos do {inst.diploma_principal} e legislação conexa)
IMPORTANTE: Se não tiveres certeza de um número de artigo, escreve [art.?] — não inventes.

## FUNDAMENTAÇÃO PROBATÓRIA
(porque é que a prova é suficiente)

## PEDIDO
(pena / sanção / indemnização concreta requerida)

Português europeu, linguagem jurídica formal. Usa termos: {inst.termo_acusado}, {inst.termo_vitima}."""

        return self.brain.call(
            messages=[{"role": "user", "content": f"CASO:\n{case_text}\n\nINSTRUÇÃO:\n{detetive}"}],
            system_prompt=sp, temperature=0.15, max_tokens=1200,
        ).content

    def _defesa(self, case_text: str, detetive: str, acusacao: str,
                ctx_rag: str, inst: InstanciaJudicial) -> str:
        sp = f"""És o {inst.termo_defesa} da Defesa no {inst.nome}, Portugal.
Diploma: {inst.diploma_principal}

{ctx_rag}

Rediges as ALEGAÇÕES DA DEFESA / CONTESTAÇÃO com:

## CONTESTAÇÃO DOS FACTOS
(o que é negado, duvidoso ou insuficientemente provado)

## DIREITOS FUNDAMENTAIS E GARANTIAS PROCESSUAIS
(CRP, CEDH, {inst.diploma_principal} — violations processuais se existirem)

## TESE ALTERNATIVA
(versão dos factos favorável ao {inst.termo_acusado} / causas de exclusão)

## PRINCÍPIO IN DUBIO PRO REO / PROPORCIONALIDADE
(aplicação ao caso concreto)

## PEDIDO
(absolvição / arquivamento / atenuação / improcedência)

Português europeu, linguagem jurídica formal."""

        return self.brain.call(
            messages=[{"role": "user", "content": f"CASO:\n{case_text}\n\nINSTRUÇÃO:\n{detetive[:800]}\n\nACUSAÇÃO:\n{acusacao[:1000]}"}],
            system_prompt=sp, temperature=0.15, max_tokens=1200,
        ).content

    def _juiz(self, case_text: str, detetive: str, acusacao: str,
              defesa: str, perfil: str, inst: InstanciaJudicial,
              ctx_rag: str = "") -> str:

        perfis = {
            "rigoroso": ("RIGOROSO", "Tens tendência para a condenação quando há indícios razoáveis. Priorizas prevenção geral."),
            "garantista": ("GARANTISTA", "Só condenas com prova sólida além de toda a dúvida razoável. In dubio pro reo é máxima."),
            "equilibrado": ("EQUILIBRADO", "Decisão ponderada, justa e proporcional, considerando todos os elementos."),
        }
        nome, desc = perfis[perfil]

        sp = f"""FUNÇÃO: Juiz {nome} — {inst.nome} — Portugal
PERFIL: {desc}
DIPLOMA: {inst.diploma_principal}
PARTES: {inst.termo_acusado} (acusado) | {inst.termo_vitima} (vítima/autor)

{ctx_rag}

TAREFA OBRIGATÓRIA: Escreve um {inst.termo_decisao} judicial formal com EXACTAMENTE estas 8 secções.
NÃO escrevas conselhos, listas de próximos passos, nem texto na primeira pessoa.
Escreve APENAS como juiz a proferir decisão judicial.

== 1. RELATÓRIO ==
[Identifica partes e sintetiza o processo em 3-5 frases]

== 2. FACTOS PROVADOS ==
[Lista numerada: 1. ... 2. ... 3. ...]

== 3. FACTOS NÃO PROVADOS ==
[Lista: — ...]

== 4. MOTIVAÇÃO DA DECISÃO DE FACTO ==
[Analisa as provas existentes e explica porque provam ou não provam os factos]

== 5. FUNDAMENTAÇÃO JURÍDICA ==
[Artigos do {inst.diploma_principal} aplicáveis. Se incerto do número: escreve [art.?]]

== 6. DISPOSITIVO ==
[Começa obrigatoriamente com: "O Tribunal DECIDE:" seguido de CONDENA/ABSOLVE/JULGA PROCEDENTE/IMPROCEDENTE + pena/sanção concreta]

== 7. CUSTAS ==
[Estimativa resumida]

== 8. NOTA ACESSÍVEL ==
[3-4 frases explicando a decisão em linguagem comum para o cidadão]"""

        ctx = (f"CASO:\n{case_text[:1000]}\n\n"
               f"INSTRUÇÃO (resumo):\n{detetive[:600]}\n\n"
               f"ACUSAÇÃO (resumo):\n{acusacao[:500]}\n\n"
               f"DEFESA (resumo):\n{defesa[:500]}")

        return self.brain.call(
            messages=[{"role": "user", "content": ctx}],
            system_prompt=sp, temperature=0.05, max_tokens=1500,
        ).content

    def _montar_ata(self, case_id, trace_id, case_text, inst: InstanciaJudicial,
                    detetive, acusacao, defesa, rigorosa, garantista, equilibrada,
                    dados_instrucao, ctx_rag) -> str:

        now = datetime.now(timezone.utc)
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        data_pt = f"{now.day} de {meses[now.month-1]} de {now.year}, {now.strftime('%H:%M')} UTC"

        sec_instrucao = ""
        if dados_instrucao and dados_instrucao.get("respostas"):
            respondidas = [(k, v) for k, v in dados_instrucao["respostas"].items()
                           if v["resposta"] != "Sem resposta"]
            if respondidas:
                sec_instrucao = f"""
{"═"*70}
SECÇÃO III — ESCLARECIMENTOS DA FASE DE INSTRUÇÃO
{"═"*70}

O {inst.termo_vitima} prestou {len(respondidas)} esclarecimento(s):

"""
                for _, item in respondidas:
                    sec_instrucao += f" [{item['categoria']}] {item['pergunta']}\n"
                    sec_instrucao += f" ➜ {item['resposta']}\n\n"
                for m in dados_instrucao.get("materiais", []):
                    sec_instrucao += f" 📎 Material referido: {m['descricao']}\n"

        # Secção RAG
        sec_rag = ""
        if ctx_rag:
            sec_rag = f"""
{"═"*70}
SECÇÃO XII — FUNDAMENTOS JURÍDICOS CONSULTADOS (RAG)
{"═"*70}

{ctx_rag[:1500]}

"""

        return f"""{"═"*70}
ATA DE SIMULAÇÃO JUDICIAL — TRIBUNAL IA PORTUGAL
{"═"*70}

PROCESSO Nº : {case_id}
TRACE ID    : {trace_id}
TRIBUNAL    : {inst.nome}
MATÉRIA     : {inst.materia}
DIPLOMA     : {inst.diploma_principal}
DATA        : {data_pt}
ESTADO      : SIMULAÇÃO EDUCATIVA — SEM VALOR JURÍDICO

Partes processuais (ficcionais):
 • {inst.termo_vitima.upper()}: Requerente/Ofendido (anonimizado)
 • {inst.termo_acusado.upper()}: Arguido/Réu (anonimizado)
 • {inst.termo_mp}: Representação pública
 • {inst.termo_defesa}: Representação privada

{"═"*70}
SECÇÃO I — DESCRIÇÃO DO CASO (ANONIMIZADO — RGPD)
{"═"*70}

{case_text}

{"═"*70}
SECÇÃO II — RELATÓRIO DE INSTRUÇÃO FACTUAL
{"═"*70}

{detetive}
{sec_instrucao}
{"═"*70}
SECÇÃO IV — ALEGAÇÕES DA ACUSAÇÃO / {inst.termo_mp.upper()}
{"═"*70}

{acusacao}

{"═"*70}
SECÇÃO V — ALEGAÇÕES DA DEFESA / {inst.termo_defesa.upper()}
{"═"*70}

{defesa}

{"═"*70}
SECÇÃO VI — {inst.termo_decisao.upper()} A: PERFIL RIGOROSO
{"═"*70}
(Juiz que aplica estritamente a lei; tende para condenação perante indícios razoáveis)

{rigorosa}

{"═"*70}
SECÇÃO VII — {inst.termo_decisao.upper()} B: PERFIL GARANTISTA
{"═"*70}
(Juiz que prioriza direitos fundamentais; exige prova sólida além de dúvida razoável)

{garantista}

{"═"*70}
SECÇÃO VIII — {inst.termo_decisao.upper()} C: PERFIL EQUILIBRADO
{"═"*70}
(Juiz ponderado que busca decisão justa e proporcional)

{equilibrada}

{"═"*70}
SECÇÃO IX — COMPARAÇÃO DOS TRÊS PERFIS DE DECISÃO
{"═"*70}

{self._comparar(rigorosa, garantista, equilibrada, inst)}

{"═"*70}
SECÇÃO X — VALIDAÇÃO DE CITAÇÕES JURÍDICAS (RAG)
{"═"*70}

{self._validar_e_adicionar_citacoes(acusacao, defesa, rigorosa, garantista, equilibrada)}

{sec_rag}
{"═"*70}
SECÇÃO XI — NOTA EDUCATIVA
{"═"*70}

Esta simulação ilustra como o mesmo caso pode ter resultados distintos
consoante o perfil do julgador e a força probatória disponível.

A divergência entre os três perfis reflecte a tensão legítima entre:
 • Segurança jurídica e prevenção geral → Perfil Rigoroso
 • Garantias processuais e direitos fundamentais → Perfil Garantista
 • Proporcionalidade e equidade → Perfil Equilibrado

Diploma aplicável: {inst.diploma_principal}
Base de conhecimento RAG: Código Penal, CPP, Código Civil, CPC, Código do Trabalho,
 Constituição da República Portuguesa, Jurisprudência STJ
Tribunal simulado: {inst.nome}

Para situações reais, consulte sempre um Advogado inscrito na
Ordem dos Advogados de Portugal: www.oa.pt

"""

    def _validar_e_adicionar_citacoes(self, acusacao: str, defesa: str,
                                       rigorosa: str, garantista: str,
                                       equilibrada: str) -> str:
        texto_completo = " ".join([acusacao, defesa, rigorosa, garantista, equilibrada])
        _, problemas = self.validador.validar_texto(texto_completo)
        return self.validador.relatorio_citacoes(problemas)

    def _comparar(self, rigorosa: str, garantista: str, equilibrada: str,
                  inst: InstanciaJudicial) -> str:
        def dispositivo(txt: str) -> str:
            m = re.search(
                r"(?:##\s*)?(?:\d+\.\s*)?DISPOSITIVO\s*\n+(.*?)(?:\n##|\n---|\Z)",
                txt, re.IGNORECASE | re.DOTALL
            )
            if m:
                d = m.group(1).strip()
                return d[:400] if len(d) > 400 else d
            m = re.search(
                r"(?:CONDENA|ABSOLVE|JULGA\s+(?:PROCEDENTE|IMPROCEDENTE)|ARQUIVA|PRONUNCIA|NÃO\s+PRONUNCIA)"
                r"[^.]*\.",
                txt, re.IGNORECASE
            )
            if m:
                return m.group(0).strip()
            return txt.strip()[:200] + "..."

        r = dispositivo(rigorosa)
        g = dispositivo(garantista)
        e = dispositivo(equilibrada)

        return f"""PERFIL RIGOROSO — {inst.termo_decisao}:
{r}

─────────────────────────────────────────
PERFIL GARANTISTA — {inst.termo_decisao}:
{g}

─────────────────────────────────────────
PERFIL EQUILIBRADO — {inst.termo_decisao}:
{e}

─────────────────────────────────────────
NOTA: As três decisões partem dos mesmos factos e provas.
A diferença reflecte ponderações distintas do in dubio pro reo
e da prevenção geral, legítimas no sistema jurídico português.
"""

    def _disclaimer(self, hash_doc: str, case_id: str) -> str:
        return (
            f"\n╔{'═'*70}╗\n"
            f"║ ⚠️ AVISO LEGAL — DOCUMENTO DE SIMULAÇÃO EDUCATIVA{' '*18}║\n"
            f"║ {' '*69}║\n"
            f"║ Este documento foi gerado por IA e NÃO constitui parecer ║\n"
            f"║ jurídico, decisão judicial ou documento oficial de qualquer ║\n"
            f"║ natureza. Para situações reais, consulte um Advogado (www.oa.pt). ║\n"
            f"║ {' '*69}║\n"
            f"║ Hash: {hash_doc:<62}║\n"
            f"║ ID: {case_id:<62}║\n"
            f"╚{'═'*70}╝\n\n"
        )

    def _watermark(self, hash_doc: str, case_id: str, trace_id: str) -> str:
        return (
            f"\n{'─'*70}\n"
            f"WATERMARK — SIMULAÇÃO TRIBUNAL IA PORTUGAL\n"
            f"Hash: {hash_doc} | ID: {case_id} | Trace: {trace_id}\n"
            f"DOCUMENTO DE SIMULAÇÃO EDUCATIVA SEM VALOR JURÍDICO\n"
            f"{'─'*70}\n"
        )


def process_case(case_description: str, instancia_codigo: str = None) -> CaseResult:
    return CaseProcessor().process(case_description, instancia_codigo=instancia_codigo)
