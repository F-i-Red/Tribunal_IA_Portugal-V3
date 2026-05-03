"""
Definição completa das instâncias judiciais portuguesas.
Cada instância tem: nome, código, matéria, agentes processuais, terminologia própria.
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class InstanciaJudicial:
    codigo: str
    nome: str
    nome_curto: str
    materia: str
    descricao: str
    # Terminologia processual específica
    termo_acusado: str        # "arguido", "réu", "recorrente", etc.
    termo_vitima: str         # "ofendido", "autor", "reclamante", etc.
    termo_mp: str             # papel do MP nesta instância
    termo_defesa: str         # "defensor", "mandatário", etc.
    termo_decisao: str        # "sentença", "acórdão", "despacho", etc.
    diploma_principal: str    # CPP, CPC, CPTA, etc.
    keywords: List[str]       # palavras-chave para detecção automática


INSTANCIAS: Dict[str, InstanciaJudicial] = {

    "TIC": InstanciaJudicial(
        codigo="TIC",
        nome="Tribunal de Instrução Criminal",
        nome_curto="T. Instrução Criminal",
        materia="Penal — Fase de Instrução",
        descricao=(
            "Controla a legalidade da investigação criminal e decide sobre "
            "a pronúncia ou não pronúncia do arguido. Intervém quando o arguido "
            "requer instrução após acusação do MP ou quando o MP arquiva e o "
            "assistente requer abertura de instrução."
        ),
        termo_acusado="arguido",
        termo_vitima="assistente / ofendido",
        termo_mp="Magistrado do Ministério Público",
        termo_defesa="defensor / patrono",
        termo_decisao="despacho de pronúncia / não pronúncia",
        diploma_principal="Código de Processo Penal (CPP)",
        keywords=["crime", "arguido", "penal", "furto", "roubo", "ofensa corporal",
                  "tortura", "assédio", "escutas", "homicídio", "ameaça", "coação",
                  "difamação", "injúria", "violação", "tráfico", "corrupção",
                  "instrução criminal", "mp arquivou", "queixa na psp",
                  "denúncia", "inquérito", "investigação"],
    ),

    "TCCR": InstanciaJudicial(
        codigo="TCCR",
        nome="Tribunal Coletivo / Singular Criminal",
        nome_curto="Tribunal Criminal",
        materia="Penal — Julgamento",
        descricao=(
            "Julgamento de crimes. Tribunal Singular para crimes com pena até "
            "5 anos. Tribunal Coletivo para crimes com pena superior a 5 anos "
            "ou crimes de catálogo (terrorismo, criminalidade organizada, etc.)."
        ),
        termo_acusado="arguido",
        termo_vitima="assistente / ofendido",
        termo_mp="Procurador do Ministério Público",
        termo_defesa="defensor nomeado / constituído",
        termo_decisao="sentença / acórdão",
        diploma_principal="Código de Processo Penal (CPP) + Código Penal (CP)",
        keywords=["julgamento criminal", "acusação formal", "pronúncia",
                  "debate instrutório", "audiência de discussão e julgamento"],
    ),

    "TCIC": InstanciaJudicial(
        codigo="TCIC",
        nome="Tribunal Central de Instrução Criminal",
        nome_curto="TCIC",
        materia="Penal — Grande Criminalidade",
        descricao=(
            "Competência especializada para criminalidade altamente organizada, "
            "terrorismo, corrupção de grande dimensão, criminalidade económico-financeira "
            "de especial complexidade, tráfico de influência, peculato."
        ),
        termo_acusado="arguido",
        termo_vitima="assistente / ofendido",
        termo_mp="Procurador da República / DCIAP",
        termo_defesa="defensor",
        termo_decisao="despacho de pronúncia",
        diploma_principal="CPP + Lei de Organização do Sistema Judiciário",
        keywords=["corrupção", "terrorismo", "criminalidade organizada", "tráfico",
                  "lavagem de dinheiro", "branqueamento", "dciap", "pj", "financeiro"],
    ),

    "TC_CIVEL": InstanciaJudicial(
        codigo="TC_CIVEL",
        nome="Tribunal Judicial de Comarca — Juízo Cível",
        nome_curto="Tribunal Cível",
        materia="Cível — Direito Privado",
        descricao=(
            "Litígios entre privados: contratos, propriedade, responsabilidade civil, "
            "indemnizações por danos, acções de divulgação/cessação, etc."
        ),
        termo_acusado="réu / demandado",
        termo_vitima="autor / demandante",
        termo_mp="Ministério Público (em representação de incapazes)",
        termo_defesa="mandatário judicial",
        termo_decisao="sentença",
        diploma_principal="Código Civil (CC) + Código de Processo Civil (CPC)",
        keywords=["contrato", "dívida", "indemnização", "danos", "propriedade",
                  "arrendamento", "responsabilidade civil", "incumprimento",
                  "resolução contratual", "execução", "penhora", "cível"],
    ),

    "TFM": InstanciaJudicial(
        codigo="TFM",
        nome="Tribunal de Família e Menores",
        nome_curto="T. Família e Menores",
        materia="Família / Menores",
        descricao=(
            "Divórcio, regulação das responsabilidades parentais, alimentos, "
            "adoção, apadrinhamento civil, tutelar educativo, promoção e protecção."
        ),
        termo_acusado="requerido",
        termo_vitima="requerente",
        termo_mp="Ministério Público (intervenção obrigatória em menores)",
        termo_defesa="mandatário",
        termo_decisao="sentença / decisão",
        diploma_principal="CC + CPC + RGPTC + LPCJP",
        keywords=["divórcio", "separação", "filho", "menor", "alimentos",
                  "responsabilidades parentais", "guarda", "tutela", "adopção",
                  "adoção", "família", "casamento", "união de facto"],
    ),

    "TRAB": InstanciaJudicial(
        codigo="TRAB",
        nome="Tribunal do Trabalho",
        nome_curto="T. Trabalho",
        materia="Laboral",
        descricao=(
            "Litígios laborais: despedimentos, salários em atraso, acidentes de trabalho, "
            "greve, convenções colectivas, reconhecimento de relação laboral."
        ),
        termo_acusado="réu / entidade empregadora",
        termo_vitima="autor / trabalhador",
        termo_mp="Ministério Público",
        termo_defesa="mandatário",
        termo_decisao="sentença",
        diploma_principal="Código do Trabalho (CT) + Código de Processo do Trabalho (CPT)",
        keywords=["trabalho", "laboral", "despedimento", "salário", "vencimento",
                  "contrato de trabalho", "férias", "subsidio", "acidente trabalho",
                  "assédio laboral", "greve", "sindicato", "empregador", "patrão"],
    ),

    "TAF": InstanciaJudicial(
        codigo="TAF",
        nome="Tribunal Administrativo e Fiscal",
        nome_curto="T. Administrativo",
        materia="Administrativo / Fiscal",
        descricao=(
            "Litígios com o Estado e entidades públicas: actos administrativos, "
            "contratos públicos, expropriações, urbanismo, impostos, coimas."
        ),
        termo_acusado="entidade demandada / administração",
        termo_vitima="autor / recorrente / contribuinte",
        termo_mp="Ministério Público",
        termo_defesa="mandatário",
        termo_decisao="sentença / acórdão",
        diploma_principal="CPTA + CPPT + CPA",
        keywords=["estado", "administração pública", "câmara municipal", "município",
                  "imposto", "irs", "irc", "iva", "coima", "multa", "licença",
                  "urbanismo", "obra", "expropriação", "concurso público",
                  "funcionário público", "acto administrativo"],
    ),

    "TCOM": InstanciaJudicial(
        codigo="TCOM",
        nome="Tribunal de Comércio",
        nome_curto="T. Comércio",
        materia="Comercial / Insolvência",
        descricao=(
            "Insolvências, recuperação de empresas (PER/PEAP), dissolução de sociedades, "
            "propriedade industrial, concorrência desleal, acções contra sociedades."
        ),
        termo_acusado="insolvente / réu",
        termo_vitima="credor / autor",
        termo_mp="Ministério Público",
        termo_defesa="mandatário / administrador insolvência",
        termo_decisao="sentença / despacho",
        diploma_principal="CIRE + CSC + CódComercial",
        keywords=["insolvência", "falência", "empresa", "sociedade", "per", "peap",
                  "credor", "recuperação", "liquidação", "dissolução", "sócio",
                  "gerente", "administrador", "propriedade industrial", "marca",
                  "patente", "concorrência desleal", "comercial"],
    ),

    "TR": InstanciaJudicial(
        codigo="TR",
        nome="Tribunal da Relação",
        nome_curto="Tribunal da Relação",
        materia="2ª Instância — Recurso",
        descricao=(
            "Segunda instância para recursos de decisões dos tribunais de 1ª instância. "
            "Há 5 Tribunais da Relação: Lisboa, Porto, Coimbra, Évora e Guimarães. "
            "Conhece factos e direito. Profere acórdãos."
        ),
        termo_acusado="recorrido / arguido",
        termo_vitima="recorrente / assistente",
        termo_mp="Procurador-Geral Adjunto",
        termo_defesa="mandatário",
        termo_decisao="acórdão",
        diploma_principal="CPP / CPC (consoante a matéria)",
        keywords=["recurso", "apelação", "recorrente", "recorrido", "relação",
                  "tribunal da relação", "segunda instância", "2ª instância",
                  "impugnar", "decisão recorrida"],
    ),

    "STJ": InstanciaJudicial(
        codigo="STJ",
        nome="Supremo Tribunal de Justiça",
        nome_curto="STJ",
        materia="3ª Instância — Direito",
        descricao=(
            "Última instância em matéria cível e penal. Conhece apenas de direito "
            "(não aprecia factos). Uniformiza jurisprudência. Profere acórdãos "
            "vinculativos. Sede em Lisboa."
        ),
        termo_acusado="recorrido",
        termo_vitima="recorrente",
        termo_mp="Procurador-Geral da República",
        termo_defesa="mandatário",
        termo_decisao="acórdão",
        diploma_principal="CPP / CPC + Estatuto STJ",
        keywords=["supremo tribunal", "stj", "terceira instância", "3ª instância",
                  "revista", "recurso de revista", "uniformização", "acórdão uniformizador"],
    ),

    "TC": InstanciaJudicial(
        codigo="TC",
        nome="Tribunal Constitucional",
        nome_curto="T. Constitucional",
        materia="Constitucional",
        descricao=(
            "Fiscaliza a constitucionalidade das normas jurídicas. Não julga casos "
            "concretos entre privados — aprecia se uma norma viola a Constituição "
            "da República Portuguesa (CRP). Sede em Lisboa."
        ),
        termo_acusado="entidade que aplica a norma",
        termo_vitima="recorrente / requerente",
        termo_mp="Procurador-Geral da República",
        termo_defesa="mandatário",
        termo_decisao="acórdão",
        diploma_principal="Constituição da República Portuguesa (CRP) + LTC",
        keywords=["constitucional", "inconstitucionalidade", "direitos fundamentais",
                  "crp", "tribunal constitucional", "fiscalização", "norma inconstitucional"],
    ),
}


def listar_instancias_menu() -> str:
    """Texto formatado para mostrar ao utilizador no início."""
    linhas = []
    grupos = [
        ("⚖️  PENAL", ["TIC", "TCCR", "TCIC"]),
        ("📋 CÍVEL", ["TC_CIVEL"]),
        ("👨‍👩‍👧 FAMÍLIA", ["TFM"]),
        ("💼 TRABALHO", ["TRAB"]),
        ("🏛️  ADMINISTRATIVO / FISCAL", ["TAF"]),
        ("🏢 COMERCIAL", ["TCOM"]),
        ("🔼 RECURSOS", ["TR", "STJ"]),
        ("📜 CONSTITUCIONAL", ["TC"]),
    ]
    for grupo, codigos in grupos:
        linhas.append(f"\n  {grupo}")
        for c in codigos:
            inst = INSTANCIAS[c]
            linhas.append(f"    [{c:8s}] {inst.nome_curto:<35} — {inst.materia}")
    return "\n".join(linhas)


def detectar_instancia_por_keywords(texto: str) -> str:
    """Detecta a instância mais provável por palavras-chave. Retorna código."""
    t = texto.lower()
    scores: Dict[str, int] = {k: 0 for k in INSTANCIAS}
    for codigo, inst in INSTANCIAS.items():
        for kw in inst.keywords:
            if kw in t:
                scores[codigo] += 1
    # Excluir instâncias de recurso da detecção automática inicial
    for exc in ["TR", "STJ", "TC", "TCIC"]:
        scores[exc] = 0
    melhor = max(scores, key=lambda k: scores[k])
    return melhor if scores[melhor] > 0 else "TIC"
