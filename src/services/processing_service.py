from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

import pandas as pd  # type: ignore[reportMissingImports]


RowValue = str | int | float | None
RowData = dict[str, RowValue]

LineExtractor = Callable[[Path], list[str]]
LineParser = Callable[[list[str], Path | None, logging.Logger | None], list[RowData]]
FrameBuilder = Callable[[list[RowData]], pd.DataFrame]
FrameWriter = Callable[[pd.DataFrame, Path], None]
TableFormatter = Callable[[Path, int, int], None]
UniquePathResolver = Callable[[Path], Path]


def assign_global_row_ids(records: list[RowData]) -> list[RowData]:
    reassigned_records: list[RowData] = []
    for index, record in enumerate(records, start=1):
        reassigned_record = dict(record)
        reassigned_record["ID"] = index
        reassigned_records.append(reassigned_record)
    return reassigned_records


def run_processing_pipeline(
    input_paths: list[Path],
    output_path: Path,
    logger: logging.Logger,
    *,
    line_extractor: LineExtractor,
    line_parser: LineParser,
    frame_builder: FrameBuilder,
    frame_writer: FrameWriter,
    table_formatter: TableFormatter,
    unique_path_resolver: UniquePathResolver,
) -> int:
    try:
        all_records: list[RowData] = []

        for index, input_path in enumerate(input_paths, start=1):
            logger.info("Iniciando processamento (%s/%s): %s", index, len(input_paths), input_path)
            lines = line_extractor(input_path)
            records = line_parser(lines, input_path=input_path, logger=logger)
            all_records.extend(records)
            logger.info(
                "Arquivo consolidado (%s/%s): %s | linhas=%s",
                index,
                len(input_paths),
                input_path,
                len(records),
            )

        all_records = assign_global_row_ids(all_records)

        frame = frame_builder(all_records)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_output_path = unique_path_resolver(output_path)
        if final_output_path != output_path:
            logger.warning(
                "Arquivo de saida ja existe. Nome alternativo aplicado: %s",
                final_output_path,
            )

        frame_writer(frame, final_output_path)
        table_formatter(final_output_path, row_count=len(frame), column_count=len(frame.columns))
        logger.info(
            "Processamento concluido com sucesso: %s | arquivos=%s | linhas=%s",
            final_output_path,
            len(input_paths),
            len(all_records),
        )
        return 0
    except (OSError, ValueError, KeyError) as exc:
        logger.exception("Falha ao processar arquivo: %s", exc)
        return 1
