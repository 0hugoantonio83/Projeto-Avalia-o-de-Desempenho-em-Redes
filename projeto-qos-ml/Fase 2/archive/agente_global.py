import pandas as pd
import joblib
from zabbix_utils import Sender, ItemValue
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ==========================================
# ESCOLHA QUAL NÓ ESTE TERMINAL VAI SIMULAR
# Descomente apenas o bloco que deseja usar neste terminal
# ==========================================

# TERMINAL 1:
NOME_DO_HOST_ZABBIX = 'Node_Netflix' 
ARQUIVO_ESPECIFICO = 'dataset_netflix_processado.csv'

# TERMINAL 2:
#NOME_DO_HOST_ZABBIX = 'Node_YouTube'
#ARQUIVO_ESPECIFICO = 'dataset_youtube_processado.csv'

# TERMINAL 3:
#NOME_DO_HOST_ZABBIX = 'Node_Amazon'
#ARQUIVO_ESPECIFICO = 'dataset_amazon_processado.csv'

# ==========================================
IP_DO_ZABBIX = '127.0.0.1'

print(f"🧠 Carregando o Cérebro da IA (modelo_qos_v2.pkl)...")
modelo_rf = joblib.load('modelo_qos_v2.pkl')

print(f"📊 Carregando dados base e o perfil específico do {NOME_DO_HOST_ZABBIX}...\n")

# Dataset Base (Agora contém as simulações perfeitas de Buffer vs Queda)
df_novo = pd.read_csv('dataset_streaming_v2.csv').sample(frac=1).reset_index(drop=True)

# Dataset Específico (Latência e Tamanho reais da plataforma - Legado da Fase 1)
df_plataforma = pd.read_csv(ARQUIVO_ESPECIFICO).sample(frac=1).reset_index(drop=True)

zabbix_sender = Sender(server=IP_DO_ZABBIX, port=10051)

print(f"🚀 Iniciando simulação Global para o host {NOME_DO_HOST_ZABBIX}...")
print("Pressione Ctrl+C para parar.\n")

try:
    limite = min(len(df_novo), len(df_plataforma))
    
    for i in range(limite):
        linha_nova = df_novo.iloc[i]
        linha_especifica = df_plataforma.iloc[i]

        vazao = linha_nova['flowBytesPerSecond']
        densidade = linha_nova['flowPktsPerSecond']
        tempo_medio = linha_nova['mean_flowiat']
        jitter = linha_nova['std_flowiat']
        tempo_ativo = linha_nova['mean_active']
        tempo_ocioso = linha_nova['mean_idle']
        
        # IA Avalia (0: Limpo/Buffer, 1: Degradação, 2: Queda Real)
        dados_rede = [[vazao, densidade, tempo_medio, jitter, tempo_ativo, tempo_ocioso]]
        previsao = modelo_rf.predict(dados_rede)[0]
        status_num = int(previsao)
        
        if status_num == 0:
            status_ia = "✅ Limpo (Streaming ou Buffer)"
        elif status_num == 1:
            status_ia = "🚨 Degradação"
        else:
            status_ia = "❌ Rede Inativa"

        latencia_real = linha_especifica['ARTT']
        tamanho_pacote = linha_especifica['Length']

        # Envio unificado para o Zabbix com Zabbix integrado ao Grafana
        metricas = [
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.latencia', float(latencia_real)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.tamanho', float(tamanho_pacote)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.status', status_num),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.vazao', float(vazao)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.jitter', float(jitter)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.idle', float(tempo_ocioso))
        ]
        
        zabbix_sender.send(metricas)
        # O print agora mostra o tempo ocioso simulado para provar que a IA está a pensar
        print(f"[{NOME_DO_HOST_ZABBIX}] Vazão: {vazao/1024:.1f} KB/s | Ocioso: {tempo_ocioso:.1f}s | IA: {status_ia}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print(f"\nSimulação do {NOME_DO_HOST_ZABBIX} encerrada pelo utilizador.")
