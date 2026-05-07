import pandas as pd
import joblib
from zabbix_utils import Sender, ItemValue
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ==========================================
# CONFIGURAÇÕES DA MÁQUINA
# ==========================================
NOME_DO_HOST_ZABBIX = 'Node_Netflix' # Altere conforme a máquina que for testar
IP_DO_ZABBIX = '127.0.0.1'

print("Carregando o novo cérebro da IA (modelo_qos_v2.pkl)...")
modelo_rf = joblib.load('modelo_qos_v2.pkl')

print("Carregando o tráfego de rede capturado...")
# Carregamos o dataset que acabamos de refinar
df = pd.read_csv('dataset_streaming_v2.csv')

# Embaralhamos os dados para a simulação ficar mais realista (misturando rede boa e ruim)
df = df.sample(frac=1).reset_index(drop=True)

zabbix_sender = Sender(server=IP_DO_ZABBIX, port=10051)

print(f"\n Iniciando transmissão de tráfego avançado para o Zabbix...")
try:
    for index, row in df.iterrows():
        # Extraímos as métricas exatas que o nosso modelo exige
        vazao = row['flowBytesPerSecond']
        densidade = row['flowPktsPerSecond']
        tempo_medio = row['mean_flowiat']
        jitter = row['std_flowiat']
        tempo_ativo = row['mean_active']
        tempo_ocioso = row['mean_idle']
        
        # A IA avalia o pacote em milissegundos
        dados_rede = [[vazao, densidade, tempo_medio, jitter, tempo_ativo, tempo_ocioso]]
        previsao = modelo_rf.predict(dados_rede)[0]
        
        status_ia = "GARGALO NA REDE" if previsao == 1 else "Streaming Limpo"

        # Empacotando tudo para o Zabbix
        metricas = [
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.status', int(previsao)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.vazao', float(vazao)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.jitter', float(jitter)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.idle', float(tempo_ocioso))
        ]
        
        zabbix_sender.send(metricas)
        print(f"[{NOME_DO_HOST_ZABBIX}] Vazão: {vazao:.0f} B/s | Jitter: {jitter:.2f} | IA: {status_ia}")
        
        # Pausa de 1 segundo para simular o tráfego ao vivo
        time.sleep(1)

except KeyboardInterrupt:
    print(f"\n[{NOME_DO_HOST_ZABBIX}] Transmissão encerrada pelo usuário.")
