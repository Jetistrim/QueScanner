# Relatório Técnico de Alterações do Chat

Data: 2026-05-28
Projeto: QueScanner
Escopo: Fase 2 (Testes e Blindagem) + reforço operacional local/CI

## 1. Objetivo deste ciclo
- Iniciar e concluir a implementação da Fase 2 com sobra.
- Aumentar a blindagem por testes com cobertura mínima obrigatória de 90%.
- Implementar suporte matricial de SUB-OPÇÃO no parser.
- Automatizar gate de cobertura para execução local e pipeline de CI.

## 2. Alterações realizadas

### 2.1 Testes e fixtures (nova suíte ampliada)
- Estrutura de testes criada e expandida em tests:
  - tests/conftest.py
  - tests/test_patterns.py
  - tests/test_state_machine.py
  - tests/test_extractor_utils.py
  - tests/test_models_validation.py
  - tests/test_main_helpers.py
  - tests/test_main_runtime.py
- Fixtures de cenário adicionadas:
  - tests/fixtures/questionario_basico.txt
  - tests/fixtures/quebra_em_alternativa.txt
  - tests/fixtures/mal_formatado_com_recuperacao.txt
  - tests/fixtures/sem_evidencia.txt
  - tests/fixtures/evidencia_multilinha.txt
  - tests/fixtures/matriz_subopcao.txt

### 2.2 Implementação de SUB-OPÇÃO matricial no parser
- Arquivo alterado: src/extractor.py
- Regras implementadas:
  - Identificação de alternativas letradas (a), b), c), ...).
  - Rastreamento da sub-opção binária ativa (Sim/Não) durante leitura do bloco.
  - Propagação de SUB-OPÇÃO para alternativas matriciais.
  - Normalização do bloco matricial para evitar emissão de linhas cruas Sim/Não quando existirem alternativas letradas no mesmo bloco.
- Funções adicionadas para suportar a lógica:
  - is_lettered_alternative
  - normalize_alternatives_for_matrix

### 2.3 Gate automático de cobertura (local e CI)
- Configuração local adicionada:
  - pytest.ini com addopts incluindo cobertura e fail-under 90.
- Pipeline CI adicionada:
  - .github/workflows/ci.yml
  - Execução de testes no GitHub Actions com o mesmo gate definido no pytest.ini.

### 2.4 Dependências e documentação
- requirements.txt atualizado para incluir pytest e pytest-cov.
- README.md atualizado com seção de testes/cobertura e explicação do gate automático.

## 3. Validações executadas durante o chat
- Execução recorrente da suíte de testes após cada bloco de mudanças.
- Resultado final validado:
  - 45 testes passando.
  - Cobertura total de 95.17%.
  - Gate mínimo de 90% atendido.

## 4. Métricas finais observadas
- main.py: 96%
- src/extractor.py: 94%
- src/models.py: 97%
- Cobertura total: 95.17%

## 5. Riscos e observações
- A implementação matricial cobre o fluxo principal com mapeamento de SUB-OPÇÃO para alternativas letradas.
- O gate de cobertura já bloqueia regressão abaixo de 90% no local e no CI.
- O arquivo historico_md/relatorio_tecnico_2026-05-27.md teve alterações revertidas pelo usuário durante o chat; este relatório consolida o estado vigente após as reversões.

## 6. Estado final do ciclo
- Fase 2 concluída com blindagem acima da meta.
- SUB-OPÇÃO matricial implementado e coberto por testes obrigatórios.
- Validação automática por cobertura habilitada para execução contínua.
