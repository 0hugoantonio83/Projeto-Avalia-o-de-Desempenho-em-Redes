import pandas as pd
import joblib
from zabbix_utils import Sender, ItemValue
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ==========================================
# CONFIGURAÇÃO DESTE NÓ (Mude para cada VM/Terminal)
# ==========================================
NOME_DO_HOST_ZABBIX = 'Node_Amazon' # Ex: Node_YouTube, Node_Amazon
NOME_DO_ARQUIVO_CSV = 'dataset_amazon.csv' # Ex: youtube.csv
IP_DO_ZABBIX = '127.0.0.1' # Se for rodar em outra VM na rede, coloque o IP do Ubuntu do Zabbix!

# ==========================================
# INICIALIZAÇÃO
# ==========================================
print(f"[{NOME_DO_HOST_ZABBIX}] Carregando cérebro da IA (modelo_ia_qos.pkl)...")
modelo_rf = joblib.load('modelo_ia_qos.pkl')

print(f"[{NOME_DO_HOST_ZABBIX}] Carregando pacote de dados: {NOME_DO_ARQUIVO_CSV}...")
df = pd.read_csv(NOME_DO_ARQUIVO_CSV)
zabbix_sender = Sender(server=IP_DO_ZABBIX, port=10051)

print(f"\n🚀 Iniciando injeção de tráfego no Zabbix...")
try:
    for index, row in df.head(300).iterrows():
        latencia = row['ARTT']
        tamanho = row['Length']
        
        # A IA avalia os dados da própria VM localmente
        previsao = modelo_rf.predict([[tamanho, latencia]])[0]
        status_ia = "Gargalo Iminente" if previsao == 1 else "Streaming Saudável"

        # Enviando para o Host específico no Zabbix
        metricas = [
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.latencia', latencia),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.tamanho', int(tamanho)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.status', int(previsao))
        ]
        
        zabbix_sender.send(metricas)
        print(f"[{NOME_DO_HOST_ZABBIX}] Enviado -> Latência: {latencia:.1f}ms | Diagnóstico: {status_ia}")
        time.sleep(1)

except KeyboardInterrupt:
    print(f"\n[{NOME_DO_HOST_ZABBIX}] Simulação interrompida.")
