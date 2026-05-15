import pandas as pd
import joblib
from zabbix_utils import Sender, ItemValue
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ==========================================
# 1. PERFIL DA MÁQUINA (Troque para cada terminal)
# ==========================================
# TERMINAL 1:
NOME_DO_HOST_ZABBIX = 'Node_Netflix' 
ARQUIVO_ESPECIFICO = 'dataset_netflix_processado.csv'

# TERMINAL 2 (Mude as variáveis acima para):
#NOME_DO_HOST_ZABBIX = 'Node_YouTube'
#ARQUIVO_ESPECIFICO = 'dataset_youtube_processado.csv'

# TERMINAL 3 (Mude as variáveis acima para):
#NOME_DO_HOST_ZABBIX = 'Node_Amazon'
#ARQUIVO_ESPECIFICO = 'dataset_amazon_processado.csv'

IP_DO_ZABBIX = '127.0.0.1'

print(" Carregando o Cérebro da IA (modelo_qos_v2.pkl)...")
modelo_rf = joblib.load('modelo_qos_v2.pkl')

print(f" Carregando dados base e o perfil específico do {NOME_DO_HOST_ZABBIX}...")
# Dataset Base (Comportamento DASH e Vazão para a IA julgar)
df_novo = pd.read_csv('dataset_streaming_v2.csv').sample(frac=1).reset_index(drop=True)

# Dataset Específico (Latência e Tamanho reais da plataforma)
df_plataforma = pd.read_csv(ARQUIVO_ESPECIFICO).sample(frac=1).reset_index(drop=True)

zabbix_sender = Sender(server=IP_DO_ZABBIX, port=10051)

print(f"\n Iniciando transmissão MULTI-CAMADAS para {NOME_DO_HOST_ZABBIX}...")

try:
    # Garante que o loop não quebre caso um arquivo seja menor que o outro
    limite = min(len(df_novo), len(df_plataforma))

    for i in range(limite):
        linha_nova = df_novo.iloc[i]
        linha_especifica = df_plataforma.iloc[i]

        # 1. Métricas Avançadas (Dataset Novo)
        vazao = linha_nova['flowBytesPerSecond']
        densidade = linha_nova['flowPktsPerSecond']
        tempo_medio = linha_nova['mean_flowiat']
        jitter = linha_nova['std_flowiat']
        tempo_ativo = linha_nova['mean_active']
        tempo_ocioso = linha_nova['mean_idle']
        
        # 2. IA Avalia a Degradação
        dados_rede = [[vazao, densidade, tempo_medio, jitter, tempo_ativo, tempo_ocioso]]
        previsao = modelo_rf.predict(dados_rede)[0]
        status_ia = "POSSÍVEL DEGRADAÇÃO" if previsao == 1 else "STREAMING LIMPO"

        # 3. Métricas Reais da Plataforma (Dataset Específico)
        # CORREÇÃO APLICADA: Sem o .iloc, chamando diretamente o nome da coluna!
        latencia_real = linha_especifica['ARTT']
        tamanho_pacote = linha_especifica['Length']

        # 4. Envio unificado para o Zabbix
        metricas = [
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.latencia', float(latencia_real)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.tamanho', float(tamanho_pacote)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.status', int(previsao)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.vazao', float(vazao)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.jitter', float(jitter)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.idle', float(tempo_ocioso))
        ]
        
        zabbix_sender.send(metricas)
        print(f"[{NOME_DO_HOST_ZABBIX}] Ping: {latencia_real:.1f}ms | Vazão: {vazao:.0f} B/s | Jitter: {jitter:.2f} | IA: {status_ia}")
        
        time.sleep(1)

except KeyboardInterrupt:
    print(f"\n[{NOME_DO_HOST_ZABBIX}] Transmissão encerrada.")
