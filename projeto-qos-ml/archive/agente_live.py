import joblib
import time
import numpy as np
from scapy.all import sniff
from zabbix_utils import Sender, ItemValue
import threading
import warnings
warnings.filterwarnings("ignore")

# ==========================================
# CONFIGURAÇÕES GERAIS
# ==========================================
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
    sniff(iface=PLACA_DE_REDE, filter="(tcp or udp) and port 443", prn=captura_pacotes, store=False)

thread = threading.Thread(target=iniciar_sniffer, daemon=True)
thread.start()

print(f"\n🚀 Escutando tráfego real na interface {PLACA_DE_REDE}...")
print("Abra o YouTube e veja o painel do Grafana ganhar vida!\n")

# Contador para tolerância do protocolo DASH
contador_inatividade = 0 

try:
    while True:
        time.sleep(1) 
        
        pacotes_atuais = pacotes_buffer.copy()
        pacotes_buffer.clear()
        
        # CENÁRIO 1: Rede ativa (Tráfego chegando)
        if len(pacotes_atuais) > 1:
            contador_inatividade = 0 # Zera o contador pois a rede respondeu
            
            tempos = [p[0] for p in pacotes_atuais]
            tamanhos = [p[1] for p in pacotes_atuais]
            
            vazao = sum(tamanhos)
            densidade = len(tamanhos)
            
            iats = np.diff(tempos)
            tempo_medio = np.mean(iats)
            jitter = np.std(iats)
            
            tempo_ocioso = sum(iat for iat in iats if iat > 0.05)
            tempo_ativo = 1.0 - tempo_ocioso if tempo_ocioso < 1.0 else 0.01
            
            dados_rede = [[vazao, densidade, tempo_medio, jitter, tempo_ativo, tempo_ocioso]]
            previsao = modelo_rf.predict(dados_rede)[0]
            
            status_num = int(previsao)
            status_ia = "🚨 Degradação" if previsao == 1 else "✅ Limpo"
            tamanho_medio = float(np.mean(tamanhos))

        # CENÁRIO 2: O Silêncio (Pode ser o DASH dormindo ou a rede que caiu)
        else:
            contador_inatividade += 1
            vazao = 0.0
            densidade = 0
            jitter = 0.0
            tempo_ocioso = 1.0 
            tamanho_medio = 0.0
            
            # Só declara morte da rede após 5 segundos de silêncio absoluto
            if contador_inatividade >= 5:
                status_num = 2 
                status_ia = "❌ Rede Inativa"
            else:
                status_num = 0 
                status_ia = "✅ Limpo"

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
