# Padrões de Excelência: Extrator de PDF ISE B3

## 1. Contexto e escopo do projeto

- **Objetivo:** Script Python que lê questionários ISE B3 em PDF, interpreta a hierarquia `Dimensão > Tema > Tópico > Questão > Alternativas` e gera uma tabela denormalizada em `.xlsx`, onde cada linha representa uma alternativa ou campo de uma questão, com todo o contexto da questão repetido em cada linha.
- **Gatilho de execução:** Orquestrado via Power Automate Desktop (PAD) por linha de comando: `python main.py <input.pdf> <output.xlsx>`.
- **Consumidores downstream:** Usuários de negócio (revisão manual no Excel) e SharePoint Lists (ingestão automatizada).
- **Restrições corporativas (Hackathon):**
  - Execução via comando único (`python main.py <input> <output>`).
  - Proibido caminhos fixos (hardcoded).
  - Obrigatório tratamento de erros, logs estruturados e uso de bibliotecas homologadas ou justificadas.
  - Ausência total de credenciais no código-fonte.

---

## 2. Stack aprovada

| Camada | Ferramenta | Papel |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.11+ | Processamento lógico e motor de extração. |
| **Manipulação de dados** | `pandas` | Estruturação da tabela denormalizada e exportação para `.xlsx`. |
| **Extração de PDF** | `pdfplumber` | Leitura linha a linha do texto semiestruturado. Preferido sobre PyMuPDF por expor as linhas na ordem de leitura visual sem ruído de layout. **Justificativa obrigatória no README.md.** |
| **Expressões regulares** | `re` (nativo) | Identificação de padrões de linha (códigos, alternativas, evidências). |
| **Observabilidade** | `logging` (nativo) | Geração de `logs/app.log` para auditoria e debug. |

**Regra de dependência:** Proibido introduzir bibliotecas de terceiros fora desta tabela sem autorização explícita.

---

## 3. Fases de desenvolvimento

### ✅ Fase 0 — Descoberta e MVP lógico `[ATIVA | RIGOR: BAIXO]`

**Foco:** Construção da Máquina de Estados iterativa, extração limpa via Regex, estruturação relacional correta no Pandas.

**A IA NÃO deve:** Criar testes unitários, configurar CI/CD, focar em performance prematura ou empacotamento complexo.

**A IA DEVE:** Isolar as funções de leitura, parsing e exportação. Manter responsabilidade única. Utilizar tipagem básica (`-> list`, `-> pd.DataFrame`).

**Critério de saída da fase:** O script processa o PDF de exemplo de ponta a ponta e gera o `.xlsx` com:
  - Nenhuma célula de contexto vazia nas colunas de propagação (ver Seção 6).
  - Todos os tipos de questão reconhecidos corretamente (SIMPLES, ÚNICA, MÚLTIPLA, QUANTITATIVA).
  - Alternativas de questões matriciais com SUB-OPÇÃO preenchida.
  - `app.log` registrando cada questão processada e eventuais avisos.

### 🔲 Fase 1 — Contratos e arquitetura `[RIGOR: MÉDIO]`
**Foco:** Validação da estrutura de dados com `pydantic`. Isolamento estrito de I/O.
**Critério de saída:** Tratamento de erros detalhado, validação de tipos antes da inserção no DataFrame.

### 🔲 Fase 2 — Testes e blindagem `[RIGOR: ALTO]`
**Foco:** Testes unitários das funções de Regex e das transições da máquina de estados usando `.txt` mockados.
**Critério de saída:** Cobertura de cenários de exceção (PDFs mal formatados, quebras de página no meio de alternativas).

### 🔲 Fase 3 — Produtização e operação `[RIGOR: MÁXIMO]`
**Foco:** Documentação final de deploy (power automate), checklist de governança, logs auditáveis.

---

## 4. Arquitetura e separação de responsabilidades

```text
/
├── main.py          # Ponto de entrada: CLI via sys.argv, orquestra o fluxo
├── extractor.py     # Máquina de estados: recebe lista de linhas, devolve list[dict]
├── models.py        # Estruturas de dados: constantes, colunas, valores esperados
├── requirements.txt # Dependências estritas e versionadas
└── logs/            # Criado em runtime pelo script
```

**Regra de ouro:** A lógica de Regex e parsing (`extractor.py`) nunca lê nem escreve arquivos. Recebe `list[str]` e devolve `list[dict]`. Todo I/O fica em `main.py`.

---

## 5. Padrões de código

- **Tipagem:** Type hints em todas as assinaturas: `def parse_question_block(lines: list[str]) -> list[dict]:`.
- **Nomenclatura:** `snake_case`. Nomes descritivos: `parse_alternatives`, `extract_evidence_table`, não `process_data`.
- **Erros:** Proibido `except Exception as e: pass`. Capturar exceções específicas. Falha em uma questão → `logger.warning()` e continua para a próxima. Nunca quebra o processo inteiro.
- **Logging:** Configurado no `main.py`. Proibido `print()`. Usar `logger.info()`, `logger.warning()`, `logger.error()`.
- **Caminhos:** Usar `pathlib.Path`. Argumentos lidos de `sys.argv`, nunca hardcoded.

---

## 6. Schema de saída — colunas do `.xlsx`

A tabela é **denormalizada**: cada linha representa uma alternativa (ou campo de resposta de questão quantitativa). Colunas de contexto da questão se repetem em todas as linhas do bloco.

### 6.1 Colunas geradas pelo script (extraídas do PDF)

| # | Coluna | Tipo Python | Presente em | Observação |
|---|--------|-------------|-------------|------------|
| 1 | `ID` | `int` | Todas as linhas | **Chave primária da linha**. Sequencial global estrito, começa em 1 e incrementa 1 por linha emitida (enunciado e alternativas). Nunca repetir o mesmo ID em linhas diferentes. |
| 2 | `TIPO` | `str` | Todas as linhas do bloco | `SIMPLES` / `ÚNICA` / `MÚLTIPLA` / `QUANTITATIVA`. Ver Seção 8.1. |
| 3 | `DIMENSÃO` | `str` | Todas as linhas do bloco | Ex: `"1. Ambiental"`. |
| 4 | `TEMA` | `str` | Todas as linhas do bloco | Ex: `"1.1. Água e Efluentes"`. |
| 5 | `TÓPICO` | `str` | Todas as linhas do bloco | Ex: `"1.1.1. Água e Efluentes"`. |
| 6 | `APLICAÇÃO SETORIAL` | `str` | Todas as linhas do bloco | Texto completo concatenado, sem quebras de linha. |
| 7 | `CÓDIGO QUESTÃO` | `str` | Todas as linhas do bloco | Ex: `"1.1.1.1"`. Sem o ponto final. |
| 8 | `ANO` | `int` | Todas as linhas do bloco | Extraído do cabeçalho do PDF ou inferido do nome do arquivo. |
| 9 | `PERGUNTA` | `str` | Todas as linhas | Linha de enunciado: texto da questão. Demais linhas: texto da alternativa. |
| 10 | `SUB-OPÇÃO` | `str` ou `None` | Linhas de alternativa | Preenchido apenas em questões matriciais. Ver Seção 8.3. |
| 11 | `ORIENTAÇÕES` | `str` ou `None` | Todas as Linhas do bloco | Texto entre parênteses após o enunciado + texto instrucional complementar. |
| 12 | `TIPO DE EVIDÊNCIA` | `str` ou `None` | Todas as linhas do bloco | Ex: `"Apenas Evidência Pública"`. |
| 13 | `EXEMPLOS DE EVIDÊNCIA` | `str` ou `None` | Todas as linhas do bloco | Texto concatenado da tabela de evidências do PDF. |

### 6.2 Colunas criadas vazias pelo script (preenchidas manualmente ou por fórmula)

| # | Coluna | Tipo esperado | Responsável pelo preenchimento |
|---|--------|---------------|-------------------------------|
| 14 | `STATUS` | `str` | Humano: `Mantida` / `Alterada` / `Nova`. |
| 15 | `PONTO FOCAL` | `str` | Humano. |
| 16 | `RESPONSÁVEL` | `str` | Humano. |
| 17 | `ENVIAR EVIDÊNCIA` | `str` | Humano: `Sim` / `Não`. |
| 18 | `PTS. CABÍVEIS` | `float` | Humano (definido pela B3 no sistema oficial). |
| 19 | `DISTRIBUIÇÃO` | `float` | Humano ou fórmula downstream. |
| 20 | `RESPOSTA` | `str` | Humano: `X` / `-` / `N` / valor numérico. Ver Seção 8.4. |
| 21 | `EVIDÊNCIA EMPRESA` | `str` | Humano: URL do SharePoint. |
| 22 | `PTS. OBTIDOS` | `float` | Fórmula Excel. |
| 23 | `%` | `float` | Fórmula Excel (somente linha de enunciado). |
| 24 | `GRI/ISO` | `str` | Humano. |
| 25 | `TRIAL` | `str` | B3 (após sorteio). |

> **Ordem das colunas no output:** As colunas devem seguir exatamente a numeração acima (1 a 25). Usar `models.py` para definir a lista de colunas como constante e garantir a ordem no DataFrame final.

### 6.3 Regra mandatória de chave e agrupamento

- `ID` é identificador técnico **único por linha** (PK da tabela flat), obrigatório para atualizações direcionadas em SharePoint/Power Automate.
- `CÓDIGO QUESTÃO` é identificador funcional de agrupamento da pergunta (enunciado + alternativas), e **não substitui** a unicidade do `ID`.
- Em consolidação de múltiplos PDFs, o `ID` deve ser reatribuído no conjunto final para manter sequência contínua `1..N`, sem duplicidade.

---

## 7. Máquina de estados (`extractor.py`)

O parser opera linha a linha sobre a lista de strings extraída do PDF. O estado atual determina como cada linha é interpretada.

### 7.1 Estados

| Estado | Descrição |
|--------|-----------|
| `IDLE` | Estado inicial. Aguarda cabeçalho de dimensão. |
| `READING_DIMENSION` | Leu `"Dimensão: ..."`. Armazena e aguarda tema. |
| `READING_THEME` | Leu `"Tema: ..."`. Armazena e aguarda tópico. |
| `READING_TOPIC` | Leu código de tópico (`X.X.X.`). Armazena e aguarda aplicação setorial ou questão. |
| `READING_SECTOR` | Leu `"Aplicação setorial:"`. Acumula linhas até encontrar próximo estado. |
| `READING_QUESTION` | Leu código de questão (`X.X.X.X.`). Acumula enunciado e orientações. |
| `READING_ALTERNATIVES` | Leu `"( ) Sim"` ou primeira alternativa `a)`. Acumula alternativas. |
| `READING_EVIDENCE` | Leu `"Tipo da evidência"`. Acumula linhas da tabela de evidências. |

### 7.2 Transições e gatilhos regex

```python
# Padrões a aplicar em cada linha, em ordem de prioridade:

PATTERNS = {
    "dimension":    r"^Dimensão:\s+(.+)$",
    "theme":        r"^Tema:\s+(.+)$",
    "topic":        r"^(\d+\.\d+\.\d+)\.\s+(.+)$",
    "sector_start": r"^Aplicação setorial:\s*(.*)$",
    "question":     r"^(\d+\.\d+\.\d+\.\d+)\.\s+(.+)$",
    "sim_nao":      r"^\(\s*\)\s+(Sim|Não)$",
    "alternative":  r"^([a-z]\))\s*(.+)$",
    "evidence_type":r"^Tipo da evidência\s+(.+)$",
    "evidence_ex":  r"^Exemplos de evidências aceitas:\s*(.*)$",
    "page_noise":   r"^(\d+|INFORMAÇÃO PÚBLICA.*)$",  # linhas a descartar
}
```

### 7.3 Diagrama de transições

```
IDLE
 └─ [dimension] ──────────────────────────→ READING_DIMENSION
                                                   │
                                            [theme]│
                                                   ↓
                                          READING_THEME
                                                   │
                                           [topic] │
                                                   ↓
                                          READING_TOPIC ←──────────────────────┐
                                                   │                            │
                                   [sector_start]  │   [question]               │
                                                   │                            │
                            READING_SECTOR ←───────┘                            │
                                    │                                            │
                            [question] or                                        │
                            [first non-sector line]                              │
                                    │                                            │
                                    ↓                                            │
                            READING_QUESTION ←─────────────────────────────┐    │
                                    │                                       │    │
                             [sim_nao] or [alternative]                     │    │
                                    │                                       │    │
                                    ↓                                       │    │
                           READING_ALTERNATIVES                             │    │
                                    │                                       │    │
                           [evidence_type]                                  │    │
                                    │                                       │    │
                                    ↓                                       │    │
                           READING_EVIDENCE                                 │    │
                                    │                                       │    │
                            [question] ─────────────────────────────────────┘   │
                            [topic]   ───────────────────────────────────────────┘
```

### 7.4 Comportamento por estado ao encontrar cada padrão

| Estado atual | Padrão detectado | Ação |
|---|---|---|
| qualquer | `page_noise` | Descartar linha. Não mudar estado. |
| `READING_SECTOR` | linha sem padrão conhecido | Concatenar ao texto de `APLICAÇÃO SETORIAL`. |
| `READING_QUESTION` | linha sem padrão conhecido | Concatenar às `ORIENTAÇÕES` da questão atual. |
| `READING_QUESTION` | `question` | Finalizar questão atual → emitir bloco → iniciar nova questão. |
| `READING_ALTERNATIVES` | linha sem padrão de alternativa | Concatenar texto à última alternativa acumulada (quebra de linha do PDF). |
| `READING_EVIDENCE` | `evidence_ex` + linhas seguintes | Concatenar até encontrar próxima questão ou tópico. |

---

## 8. Regras de negócio e denormalização

### 8.1 Determinação do TIPO da questão

Analisar o texto de `ORIENTAÇÕES` da questão:

| Texto encontrado em ORIENTAÇÕES | TIPO atribuído |
|---|---|
| Contém `"Selecione todas que se aplicam"` | `MÚLTIPLA` |
| Contém `"Preencha todas que se aplicam"` | `QUANTITATIVA` |
| Contém `"Selecione uma"` ou `"Selecione apenas uma"` | `ÚNICA` |
| Apenas `( ) Sim` e `( ) Não`, sem sub-elementos `a)..f)` | `SIMPLES` |
| Qualquer outro caso não identificado | `ÚNICA` (default) + `logger.warning()` |

### 8.2 Regras de propagação (denormalização)

Ao emitir as linhas de um bloco questão, as seguintes colunas devem ser **repetidas em todas as linhas** (enunciado + todas as alternativas):

```
TIPO, DIMENSÃO, TEMA, TÓPICO, APLICAÇÃO SETORIAL, CÓDIGO QUESTÃO, ANO, 
ORIENTAÇÕES, TIPO DE EVIDÊNCIA, EXEMPLOS DE EVIDÊNCIA,
STATUS (vazio), PONTO FOCAL (vazio), RESPONSÁVEL (vazio),
ENVIAR EVIDÊNCIA (vazio), PTS. CABÍVEIS (vazio), GRI/ISO (vazio), TRIAL (vazio)
```
As seguintes colunas possuem comportamento dinâmico dependendo da linha gerada:

- `ID`: sempre único por linha; não herda nem replica o mesmo valor entre linhas do mesmo bloco.

- `PERGUNTA:` Emitida em todas as linhas. Na linha de enunciado, contém o texto principal da questão. Nas demais, contém o texto da alternativa.

- `SUB-OPÇÃO`: Emitida apenas nas linhas de alternativa (se aplicável). Fica None no enunciado.

- `DISTRIBUIÇÃO (vazio) e RESPOSTA (vazio)`: Emitidas apenas nas linhas de alternativa (pois a resposta é marcada na alternativa). Ficam vazias no enunciado.

- `EVIDÊNCIA EMPRESA (vazio) e PTS. OBTIDOS (vazio):` Podem ser preenchidas apenas na linha do enunciado (caso a evidência/pontuação seja anexada à questão como um todo) ou em todas, dependendo de como o cálculo downstream funcionará. (Recomendação padrão: propagar para todas).

- `% (vazio):` Emitida apenas na linha de enunciado (fórmula global da questão).

### 8.3 Questões matriciais e SUB-OPÇÃO

Uma questão matricial é identificada quando, sob `( ) Sim`, surgem sub-alternativas `a), b), c)...` e cada uma delas precisa ser respondida para múltiplas condições (ex: "Há atribuições", "Não há atribuições", "Nível inexiste").

> **Atenção:** No PDF de exemplo atual (Água e Efluentes), não há questões matriciais. O padrão foi identificado no questionário ISE 2025 interno. Implementar suporte básico, ativado quando o parser detectar linhas do tipo `"Há atribuições / Não há atribuições / Nível inexiste"` em posição de cabeçalho de coluna.

Para cada combinação `alternativa × sub-opção`, emitir uma linha separada com:
- `PERGUNTA` = texto da alternativa (ex: `"a) Conselho de Administração"`)
- `SUB-OPÇÃO` = condição (ex: `"Há atribuições"`)

Para questões não-matriciais, `SUB-OPÇÃO` fica `None`.

### 8.4 Valores válidos para RESPOSTA

A coluna `RESPOSTA` é gerada vazia pelo script. Documentar no README os valores esperados:

| Valor | Significado |
|---|---|
| `X` | Alternativa marcada pela empresa. |
| `-` | Alternativa não marcada. |
| `N` | Questão não se aplica ao setor (todas as alternativas do bloco recebem `N`). |
| Valor numérico | Exclusivo para questões `QUANTITATIVA` (ex: `45230`). |

### 8.5 Extração do ANO

1. Tentar extrair do cabeçalho do PDF: padrão `r"(\d{4})\s*/\s*(\d{4})"` → usar o primeiro ano.
2. Fallback: extrair 4 dígitos do nome do arquivo de entrada.
3. Fallback final: `None` + `logger.warning("Ano não identificado")`.

### 8.6 Código da questão

O padrão `r"^(\d+\.\d+\.\d+\.\d+)\."` captura o código com os quatro níveis. Armazenar **sem o ponto final** (ex: `"1.1.1.1"`, não `"1.1.1.1."`).

---

## 9. Casos de borda conhecidos

| Caso | Comportamento esperado |
|---|---|
| Quebra de página no meio do enunciado de uma questão | O estado `READING_QUESTION` persiste entre páginas. Concatenar linhas normalmente. |
| Quebra de página no meio de `APLICAÇÃO SETORIAL` | O estado `READING_SECTOR` persiste. Concatenar até encontrar próximo código de questão ou tópico. |
| Quebra de página no meio de uma alternativa `a)...` | Concatenar linha seguinte à última alternativa em buffer. |
| `EXEMPLOS DE EVIDÊNCIA` com texto em múltiplas linhas | Concatenar com espaço até encontrar próxima questão ou tópico. |
| Linha `"INFORMAÇÃO PÚBLICA – PUBLIC INFORMATION"` e número de página isolado | Descartar via padrão `page_noise`. |
| Questão sem `( ) Não` (apenas elementos positivos) | Emitir o que foi coletado + `logger.warning()`. |
| Questão sem tabela de evidências | `TIPO DE EVIDÊNCIA` e `EXEMPLOS DE EVIDÊNCIA` ficam `None`. |

---

## 10. Testes 🔲 Contrato

*(Ativar na Fase 2)*

Foco em testar funções puras do parser isoladamente, sem invocar leitura de PDF do disco a cada execução.

---

## 11. CI/CD e gates de qualidade 🔲 Contrato

*(Ativar na Fase 3)*

Entrega de artefatos limpos e script de validação de ambiente (`setup.bat`).

---

## 12. Segurança e observabilidade ✅ Materializado (básico)

- Log: arquivo `logs/app.log` com formato `[DATA] [NÍVEL] - MENSAGEM`.
- Nenhuma chave, credencial ou token no código, mesmo em comentários.
- Criar o diretório `logs/` programaticamente se não existir (`Path("logs").mkdir(exist_ok=True)`).

---

## 13. Documentação operacional ✅ Materializado (Fase 0)

O `README.md` deve conter:
- Instruções de execução em comando único.
- Justificativa técnica para `pdfplumber` (por que não `PyMuPDF`).
- Como o Power Automate Desktop aciona o script.
- Descrição das 25 colunas de saída e quais são preenchidas automaticamente vs. manualmente.

---

## 14. Checklist de nova sessão com a IA

- [ ] Informar fase atual + última decisão relevante antes de qualquer prompt técnico.
- [ ] Não implementar nada além do escopo da fase sem aprovação explícita.
- [ ] Se uma dependência nova for sugerida, justificá-la conforme o regulamento antes de adicioná-la ao `requirements.txt`.
- [ ] Confirmar que o PDF de teste a ser usado é `1_1__AMB_-_Água_e_Efluentes_-_EF.pdf` (único arquivo com padrões reais mapeados).