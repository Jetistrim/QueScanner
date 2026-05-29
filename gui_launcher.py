from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import main as app_main

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except ImportError:  # pragma: no cover - fallback for environments without Tk
    tk = None
    filedialog = None
    messagebox = None


def create_hidden_root() -> Any:
    if tk is None:
        raise RuntimeError("Tkinter não está disponível neste ambiente Python")

    root = tk.Tk()
    root.withdraw()
    return root


def select_input_pdfs() -> list[Path]:
    if filedialog is None:
        return []

    selected = filedialog.askopenfilenames(
        title="Selecione um ou mais arquivos PDF",
        filetypes=[("Arquivos PDF", "*.pdf")],
    )
    return [Path(path) for path in selected]


def select_output_directory() -> Path | None:
    if filedialog is None:
        return None

    selected = filedialog.askdirectory(title="Selecione a pasta para salvar o XLS")
    if not selected:
        return None
    return Path(selected)


def show_warning(title: str, text: str) -> None:
    if messagebox is None:
        return
    messagebox.showwarning(title, text)


def show_info(title: str, text: str) -> None:
    if messagebox is None:
        return
    messagebox.showinfo(title, text)


def show_error(title: str, text: str) -> None:
    if messagebox is None:
        return
    messagebox.showerror(title, text)


def launch_gui_flow() -> int:
    logger = app_main.configure_logging()

    try:
        root = create_hidden_root()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        show_info(
            "QueScanner - Instrução",
            "Passo 1 de 2:\nSelecione um ou mais arquivos PDF para processamento.",
        )
        input_paths = select_input_pdfs()
        if not input_paths:
            logger.warning("Execução cancelada: nenhum PDF selecionado")
            show_warning("QueScanner", "Nenhum PDF foi selecionado. Operação cancelada.")
            return 1

        show_info(
            "QueScanner - Instrução",
            "Passo 2 de 2:\nSelecione a pasta onde o arquivo XLS será salvo.",
        )
        output_dir = select_output_directory()
        if output_dir is None:
            logger.warning("Execução cancelada: pasta de saída não selecionada")
            show_warning("QueScanner", "Nenhuma pasta de saída foi selecionada. Operação cancelada.")
            return 1

        output_path = app_main.resolve_output_path(output_dir)
        status_code = app_main.run_processing(input_paths, output_path, logger)

        if status_code == 0:
            show_info(
                "QueScanner",
                "Processamento concluído com sucesso.\n"
                f"Arquivo salvo em: {output_path.parent}",
            )
            return 0

        show_error(
            "QueScanner",
            "O processamento terminou com erro. Consulte logs/app.log para detalhes.",
        )
        return 1
    finally:
        root.destroy()


if __name__ == "__main__":
    raise SystemExit(launch_gui_flow())
