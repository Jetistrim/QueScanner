from __future__ import annotations

import logging
from pathlib import Path

from main import assign_global_row_ids, ensure_unique_output_path, parse_cli_args, resolve_output_path


def test_assign_global_row_ids_is_sequential_and_preserves_other_fields() -> None:
    records: list[dict[str, str | int | float | None]] = [
        {"ID": 10, "PERGUNTA": "Q1"},
        {"ID": 10, "PERGUNTA": "A1"},
        {"ID": 20, "PERGUNTA": "Q2"},
    ]

    output = assign_global_row_ids(records)

    assert [row["ID"] for row in output] == [1, 2, 3]
    assert [row["PERGUNTA"] for row in output] == ["Q1", "A1", "Q2"]


def test_resolve_output_path_for_filename_uses_outputs_directory() -> None:
    output = resolve_output_path(Path("resultado.xlsx"))

    assert output.name == "resultado.xlsx"
    assert output.parent.name == "outputs"


def test_resolve_output_path_for_directory_generates_xlsx_name(tmp_path: Path) -> None:
    output = resolve_output_path(tmp_path)

    assert output.parent == tmp_path
    assert output.suffix == ".xlsx"
    assert output.stem.startswith("consolidado_")


def test_ensure_unique_output_path_returns_incremental_name(tmp_path: Path) -> None:
    base_output = tmp_path / "saida.xlsx"
    base_output.write_text("x", encoding="utf-8")
    (tmp_path / "saida_01.xlsx").write_text("x", encoding="utf-8")

    output = ensure_unique_output_path(base_output)

    assert output == tmp_path / "saida_02.xlsx"


def test_parse_cli_args_returns_none_when_missing_pdf(tmp_path: Path) -> None:
    logger = logging.getLogger("test-cli-missing")

    result = parse_cli_args(["main.py", "inexistente.pdf", "saida.xlsx"], logger)

    assert result is None


def test_parse_cli_args_returns_inputs_and_output_when_valid(tmp_path: Path) -> None:
    logger = logging.getLogger("test-cli-valid")
    input_pdf = tmp_path / "entrada.pdf"
    input_pdf.write_text("fake", encoding="utf-8")

    result = parse_cli_args(["main.py", str(input_pdf), "saida.xlsx"], logger)

    assert result is not None
    inputs, output = result
    assert inputs == [input_pdf]
    assert output.name == "saida.xlsx"


def test_parse_cli_args_accepts_output_directory(tmp_path: Path) -> None:
    logger = logging.getLogger("test-cli-output-dir")
    input_pdf = tmp_path / "entrada com espaco.pdf"
    input_pdf.write_text("fake", encoding="utf-8")
    output_dir = tmp_path / "saida pasta"

    result = parse_cli_args(["main.py", str(input_pdf), str(output_dir)], logger)

    assert result is not None
    _, output = result
    assert output.parent == output_dir
    assert output.suffix == ".xlsx"
