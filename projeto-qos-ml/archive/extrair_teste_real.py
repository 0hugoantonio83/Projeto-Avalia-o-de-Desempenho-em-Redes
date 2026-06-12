import pandas as pd
import numpy as np

print("🔍 Lendo o CSV bruto do Wireshark...")
# Carrega o CSV gerado pelo Wireshark
df = pd.read_csv('captura_real_bruta.csv')

# Limpa o nome das colunas (o Wireshark às vezes coloca aspas)
df.columns = df.columns.str.replace('"', '').str.strip()

# Verifica se as colunas essenciais estão no arquivo
if 'Time' not in df.columns or 'Length' not in df.columns:
    print("Erro: O formato do CSV não é o esperado pelo Wireshark.")
    print("Colunas encontradas:", df.columns.tolist())
    exit()

# Garante que os dados são numéricos
df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
df['Length'] = pd.to_numeric(df['Length'], errors='coerce')
df = df.dropna(subset=['Time', 'Length'])

# Agrupa o tempo quebrando os milissegundos para gerar janelas de 1 segundo exato
df['Segundo_Absoluto'] = np.floor(df['Time']).astype(int)

resultados = []

print("⚙️ Calculando Vazão, Jitter e Densidade segundo a segundo...")
for sec, group in df.groupby('Segundo_Absoluto'):
    tempos = group['Time'].values
    tamanhos = group['Length'].values
    
    densidade = len(tamanhos)
    vazao = np.sum(tamanhos)
    
    if densidade > 1:
        iats = np.diff(tempos)
        tempo_medio = np.mean(iats)
        jitter = np.std(iats)
        tempo_ocioso = sum(iat for iat in iats if iat > 0.05)
        tempo_ativo = 1.0 - tempo_ocioso if tempo_ocioso < 1.0 else 0.01
    else:
        # Se só teve 1 pacote no segundo, zeramos o jitter
        tempo_medio = 0
        jitter = 0
        tempo_ocioso = 1.0
        tempo_ativo = 0.01
        
    resultados.append({
        'Tempo_Segundos': sec,
        'Vazao_Bytes_sec': vazao,
        'Densidade_Pkts_sec': densidade,
        'Jitter': round(jitter, 6),
        'Tempo_Ocioso': round(tempo_ocioso, 4),
        'Tempo_Ativo': round(tempo_ativo, 4),
        'Tamanho_Medio_Pkt': round(np.mean(tamanhos), 2) if densidade > 0 else 0
    })

# Salva a nova planilha limpa
df_metricas = pd.DataFrame(resultados)
df_metricas.to_csv('metricas_reais_relatorio.csv', index=False)

print("✅ Sucesso! O arquivo 'metricas_reais_relatorio.csv' foi gerado com excelência!")
print(f"Foram analisados {len(df_metricas)} segundos de tráfego real.")
