# Guia de Deploy para Produção

## Criar Endpoint no Canvas
1. No modelo treinado, clicar em "Share"
2. Selecionar "Deploy to real-time endpoint"
3. Escolher instância (recomendado: ml.m5.large)
4. Nomear endpoint: `estoque-prediction-endpoint`

## Testar Endpoint
```bash
curl -X POST \
  https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/estoque-prediction-endpoint/invocations \
  -H 'Content-Type: text/csv' \
  -d '1001,0,50'