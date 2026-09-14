# Integrar a API de Dados Abertos do Senado Federal

A v1 do MCP cobre apenas a Câmara dos Deputados (`dadosabertos.camara.leg.br`). Como PECs (Propostas de Emenda à Constituição) tramitam também no Senado Federal, a análise do ciclo completo de uma PEC fica incompleta sem os dados da casa revisora. Esta feature adiciona a integração com a API de Dados Abertos do Senado (Legislação/Matérias e Votações) para complementar tramitações e votações do outro lado do Congresso.

O resultado esperado é permitir, dado o número/ano ou identificador de uma PEC, recuperar tramitações e votações também no Senado, correlacionando as duas casas quando possível, mantendo a mesma forma de ferramentas curadas já usada para a Câmara.

Motivação registrada em 2026-09-14: o usuário optou por começar a v1 apenas pela Câmara para entregar valor rápido, deixando o Senado como expansão planejada. O nome amplo do repositório (`mcp-api-publica-governo-brasil`) reforça a intenção de crescer para múltiplas APIs públicas do governo brasileiro.
