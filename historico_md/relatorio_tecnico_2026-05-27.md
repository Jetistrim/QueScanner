# Relatório Técnico Detalhado

Data: 2026-05-27
Projeto: QueScanner
Escopo: Fase 0 (MVP funcional)

## 1. Contexto e objetivo técnico
- Objetivo implementado: extrair linhas do PDF ISE, interpretar hierarquia de contexto e produzir XLSX denormalizado com 25 colunas em ordem fixa.
- Restrições respeitadas na implementação:
  - execução por CLI
  - sem caminhos hardcoded para input/output absoluto obrigatório
  - logs em arquivo
  - sem credenciais no código

## 2. Arquitetura materializada
- main.py
  - entrada CLI
  - configuração de logging
  - leitura de PDF
  - orquestração do parser
  - montagem e exportação do DataFrame
- src/models.py
  - ordem de colunas
  - regex de padrões
  - constantes de tipos
  - contexto de parsing
- src/extractor.py
  - heurísticas de parsing por estado
  - inferência de ano
  - inferência de tipo de questão
  - emissão de linhas de enunciado e alternativas

## 3. Mudanças importantes feitas no ciclo
### 3.1 Compatibilidade de ambiente
- Identificado ambiente ativo com Python 3.13.
- Dependências ajustadas para compatibilidade:
  - pandas==2.2.3
  - pdfplumber==0.11.5
  - openpyxl==3.1.5

### 3.2 Observabilidade e paths
- Logging ancorado no diretório do projeto (evita criação fora do workspace).
- logs/app.log validado com eventos de início/fim e erros quando ocorridos.

### 3.3 Refino de parsing
- Evolução de parser básico para versão com menos ruído:
  - distinção entre continuidade de enunciado e orientação
  - tratamento de cabeçalhos intermediários de alternativas
  - concatenação de alternativa apenas quando linha parece continuação válida
- Ajuste Unicode-aware:
  - remoção de regex manual com lista de acentos
  - uso de isalpha()/isdigit() para detectar continuação de texto

### 3.4 Tipagem e lint
- Tipagem explícita adicionada em extractor.py:
  - RowData
  - AlternativeItem (TypedDict)
- Ajustes em main.py para reduzir alertas de análise estática com bibliotecas sem stubs completos.
- Configuração de workspace criada:
  - .vscode/settings.json com interpretador padrão e extraPaths.

## 4. Organização de artefatos
- Pastas criadas:
  - outputs/ para planilhas de teste
  - historico_md/ para histórico legível
- Comportamento de saída atualizado em main.py:
  - output sem pasta -> vai automaticamente para outputs/
  - output absoluto -> respeitado
  - output relativo com subpasta -> resolvido relativo ao projeto

## 5. Validação executada
- Compilação de módulos Python.
- Execuções ponta a ponta com PDF real informado.
- Conferência de workbook:
  - presença de 25 colunas
  - ordem das colunas
  - amostras de linhas de enunciado e alternativa
- Tratamento de incidentes de validação:
  - lock de arquivo XLSX aberto (PermissionError)
  - correção via novo nome de saída para continuidade dos testes

## 6. Situação atual do sistema
- Pipeline operacional estável para o caso de teste informado.
- Parser com qualidade melhor que a versão inicial, porém ainda incremental para regras avançadas de cenários específicos.
- Base pronta para próximos refinamentos mantendo Fase 0.

## 7. Diferença de finalidade deste relatório
- Este documento técnico prioriza decisões de implementação, diagnósticos, ajustes de ambiente e evidências de validação.
- Complementa o relatório executivo, que resume o status para leitura rápida gerencial.

## 8. Backlog técnico explícito (pós-Fase 2)
- TODO: implementar suporte completo de questões matriciais com preenchimento de `SUB-OPÇÃO`.
- Decisão desta rodada: não implementar a lógica funcional de `SUB-OPÇÃO`, apenas reforçar testes e blindagem geral.
- Critério de aceite futuro para este item:
  - identificar questões matriciais no parsing
  - emitir linhas com `SUB-OPÇÃO` preenchido para alternativas aplicáveis
  - manter compatibilidade com denormalização existente e validações do modelo
