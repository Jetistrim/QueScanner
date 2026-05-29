from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import TypeAlias

import pandas as pd  # type: ignore[reportMissingImports]
import pdfplumber  # type: ignore[reportMissingImports]

from src.extractor import parse_pdf_lines
from src.exporters import xlsx_exporter
from src.io import pdf_reader
from src.models import COLUMN_ORDER as MODEL_COLUMN_ORDER
from src.services.processing_service import (
    assign_global_row_ids as service_assign_global_row_ids,
    run_processing_pipeline,
)


LOGGER_NAME = "que_scanner"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"
DEFAULT_OUTPUT_BASENAME = "consolidado"
RowValue: TypeAlias = str | int | float | None
RowData: TypeAlias = dict[str, RowValue]
COLUMN_ORDER = MODEL_COLUMN_ORDER


def configure_logging() -> logging.Logger:
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s")

    file_handler = logging.FileHandler(logs_dir / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def extract_lines_from_pdf(pdf_path: Path) -> list[str]:
    pdf_reader.pdfplumber = pdfplumber
    return pdf_reader.extract_lines_from_pdf(pdf_path)


def build_dataframe(records: list[RowData]) -> pd.DataFrame:
    return xlsx_exporter.build_dataframe(records)


def apply_basic_table_format(output_path: Path, row_count: int, column_count: int) -> None:
    xlsx_exporter.apply_basic_table_format(output_path, row_count=row_count, column_count=column_count)


def build_generated_output_filename() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{DEFAULT_OUTPUT_BASENAME}_{timestamp}.xlsx"


def ensure_unique_output_path(output_path: Path) -> Path:
    if not output_path.exists():
        return output_path

    stem = output_path.stem
    suffix = output_path.suffix
    counter = 1
    while True:
        candidate = output_path.with_name(f"{stem}_{counter:02d}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def resolve_output_path(raw_output_path: Path) -> Path:
    is_xlsx_file = raw_output_path.suffix.lower() == ".xlsx"

    if not is_xlsx_file:
        output_dir = raw_output_path if raw_output_path.is_absolute() else (PROJECT_ROOT / raw_output_path).resolve()
        return output_dir / build_generated_output_filename()

    if raw_output_path.is_absolute():
        return raw_output_path

    # If only a filename is provided, keep test artifacts under outputs/.
    if raw_output_path.parent == Path("."):
        return DEFAULT_OUTPUT_DIR / raw_output_path.name

    return (PROJECT_ROOT / raw_output_path).resolve()


def parse_cli_args(argv: list[str], logger: logging.Logger) -> tuple[list[Path], Path] | None:
    if len(argv) < 3:
        logger.error(
            "Uso esperado: python main.py <input1.pdf> [input2.pdf ...] <output.xlsx|output_dir>"
        )
        return None

    input_paths = [Path(value) for value in argv[1:-1]]
    raw_output_arg = Path(argv[-1])
    output_path = resolve_output_path(raw_output_arg)

    missing_inputs = [path for path in input_paths if not path.exists()]
    if missing_inputs:
        for missing in missing_inputs:
            logger.error("Arquivo PDF não encontrado: %s", missing)
        return None

    invalid_inputs = [path for path in input_paths if not path.is_file() or path.suffix.lower() != ".pdf"]
    if invalid_inputs:
        for invalid in invalid_inputs:
            logger.error("Entrada inválida (esperado arquivo .pdf): %s", invalid)
        return None

    if raw_output_arg.suffix.lower() == ".xlsx":
        logger.info("Modo de saída: arquivo explícito (.xlsx)")
    else:
        logger.info("Modo de saída: pasta (nome de arquivo gerado automaticamente)")

    return input_paths, output_path


def assign_global_row_ids(records: list[RowData]) -> list[RowData]:
    return service_assign_global_row_ids(records)


def run_processing(input_paths: list[Path], output_path: Path, logger: logging.Logger) -> int:
    return run_processing_pipeline(
        input_paths,
        output_path,
        logger,
        line_extractor=extract_lines_from_pdf,
        line_parser=parse_pdf_lines,
        frame_builder=build_dataframe,
        frame_writer=xlsx_exporter.export_to_xlsx,
        table_formatter=apply_basic_table_format,
        unique_path_resolver=ensure_unique_output_path,
    )


def main() -> int:
    logger = configure_logging()

    parsed = parse_cli_args(sys.argv, logger)
    if parsed is None:
        return 1

    input_paths, output_path = parsed
    return run_processing(input_paths, output_path, logger)


if __name__ == "__main__":
    raise SystemExit(main())