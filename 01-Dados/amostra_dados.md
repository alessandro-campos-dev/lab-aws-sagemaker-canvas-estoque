# 📊 Amostra de Dados - Histórico de Vendas e Estoque

## 📈 Visão Geral do Dataset

**Arquivo:** `historico_vendas_estoque.csv`  
**Registros:** 500  
**Período:** 31/12/2023 a 19/01/2024  
**Produtos únicos:** 50 (IDs 1001 a 1050)  
**Formato:** CSV (UTF-8, separador vírgula)

## 🔍 Amostra dos 10 Primeiros Registros

| ID | ID_PRODUTO | DIA | FLAG_PROMOCAO | QUANTIDADE_ESTOQUE |
|----|------------|-----|---------------|-------------------|
| 1 | 1041 | 31/12/2023 | 0 | 272 |
| 2 | 1025 | 31/12/2023 | 1 | 269 |
| 3 | 1046 | 31/12/2023 | 0 | 285 |
| 4 | 1007 | 31/12/2023 | 0 | 245 |
| 5 | 1010 | 31/12/2023 | 1 | 230 |
| 6 | 1028 | 31/12/2023 | 0 | 271 |
| 7 | 1035 | 31/12/2023 | 0 | 259 |
| 8 | 1004 | 31/12/2023 | 0 | 291 |
| 9 | 1023 | 31/12/2023 | 0 | 244 |
| 10 | 1030 | 31/12/2023 | 0 | 273 |

## 📊 Estatísticas Básicas

- **Promoções:** ~30% dos registros
- **Estoque médio inicial:** ~250 unidades
- **Produtos por dia:** 25 diferentes
- **Variação diária:** 5-20 unidades (sem promoção), 15-30 unidades (com promoção)

## 🎯 Para uso no SageMaker Canvas

Este dataset está otimizado para:
1. **Previsão de séries temporais** (coluna `DIA`)
2. **Classificação binária** (coluna `FLAG_PROMOCAO`)
3. **Regressão** (coluna `QUANTIDADE_ESTOQUE`)
4. **Análise de tendências** por produto