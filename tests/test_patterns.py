from __future__ import annotations

from src.models import PATTERNS


def test_patterns_match_core_lines() -> None:
    assert PATTERNS["dimension"].match("Dimensão: 1. Ambiental")
    assert PATTERNS["theme"].match("Tema: 1.1. Água e Efluentes")
    assert PATTERNS["topic"].match("1.1.1. Água e Efluentes")
    assert PATTERNS["sector_start"].match("Aplicação setorial: Aplicável")
    assert PATTERNS["question"].match("1.1.1.1. Pergunta exemplo")
    assert PATTERNS["sim_nao"].match("( ) Sim")
    assert PATTERNS["alternative"].match("a) Alternativa A")
    assert PATTERNS["evidence_type"].match("Tipo da evidência Apenas Evidência Pública")
    assert PATTERNS["evidence_examples"].match("Exemplos de evidências aceitas: Relatório")


def test_page_noise_pattern_identifies_headers_and_numbers() -> None:
    assert PATTERNS["page_noise"].match("12")
    assert PATTERNS["page_noise"].match("INFORMAÇÃO PÚBLICA - ISE B3")
    assert not PATTERNS["page_noise"].match("a) Alternativa válida")


def test_sector_general_pattern_is_case_insensitive() -> None:
    assert PATTERNS["sector_general"].match("(Aplicação geral)")
    assert PATTERNS["sector_general"].match("(APLICAÇÃO GERAL)")


def test_sim_nao_pattern_rejects_unchecked_format() -> None:
    assert PATTERNS["sim_nao"].match("( ) Não")
    assert not PATTERNS["sim_nao"].match("(x) Sim")


def test_evidence_patterns_require_expected_prefix() -> None:
    assert not PATTERNS["evidence_type"].match("Tipo evidência Pública")
    assert not PATTERNS["evidence_examples"].match("Exemplos: Relatório")
