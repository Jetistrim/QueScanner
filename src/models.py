from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUntypedFunctionDecorator=false

from dataclasses import dataclass
import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


COLUMN_ORDER: list[str] = [
    "ID",
    "TIPO",
    "DIMENSÃO",
    "TEMA",
    "TÓPICO",
    "APLICAÇÃO SETORIAL",
    "CÓDIGO QUESTÃO",
    "ANO",
    "PERGUNTA",
    "SUB-OPÇÃO",
    "ORIENTAÇÕES",
    "TIPO DE EVIDÊNCIA",
    "EXEMPLOS DE EVIDÊNCIA",
    "STATUS",
    "PONTO FOCAL",
    "RESPONSÁVEL",
    "ENVIAR EVIDÊNCIA",
    "PTS. CABÍVEIS",
    "DISTRIBUIÇÃO",
    "RESPOSTA",
    "EVIDÊNCIA EMPRESA",
    "PTS. OBTIDOS",
    "%",
    "GRI/ISO",
    "TRIAL",
]


PATTERNS: dict[str, re.Pattern[str]] = {
    "dimension": re.compile(r"^Dimensão:\s+(.+)$"),
    "theme": re.compile(r"^Tema:\s+(.+)$"),
    "topic": re.compile(r"^(\d+\.\d+\.\d+)\.\s+(.+)$"),
    "sector_start": re.compile(r"^Aplicação setorial:\s*(.*)$"),
    "sector_general": re.compile(r"^\(Aplicação geral\)$", re.IGNORECASE),
    "question": re.compile(r"^(\d+\.\d+\.\d+\.\d+)\.\s+(.+)$"),
    "sim_nao": re.compile(r"^\(\s*\)\s+(Sim|Não)$"),
    "alternative": re.compile(r"^([a-z]\))\s*(.+)$"),
    "evidence_type": re.compile(r"^Tipo da evidência\s+(.+)$"),
    "evidence_examples": re.compile(r"^Exemplos de evidências aceitas:\s*(.*)$"),
    "page_noise": re.compile(r"^(\d+|INFORMAÇÃO PÚBLICA.*)$"),
}


QUESTION_TYPES = {
    "multiple": "MÚLTIPLA",
    "quantitative": "QUANTITATIVA",
    "single": "ÚNICA",
    "simple": "SIMPLES",
}


class OutputRowModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, str_strip_whitespace=True)

    id: int = Field(alias="ID", ge=1)
    question_type: str = Field(alias="TIPO")
    dimension: str | None = Field(alias="DIMENSÃO", default=None)
    theme: str | None = Field(alias="TEMA", default=None)
    topic: str | None = Field(alias="TÓPICO", default=None)
    sector_application: str | None = Field(alias="APLICAÇÃO SETORIAL", default=None)
    question_code: str | None = Field(alias="CÓDIGO QUESTÃO", default=None)
    year: int | None = Field(alias="ANO", default=None)
    question_text: str | None = Field(alias="PERGUNTA", default=None)
    sub_option: str | None = Field(alias="SUB-OPÇÃO", default=None)
    orientations: str | None = Field(alias="ORIENTAÇÕES", default=None)
    evidence_type: str | None = Field(alias="TIPO DE EVIDÊNCIA", default=None)
    evidence_examples: str | None = Field(alias="EXEMPLOS DE EVIDÊNCIA", default=None)
    status: str | None = Field(alias="STATUS", default=None)
    focal_point: str | None = Field(alias="PONTO FOCAL", default=None)
    responsible: str | None = Field(alias="RESPONSÁVEL", default=None)
    send_evidence: str | None = Field(alias="ENVIAR EVIDÊNCIA", default=None)
    possible_points: float | int | None = Field(alias="PTS. CABÍVEIS", default=None)
    distribution: float | int | None = Field(alias="DISTRIBUIÇÃO", default=None)
    response: str | int | float | None = Field(alias="RESPOSTA", default=None)
    company_evidence: str | None = Field(alias="EVIDÊNCIA EMPRESA", default=None)
    achieved_points: float | int | None = Field(alias="PTS. OBTIDOS", default=None)
    percent: float | int | None = Field(alias="%", default=None)
    gri_iso: str | None = Field(alias="GRI/ISO", default=None)
    trial: str | None = Field(alias="TRIAL", default=None)

    @field_validator("question_type")
    @classmethod
    def validate_question_type(cls, value: str) -> str:
        valid_types = set(QUESTION_TYPES.values())
        if value not in valid_types:
            raise ValueError(f"TIPO inválido: {value}. Esperados: {sorted(valid_types)}")
        return value

    @field_validator("question_code")
    @classmethod
    def validate_question_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.match(r"^\d+\.\d+\.\d+\.\d+$", value):
            raise ValueError(f"CÓDIGO QUESTÃO inválido: {value}")
        return value

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 2000 or value > 2100:
            raise ValueError(f"ANO fora do intervalo esperado: {value}")
        return value


def validate_output_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    validated: list[dict[str, object]] = []
    for index, record in enumerate(records, start=1):
        try:
            model = OutputRowModel.model_validate(record)
        except ValidationError as exc:
            raise ValueError(f"Registro inválido na linha {index}: {exc}") from exc
        validated.append(model.model_dump(by_alias=True))
    return validated


@dataclass(slots=True)
class ParseContext:
    dimension: str | None = None
    theme: str | None = None
    topic: str | None = None
    sector: str | None = None
    question_code: str | None = None
    question_text: str | None = None
    orientations: str | None = None
    evidence_type: str | None = None
    evidence_examples: str | None = None
    question_id: int = 0