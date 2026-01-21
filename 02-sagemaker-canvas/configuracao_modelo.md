⚙️ Configuração do Modelo - SageMaker Canvas
📋 Especificações Técnicas do Modelo Treinado
Informações Básicas
Nome do Modelo: estoque-prediction-model-v1

Ambiente: SageMaker Canvas (No-code/Low-code)

Data de Treinamento: 26/01/2024

Versão: 1.0.0

Status: ✅ Production Ready

🎯 Configurações do Problema
Tipo de Problema
text
Problema: Time Series Forecasting (Previsão de Séries Temporais)
Alvo Principal: QUANTIDADE_ESTOQUE (Regressão)
Alvo Secundário: NIVEL_ALERTA (Classificação Multiclasse)
Definição da Série Temporal
Parâmetro	Configuração	Justificativa
Coluna de Tempo	DIA	Data das observações
Frequência	Diária	Dados coletados diariamente
Horizonte de Previsão	7 dias	Período útil para planejamento
Janela de Treinamento	20 dias	Balance entre dados e recenticidade
Seasonality	Weekly (7 dias)	Padrão semanal identificado
