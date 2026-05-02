"""
Testes do sistema de anonimização.
"""

import pytest
from src.utils.anonymizer import anonymize_text, deanonymize_text


def test_anonimiza_nomes_proprios():
    texto = "João Silva foi visto na Rua das Flores, em Lisboa."
    anon, ents = anonymize_text(texto)
    assert "João Silva" not in anon
    assert any(e.text == "João Silva" for e in ents)


def test_anonimiza_endereco():
    texto = "O incidente ocorreu na Av. da Liberdade, nº 123, 4º Esq."
    anon, ents = anonymize_text(texto)
    assert "Av. da Liberdade" not in anon
    assert any("Liberdade" in e.text for e in ents)


def test_anonimiza_email():
    texto = "Contacte-me via maria.santos@email.pt"
    anon, ents = anonymize_text(texto)
    assert "maria.santos@email.pt" not in anon


def test_anonimiza_telefone():
    texto = "Ligue para 912345678 ou +351 912 345 678"
    anon, ents = anonymize_text(texto)
    assert "912345678" not in anon


def test_anonimiza_nif():
    texto = "NIF 123456789"
    anon, ents = anonymize_text(texto)
    assert "123456789" not in anon


def test_anonimiza_processo():
    texto = "Processo nº 1234/25.1T8LSB"
    anon, ents = anonymize_text(texto)
    assert "1234/25.1T8LSB" not in anon


def test_reversibilidade():
    texto = "O Sr. António Costa mora em Braga."
    anon, ents = anonymize_text(texto)
    revertido = deanonymize_text(anon, ents)
    assert "António Costa" in revertido


def test_sem_entidades():
    texto = "O gato subiu à árvore."
    anon, ents = anonymize_text(texto)
    assert len(ents) == 0
    assert anon == texto


def test_texto_longo():
    texto = " ".join(["João Silva"] * 100)
    anon, ents = anonymize_text(texto)
    assert "João Silva" not in anon
    assert len(ents) == 100


def test_anonimiza_tribunal():
    texto = "O caso foi julgado no Tribunal da Relação de Lisboa."
    anon, ents = anonymize_text(texto)
    assert "Tribunal da Relação de Lisboa" not in anon
