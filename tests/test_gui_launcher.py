from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

import gui_launcher


class FakeRoot:
    def __init__(self) -> None:
        self.destroy_called = False

    def destroy(self) -> None:
        self.destroy_called = True


class FakeLogger:
    def __init__(self) -> None:
        self.warnings: list[str] = []

    def warning(self, message: str) -> None:
        self.warnings.append(message)


def test_launch_gui_flow_returns_1_when_no_pdf_selected(monkeypatch: MonkeyPatch) -> None:
    root = FakeRoot()
    logger = FakeLogger()
    warnings: list[str] = []

    monkeypatch.setattr(gui_launcher.app_main, "configure_logging", lambda: logger)
    monkeypatch.setattr(gui_launcher, "create_hidden_root", lambda: root)
    monkeypatch.setattr(gui_launcher, "select_input_pdfs", lambda: [])
    monkeypatch.setattr(gui_launcher, "show_warning", lambda _title, text: warnings.append(text))

    status = gui_launcher.launch_gui_flow()

    assert status == 1
    assert root.destroy_called is True
    assert warnings


def test_launch_gui_flow_returns_1_when_no_output_directory(monkeypatch: MonkeyPatch) -> None:
    root = FakeRoot()
    logger = FakeLogger()
    warnings: list[str] = []

    monkeypatch.setattr(gui_launcher.app_main, "configure_logging", lambda: logger)
    monkeypatch.setattr(gui_launcher, "create_hidden_root", lambda: root)
    monkeypatch.setattr(gui_launcher, "select_input_pdfs", lambda: [Path("entrada.pdf")])
    monkeypatch.setattr(gui_launcher, "select_output_directory", lambda: None)
    monkeypatch.setattr(gui_launcher, "show_warning", lambda _title, text: warnings.append(text))

    status = gui_launcher.launch_gui_flow()

    assert status == 1
    assert root.destroy_called is True
    assert warnings


def test_launch_gui_flow_returns_0_on_success(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    root = FakeRoot()
    logger = FakeLogger()
    infos: list[str] = []

    output_dir = tmp_path / "saida"
    output_path = output_dir / "consolidado_20260529_010203.xlsx"

    monkeypatch.setattr(gui_launcher.app_main, "configure_logging", lambda: logger)
    monkeypatch.setattr(gui_launcher, "create_hidden_root", lambda: root)
    monkeypatch.setattr(gui_launcher, "select_input_pdfs", lambda: [tmp_path / "entrada.pdf"])
    monkeypatch.setattr(gui_launcher, "select_output_directory", lambda: output_dir)
    monkeypatch.setattr(gui_launcher.app_main, "resolve_output_path", lambda _path: output_path)
    monkeypatch.setattr(gui_launcher.app_main, "run_processing", lambda _inputs, _output, _logger: 0)
    monkeypatch.setattr(gui_launcher, "show_info", lambda _title, text: infos.append(text))

    status = gui_launcher.launch_gui_flow()

    assert status == 0
    assert root.destroy_called is True
    assert infos


def test_launch_gui_flow_returns_1_on_processing_error(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    root = FakeRoot()
    logger = FakeLogger()
    errors: list[str] = []

    output_dir = tmp_path / "saida"
    output_path = output_dir / "consolidado_20260529_010203.xlsx"

    monkeypatch.setattr(gui_launcher.app_main, "configure_logging", lambda: logger)
    monkeypatch.setattr(gui_launcher, "create_hidden_root", lambda: root)
    monkeypatch.setattr(gui_launcher, "select_input_pdfs", lambda: [tmp_path / "entrada.pdf"])
    monkeypatch.setattr(gui_launcher, "select_output_directory", lambda: output_dir)
    monkeypatch.setattr(gui_launcher.app_main, "resolve_output_path", lambda _path: output_path)
    monkeypatch.setattr(gui_launcher.app_main, "run_processing", lambda _inputs, _output, _logger: 1)
    monkeypatch.setattr(gui_launcher, "show_error", lambda _title, text: errors.append(text))

    status = gui_launcher.launch_gui_flow()

    assert status == 1
    assert root.destroy_called is True
    assert errors
