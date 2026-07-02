import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

print("1. Carregando dados originais para estudo...")
# Aqui usamos o seu dataset já processado da Fase 1
df = pd.read_csv('dataset_netflix_processado.csv')
X = df[['Length', 'ARTT']]
y = df['Status']

print("2. Treinando a Inteligência Artificial...")
modelo_rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
modelo_rf.fit(X, y)

print("3. Salvando o 'Cérebro' no disco...")
# Isso cria um arquivo físico com o modelo treinado
joblib.dump(modelo_rf, 'modelo_ia_qos.pkl')
print("Sucesso! O arquivo 'modelo_ia_qos.pkl' está pronto para ser enviado para as VMs.")
