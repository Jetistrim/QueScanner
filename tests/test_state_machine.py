from __future__ import annotations

import logging
from pathlib import Path

from _pytest.logging import LogCaptureFixture

from src.extractor import infer_year, parse_pdf_lines
from conftest import load_fixture_lines


def test_parse_basic_question_block_from_txt_fixture() -> None:
    lines = load_fixture_lines("questionario_basico.txt")

    records = parse_pdf_lines(lines, input_path=Path("ISE_2025_questionario.pdf"))

    assert len(records) == 3
    assert records[0]["PERGUNTA"] == "A companhia possui política para monitoramento hídrico?"
    assert str(records[1]["PERGUNTA"]).startswith("a) ")
    assert str(records[2]["PERGUNTA"]).startswith("b) ")
    assert records[0]["TIPO"] == "ÚNICA"
    assert records[0]["CÓDIGO QUESTÃO"] == "1.1.1.1"
    assert records[0]["ANO"] == 2025


def test_handles_page_break_inside_alternative_without_losing_text() -> None:
    lines = load_fixture_lines("quebra_em_alternativa.txt")

    records = parse_pdf_lines(lines, input_path=Path("questionario_2026.pdf"))

    assert len(records) == 3
    assert records[0]["TIPO"] == "MÚLTIPLA"
    assert "com trilhas anuais e indicadores" in str(records[1]["PERGUNTA"])
    assert records[1]["PERGUNTA"] != records[2]["PERGUNTA"]


def test_malformed_question_keeps_parser_running_for_next_question() -> None:
    lines = load_fixture_lines("mal_formatado_com_recuperacao.txt")

    records = parse_pdf_lines(lines, input_path=Path("arquivo_2024.pdf"))

    assert len(records) >= 4
    assert any(row["CÓDIGO QUESTÃO"] == "3.1.1.2" for row in records)
    second_question_rows = [row for row in records if row["CÓDIGO QUESTÃO"] == "3.1.1.2"]
    assert len(second_question_rows) == 3


def test_infer_year_from_header_range() -> None:
    lines = ["Questionário ISE B3 2026 / 2027", "Dimensão: 1. Ambiental"]

    year = infer_year(lines)

    assert year == 2026


def test_denormalized_context_is_repeated_for_all_rows_in_question_block() -> None:
    lines = load_fixture_lines("questionario_basico.txt")
    records = parse_pdf_lines(lines, input_path=Path("ISE_2025_questionario.pdf"))

    context_columns = [
        "TIPO",
        "DIMENSÃO",
        "TEMA",
        "TÓPICO",
        "APLICAÇÃO SETORIAL",
        "CÓDIGO QUESTÃO",
        "ANO",
        "ORIENTAÇÕES",
        "TIPO DE EVIDÊNCIA",
        "EXEMPLOS DE EVIDÊNCIA",
    ]

    reference = {column: records[0][column] for column in context_columns}
    for row in records[1:]:
        for column in context_columns:
            assert row[column] == reference[column]


def test_parse_question_without_evidence_table_keeps_evidence_columns_none() -> None:
    lines = load_fixture_lines("sem_evidencia.txt")

    records = parse_pdf_lines(lines, input_path=Path("arquivo_2026.pdf"))

    assert len(records) == 3
    assert records[0]["TIPO"] == "SIMPLES"
    for row in records:
        assert row["TIPO DE EVIDÊNCIA"] is None
        assert row["EXEMPLOS DE EVIDÊNCIA"] is None


def test_parse_pdf_lines_empty_input_returns_empty_list() -> None:
    assert parse_pdf_lines([]) == []


def test_evidence_examples_are_concatenated_across_lines() -> None:
    lines = load_fixture_lines("evidencia_multilinha.txt")

    records = parse_pdf_lines(lines, input_path=Path("arquivo_2026.pdf"))

    assert len(records) == 2
    assert records[0]["TIPO DE EVIDÊNCIA"] == "Apenas Evidência Pública"
    evidence_examples = str(records[0]["EXEMPLOS DE EVIDÊNCIA"])
    assert "Relatório de sustentabilidade" in evidence_examples
    assert "detalhamento metodológico" in evidence_examples
    assert "GHG Protocol" in evidence_examples


def test_logs_warning_when_year_is_not_found(caplog: LogCaptureFixture) -> None:
    logger = logging.getLogger("test-logger-year")
    lines = [
        "Dimensão: 1. Ambiental",
        "Tema: 1.1. Água e Efluentes",
        "1.1.1. Água e Efluentes",
    ]

    with caplog.at_level(logging.WARNING):
        parse_pdf_lines(lines, input_path=Path("sem_ano.pdf"), logger=logger)

    assert "Ano não identificado" in caplog.text


def test_sector_text_is_concatenated_when_spans_multiple_lines() -> None:
    lines = [
        "Dimensão: 1. Ambiental",
        "Tema: 1.1. Água e Efluentes",
        "1.1.1. Água e Efluentes",
        "Aplicação setorial: Aplicável ao setor",
        "com detalhamento complementar",
        "1.1.1.1. Questão exemplo",
        "( ) Sim",
        "( ) Não",
    ]

    records = parse_pdf_lines(lines, input_path=Path("arquivo_2026.pdf"))

    assert len(records) == 3
    assert records[0]["APLICAÇÃO SETORIAL"] == "Aplicável ao setor com detalhamento complementar"


def test_alternative_header_line_is_moved_to_orientations_not_alternative_text() -> None:
    lines = [
        "Dimensão: 1. Ambiental",
        "Tema: 1.1. Água e Efluentes",
        "1.1.1. Água e Efluentes",
        "Aplicação setorial: Aplicável",
        "1.1.1.1. Questão exemplo",
        "a) Opção principal",
        "Indique as evidências:",
    ]

    records = parse_pdf_lines(lines, input_path=Path("arquivo_2026.pdf"))

    assert len(records) == 2
    assert records[1]["PERGUNTA"] == "a) Opção principal"
    assert records[0]["ORIENTAÇÕES"] == "Indique as evidências:"


def test_reading_evidence_accepts_free_text_after_type_without_examples_prefix() -> None:
    lines = [
        "Dimensão: 1. Ambiental",
        "Tema: 1.1. Água e Efluentes",
        "1.1.1. Água e Efluentes",
        "Aplicação setorial: Aplicável",
        "1.1.1.1. Questão exemplo",
        "( ) Sim",
        "( ) Não",
        "Tipo da evidência Apenas Evidência Pública",
        "Relatório institucional anual",
    ]

    records = parse_pdf_lines(lines, input_path=Path("arquivo_2026.pdf"))

    assert len(records) == 3
    assert records[0]["TIPO DE EVIDÊNCIA"] == "Apenas Evidência Pública"
    assert records[0]["EXEMPLOS DE EVIDÊNCIA"] == "Relatório institucional anual"


def test_matrix_question_populates_subopcao_and_avoids_raw_sim_nao_rows() -> None:
    lines = load_fixture_lines("matriz_subopcao.txt")

    records = parse_pdf_lines(lines, input_path=Path("arquivo_2026.pdf"))

    assert len(records) == 4
    assert records[0]["TIPO"] == "MÚLTIPLA"

    matrix_rows = records[1:]
    assert [row["PERGUNTA"] for row in matrix_rows] == [
        "a) Há atribuições formais documentadas",
        "b) Há avaliação periódica das atribuições",
        "c) Não há atribuições formais para o tema",
    ]
    assert [row["SUB-OPÇÃO"] for row in matrix_rows] == ["Sim", "Sim", "Não"]
    assert all(row["PERGUNTA"] not in {"Sim", "Não"} for row in matrix_rows)

