import pandas as pd

# Substitua pelo nome real de um dos arquivos CSV extraídos
caminho_arquivo = 'dados/archive/Local/Video Streaming/Netflix/Netflix5Agg.csv'

try:
    # Carregando o dataset
    print(f"Carregando dados de: {caminho_arquivo}...\n")
    df = pd.read_csv(caminho_arquivo)
    
    # Exibindo o tamanho do dataset
    linhas, colunas = df.shape
    print(f"Dataset carregado com sucesso!")
    print(f"Total de Linhas (Amostras de Tráfego): {linhas}")
    print(f"Total de Colunas (Features): {colunas}\n")
    
    # Exibindo os nomes de todas as colunas
    print("--- Nomes das Colunas ---")
    print(df.columns.tolist())
    print("\n--- Resumo Estatístico das Features Numéricas ---")
    
    # O método describe() gera a contagem, média, desvio padrão e os quartis
    print(df.describe())

except FileNotFoundError:
    print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
