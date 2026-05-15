import subprocess
import pandas as pd
import time
import io

# Configuração do Extrator
INTERFACE_REDE = "eth0" # Mude para a sua interface de internet (use o comando 'ip a' no terminal para descobrir, pode ser enp0s3)
TEMPO_CAPTURA_SEGUNDOS = 60 # Quanto tempo ele vai gravar a rede antes de gerar o CSV
ARQUIVO_SAIDA = "meu_tráfego_ao_vivo.csv"

print(f"📡 Iniciando a escuta na interface {INTERFACE_REDE} por {TEMPO_CAPTURA_SEGUNDOS} segundos...")
print("Abra a Netflix/YouTube agora para gerar tráfego!")

# Comando mágico do TShark (captura só tráfego HTTPS/Vídeo)
comando_tshark = [
    "tshark", "-i", INTERFACE_REDE, 
    "-Y", "tcp.port==443", # Filtra só tráfego web seguro (onde os streamings rodam)
    "-T", "fields",
    "-e", "frame.time_epoch",         # Timestamp
    "-e", "tcp.window_size_value",    # Janela TCP (indicador de engarrafamento)
    "-e", "tcp.analysis.retransmission", # Pacotes perdidos
    "-e", "frame.len",                # Tamanho do pacote
    "-E", "header=y", "-E", "separator=,"
]

# Executa o TShark e guarda o resultado na memória
processo = subprocess.Popen(comando_tshark, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)

try:
    # Deixa o TShark rodando pelo tempo definido
    time.sleep(TEMPO_CAPTURA_SEGUNDOS)
    processo.terminate() # Para a gravação
    
    # Pega o texto gerado (o formato CSV cru)
    saida_csv, _ = processo.communicate()
    
    print("Processando os dados com Pandas...")
    # Lê os dados crus como um DataFrame
    df_cru = pd.read_csv(io.StringIO(saida_csv))
    
    # Limpeza básica: O TShark deixa espaços vazios onde não há retransmissão
    df_cru['tcp.analysis.retransmission'] = df_cru['tcp.analysis.retransmission'].fillna(0)
    
    # ----------------------------------------------------
    # MATEMÁTICA DO DASH (Agrupando os dados por segundo)
    # ----------------------------------------------------
    # Em vez de olhar pacote por pacote, nós tiramos a média de cada segundo
    df_cru['segundo_exato'] = pd.to_datetime(df_cru['frame.time_epoch'], unit='s').dt.floor('S')
    
    df_processado = df_cru.groupby('segundo_exato').agg(
        total_pacotes=('frame.len', 'count'),
        tamanho_medio_pacote=('frame.len', 'mean'),
        retransmissoes_tcp_soma=('tcp.analysis.retransmission', 'sum'),
        janela_tcp_media=('tcp.window_size_value', 'mean')
    ).reset_index()

    # Salva o arquivo polido!
    df_processado.to_csv(ARQUIVO_SAIDA, index=False)
    print(f"Sucesso! Dados mastigados e salvos em: {ARQUIVO_SAIDA}")
    print("Dê uma olhada no CSV. É exatamente isso que a IA vai comer!")

except Exception as e:
    print(f"Erro durante a captura: {e}")
    processo.terminate()
