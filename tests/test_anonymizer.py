"""Testes para o anonimizador."""
import pytest
from src.utils.anonymizer import anonymize_text, PortugueseLegalAnonymizer


def test_nif_removido():
    text = "O arguido tem NIF 123456789."
    anon, ents = anonymize_text(text)
    assert "123456789" not in anon
    assert any(e.label == "NIF" for e in ents)


def test_telefone_removido():
    text = "Contacte pelo 912345678."
    anon, ents = anonymize_text(text)
    assert "912345678" not in anon
    assert any(e.label == "TELEFONE" for e in ents)


def test_email_removido():
    text = "Envie para joao.silva@email.pt."
    anon, ents = anonymize_text(text)
    assert "joao.silva@email.pt" not in anon
    assert any(e.label == "EMAIL" for e in ents)


def test_codigo_postal_removido():
    text = "Residente em 1200-150 Lisboa."
    anon, ents = anonymize_text(text)
    assert "1200-150" not in anon
    assert any(e.label == "CODIGO_POSTAL" for e in ents)


def test_nome_com_prefixo():
    text = "O arguido Manuel Ferreira Santos foi detido."
    anon, ents = anonymize_text(text)
    assert "Manuel Ferreira Santos" not in anon
    assert any(e.label == "PESSOA" for e in ents)


def test_tribunal_removido():
    text = "No Tribunal da Comarca de Lisboa foi proferida sentença."
    anon, ents = anonymize_text(text)
    assert any(e.label == "LOCAL" for e in ents)


def test_cidade_removida():
    text = "O incidente ocorreu em Lisboa."
    anon, ents = anonymize_text(text)
    assert any(e.label == "LOCAL" for e in ents)


def test_sem_falsos_positivos():
    text = "Existem duas testemunhas no processo."
    anon, ents = anonymize_text(text)
    # "duas testemunhas" não deve ser detetado como PESSOA
    pessoas = [e for e in ents if e.label == "PESSOA"]
    assert len(pessoas) == 0


def test_pseudonimo_consistente():
    """O mesmo nome deve gerar sempre o mesmo pseudónimo."""
    anon = PortugueseLegalAnonymizer()
    p1 = anon._pseudonym("PESSOA", "Manuel Silva")
    p2 = anon._pseudonym("PESSOA", "Manuel Silva")
    assert p1 == p2


def test_data_nascimento_com_contexto():
    text = "Nascido em 15 de março de 1980."
    anon, ents = anonymize_text(text)
    assert any(e.label == "DATA_NASCIMENTO" for e in ents)


def test_data_generica_nao_anonimizada():
    """Datas sem contexto de nascimento não devem ser removidas."""
    text = "O crime ocorreu no dia 15 de março de 2024."
    anon, ents = anonymize_text(text)
    nascimentos = [e for e in ents if e.label == "DATA_NASCIMENTO"]
    assert len(nascimentos) == 0
