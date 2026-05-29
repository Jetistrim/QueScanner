# QueScanner

Extrator em Python para ler questionários ISE B3 em PDF e gerar uma planilha `.xlsx` denormalizada.

## Execução

```bash
python main.py <input.pdf> <output.xlsx>
```

Também é possível consolidar vários PDFs em uma única planilha:

```bash
python main.py <input1.pdf> <input2.pdf> ... <output.xlsx>
```

Para uso via Power Automate Desktop (DOS), também é possível informar uma pasta de saída
como último argumento. Nesse modo, o programa gera automaticamente o nome final do arquivo:

```bash
python main.py <input1.pdf> <input2.pdf> ... <output_dir>
```

Regras do modo pasta de saída:

- Nome gerado no padrão `consolidado_YYYYMMDD_HHMMSS.xlsx`.
- Se já existir arquivo com o mesmo nome, o script gera sufixo incremental (`_01`, `_02`, ...).
- O script não sobrescreve arquivos existentes.

O script foi preparado para uso via Power Automate Desktop e depende apenas de caminhos informados na linha de comando.

## Execução manual no Windows (.bat)

Para executar sem Power Automate e sem informar caminhos na CLI, use:

```bat
run_gui.bat
```

Fluxo da execução manual:

- Abre seletor para escolher um ou mais arquivos `.pdf`.
- Abre seletor para escolher a pasta onde será salvo o `.xlsx`.
- O arquivo final mantém o padrão de nome automático `consolidado_YYYYMMDD_HHMMSS.xlsx`.
- Se já existir nome igual, aplica sufixo incremental (`_01`, `_02`, ...).
- Exibe popup de sucesso ou erro ao final do processamento.

Se o usuário cancelar qualquer seletor, a execução é encerrada sem gerar arquivo.

## Dependências

- `pandas` para montar o `DataFrame` e exportar o Excel.
- `pdfplumber` para extrair texto linha a linha preservando a ordem de leitura visual.
- `openpyxl` como backend de escrita `.xlsx`.

## Estrutura inicial

- `main.py` na raiz: CLI, logging, leitura do PDF e exportação.
- `src/extractor.py`: máquina de estados e parsing.
- `src/models.py`: colunas, padrões e constantes.

## Arquitetura modular e extensibilidade

O projeto foi organizado para permitir crescimento incremental sem quebrar o pipeline principal.

Componentes atuais:

- `main.py`: orquestra entrada/saída (CLI), logging e fluxo de processamento.
- `src/extractor.py`: parser do questionário (máquina de estados) sem I/O de arquivos.
- `src/models.py`: contratos de dados, colunas de saída e validações.

Como expandir com segurança:

1. Criar o novo módulo por responsabilidade (`parser`, `exporter`, `transformer` ou `validator`).
2. Definir contrato explícito com tipagem nas funções públicas.
3. Integrar no fluxo de `main.py` sem duplicar regras de negócio.
4. Reutilizar validações e constantes de `src/models.py`.
5. Adicionar testes unitários e de integração para o novo comportamento.

Estrutura recomendada para novos módulos:

- `src/parsers/<origem>.py`: novos formatos de entrada (ex.: outro layout de questionário).
- `src/exporters/<formato>.py`: novos formatos de saída (ex.: CSV, JSON, Parquet).
- `src/transformers/<operacao>.py`: transformações de dados antes da saída final.
- `src/validators/<regra>.py`: validações adicionais de consistência.

As regras normativas de modularidade (contratos, naming e checklist) estão em `PADRÃO DE CÓDIGO.md`.

## Saída esperada

O arquivo final deve conter as 25 colunas na ordem definida no padrão do projeto. As colunas manuais permanecem vazias no bootstrap inicial.

O campo `ID` é gerado como identificador único por linha (chave primária da tabela denormalizada), útil para atualizações direcionadas em fluxos downstream (Power Automate/SharePoint).

## Logs

O processamento registra eventos em `logs/app.log` com formato de data, nível e mensagem.

## Testes e cobertura

Executar a suíte de testes:

```bash
python -m pytest -q tests
```

Executar com cobertura:

```bash
python -m pytest --cov=src --cov=main --cov-report=term-missing -q tests
```

Critério atual de aprovação da Fase 2: cobertura total mínima de 90%.

O gate de cobertura está automatizado em `pytest.ini` com `--cov-fail-under=90`.
Isso faz com que tanto execução local quanto CI falhem automaticamente abaixo de 90%.