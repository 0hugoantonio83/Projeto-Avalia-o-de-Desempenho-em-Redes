import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

print("1. Lendo o tráfego bruto do Kaggle...")
df_bruto = pd.read_csv('consolidated_traffic_data.csv')

# Isolamos APENAS o tráfego de Streaming
df_streaming = df_bruto[df_bruto['traffic_type'] == 'STREAMING'].copy()

# Selecionamos as nossas "Métricas de Ouro" (Feature Engineering)
colunas_ouro = [
    'flowBytesPerSecond', # Throughput (Vazão)
    'flowPktsPerSecond',  # Densidade
    'mean_flowiat',       # Tempo médio de chegada
    'std_flowiat',        # Jitter (A variação que o DASH odeia)
    'mean_active',        # Tempo de download do chunk
    'mean_idle'           # Tempo de descanso do player
]
df_limpo = df_streaming[colunas_ouro].copy()

# Removemos qualquer sujeira (NaN) que possa ter vindo do dataset original
df_limpo = df_limpo.dropna()

print(f"-> Encontradas {len(df_limpo)} amostras de Streaming perfeito.")

# ==========================================
# 2. INJEÇÃO DE ANOMALIAS SINTÉTICAS
# ==========================================
print("2. Fabricando dados de degradação (Gargalos de Rede)...")

# Pegamos metade dos dados de streaming perfeitos para "estragar"
df_bom = df_limpo.sample(frac=0.5, random_state=42).copy()
df_bom['Status'] = 0 # 0 = Rede Normal

# A outra metade nós vamos transformar em uma rede congestionada
df_ruim = df_limpo.drop(df_bom.index).copy()

# A Matemática do Caos: Como um gargalo afeta a rede
df_ruim['flowBytesPerSecond'] = df_ruim['flowBytesPerSecond'] * np.random.uniform(0.1, 0.4) # Vazão cai 60 a 90%
df_ruim['std_flowiat'] = df_ruim['std_flowiat'] * np.random.uniform(3.0, 6.0) # Jitter explode (pacotes fora de ordem)
df_ruim['mean_idle'] = df_ruim['mean_idle'] * np.random.uniform(0.0, 0.2) # Player quase não descansa (tenta ler buffer o tempo todo)
df_ruim['Status'] = 1 # 1 = DEGRADAÇÃO DETECTADA

# Juntamos tudo em um único dataset final
df_final = pd.concat([df_bom, df_ruim])

# ==========================================
# 3. O TREINAMENTO DO NOVO CÉREBRO
# ==========================================
print("3. Treinando o modelo Random Forest Avançado...")
X = df_final.drop('Status', axis=1)
y = df_final['Status']

# Separamos 20% para a prova final da IA
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

modelo_v2 = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
modelo_v2.fit(X_train, y_train)

print("\n--- BOLETIM DA INTELIGÊNCIA ARTIFICIAL ---")
previsoes = modelo_v2.predict(X_test)
print(classification_report(y_test, previsoes, target_names=['Normal (0)', 'Degradado (1)']))

# ==========================================
# 4. SALVANDO O MODELO E O NOVO DATASET
# ==========================================
print("4. Salvando os arquivos em disco...")
joblib.dump(modelo_v2, 'modelo_qos_v2.pkl')
df_final.to_csv('dataset_streaming_v2.csv', index=False)

print("Sucesso! O novo 'modelo_qos_v2.pkl' está pronto para ser acoplado no Zabbix.")
