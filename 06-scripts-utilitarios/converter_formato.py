#!/usr/bin/env python3
"""
Conversor de Formatos de Dados para Previsão de Estoque

Conversões suportadas:
- CSV para Parquet/JSON
- JSON para CSV/Parquet
- Parquet para CSV/JSON
- Normalização de datas
- Conversão de codificação
"""

import pandas as pd
import argparse
import json
import os
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class DataConverter:
    """Classe principal para conversão de formatos de dados"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'parquet', 'xlsx']
        self.date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']
    
    def detect_format(self, file_path):
        """Detecta o formato do arquivo baseado na extensão"""
        ext = Path(file_path).suffix.lower().replace('.', '')
        if ext in self.supported_formats:
            return ext
        raise ValueError(f"Formato não suportado: {ext}. Formatos suportados: {self.supported_formats}")
    
    def normalize_dates(self, df, date_column='DIA'):
        """Normaliza formatos de data para padrão brasileiro"""
        if date_column in df.columns:
            for date_format in self.date_formats:
                try:
                    df[date_column] = pd.to_datetime(df[date_column], format=date_format, errors='coerce')
                    # Converte para formato padrão dd/mm/yyyy
                    df[date_column] = df[date_column].dt.strftime('%d/%m/%Y')
                    break
                except:
                    continue
        return df
    
    def validate_data(self, df):
        """Validações básicas dos dados"""
        required_columns = ['ID_PRODUTO', 'DIA', 'FLAG_PROMOCAO', 'QUANTIDADE_ESTOQUE']
        
        # Verifica colunas necessárias
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Aviso: Colunas faltando: {missing_columns}")
        
        # Validações específicas
        if 'ID_PRODUTO' in df.columns:
            df['ID_PRODUTO'] = pd.to_numeric(df['ID_PRODUTO'], errors='coerce').astype('Int64')
        
        if 'FLAG_PROMOCAO' in df.columns:
            df['FLAG_PROMOCAO'] = pd.to_numeric(df['FLAG_PROMOCAO'], errors='coerce').fillna(0).astype(int)
            # Garante que seja 0 ou 1
            df['FLAG_PROMOCAO'] = df['FLAG_PROMOCAO'].apply(lambda x: 1 if x >= 1 else 0)
        
        if 'QUANTIDADE_ESTOQUE' in df.columns:
            df['QUANTIDADE_ESTOQUE'] = pd.to_numeric(df['QUANTIDADE_ESTOQUE'], errors='coerce').fillna(0).astype(int)
            # Garante valores não negativos
            df['QUANTIDADE_ESTOQUE'] = df['QUANTIDADE_ESTOQUE'].clip(lower=0)
        
        return df
    
    def read_file(self, input_path, input_format=None):
        """Lê arquivo no formato especificado"""
        if not input_format:
            input_format = self.detect_format(input_path)
        
        print(f"Lendo arquivo: {input_path} ({input_format.upper()})")
        
        try:
            if input_format == 'csv':
                df = pd.read_csv(input_path, encoding='utf-8-sig')
            elif input_format == 'json':
                df = pd.read_json(input_path)
            elif input_format == 'parquet':
                df = pd.read_parquet(input_path)
            elif input_format == 'xlsx':
                df = pd.read_excel(input_path)
            else:
                raise ValueError(f"Formato não suportado: {input_format}")
            
            print(f"  Registros lidos: {len(df):,}")
            print(f"  Colunas: {list(df.columns)}")
            
            # Aplica validações e normalizações
            df = self.normalize_dates(df)
            df = self.validate_data(df)
            
            return df
            
        except Exception as e:
            print(f"Erro ao ler arquivo {input_path}: {str(e)}")
            raise
    
    def write_file(self, df, output_path, output_format=None):
        """Escreve arquivo no formato especificado"""
        if not output_format:
            output_format = self.detect_format(output_path)
        
        # Cria diretório se não existir
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Escrevendo arquivo: {output_path} ({output_format.upper()})")
        
        try:
            if output_format == 'csv':
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif output_format == 'json':
                df.to_json(output_path, orient='records', indent=2, force_ascii=False)
            elif output_format == 'parquet':
                df.to_parquet(output_path, index=False)
            elif output_format == 'xlsx':
                df.to_excel(output_path, index=False)
            else:
                raise ValueError(f"Formato de saída não suportado: {output_format}")
            
            file_size = os.path.getsize(output_path) / 1024  # KB
            print(f"  Arquivo criado: {file_size:.2f} KB")
            print(f"  Registros escritos: {len(df):,}")
            
        except Exception as e:
            print(f"Erro ao escrever arquivo {output_path}: {str(e)}")
            raise
    
    def convert(self, input_path, output_path, input_format=None, output_format=None):
        """Converte arquivo entre formatos"""
        start_time = datetime.now()
        
        # Detecta formatos se não especificados
        if not input_format:
            input_format = self.detect_format(input_path)
        
        if not output_format:
            output_format = self.detect_format(output_path)
        
        print(f"\n{'='*60}")
        print(f"CONVERSÃO: {input_format.upper()} → {output_format.upper()}")
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print(f"{'='*60}")
        
        # Executa conversão
        df = self.read_file(input_path, input_format)
        self.write_file(df, output_path, output_format)
        
        # Estatísticas
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print("ESTATÍSTICAS DA CONVERSÃO:")
        print(f"  Tempo de processamento: {processing_time:.2f} segundos")
        print(f"  Registros convertidos: {len(df):,}")
        print(f"  Colunas: {len(df.columns)}")
        
        # Informações sobre tipos de dados
        print(f"\nTIPOS DE DADOS:")
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].count()
            print(f"  {col}: {dtype} ({non_null}/{len(df)} não nulos)")
        
        print(f"{'='*60}\n")
        return df
    
    def batch_convert(self, input_pattern, output_dir, output_format='parquet'):
        """Converte múltiplos arquivos em lote"""
        input_files = Path().glob(input_pattern)
        
        for input_file in input_files:
            if input_file.is_file():
                output_file = output_dir / f"{input_file.stem}.{output_format}"
                try:
                    self.convert(str(input_file), str(output_file))
                except Exception as e:
                    print(f"Erro ao converter {input_file}: {str(e)}")
    
    def create_sample(self, input_path, output_path, sample_size=100, random_state=42):
        """Cria uma amostra do dataset"""
        df = self.read_file(input_path)
        
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=random_state).sort_index()
        else:
            df_sample = df.copy()
            print(f"Dataset menor que amostra solicitada. Usando todos os {len(df)} registros.")
        
        self.write_file(df_sample, output_path)
        return df_sample

def main():
    parser = argparse.ArgumentParser(description='Conversor de Formatos de Dados')
    
    # Argumentos principais
    parser.add_argument('input', help='Arquivo de entrada ou padrão para múltiplos arquivos')
    parser.add_argument('output', help='Arquivo de saída ou diretório para batch')
    
    # Opções de formato
    parser.add_argument('--input-format', choices=['csv', 'json', 'parquet', 'xlsx'],
                       help='Formato do arquivo de entrada (autodetectado se não especificado)')
    parser.add_argument('--output-format', choices=['csv', 'json', 'parquet', 'xlsx'],
                       help='Formato do arquivo de saída (autodetectado se não especificado)')
    
    # Opções de processamento
    parser.add_argument('--batch', action='store_true',
                       help='Modo batch para múltiplos arquivos')
    parser.add_argument('--sample', type=int,
                       help='Cria amostra com N registros')
    parser.add_argument('--sample-seed', type=int, default=42,
                       help='Seed para amostragem aleatória (padrão: 42)')
    
    # Opções de validação
    parser.add_argument('--validate-only', action='store_true',
                       help='Apenas valida o arquivo sem converter')
    parser.add_argument('--stats', action='store_true',
                       help='Mostra estatísticas detalhadas')
    
    args = parser.parse_args()
    converter = DataConverter()
    
    try:
        if args.validate_only:
            # Apenas validação
            df = converter.read_file(args.input, args.input_format)
            print("\nValidação concluída com sucesso!")
            if args.stats:
                print(df.describe().to_string())
        
        elif args.batch:
            # Modo batch
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            converter.batch_convert(args.input, output_dir, args.output_format)
        
        elif args.sample:
            # Cria amostra
            df_sample = converter.create_sample(
                args.input, 
                args.output, 
                sample_size=args.sample,
                random_state=args.sample_seed
            )
            if args.stats:
                print(df_sample.describe().to_string())
        
        else:
            # Conversão simples
            df = converter.convert(args.input, args.output, args.input_format, args.output_format)
            if args.stats:
                print(df.describe().to_string())
        
        print("\n✅ Operação concluída com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())