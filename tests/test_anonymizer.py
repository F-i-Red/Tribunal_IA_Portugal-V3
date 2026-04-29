"""
Testes unitários para o anonimizador jurídico português.
"""

import pytest
from src.utils.anonymizer import PortugueseLegalAnonymizer, Entity


class TestPortugueseLegalAnonymizer:
    """Testes do anonimizador."""

    @pytest.fixture
    def anonymizer(self):
        return PortugueseLegalAnonymizer()

    def test_nif_detection(self, anonymizer):
        """Testa deteção de NIF português."""
        text = "O arguido João Silva, com NIF 123456789, foi acusado."
        result, entities = anonymizer.anonymize(text)

        assert "[NIF_REMOVIDO]" in result
        assert any(e.label == "NIF" for e in entities)
        assert not any(e.text == "123456789" for e in entities)  # NIF não deve aparecer

    def test_telefone_detection(self, anonymizer):
        """Testa deteção de telemóvel."""
        text = "Contacto do testemunha: 912345678 ou +351 912345678"
        result, entities = anonymizer.anonymize(text)

        assert "[TELEFONE_REMOVIDO]" in result
        assert sum(1 for e in entities if e.label == "TELEFONE") == 2

    def test_email_detection(self, anonymizer):
        """Testa deteção de email."""
        text = "Email do advogado: joao.silva@email.pt"
        result, entities = anonymizer.anonymize(text)

        assert "[EMAIL_REMOVIDO]" in result
        assert any(e.label == "EMAIL" for e in entities)

    def test_person_name_detection(self, anonymizer):
        """Testa deteção de nomes de pessoas."""
        text = "O arguido Manuel Ferreira Santos foi detido em Lisboa."
        result, entities = anonymizer.anonymize(text)

        assert "[PESSOA_" in result
        assert any(e.label == "PESSOA" for e in entities)

    def test_tribunal_detection(self, anonymizer):
        """Testa deteção de tribunais."""
        text = "O processo foi distribuído pelo Tribunal da Comarca de Lisboa."
        result, entities = anonymizer.anonymize(text)

        assert "[LOCAL_" in result
        assert any(e.label == "LOCAL" for e in entities)

    def test_no_false_positives_common_words(self, anonymizer):
        """Testa que palavras comuns não são anonimizadas."""
        text = "O tribunal decidiu que o direito foi aplicado."
        result, entities = anonymizer.anonymize(text)

        assert "tribunal" in result.lower()
        assert "direito" in result.lower()
        assert len(entities) == 0

    def test_multiple_entities(self, anonymizer):
        """Testa cenário com múltiplas entidades."""
        text = """
        O arguido Carlos Mendes (NIF 123456789, tel. 912345678, 
        email carlos@mail.pt) reside em Rua das Flores, Lisboa.
        O processo 1234/23.0001 está no Tribunal de Sintra.
        """
        result, entities = anonymizer.anonymize(text)

        labels = [e.label for e in entities]
        assert "NIF" in labels
        assert "TELEFONE" in labels
        assert "EMAIL" in labels
        assert "PESSOA" in labels
        assert "LOCAL" in labels
        assert "PROCESSO" in labels

    def test_deterministic_pseudonyms(self, anonymizer):
        """Testa que o mesmo texto gera o mesmo pseudónimo."""
        text = "O arguido Pedro Alves foi acusado."
        result1, _ = anonymizer.anonymize(text)
        result2, _ = anonymizer.anonymize(text)

        assert result1 == result2

    def test_preserve_structure(self, anonymizer):
        """Testa que a estrutura do texto é preservada."""
        text = "O arguido João Silva, NIF 123456789, cometeu o crime."
        result, _ = anonymizer.anonymize(text)

        assert "O arguido" in result
        assert "cometeu o crime" in result
        assert "NIF" not in result  # NIF foi removido


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
