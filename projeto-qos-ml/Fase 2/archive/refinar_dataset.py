import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

print("1. A ler o tráfego bruto do Kaggle...")
df_bruto = pd.read_csv('consolidated_traffic_data.csv')

# Isolamos APENAS o tráfego de Streaming
df_streaming = df_bruto[df_bruto['traffic_type'] == 'STREAMING'].copy()

colunas = [
    'flowBytesPerSecond', # Throughput (Vazão)
    'flowPktsPerSecond',  # Densidade
    'mean_flowiat',       # Tempo médio de chegada
    'std_flowiat',        # Jitter (A variação que o DASH odeia)
    'mean_active',        # Tempo de download do chunk
    'mean_idle'           # Tempo de descanso do player
]
df_limpo = df_streaming[colunas].copy()

# Removemos qualquer sujidade (NaN) que possa ter vindo do dataset original
df_limpo = df_limpo.dropna()

print(f"-> Encontradas {len(df_limpo)} amostras de Streaming perfeito.")


# INJEÇÃO DE ANOMALIAS SINTÉTICAS (3 CENÁRIOS)
print("2. A fabricar cenários de Rede (Normal, Gargalo e Queda)...")

# CENÁRIO 0: REDE SAUDÁVEL (34% dos dados)
df_bom = df_limpo.sample(frac=0.34, random_state=42).copy()
df_bom['Status'] = 0 

restante = df_limpo.drop(df_bom.index)

# CENÁRIO 1: DEGRADAÇÃO / GARGALO (33% dos dados)
df_ruim = restante.sample(frac=0.5, random_state=42).copy()
df_ruim['flowBytesPerSecond'] = df_ruim['flowBytesPerSecond'] * np.random.uniform(0.1, 0.4) 
df_ruim['std_flowiat'] = df_ruim['std_flowiat'] * np.random.uniform(3.0, 6.0) 
df_ruim['mean_idle'] = df_ruim['mean_idle'] * np.random.uniform(0.0, 0.2) 
df_ruim['Status'] = 1 

# CENÁRIO 2: QUEDA DE REDE / SILÊNCIO (33% dos dados)
df_silencio = restante.drop(df_ruim.index).copy()

df_silencio['flowBytesPerSecond'] = 0.0
df_silencio['flowPktsPerSecond'] = 0.0
df_silencio['mean_flowiat'] = 0.0
df_silencio['std_flowiat'] = 0.0
df_silencio['mean_active'] = 0.0
df_silencio['mean_idle'] = 1.0
df_silencio['Status'] = 2 

# Juntamos tudo num único dataset final
df_final = pd.concat([df_bom, df_ruim, df_silencio])

# TREINAMENTO DA IA

print("3. A treinar o modelo Random Forest Definitivo...")
X = df_final.drop('Status', axis=1)
y = df_final['Status']

# Separamos 20% para a prova final da IA
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

modelo_v2 = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
modelo_v2.fit(X_train, y_train)

print("\n--- Boletim da IA ---")
previsoes = modelo_v2.predict(X_test)
print(classification_report(y_test, previsoes, target_names=['Normal (0)', 'Degradação (1)', 'Queda/Silêncio (2)']))

# EXPORTAÇÃO

joblib.dump(modelo_v2, 'modelo_qos_v2.pkl')
df_final.to_csv('dataset_streaming_v2.csv', index=False)

print("Sucesso! O ficheiro 'modelo_qos_v2.pkl' reconhece os 3 cenários de rede de forma autónoma.")
