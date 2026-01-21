# Guia de Configuração - SageMaker Canvas

## Passo 1: Acessar SageMaker Canvas
1. Login no console AWS
2. Navegar para "Amazon SageMaker"
3. Clicar em "Canvas" no menu lateral

## Passo 2: Importar Dataset
1. Clicar em "Import data"
2. Selecionar "Upload from computer"
3. Escolher `historico_vendas_estoque.csv`
4. Aguardar processamento

## Passo 3: Configurar Análise
1. Selecionar coluna alvo: `QUANTIDADE_ESTOQUE`
2. Tipo de problema: "Time series forecasting"
3. Configurar parâmetros de tempo

## Passo 4: Treinar Modelo
1. Clicar em "Quick build"
2. Aguardar treinamento (2-5 minutos)
3. Analisar métricas de performance