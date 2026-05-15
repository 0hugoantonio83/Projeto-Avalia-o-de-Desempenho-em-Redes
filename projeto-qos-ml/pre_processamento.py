import pandas as pd
import numpy as np

# Caminho do nosso arquivo perfeito da Netflix
caminho_arquivo = 'dados/archive/Local/Video Streaming/YouTube/YouTube10Agg.csv'

print(f"Iniciando o pré-processamento do arquivo: {caminho_arquivo}")
df = pd.read_csv(caminho_arquivo)

# 1. Definir a regra de Degradação (Labeling)
# Limiar escolhido com base no 3º Quartil (75%) da análise exploratória.
LIMIAR_LATENCIA = 45.0

# Cria a coluna 'Status': 1 se ARTT > 45 (Degradação), 0 caso contrário (Normal)
df['Status'] = np.where(df['ARTT'] > LIMIAR_LATENCIA, 1, 0)

# 2. Limpeza de Features
# Vamos manter apenas 'Time' (para usarmos na simulação de tempo real depois),
# 'Length' (Throughput em bytes) e 'ARTT' (Latência).
colunas_uteis = ['Time', 'Length', 'ARTT', 'Status']
df_limpo = df[colunas_uteis].copy()

# Remove qualquer linha com dados corrompidos ou vazios
df_limpo.dropna(inplace=True)

# 3. Exibir o balanceamento das classes
print("\n--- Distribuição do Tráfego ---")
contagem = df_limpo['Status'].value_counts()
porcentagem = df_limpo['Status'].value_counts(normalize=True) * 100

for status, count in contagem.items():
    rotulo = "Normal" if status == 0 else "Degradação"
    pct = porcentagem[status]
    print(f"[{status}] {rotulo}: {count} amostras ({pct:.2f}%)")

# 4. Exportação do Dataset Limpo
nome_arquivo_saida = 'dataset_youtube_processado.csv'
df_limpo.to_csv(nome_arquivo_saida, index=False)

print(f"\nPré-processamento concluído! Arquivo final salvo como '{nome_arquivo_saida}'")
