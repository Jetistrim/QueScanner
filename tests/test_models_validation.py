from __future__ import annotations

import pytest

from src.models import QUESTION_TYPES, validate_output_records


def make_valid_record() -> dict[str, object]:
    return {
        "ID": 1,
        "TIPO": QUESTION_TYPES["single"],
        "DIMENSÃO": "1. Ambiental",
        "TEMA": "1.1. Água e Efluentes",
        "TÓPICO": "1.1.1. Água e Efluentes",
        "APLICAÇÃO SETORIAL": "Aplicável",
        "CÓDIGO QUESTÃO": "1.1.1.1",
        "ANO": 2026,
        "PERGUNTA": "Pergunta",
        "SUB-OPÇÃO": None,
        "ORIENTAÇÕES": "Selecione uma alternativa",
        "TIPO DE EVIDÊNCIA": "Apenas Evidência Pública",
        "EXEMPLOS DE EVIDÊNCIA": "Relatório anual",
        "STATUS": None,
        "PONTO FOCAL": None,
        "RESPONSÁVEL": None,
        "ENVIAR EVIDÊNCIA": None,
        "PTS. CABÍVEIS": None,
        "DISTRIBUIÇÃO": None,
        "RESPOSTA": None,
        "EVIDÊNCIA EMPRESA": None,
        "PTS. OBTIDOS": None,
        "%": None,
        "GRI/ISO": None,
        "TRIAL": None,
    }


def test_validate_output_records_accepts_valid_record() -> None:
    validated = validate_output_records([make_valid_record()])

    assert len(validated) == 1
    assert validated[0]["TIPO"] == "ÚNICA"


def test_validate_output_records_rejects_invalid_type() -> None:
    invalid = make_valid_record()
    invalid["TIPO"] = "INVALIDO"

    with pytest.raises(ValueError, match="Registro inválido"):
        validate_output_records([invalid])


def test_validate_output_records_rejects_invalid_question_code() -> None:
    invalid = make_valid_record()
    invalid["CÓDIGO QUESTÃO"] = "1.1"

    with pytest.raises(ValueError, match="Registro inválido"):
        validate_output_records([invalid])


def test_validate_output_records_rejects_out_of_range_year() -> None:
    invalid = make_valid_record()
    invalid["ANO"] = 1999

    with pytest.raises(ValueError, match="Registro inválido"):
        validate_output_records([invalid])
