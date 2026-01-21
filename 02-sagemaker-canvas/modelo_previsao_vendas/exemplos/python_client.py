"""
Cliente Python para consumir o modelo de previsão
"""
import json
import pandas as pd
import boto3
from datetime import datetime
from typing import Dict, List, Union

class EstoquePredictionClient:
    """
    Cliente para consumir o endpoint do modelo de previsão
    """
    
    def __init__(self, endpoint_name: str = None, region: str = 'us-east-1'):
        """
        Inicializa o cliente do modelo
        
        Args:
            endpoint_name: Nome do endpoint SageMaker
            region: Região AWS
        """
        self.endpoint_name = endpoint_name or 'estoque-prediction-endpoint'
        self.region = region
        
        # Inicializar cliente SageMaker Runtime
        self.runtime_client = boto3.client(
            'runtime.sagemaker',
            region_name=self.region
        )
    
    def predict_single(
        self, 
        produto_id: int, 
        data: str, 
        flag_promocao: int, 
        estoque_atual: int
    ) -> Dict:
        """
        Faz previsão para um único produto
        
        Args:
            produto_id: ID do produto
            data: Data da previsão (dd/mm/aaaa)
            flag_promocao: 0 ou 1
            estoque_atual: Quantidade atual em estoque
            
        Returns:
            Dicionário com previsão e alertas
        """
        # Preparar dados no formato CSV
        csv_data = f"{produto_id},{flag_promocao},{estoque_atual}"
        
        try:
            # Invocar endpoint
            response = self.runtime_client.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='text/csv',
                Body=csv_data.encode('utf-8')
            )
            
            # Processar resposta
            result_bytes = response['Body'].read()
            result = json.loads(result_bytes.decode('utf-8'))
            
            # Adicionar metadados
            result['metadata'] = {
                'produto_id': produto_id,
                'data_previsao': data,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'metadata': {
                    'produto_id': produto_id,
                    'data_previsao': data,
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def predict_batch(self, dados: pd.DataFrame) -> List[Dict]:
        """
        Faz previsões em lote
        
        Args:
            dados: DataFrame com colunas:
                  ID_PRODUTO, DIA, FLAG_PROMOCAO, QUANTIDADE_ESTOQUE
                  
        Returns:
            Lista de previsões
        """
        predictions = []
        
        for _, row in dados.iterrows():
            prediction = self.predict_single(
                produto_id=row['ID_PRODUTO'],
                data=row['DIA'],
                flag_promocao=row['FLAG_PROMOCAO'],
                estoque_atual=row['QUANTIDADE_ESTOQUE']
            )
            predictions.append(prediction)
        
        return predictions
    
    def get_alerts_summary(self, predictions: List[Dict]) -> Dict:
        """
        Gera resumo de alertas a partir das previsões
        
        Args:
            predictions: Lista de previsões
            
        Returns:
            Resumo de alertas
        """
        summary = {
            'total_produtos': len(predictions),
            'criticos': 0,
            'alerta': 0,
            'normal': 0,
            'produtos_criticos': [],
            'produtos_alerta': []
        }
        
        for pred in predictions:
            if 'alerts' in pred:
                nivel = pred['alerts']['level']
                
                if nivel == 'CRITICO':
                    summary['criticos'] += 1
                    summary['produtos_criticos'].append({
                        'produto_id': pred['metadata']['produto_id'],
                        'dias_ate_ruptura': pred['alerts'].get('dias_ate_ruptura', 'N/A')
                    })
                elif nivel == 'ALERTA':
                    summary['alerta'] += 1
                    summary['produtos_alerta'].append({
                        'produto_id': pred['metadata']['produto_id'],
                        'dias_ate_ruptura': pred['alerts'].get('dias_ate_ruptura', 'N/A')
                    })
                else:
                    summary['normal'] += 1
        
        return summary

# Exemplo de uso
if __name__ == "__main__":
    # Criar cliente
    client = EstoquePredictionClient()
    
    # Exemplo 1: Previsão única
    print("=== Exemplo 1: Previsão Única ===")
    resultado = client.predict_single(
        produto_id=1001,
        data="20/01/2024",
        flag_promocao=0,
        estoque_atual=50
    )
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    
    # Exemplo 2: Previsão em lote
    print("\n=== Exemplo 2: Previsão em Lote ===")
    dados_exemplo = pd.DataFrame({
        'ID_PRODUTO': [1001, 1002, 1003],
        'DIA': ['20/01/2024', '21/01/2024', '22/01/2024'],
        'FLAG_PROMOCAO': [0, 1, 0],
        'QUANTIDADE_ESTOQUE': [50, 120, 30]
    })
    
    previsoes = client.predict_batch(dados_exemplo)
    
    for i, pred in enumerate(previsoes):
        print(f"\nProduto {pred['metadata']['produto_id']}:")
        print(f"  Estoque previsto: {pred['prediction']['estoque_previsto']}")
        print(f"  Nível alerta: {pred['alerts']['level']}")
        print(f"  Confiança: {pred['confidence']['score']:.2%}")
    
    # Exemplo 3: Resumo de alertas
    print("\n=== Exemplo 3: Resumo de Alertas ===")
    resumo = client.get_alerts_summary(previsoes)
    print(f"Total produtos: {resumo['total_produtos']}")
    print(f"Críticos: {resumo['criticos']}")
    print(f"Alerta: {resumo['alerta']}")
    print(f"Normal: {resumo['normal']}")
    
    if resumo['produtos_criticos']:
        print("\nProdutos em situação CRÍTICA:")
        for produto in resumo['produtos_criticos']:
            print(f"  - Produto {produto['produto_id']} ({produto['dias_ate_ruptura']} dias até ruptura)")