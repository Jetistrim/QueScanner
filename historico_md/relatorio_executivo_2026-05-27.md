# Relatório Executivo

Data: 2026-05-27
Projeto: QueScanner

## Objetivo
Implementar um MVP (Fase 0) para extrair questionários ISE em PDF e gerar planilha XLSX denormalizada.

## Resultado
- Pipeline funcional de ponta a ponta (PDF -> XLSX).
- Estrutura base do projeto criada e organizada.
- Logs funcionais em arquivo.
- Parser refinado para reduzir ruído em PERGUNTA e ORIENTAÇÕES.
- Lint estabilizado nos arquivos principais.

## Entregas-chave
- Código principal: main.py, src/extractor.py, src/models.py.
- Dependências compatíveis com Python 3.13.
- Pastas de organização: outputs/ e historico_md/.
- Direcionamento automático de saída para outputs/ quando só o nome do arquivo é informado.

## Validação
- Execuções repetidas com PDF real informado.
- Geração de arquivos de saída sem falha crítica.
- Verificação de colunas e conteúdo amostral da planilha.

## Estado Atual
Projeto apto para continuidade de refinamentos de parsing na Fase 0, mantendo o fluxo operacional estável.

## Próximos passos sugeridos
- Refinar cenários quantitativos e matriciais.
- Padronizar regras de normalização de texto.
- Evoluir documentação operacional para uso contínuo.
