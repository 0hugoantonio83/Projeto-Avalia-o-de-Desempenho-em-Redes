import joblib
import time
import numpy as np
from scapy.all import sniff
from zabbix_utils import Sender, ItemValue
import threading
import warnings
warnings.filterwarnings("ignore")

# CONFIGURAÇÕES GERAIS
PLACA_DE_REDE = "enp4s0"
NOME_DO_HOST_ZABBIX = 'Node_YouTube' 
IP_DO_ZABBIX = '127.0.0.1'

print("Carregando Cérebro da IA para Inferência em TEMPO REAL...")
modelo_rf = joblib.load('modelo_qos_v2.pkl')
zabbix_sender = Sender(server=IP_DO_ZABBIX, port=10051)

pacotes_buffer = []

def captura_pacotes(pkt):
    pacotes_buffer.append((time.time(), len(pkt)))

def iniciar_sniffer():
    # Filtro para tráfego seguro (web/streaming), ignorando pacotes locais
    sniff(iface=PLACA_DE_REDE, filter="(tcp or udp) and port 443", prn=captura_pacotes, store=False)

thread = threading.Thread(target=iniciar_sniffer, daemon=True)
thread.start()

print(f"\n🚀 Escutando tráfego real na interface {PLACA_DE_REDE}...")
print("Abra o YouTube e veja o painel do Grafana ganhar vida!\n")

try:
    while True:
        time.sleep(1) 
        
        # Cria uma cópia da janela de pacotes e limpa o buffer principal
        pacotes_atuais = pacotes_buffer.copy()
        pacotes_buffer.clear()
        
        # CENÁRIO 1: Rede ativa (temos dados para a IA analisar)
        if len(pacotes_atuais) > 1:
            tempos = [p[0] for p in pacotes_atuais]
            tamanhos = [p[1] for p in pacotes_atuais]
            
            vazao = sum(tamanhos)
            densidade = len(tamanhos)
            
            iats = np.diff(tempos)
            tempo_medio = np.mean(iats)
            jitter = np.std(iats)
            
            tempo_ocioso = sum(iat for iat in iats if iat > 0.05)
            tempo_ativo = 1.0 - tempo_ocioso if tempo_ocioso < 1.0 else 0.01
            
            # Julgamento da IA
            dados_rede = [[vazao, densidade, tempo_medio, jitter, tempo_ativo, tempo_ocioso]]
            previsao = modelo_rf.predict(dados_rede)[0]
            
            status_num = int(previsao)
            status_ia = "🚨 Degradação" if previsao == 1 else "✅ Limpo"
            tamanho_medio = float(np.mean(tamanhos))

        else:
            vazao = 0.0
            densidade = 0
            jitter = 0.0
            tempo_ocioso = 1.0 # 100% de ociosidade neste 1 segundo
            
            status_num = 2 # Novo código de status para o Grafana alertar queda total!
            status_ia = "❌ Rede Inativa (Zero Tráfego)"
            tamanho_medio = 0.0

        # Envio para o Zabbix
        metricas = [
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.status', status_num),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.vazao', float(vazao)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.jitter', float(jitter)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.idle', float(tempo_ocioso)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.tamanho', tamanho_medio)
        ]
        zabbix_sender.send(metricas)
        
        print(f"[{time.strftime('%H:%M:%S')}] Pkts: {densidade} | Vazão: {vazao} B/s | Jitter: {jitter:.4f} | IA: {status_ia}")

except KeyboardInterrupt:
    print("\nTransmissão ao vivo encerrada.")
