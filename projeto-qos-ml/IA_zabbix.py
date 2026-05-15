import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from zabbix_utils import Sender, ItemValue
import time
import warnings

# Ignora avisos chatos do Scikit-Learn no terminal
warnings.filterwarnings("ignore", category=UserWarning)

# 1. Treinamento da IA
print("Carregando dados processados da Netflix...")
df = pd.read_csv('dataset_netflix_processado.csv')

# Separando as métricas (X) do resultado esperado (y)
X = df[['Length', 'ARTT']]
y = df['Status']

print("Treinando o modelo Random Forest (com balanceamento de classes)...")
# O class_weight='balanced' é o segredo para a IA não ignorar os raros gargalos de 7%!
modelo_rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
modelo_rf.fit(X, y)

print("IA treinada com sucesso!\n")

# 2. Simulação de Tráfego (DATA REPLAY)
# Configurando a entrega dos dados no Zabbix (porta 10051 padrão)
zabbix_sender = Sender(server='127.0.0.1', port=10051)
host_zabbix = 'Netflix_Node'

print("Iniciando injeção de dados no Zabbix...")
print("Pressione Ctrl+C para interromper a simulação.\n")

try:
    # Vamos simular as primeiras 200 linhas do CSV como se fosse tráfego em tempo real
    for index, row in df.head(200).iterrows():
        latencia = row['ARTT']
        tamanho = row['Length']
        
        # A IA avalia a amostra atual no exato momento
        previsao = modelo_rf.predict([[tamanho, latencia]])[0]
        status_ia = "DEGRADAÇÃO" if previsao == 1 else "Normal"

        # Empacotando os dados com as chaves exatas que criamos na interface do Zabbix
        metricas = [
            ItemValue(host_zabbix, 'netflix.artt', latencia),
            ItemValue(host_zabbix, 'netflix.length', int(tamanho)),
            ItemValue(host_zabbix, 'netflix.status', int(previsao))
        ]
        
        # Enviando para o Zabbix
        resultado = zabbix_sender.send(metricas)
        
        # Log no terminal para você acompanhar a IA trabalhando
        print(f"Enviado -> Latência: {latencia}ms | Pacote: {int(tamanho)}B | Diagnóstico IA: {status_ia}")
        
        # Pausa de 1 segundo para simular o tempo real do streaming DASH
        time.sleep(1)

except KeyboardInterrupt:
    print("\nSimulação interrompida pelo usuário.")
