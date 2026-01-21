import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Configuração
np.random.seed(42)
random.seed(42)

num_registros = 500
num_produtos = 50
dias_periodo = 20
produtos_por_dia = 25

# Datas
data_inicio = datetime(2023, 12, 31)
datas = [data_inicio + timedelta(days=i) for i in range(dias_periodo)]

# IDs dos produtos
ids_produtos = list(range(1001, 1001 + num_produtos))

# Estoque inicial
estoque_inicial = {pid: random.randint(100, 300) for pid in ids_produtos}

# Coletar dados
dados = []
contador_id = 1

for dia_idx, data_atual in enumerate(datas):
    produtos_do_dia = random.sample(ids_produtos, produtos_por_dia)
    
    for produto_id in produtos_do_dia:
        flag_promocao = random.random() < 0.3
        
        if produto_id in estoque_inicial:
            estoque_atual = estoque_inicial[produto_id]
            
            if estoque_atual > 0:
                if flag_promocao:
                    vendas = random.randint(15, 30)
                else:
                    vendas = random.randint(5, 20)
                
                vendas = min(vendas, estoque_atual)
                novo_estoque = max(0, estoque_atual - vendas)
                estoque_inicial[produto_id] = novo_estoque
            else:
                novo_estoque = 0
        else:
            novo_estoque = 0
        
        dados.append({
            'ID': contador_id,
            'ID_PRODUTO': produto_id,
            'DIA': data_atual.strftime('%d/%m/%Y'),
            'FLAG_PROMOCAO': 1 if flag_promocao else 0,
            'QUANTIDADE_ESTOQUE': novo_estoque
        })
        
        contador_id += 1
        
        if len(dados) >= num_registros:
            break
    
    if len(dados) >= num_registros:
        break

# Criar DataFrame
df = pd.DataFrame(dados)
df = df.head(500)

# Salvar
df.to_csv('historico_vendas_estoque.csv', index=False, encoding='utf-8-sig')
print("Arquivo 'historico_vendas_estoque.csv' criado com sucesso!")
print(f"Registros: {len(df)}")
