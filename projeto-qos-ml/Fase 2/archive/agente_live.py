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
    sniff(iface=PLACA_DE_REDE, filter="(tcp or udp) and port 443", prn=captura_pacotes, store=False)

thread = threading.Thread(target=iniciar_sniffer, daemon=True)
thread.start()

print(f"\n🚀 Escutando tráfego real na interface {PLACA_DE_REDE}...")
print("Abra o YouTube e veja o painel do Grafana ganhar vida!\n")

try:
    while True:
        time.sleep(1) 
        
        pacotes_atuais = pacotes_buffer.copy()
        pacotes_buffer.clear()

        # CENÁRIO 1: Rede Ativa (Temos pacotes fluindo)
        if len(pacotes_atuais) > 0:
            tempos = [p[0] for p in pacotes_atuais]
            tamanhos = [p[1] for p in pacotes_atuais]

            vazao = sum(tamanhos)
            densidade = len(pacotes_atuais)

            if densidade > 1:
                iats = np.diff(tempos)
                tempo_medio = float(np.mean(iats))
                jitter = float(np.std(iats))
            else:
                tempo_medio = 0.0
                jitter = 0.0

            tempo_ativo = tempos[-1] - tempos[0] if densidade > 1 else 0.0
            tempo_ocioso = 1.0 - tempo_ativo if tempo_ativo < 1.0 else 0.0

            # Passamos os dados para a IA
            dados_rede = [[vazao, densidade, tempo_medio, jitter, tempo_ativo, tempo_ocioso]]
            previsao = modelo_rf.predict(dados_rede)[0]
            
            status_num = int(previsao)
            tamanho_medio = float(np.mean(tamanhos))

        # CENÁRIO 2: O Silêncio Absoluto (Zero pacotes)
        else:
            vazao = 0.0
            densidade = 0
            tempo_medio = 0.0
            jitter = 0.0
            tempo_ativo = 0.0
            tempo_ocioso = 1.0 
            tamanho_medio = 0.0
            
            
            dados_rede = [[vazao, densidade, tempo_medio, jitter, tempo_ativo, tempo_ocioso]]
            previsao = modelo_rf.predict(dados_rede)[0]
            status_num = int(previsao)

        # Tradutor de logs para o ecrã
        if status_num == 0:
            status_ia = "✅ Limpo"
        elif status_num == 1:
            status_ia = "🚨 Degradação"
        else:
            status_ia = "❌ Rede Inativa"

        metricas = [
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.status', status_num),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.vazao', float(vazao)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.jitter', float(jitter)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.idle', float(tempo_ocioso)),
            ItemValue(NOME_DO_HOST_ZABBIX, 'qos.tamanho', float(tamanho_medio))
        ]
        
        zabbix_sender.send(metricas)
        print(f"[{NOME_DO_HOST_ZABBIX}] Vazão: {vazao/1024:.1f} KB/s | Jitter: {jitter:.4f}s | IA: {status_ia}")

except KeyboardInterrupt:
    print("\nMonitoramento encerrado pelo usuário.")
