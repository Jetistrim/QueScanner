from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TypeAlias, TypedDict

from src.models import COLUMN_ORDER, PATTERNS, QUESTION_TYPES, ParseContext


RowValue: TypeAlias = str | int | float | None
RowData: TypeAlias = dict[str, RowValue]
DEFAULT_ORIENTATIONS_TEXT = "Sem orientacoes especificas."


class AlternativeItem(TypedDict):
    label: str
    text: str
    sub_option: str | None


def is_question_orientation_start(line: str) -> bool:
    stripped = line.strip()
    lowered = stripped.lower()
    return stripped.startswith("(") and ("selecione" in lowered or "preencha" in lowered)


def is_alternative_header_line(line: str) -> bool:
    stripped = line.strip()
    return (
        stripped.endswith(":")
        or stripped.startswith("Indique ")
        or stripped.startswith("________________")
    )


def is_alternative_continuation(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.endswith(":"):
        return False
    first_char = stripped[0]
    return first_char.isalpha() or first_char.isdigit()


def infer_year(lines: list[str], input_path: Path | None = None) -> int | None:
    for line in lines[:50]:
        match = re.search(r"(\d{4})\s*/\s*(\d{4})", line)
        if match:
            return int(match.group(1))

    if input_path is not None:
        match = re.search(r"(\d{4})", input_path.name)
        if match:
            return int(match.group(1))

    return None


def infer_question_type(orientations: str | None, alternatives: list[AlternativeItem]) -> tuple[str, bool]:
    text = (orientations or "").lower()
    if "selecione todas que se aplicam" in text:
        return QUESTION_TYPES["multiple"], False
    if "preencha todas que se aplicam" in text:
        return QUESTION_TYPES["quantitative"], False
    if "selecione uma" in text or "selecione apenas uma" in text:
        return QUESTION_TYPES["single"], False
    if alternatives and all(item["label"] in {"Sim", "Não"} for item in alternatives):
        return QUESTION_TYPES["simple"], False
    if not alternatives and "sim" in text and "não" in text:
        return QUESTION_TYPES["simple"], False
    return QUESTION_TYPES["single"], True


def is_lettered_alternative(label: str) -> bool:
    return bool(re.match(r"^[a-z]\)$", label, flags=re.IGNORECASE))


def normalize_alternatives_for_matrix(alternatives: list[AlternativeItem]) -> list[AlternativeItem]:
    has_matrix_items = any(is_lettered_alternative(item["label"]) for item in alternatives)
    if not has_matrix_items:
        return alternatives

    return [item for item in alternatives if item["label"] not in {"Sim", "Não"}]


def empty_row() -> RowData:
    return {column: None for column in COLUMN_ORDER}


def normalize_orientations(orientations: str | None) -> str:
    if orientations is None:
        return DEFAULT_ORIENTATIONS_TEXT

    normalized = orientations.strip()
    return normalized if normalized else DEFAULT_ORIENTATIONS_TEXT


def emit_question_rows(
    context: ParseContext,
    year: int | None,
    alternatives: list[AlternativeItem],
    logger: logging.Logger | None = None,
) -> list[RowData]:
    if not context.question_code or not context.question_text:
        return []

    normalized_alternatives = normalize_alternatives_for_matrix(alternatives)
    question_type, used_fallback = infer_question_type(context.orientations, normalized_alternatives)
    normalized_orientations = normalize_orientations(context.orientations)
    if used_fallback and logger is not None:
        logger.warning(
            "Tipo de questão não identificado de forma explícita. Usando default ÚNICA para %s",
            context.question_code,
        )
    base: RowData = {
        "TIPO": question_type,
        "DIMENSÃO": context.dimension,
        "TEMA": context.theme,
        "TÓPICO": context.topic,
        "APLICAÇÃO SETORIAL": context.sector,
        "CÓDIGO QUESTÃO": context.question_code,
        "ANO": year,
        "ORIENTAÇÕES": normalized_orientations,
        "TIPO DE EVIDÊNCIA": context.evidence_type,
        "EXEMPLOS DE EVIDÊNCIA": context.evidence_examples,
        "STATUS": None,
        "PONTO FOCAL": None,
        "RESPONSÁVEL": None,
        "ENVIAR EVIDÊNCIA": None,
        "PTS. CABÍVEIS": None,
        "DISTRIBUIÇÃO": None,
        "EVIDÊNCIA EMPRESA": None,
        "PTS. OBTIDOS": None,
        "%": None,
        "GRI/ISO": None,
        "TRIAL": None,
    }

    record = empty_row()
    record.update(base)
    record["ID"] = context.question_id
    record["PERGUNTA"] = context.question_text
    record["SUB-OPÇÃO"] = None
    record["RESPOSTA"] = None

    records = [record]

    if normalized_alternatives:
        for alternative in normalized_alternatives:
            alt_row = empty_row()
            alt_row.update(base)
            alt_row["ID"] = context.question_id
            alt_row["PERGUNTA"] = alternative["text"]
            alt_row["SUB-OPÇÃO"] = alternative.get("sub_option")
            alt_row["RESPOSTA"] = None
            records.append(alt_row)
    elif question_type == QUESTION_TYPES["simple"]:
        for option in ("Sim", "Não"):
            alt_row = empty_row()
            alt_row.update(base)
            alt_row["ID"] = context.question_id
            alt_row["PERGUNTA"] = option
            alt_row["SUB-OPÇÃO"] = None
            alt_row["RESPOSTA"] = None
            records.append(alt_row)

    if logger is not None:
        logger.info(
            "Questão processada: %s | tipo=%s | alternativas=%s",
            context.question_code,
            question_type,
            len(records) - 1,
        )

    return records


def parse_pdf_lines(
    lines: list[str],
    input_path: Path | None = None,
    logger: logging.Logger | None = None,
) -> list[RowData]:
    context = ParseContext()
    year = infer_year(lines, input_path=input_path)
    if year is None and logger is not None:
        logger.warning("Ano não identificado no conteúdo e no nome do arquivo")

    records: list[RowData] = []
    current_sector_parts: list[str] = []
    current_orientation_parts: list[str] = []
    current_alternatives: list[AlternativeItem] = []
    current_matrix_sub_option: str | None = None

    state = "IDLE"

    def flush_current_question() -> None:
        if context.question_code and context.question_text:
            records.extend(emit_question_rows(context, year, current_alternatives, logger=logger))

    for raw_line in lines:
        line = raw_line.strip()
        if not line or PATTERNS["page_noise"].match(line):
            continue

        if match := PATTERNS["dimension"].match(line):
            context.dimension = match.group(1).strip()
            state = "READING_DIMENSION"
            continue

        if match := PATTERNS["theme"].match(line):
            context.theme = match.group(1).strip()
            state = "READING_THEME"
            continue

        if match := PATTERNS["topic"].match(line):
            context.topic = f"{match.group(1)}. {match.group(2).strip()}"
            context.sector = None
            current_sector_parts = []
            state = "READING_TOPIC"
            continue

        if match := PATTERNS["sector_start"].match(line):
            current_sector_parts = [match.group(1).strip()] if match.group(1).strip() else []
            context.sector = " ".join(current_sector_parts) if current_sector_parts else None
            state = "READING_SECTOR"
            continue

        if PATTERNS["sector_general"].match(line):
            context.sector = "(Aplicação geral)"
            current_sector_parts = [context.sector]
            state = "READING_SECTOR"
            continue

        if match := PATTERNS["question"].match(line):
            flush_current_question()
            context.question_id += 1
            context.question_code = match.group(1)
            context.question_text = match.group(2).strip()
            current_orientation_parts = []
            current_alternatives = []
            current_matrix_sub_option = None
            context.orientations = None
            context.evidence_type = None
            context.evidence_examples = None
            state = "READING_QUESTION"
            continue

        if match := PATTERNS["sim_nao"].match(line):
            current_matrix_sub_option = match.group(1)
            current_alternatives.append({"label": match.group(1), "text": match.group(1), "sub_option": None})
            state = "READING_ALTERNATIVES"
            continue

        if match := PATTERNS["alternative"].match(line):
            current_alternatives.append(
                {
                    "label": match.group(1),
                    "text": f"{match.group(1)} {match.group(2).strip()}",
                    "sub_option": current_matrix_sub_option,
                }
            )
            state = "READING_ALTERNATIVES"
            continue

        if match := PATTERNS["evidence_type"].match(line):
            context.evidence_type = match.group(1).strip()
            state = "READING_EVIDENCE"
            continue

        if match := PATTERNS["evidence_examples"].match(line):
            context.evidence_examples = match.group(1).strip() or None
            state = "READING_EVIDENCE"
            continue

        if state == "READING_SECTOR":
            current_sector_parts.append(line)
            context.sector = " ".join(current_sector_parts).strip()
            continue

        if state == "READING_QUESTION":
            if context.orientations is None and not is_question_orientation_start(line):
                context.question_text = f"{context.question_text} {line}".strip()
            else:
                current_orientation_parts.append(line)
                context.orientations = " ".join(current_orientation_parts).strip()
            continue

        if state == "READING_ALTERNATIVES" and current_alternatives:
            if is_alternative_continuation(line) and not is_alternative_header_line(line):
                current_alternatives[-1]["text"] = f'{current_alternatives[-1]["text"]} {line}'.strip()
            else:
                current_orientation_parts.append(line)
                context.orientations = " ".join(current_orientation_parts).strip()
            continue

        if state == "READING_EVIDENCE":
            if context.evidence_examples:
                context.evidence_examples = f"{context.evidence_examples} {line}".strip()
            else:
                context.evidence_examples = line
            continue

    flush_current_question()
    return records