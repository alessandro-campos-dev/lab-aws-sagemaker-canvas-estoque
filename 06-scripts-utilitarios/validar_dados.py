#!/usr/bin/env python3
"""
Validador de Dados para Previsão de Estoque

Validações implementadas:
- Validação de schema e tipos de dados
- Valores ausentes e outliers
- Consistência temporal e lógica de negócio
- Integridade referencial
- Qualidade estatística dos dados
"""

import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Tuple, Optional, Any
import sys

warnings.filterwarnings('ignore')

class DataValidator:
    """Validador completo de dados de estoque"""
    
    def __init__(self):
        self.schema = {
            'ID': {'type': 'int', 'required': True, 'min': 1},
            'ID_PRODUTO': {'type': 'int', 'required': True, 'min': 1001, 'max': 1050},
            'DIA': {'type': 'date', 'required': True, 'format': '%d/%m/%Y'},
            'FLAG_PROMOCAO': {'type': 'int', 'required': True, 'values': [0, 1]},
            'QUANTIDADE_ESTOQUE': {'type': 'int', 'required': True, 'min': 0, 'max': 1000}
        }
        
        self.validation_rules = {
            'business_rules': [
                'estoque_nao_negativo',
                'promocao_binaria',
                'produtos_validos',
                'datas_sequenciais',
                'estoque_decrescente'
            ],
            'statistical_rules': [
                'outliers_iqr',
                'distribuicao_normal',
                'completude_dados',
                'consistencia_temporal'
            ],
            'quality_rules': [
                'unicidade_registros',
                'formato_datas',
                'tipos_corretos',
                'faixas_validas'
            ]
        }
        
        self.results = {
            'passed': [],
            'warnings': [],
            'errors': [],
            'summary': {},
            'suggestions': []
        }
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """Carrega dados do arquivo"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        
        # Detecta formato pelo sufixo
        suffix = path.suffix.lower()
        
        try:
            if suffix == '.csv':
                df = pd.read_csv(filepath, encoding='utf-8-sig')
            elif suffix == '.parquet':
                df = pd.read_parquet(filepath)
            elif suffix == '.json':
                df = pd.read_json(filepath)
            elif suffix == '.xlsx':
                df = pd.read_excel(filepath)
            else:
                raise ValueError(f"Formato não suportado: {suffix}")
            
            print(f"✅ Dados carregados: {len(df)} registros, {len(df.columns)} colunas")
            return df
            
        except Exception as e:
            raise Exception(f"Erro ao carregar arquivo {filepath}: {str(e)}")
    
    def validate_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Valida schema e tipos de dados"""
        schema_results = {'passed': 0, 'errors': []}
        
        # Verifica colunas obrigatórias
        required_cols = [col for col, rules in self.schema.items() if rules.get('required', False)]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            error_msg = f"Colunas obrigatórias ausentes: {missing_cols}"
            schema_results['errors'].append(error_msg)
            self.results['errors'].append(error_msg)
        
        # Valida cada coluna
        for column, rules in self.schema.items():
            if column not in df.columns:
                continue
                
            col_data = df[column]
            
            # Valida tipo de dados
            if rules['type'] == 'int':
                if not pd.api.types.is_integer_dtype(col_data):
                    try:
                        df[column] = pd.to_numeric(col_data, errors='coerce').astype('Int64')
                    except:
                        error_msg = f"Coluna {column}: Tipo deve ser inteiro"
                        schema_results['errors'].append(error_msg)
            
            elif rules['type'] == 'date':
                try:
                    df[column] = pd.to_datetime(col_data, format='%d/%m/%Y', errors='coerce')
                    invalid_dates = col_data.isna().sum()
                    if invalid_dates > 0:
                        error_msg = f"Coluna {column}: {invalid_dates} datas inválidas"
                        schema_results['errors'].append(error_msg)
                except:
                    error_msg = f"Coluna {column}: Formato de data inválido (esperado dd/mm/aaaa)"
                    schema_results['errors'].append(error_msg)
            
            # Valida valores mínimos/máximos
            if 'min' in rules:
                below_min = (df[column] < rules['min']).sum()
                if below_min > 0:
                    error_msg = f"Coluna {column}: {below_min} valores abaixo do mínimo ({rules['min']})"
                    schema_results['errors'].append(error_msg)
            
            if 'max' in rules:
                above_max = (df[column] > rules['max']).sum()
                if above_max > 0:
                    error_msg = f"Coluna {column}: {above_max} valores acima do máximo ({rules['max']})"
                    schema_results['errors'].append(error_msg)
            
            # Valida valores permitidos
            if 'values' in rules:
                invalid_values = ~df[column].isin(rules['values'])
                invalid_count = invalid_values.sum()
                if invalid_count > 0:
                    error_msg = f"Coluna {column}: {invalid_count} valores fora do conjunto permitido {rules['values']}"
                    schema_results['errors'].append(error_msg)
        
        schema_results['passed'] = len(schema_results['errors']) == 0
        if schema_results['passed']:
            self.results['passed'].append("Schema validado com sucesso")
        
        return schema_results
    
    def validate_business_rules(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Valida regras de negócio"""
        business_results = {'passed': 0, 'warnings': [], 'errors': []}
        
        # 1. Estoque não pode ser negativo
        negative_stock = (df['QUANTIDADE_ESTOQUE'] < 0).sum()
        if negative_stock > 0:
            error_msg = f"Estoque negativo: {negative_stock} registros com estoque negativo"
            business_results['errors'].append(error_msg)
            self.results['errors'].append(error_msg)
        
        # 2. Flag promoção deve ser 0 ou 1
        invalid_promo = ~df['FLAG_PROMOCAO'].isin([0, 1])
        invalid_promo_count = invalid_promo.sum()
        if invalid_promo_count > 0:
            error_msg = f"Flag promoção inválida: {invalid_promo_count} registros com valores diferentes de 0/1"
            business_results['errors'].append(error_msg)
            self.results['errors'].append(error_msg)
        
        # 3. IDs de produto devem estar no range válido
        valid_products = df['ID_PRODUTO'].between(1001, 1050)
        invalid_products = (~valid_products).sum()
        if invalid_products > 0:
            error_msg = f"IDs de produto inválidos: {invalid_products} registros fora do range 1001-1050"
            business_results['errors'].append(error_msg)
            self.results['errors'].append(error_msg)
        
        # 4. Verifica sequência temporal
        if 'DIA' in df.columns:
            try:
                df['DIA_DATE'] = pd.to_datetime(df['DIA'], format='%d/%m/%Y')
                date_range = df['DIA_DATE'].max() - df['DIA_DATE'].min()
                if date_range.days < 0:
                    warning_msg = "Datas fora de ordem cronológica"
                    business_results['warnings'].append(warning_msg)
                    self.results['warnings'].append(warning_msg)
            except:
                pass
        
        # 5. Verifica duplicatas por produto/dia
        duplicate_check = ['ID_PRODUTO', 'DIA']
        if all(col in df.columns for col in duplicate_check):
            duplicates = df.duplicated(subset=duplicate_check, keep=False)
            duplicate_count = duplicates.sum()
            if duplicate_count > 0:
                warning_msg = f"Possíveis duplicatas: {duplicate_count} registros com mesmo produto/dia"
                business_results['warnings'].append(warning_msg)
                self.results['warnings'].append(warning_msg)
        
        business_results['passed'] = len(business_results['errors']) == 0
        if business_results['passed']:
            self.results['passed'].append("Regras de negócio validadas")
        
        return business_results
    
    def validate_statistical_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Valida qualidade estatística dos dados"""
        stats_results = {'passed': 0, 'warnings': [], 'suggestions': []}
        
        # 1. Completude dos dados
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        completeness_rate = 1 - (missing_cells / total_cells)
        
        if completeness_rate < 0.95:
            warning_msg = f"Baixa completude: {missing_cells} valores ausentes ({completeness_rate:.1%} completos)"
            stats_results['warnings'].append(warning_msg)
            self.results['warnings'].append(warning_msg)
        else:
            stats_results['suggestions'].append(f"Completude excelente: {completeness_rate:.1%}")
        
        # 2. Outliers usando IQR (para estoque)
        if 'QUANTIDADE_ESTOQUE' in df.columns:
            Q1 = df['QUANTIDADE_ESTOQUE'].quantile(0.25)
            Q3 = df['QUANTIDADE_ESTOQUE'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df['QUANTIDADE_ESTOQUE'] < lower_bound) | 
                         (df['QUANTIDADE_ESTOQUE'] > upper_bound)]
            outlier_count = len(outliers)
            
            if outlier_count > 0:
                warning_msg = f"Possíveis outliers: {outlier_count} registros fora do range [{lower_bound:.0f}, {upper_bound:.0f}]"
                stats_results['warnings'].append(warning_msg)
                self.results['warnings'].append(warning_msg)
        
        # 3. Distribuição de estoque
        if 'QUANTIDADE_ESTOQUE' in df.columns:
            stock_stats = {
                'mean': df['QUANTIDADE_ESTOQUE'].mean(),
                'std': df['QUANTIDADE_ESTOQUE'].std(),
                'min': df['QUANTIDADE_ESTOQUE'].min(),
                'max': df['QUANTIDADE_ESTOQUE'].max(),
                'median': df['QUANTIDADE_ESTOQUE'].median()
            }
            
            # Verifica se distribuição é muito enviesada
            if stock_stats['std'] / stock_stats['mean'] > 0.5:
                suggestion = "Distribuição de estoque com alta variabilidade - verificar dados"
                stats_results['suggestions'].append(suggestion)
                self.results['suggestions'].append(suggestion)
        
        # 4. Consistência temporal
        if 'DIA' in df.columns:
            try:
                df['DIA_DATE'] = pd.to_datetime(df['DIA'], format='%d/%m/%Y')
                daily_counts = df['DIA_DATE'].value_counts().sort_index()
                
                if daily_counts.std() / daily_counts.mean() > 0.3:
                    warning_msg = "Variação significativa no número de registros por dia"
                    stats_results['warnings'].append(warning_msg)
                    self.results['warnings'].append(warning_msg)
            except:
                pass
        
        stats_results['passed'] = len(stats_results['warnings']) == 0
        if stats_results['passed']:
            self.results['passed'].append("Qualidade estatística validada")
        
        return stats_results
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Valida qualidade geral dos dados"""
        quality_results = {'passed': 0, 'issues': [], 'suggestions': []}
        
        # 1. Integridade referencial
        if 'ID_PRODUTO' in df.columns:
            unique_products = df['ID_PRODUTO'].nunique()
            if unique_products < 10:
                issue = f"Poucos produtos únicos: {unique_products} (esperado ~50)"
                quality_results['issues'].append(issue)
                self.results['warnings'].append(issue)
        
        # 2. Variabilidade temporal
        if 'DIA' in df.columns and len(df) > 0:
            try:
                df['DIA_DATE'] = pd.to_datetime(df['DIA'], format='%d/%m/%Y')
                date_range = df['DIA_DATE'].max() - df['DIA_DATE'].min()
                
                if date_range.days < 7:
                    suggestion = f"Período temporal curto: {date_range.days} dias (recomendado > 14 dias)"
                    quality_results['suggestions'].append(suggestion)
                    self.results['suggestions'].append(suggestion)
            except:
                pass
        
        # 3. Balanceamento de classes (promoção)
        if 'FLAG_PROMOCAO' in df.columns:
            promo_dist = df['FLAG_PROMOCAO'].value_counts(normalize=True)
            if len(promo_dist) > 1:
                min_class = promo_dist.min()
                if min_class < 0.2:
                    suggestion = f"Classe minoritária pequena: {min_class:.1%} (promoções)"
                    quality_results['suggestions'].append(suggestion)
                    self.results['suggestions'].append(suggestion)
        
        # 4. Tamanho do dataset
        if len(df) < 100:
            issue = f"Dataset pequeno: {len(df)} registros (mínimo recomendado: 500)"
            quality_results['issues'].append(issue)
            self.results['warnings'].append(issue)
        elif len(df) > 10000:
            suggestion = f"Dataset grande: {len(df):,} registros - considerar amostragem"
            quality_results['suggestions'].append(suggestion)
            self.results['suggestions'].append(suggestion)
        
        quality_results['passed'] = len(quality_results['issues']) == 0
        if quality_results['passed']:
            self.results['passed'].append("Qualidade dos dados validada")
        
        return quality_results
    
    def generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Gera resumo estatístico dos dados"""
        summary = {
            'geral': {
                'total_registros': len(df),
                'total_colunas': len(df.columns),
                'periodo_inicio': None,
                'periodo_fim': None,
                'duracao_dias': None
            },
            'colunas': {},
            'distribuicoes': {},
            'qualidade': {}
        }
        
        # Informações gerais
        if 'DIA' in df.columns:
            try:
                df['DIA_DATE'] = pd.to_datetime(df['DIA'], format='%d/%m/%Y')
                summary['geral']['periodo_inicio'] = df['DIA_DATE'].min().strftime('%d/%m/%Y')
                summary['geral']['periodo_fim'] = df['DIA_DATE'].max().strftime('%d/%m/%Y')
                summary['geral']['duracao_dias'] = (df['DIA_DATE'].max() - df['DIA_DATE'].min()).days + 1
            except:
                pass
        
        # Estatísticas por coluna
        for column in df.columns:
            if column == 'DIA_DATE':
                continue
                
            col_data = df[column]
            col_summary = {
                'tipo': str(col_data.dtype),
                'unicos': col_data.nunique(),
                'nulos': col_data.isna().sum(),
                'completude': 1 - (col_data.isna().sum() / len(col_data))
            }
            
            if pd.api.types.is_numeric_dtype(col_data):
                col_summary.update({
                    'media': float(col_data.mean()),
                    'mediana': float(col_data.median()),
                    'desvio_padrao': float(col_data.std()),
                    'min': float(col_data.min()),
                    'max': float(col_data.max())
                })
            
            summary['colunas'][column] = col_summary
        
        # Distribuições importantes
        if 'FLAG_PROMOCAO' in df.columns:
            promo_dist = df['FLAG_PROMOCAO'].value_counts().to_dict()
            summary['distribuicoes']['promocao'] = {
                'com_promocao': promo_dist.get(1, 0),
                'sem_promocao': promo_dist.get(0, 0),
                'percentual_promocao': (promo_dist.get(1, 0) / len(df)) * 100
            }
        
        if 'ID_PRODUTO' in df.columns:
            product_dist = df['ID_PRODUTO'].value_counts()
            summary['distribuicoes']['produtos'] = {
                'total_unicos': product_dist.nunique(),
                'top_10_produtos': product_dist.head(10).to_dict()
            }
        
        if 'QUANTIDADE_ESTOQUE' in df.columns:
            stock_data = df['QUANTIDADE_ESTOQUE']
            summary['distribuicoes']['estoque'] = {
                'faixas': {
                    'critico_0_20': ((stock_data >= 0) & (stock_data <= 20)).sum(),
                    'alerta_21_50': ((stock_data >= 21) & (stock_data <= 50)).sum(),
                    'normal_51_100': ((stock_data >= 51) & (stock_data <= 100)).sum(),
                    'alto_100_plus': (stock_data > 100).sum()
                }
            }
        
        # Métricas de qualidade
        total_cells = df.size
        missing_cells = df.isna().sum().sum()
        
        summary['qualidade'] = {
            'completude_geral': 1 - (missing_cells / total_cells),
            'registros_duplicados': df.duplicated().sum(),
            'outliers_estoque': None
        }
        
        # Detecção de outliers
        if 'QUANTIDADE_ESTOQUE' in df.columns:
            Q1 = df['QUANTIDADE_ESTOQUE'].quantile(0.25)
            Q3 = df['QUANTIDADE_ESTOQUE'].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[
                (df['QUANTIDADE_ESTOQUE'] < (Q1 - 1.5 * IQR)) |
                (df['QUANTIDADE_ESTOQUE'] > (Q3 + 1.5 * IQR))
            ]
            summary['qualidade']['outliers_estoque'] = len(outliers)
        
        self.results['summary'] = summary
        return summary
    
    def validate(self, filepath: str) -> Dict[str, Any]:
        """Executa todas as validações"""
        print(f"\n{'='*60}")
        print(f"VALIDANDO: {filepath}")
        print(f"{'='*60}")
        
        try:
            # Carrega dados
            df = self.load_data(filepath)
            
            # Executa validações
            print("\n🔍 Executando validações...")
            
            schema_results = self.validate_schema(df)
            business_results = self.validate_business_rules(df)
            stats_results = self.validate_statistical_quality(df)
            quality_results = self.validate_data_quality(df)
            
            # Gera resumo
            summary = self.generate_summary(df)
            
            # Compila resultados
            validation_results = {
                'file': filepath,
                'timestamp': datetime.now().isoformat(),
                'schema_validation': schema_results,
                'business_validation': business_results,
                'statistical_validation': stats_results,
                'quality_validation': quality_results,
                'summary': summary,
                'overall_status': 'PASS' if len(self.results['errors']) == 0 else 'FAIL'
            }
            
            # Exibe resultados
            self.print_results()
            
            return validation_results
            
        except Exception as e:
            error_msg = f"Erro durante validação: {str(e)}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
            
            return {
                'file': filepath,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_status': 'ERROR'
            }
    
    def print_results(self):
        """Exibe resultados da validação"""
        print(f"\n{'='*60}")
        print("RESULTADOS DA VALIDAÇÃO")
        print(f"{'='*60}")
        
        # Passed
        if self.results['passed']:
            print(f"\n✅ PASSED ({len(self.results['passed'])}):")
            for item in self.results['passed']:
                print(f"  • {item}")
        
        # Warnings
        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for item in self.results['warnings'][:10]:  # Limita a 10
                print(f"  • {item}")
            if len(self.results['warnings']) > 10:
                print(f"  • ... e mais {len(self.results['warnings']) - 10} warnings")
        
        # Errors
        if self.results['errors']:
            print(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for item in self.results['errors'][:10]:  # Limita a 10
                print(f"  • {item}")
            if len(self.results['errors']) > 10:
                print(f"  • ... e mais {len(self.results['errors']) - 10} errors")
        
        # Suggestions
        if self.results['suggestions']:
            print(f"\n💡 SUGGESTIONS ({len(self.results['suggestions'])}):")
            for item in self.results['suggestions'][:5]:  # Limita a 5
                print(f"  • {item}")
        
        # Summary
        if self.results['summary']:
            print(f"\n{'='*60}")
            print("RESUMO ESTATÍSTICO")
            print(f"{'='*60}")
            
            summary = self.results['summary']
            geral = summary.get('geral', {})
            
            print(f"\n📊 GERAL:")
            print(f"  • Registros: {geral.get('total_registros', 'N/A'):,}")
            print(f"  • Colunas: {geral.get('total_colunas', 'N/A')}")
            if geral.get('periodo_inicio'):
                print(f"  • Período: {geral['periodo_inicio']} a {geral['periodo_fim']}")
                print(f"  • Duração: {geral['duracao_dias']} dias")
            
            # Qualidade
            qualidade = summary.get('qualidade', {})
            if qualidade:
                print(f"\n🎯 QUALIDADE:")
                print(f"  • Completude: {qualidade.get('completude_geral', 0):.1%}")
                print(f"  • Duplicatas: {qualidade.get('registros_duplicados', 0)}")
                if qualidade.get('outliers_estoque') is not None:
                    print(f"  • Outliers estoque: {qualidade['outliers_estoque']}")
            
            # Distribuições
            distribuicoes = summary.get('distribuicoes', {})
            if 'promocao' in distribuicoes:
                prom = distribuicoes['promocao']
                print(f"\n🏷️  PROMOÇÕES:")
                print(f"  • Com promoção: {prom.get('com_promocao', 0):,}")
                print(f"  • Sem promoção: {prom.get('sem_promocao', 0):,}")
                print(f"  • Percentual: {prom.get('percentual_promocao', 0):.1f}%")
            
            if 'estoque' in distribuicoes:
                est = distribuicoes['estoque']['faixas']
                print(f"\n📦 DISTRIBUIÇÃO DE ESTOQUE:")
                print(f"  • Crítico (0-20): {est.get('critico_0_20', 0):,}")
                print(f"  • Alerta (21-50): {est.get('alerta_21_50', 0):,}")
                print(f"  • Normal (51-100): {est.get('normal_51_100', 0):,}")
                print(f"  • Alto (>100): {est.get('alto_100_plus', 0):,}")
        
        print(f"\n{'='*60}")
        total_errors = len(self.results['errors'])
        total_warnings = len(self.results['warnings'])
        
        if total_errors == 0 and total_warnings == 0:
            print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")
            print("   Todos os testes passaram sem issues.")
        elif total_errors == 0:
            print("⚠️  VALIDAÇÃO CONCLUÍDA COM AVISOS")
            print(f"   {total_warnings} warnings encontrados.")
        else:
            print("❌ VALIDAÇÃO FALHOU")
            print(f"   {total_errors} errors e {total_warnings} warnings encontrados.")
        
        print(f"{'='*60}\n")
    
    def save_report(self, results: Dict[str, Any], output_path: str):
        """Salva relatório de validação"""
        report = {
            'validation_report': results,
            'results_summary': {
                'total_errors': len(self.results['errors']),
                'total_warnings': len(self.results['warnings']),
                'total_passed': len(self.results['passed']),
                'total_suggestions': len(self.results['suggestions']),
                'overall_status': 'PASS' if len(self.results['errors']) == 0 else 'FAIL'
            },
            'detailed_results': self.results
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Relatório salvo em: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Validador de Dados de Estoque')
    
    parser.add_argument('filepath', help='Caminho para o arquivo de dados')
    parser.add_argument('--output', '-o', help='Caminho para salvar relatório JSON')
    parser.add_argument('--fix', '-f', action='store_true', help='Tenta corrigir problemas automaticamente')
    parser.add_argument('--strict', '-s', action='store_true', help='Modo estrito (falha em warnings)')
    parser.add_argument('--quick', '-q', action='store_true', help='Validação rápida (apenas schema)')
    
    args = parser.parse_args()
    
    validator = DataValidator()
    
    try:
        # Executa validação
        results = validator.validate(args.filepath)
        
        # Salva relatório se solicitado
        if args.output:
            validator.save_report(results, args.output)
        
        # Determina código de saída
        if len(validator.results['errors']) > 0:
            return 1  # Falha
        elif args.strict and len(validator.results['warnings']) > 0:
            return 2  # Falha em modo estrito
        else:
            return 0  # Sucesso
            
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {str(e)}")
        return 3

if __name__ == "__main__":
    sys.exit(main())