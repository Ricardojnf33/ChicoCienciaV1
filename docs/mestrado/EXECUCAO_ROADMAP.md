# Execução incremental do roadmap

Atualizado em 27/09/2026. [Roadmap HTML](roadmap.html) · [Backlog estruturado](roadmap.json).

## Acordo de execução

Solicitação do responsável: uma branch de trabalho por vez, criação de PR,
preparação do teste no Actions, disparo manual pelo usuário e pausa antes do
próximo incremento. Todos os resultados e limitações devem alimentar o relatório
final com referências. Nenhuma execução paga nova é autorizada implicitamente por
este documento.

As PRs históricas #7 e #1 já existem; não serão fechadas ou alteradas por esta
regra. Ela vale para novos incrementos. A branch E00 parte de main e não incorpora
nem executa a implementação live da PR #7.

## Incremento atual: E00 — baseline e governança

- Escopo: E00.H02 e preparação operacional de E00.H03.
- E00.H01 permanece parcial: orientação, situação acadêmica, prazo e capacidade
  exigem informação do responsável; ver [pendências](PENDENCIAS_USUARIO.md).
- Entregas: roadmap v1.1, snapshot, registro de evidências, relatório final em
  construção e workflow manual de integridade documental.
- Não inclui: correção E01, prova E2E, implantação de Jev ou avanço experimental.
- Gate: validação local registrada; validação manual remota aguardada.

## Ciclo obrigatório por incremento

1. Revalidar referências, instruções do repositório e evidências do incremento anterior.
2. Criar uma única branch a partir da base correta. Para E01, decidir como tratar
   a PR #7 antes de editar: não presumir que seu código está na main.
3. Implementar apenas tarefas desbloqueadas, com testes pertinentes.
4. Atualizar registro de processo, índice de evidências e relatório final.
5. Abrir PR com objetivo, IDs do roadmap, mudanças, testes e limitações.
6. O usuário executa o workflow manual indicado; o agente não dispara nem faz merge.
7. Ler o run pela API quando disponível, conferir commit, steps, artifacts e custos.
8. Versionar o resultado antes de abrir a próxima branch. Correções do mesmo
   incremento permanecem na mesma branch enquanto ela estiver aberta.

A CI existente continua automática em push/PR. Sua aprovação não substitui a
execução manual solicitada e não permite avançar sozinha.

## Bootstrap do novo workflow E00

Um workflow novo com workflow_dispatch precisa existir na branch padrão para
ficar disponível para despacho manual. Por isso:

1. Revisar e integrar manualmente esta PR documental após a CI ficar verde.
2. Em Actions, abrir **Roadmap E00 - manual evidence gate**.
3. Escolher **Run workflow**, branch **main**, confirmação **VALIDAR_E00_SEM_LLM**.
4. Executar uma vez. Não executar workflows Phase 5 nesta etapa.
5. Enviar o link do run. A leitura de logs e artefatos será feita pelo conector;
   solicitar print/arquivo somente se houver impedimento concreto de acesso.

O workflow usa apenas Python da imagem, não instala o projeto, não recebe secrets,
não chama serviços de modelos e não escreve no GitHub. Seu resultado valida
somente a integridade do plano/documentos. Gate G2 continua pendente.

## Evidências por incremento

O índice versionado deve ligar tarefa → commit → PR → workflow/run → pacote →
conclusão. Registrar também falhas, cancelamentos e tentativas não iniciadas.
O artifact do E00 contém report.json, checksums.json e summary.md, com identidade
da execução. A retenção solicitada é 90 dias, sujeita ao limite do repositório.
Após o run, copiar relatório e checksums para o índice de evidências antes de
expirarem. Bundles grandes precisam de destino durável acordado com o responsável.
Links temporários não são arquivo científico permanente.

Mudanças pós-G2 devem atender GM/E12 antes de novas campanhas ou Jev. O fluxo
OFF → SHADOW → ACTIVE exige versões, decisões, métricas, orçamento e critérios
registrados. Adotar Jev depende da evidência; monitorá-lo é obrigatório.

## Regra para pedir informação

Consultar primeiro código, Actions e documentos acessíveis. Pedir ao usuário
apenas decisões, informações institucionais ou elementos realmente inacessíveis.
Nunca solicitar chaves por chat; configuração deve usar Secrets/Environment.
Distinguir bloqueio técnico de pendência que pode correr em paralelo.
