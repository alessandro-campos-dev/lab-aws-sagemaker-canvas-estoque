# Esquema do Dataset - Histórico de Vendas

## Colunas
| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| ID | Integer | Identificador único do registro | 1 |
| ID_PRODUTO | Integer | Código do produto (1001-1050) | 1001 |
| DIA | Date | Data da observação (dd/mm/aaaa) | 31/12/2023 |
| FLAG_PROMOCAO | Binary | Indica se produto estava em promoção (0/1) | 1 |
| QUANTIDADE_ESTOQUE | Integer | Quantidade em estoque no final do dia | 150 |

## Estatísticas
- Período: 31/12/2023 a 19/01/2024
- Produtos únicos: 50
- Registros: 500
- Promoções: ~30% dos registros