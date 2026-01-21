"""
Testes de inferência para o modelo de previsão
"""
import unittest
import json
import pandas as pd
from model_predictor import ModelPredictor

class TestModelInference(unittest.TestCase):
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.predictor = ModelPredictor()
        self.sample_data = pd.DataFrame({
            'ID_PRODUTO': [1001, 1002, 1003],
            'DIA': ['20/01/2024', '21/01/2024', '22/01/2024'],
            'FLAG_PROMOCAO': [0, 1, 0],
            'QUANTIDADE_ESTOQUE': [50, 120, 30]
        })
    
    def test_single_prediction(self):
        """Teste de previsão única"""
        result = self.predictor.predict(self.sample_data.iloc[0])
        self.assertIn('prediction', result)
        self.assertIn('confidence', result)
        self.assertIn('alerts', result)
        self.assertGreater(result['confidence']['score'], 0.5)
    
    def test_batch_prediction(self):
        """Teste de previsão em lote"""
        results = self.predictor.predict_batch(self.sample_data)
        self.assertEqual(len(results), len(self.sample_data))
        
        for result in results:
            self.assertIn('estoque_previsto', result['prediction'])
            self.assertIsInstance(result['prediction']['estoque_previsto'], (int, float))
    
    def test_prediction_limits(self):
        """Teste de limites das previsões"""
        # Teste com estoque zero
        data_zero = pd.Series({
            'ID_PRODUTO': 1001,
            'DIA': '20/01/2024',
            'FLAG_PROMOCAO': 0,
            'QUANTIDADE_ESTOQUE': 0
        })
        
        result = self.predictor.predict(data_zero)
        self.assertEqual(result['alerts']['level'], 'CRITICO')
    
    def test_inference_speed(self):
        """Teste de performance de inferência"""
        import time
        
        start_time = time.time()
        for _ in range(100):
            self.predictor.predict(self.sample_data.iloc[0])
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100 * 1000  # ms
        
        self.assertLess(avg_time, 100)  # Inferência deve ser < 100ms
    
    def test_output_schema(self):
        """Teste de conformidade com schema de output"""
        result = self.predictor.predict(self.sample_data.iloc[0])
        
        # Carregar schema
        with open('config/schema_output.json') as f:
            schema = json.load(f)
        
        # Validar schema (implementação simplificada)
        required_fields = schema['required']
        for field in required_fields:
            self.assertIn(field, result)
        
        # Validar tipos
        self.assertIsInstance(result['prediction'], dict)
        self.assertIsInstance(result['confidence']['score'], float)
        self.assertIn(result['alerts']['level'], ['NORMAL', 'ALERTA', 'CRITICO'])

if __name__ == '__main__':
    unittest.main()