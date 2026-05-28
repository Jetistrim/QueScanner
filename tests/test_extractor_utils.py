from __future__ import annotations

import logging
from pathlib import Path

from pytest import LogCaptureFixture

from src.extractor import (
    AlternativeItem,
    emit_question_rows,
    infer_question_type,
    infer_year,
    is_lettered_alternative,
    is_alternative_continuation,
    is_alternative_header_line,
    is_question_orientation_start,
    normalize_alternatives_for_matrix,
    normalize_orientations,
)
from src.models import ParseContext


def test_infer_question_type_supports_all_types() -> None:
    assert infer_question_type("Selecione todas que se aplicam", [])[0] == "MÚLTIPLA"
    assert infer_question_type("Preencha todas que se aplicam", [])[0] == "QUANTITATIVA"
    assert infer_question_type("Selecione apenas uma", [])[0] == "ÚNICA"
    assert (
        infer_question_type(
            None,
            [
                {"label": "Sim", "text": "Sim", "sub_option": None},
                {"label": "Não", "text": "Não", "sub_option": None},
            ],
        )[0]
        == "SIMPLES"
    )


def test_infer_question_type_fallback_returns_single_and_flag() -> None:
    question_type, used_fallback = infer_question_type(
        "Texto sem gatilho de tipo",
        [{"label": "a)", "text": "a) Opção", "sub_option": None}],
    )

    assert question_type == "ÚNICA"
    assert used_fallback is True


def test_normalize_orientations_handles_none_empty_and_whitespace() -> None:
    assert normalize_orientations(None) == "Sem orientacoes especificas."
    assert normalize_orientations("") == "Sem orientacoes especificas."
    assert normalize_orientations("   ") == "Sem orientacoes especificas."
    assert normalize_orientations(" Selecione uma ") == "Selecione uma"


def test_infer_year_from_filename_and_none_when_missing() -> None:
    assert infer_year(["Sem período aqui"], input_path=Path("questoes_2024.pdf")) == 2024
    assert infer_year(["Sem período aqui"], input_path=Path("questoes_sem_ano.pdf")) is None


def test_line_classifiers_cover_orientation_and_alternative_cases() -> None:
    assert is_question_orientation_start("(Selecione uma alternativa)")
    assert not is_question_orientation_start("Texto comum")

    assert is_alternative_header_line("Indique as evidências:")
    assert is_alternative_header_line("________________")
    assert not is_alternative_header_line("continuação de alternativa")

    assert is_alternative_continuation("continuação válida")
    assert is_alternative_continuation("2) complemento")
    assert not is_alternative_continuation(" ")
    assert not is_alternative_continuation("Cabeçalho:")


def test_emit_question_rows_logs_fallback_warning(caplog: LogCaptureFixture) -> None:
    logger = logging.getLogger("test-fallback")
    context = ParseContext(
        dimension="1. Ambiental",
        theme="1.1. Água",
        topic="1.1.1. Água",
        sector="Aplicável",
        question_code="1.1.1.1",
        question_text="Pergunta sem gatilho claro",
        orientations="Texto livre",
    )

    with caplog.at_level(logging.WARNING):
        records = emit_question_rows(
            context,
            year=2026,
            alternatives=[{"label": "a)", "text": "a) Opção", "sub_option": None}],
            logger=logger,
        )

    assert len(records) == 2
    assert records[0]["TIPO"] == "ÚNICA"
    assert "Usando default ÚNICA" in caplog.text


def test_emit_question_rows_returns_empty_when_context_missing_question_data() -> None:
    empty_context = ParseContext()

    records = emit_question_rows(empty_context, year=2026, alternatives=[])

    assert records == []


def test_infer_question_type_detects_simple_from_orientation_text_only() -> None:
    question_type, used_fallback = infer_question_type("Marque Sim e Não conforme aplicável", [])

    assert question_type == "SIMPLES"
    assert used_fallback is False


def test_matrix_normalization_keeps_only_lettered_rows_when_present() -> None:
    alternatives: list[AlternativeItem] = [
        {"label": "Sim", "text": "Sim", "sub_option": None},
        {"label": "a)", "text": "a) Opção A", "sub_option": "Sim"},
        {"label": "b)", "text": "b) Opção B", "sub_option": "Não"},
        {"label": "Não", "text": "Não", "sub_option": None},
    ]

    normalized = normalize_alternatives_for_matrix(alternatives)

    assert len(normalized) == 2
    assert [item["label"] for item in normalized] == ["a)", "b)"]
    assert [item["sub_option"] for item in normalized] == ["Sim", "Não"]


def test_is_lettered_alternative_supports_lower_and_uppercase() -> None:
    assert is_lettered_alternative("a)")
    assert is_lettered_alternative("B)")
    assert not is_lettered_alternative("Sim")
