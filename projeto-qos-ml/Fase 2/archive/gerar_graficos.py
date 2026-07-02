import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Estilo acadêmico
sns.set_theme(style="whitegrid", context="talk")

print("🔍 Carregando os datasets do Laboratório...")
arquivos = {
    'Netflix': 'dataset_netflix_processado.csv',
    'YouTube': 'dataset_youtube_processado.csv',
    'Amazon': 'dataset_amazon_processado.csv'
}

dfs = []
for plataforma, caminho in arquivos.items():
    try:
        df_temp = pd.read_csv(caminho)
        df_temp = df_temp.head(150).copy() 
        df_temp['Terminal'] = plataforma
        df_temp['Tempo_Amostra'] = range(len(df_temp))
        dfs.append(df_temp)
    except FileNotFoundError:
        print(f"⚠️ Aviso: O arquivo {caminho} não foi encontrado.")

df_geral = pd.concat(dfs, ignore_index=True)
paleta_ia = {0: '#2ca02c', 1: '#d62728'} # Verde e Vermelho

# ==========================================
# GRÁFICO 1: MANTIDO (Linha do Tempo)
# ==========================================
print("📊 Gerando Gráfico 1 (Linha do Tempo)...")
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
fig.suptitle('Monitoramento Preditivo Simultâneo: Detecção de Latência (ARTT)', fontsize=16, fontweight='bold', y=0.98)
terminais = list(arquivos.keys())

for i, ax in enumerate(axes):
    dados_plataforma = df_geral[df_geral['Terminal'] == terminais[i]]
    sns.scatterplot(
        ax=ax, x='Tempo_Amostra', y='ARTT', hue='Status', 
        palette=paleta_ia, data=dados_plataforma, 
        s=70, alpha=0.9, edgecolor='white', linewidth=1, legend=False
    )
    ax.axhline(y=45, color='#ff7f0e', linestyle='--', linewidth=2.5, label='Limiar Crítico (45ms)')
    ax.set_title(f"Nó de Tráfego: {terminais[i]}", fontsize=14)
    ax.set_ylabel("Latência (ms)", fontsize=12)
    if i == 0:
        ax.legend(['Normal (0)', 'Degradação (1)', 'Limiar Crítico (45ms)'], loc='upper right', fontsize=11)

axes[-1].set_xlabel("Tempo de Simulação (Amostras Sequenciais)", fontsize=12)
plt.tight_layout()
plt.savefig('grafico_1_linha_tempo_terminais.png', dpi=300, bbox_inches='tight')
plt.close()

# ==========================================
# GRÁFICO 2: CORRIGIDO (Escala Logarítmica e Legenda)
# ==========================================
print("📊 Gerando Gráfico 2 (Escala Logarítmica)...")
plt.figure(figsize=(10, 6))
ax = plt.gca()

max_y = df_geral['ARTT'].max() * 1.1 
ax.axhspan(0, 45, color='#2ca02c', alpha=0.1, label='Zona Saudável (IA: 0)')
ax.axhspan(45, max_y, color='#d62728', alpha=0.1, label='Zona de Gargalo (IA: 1)')

sns.scatterplot(
    x='Length', y='ARTT', hue='Status', palette=paleta_ia, 
    data=df_geral, s=40, alpha=0.8, linewidth=0, legend=False, ax=ax
)

plt.axhline(y=45, color='black', linestyle='--', linewidth=2, label='Fronteira Exata (45ms)')

# A mágica que resolve o acumulo de pontos na esquerda: Escala Logarítmica
plt.xscale('log')

plt.title("Visão Global Logarítmica: Fronteira de Decisão da Inteligência Artificial", fontsize=15, fontweight='bold', pad=15)
plt.xlabel("Tamanho do Pacote - Throughput (Bytes) [Escala Logarítmica]", fontsize=12)
plt.ylabel("Latência - ARTT (ms)", fontsize=12)
plt.ylim(0, max_y)

# Move a legenda para o topo à DIREITA, fora do caminho dos dados
handles, labels = ax.get_legend_handles_labels()
plt.legend(handles=handles, labels=labels, loc='upper right', frameon=True, shadow=True, fontsize=11, title="Mapeamento")

plt.tight_layout()
plt.savefig('grafico_2_dispersao_global.png', dpi=300, bbox_inches='tight')
plt.close()

# ==========================================
# GRÁFICO 3: NOVO! (Jitter vs Tempo Ocioso - Máquina Real)
# ==========================================
print("📊 Gerando Gráfico 3 (Novas Métricas: Jitter e Tempo Ocioso)...")
try:
    df_real = pd.read_csv('metricas_reais_relatorio.csv')
    
    plt.figure(figsize=(10, 6))
    ax2 = plt.gca()
    
    # Define a condição de gargalo baseado na sua métrica de Tempo Ocioso alto (queda da rede)
    df_real['Status_IA'] = np.where(df_real['Tempo_Ocioso'] > 0.5, 1, 0)
    
    # Zonas de perigo para o Jitter e Ociosidade
    max_jitter = df_real['Jitter'].max() * 1.1 if df_real['Jitter'].max() > 0 else 1.0
    ax2.axvspan(0, 0.5, color='#2ca02c', alpha=0.1, label='Rede Fluida')
    ax2.axvspan(0.5, df_real['Tempo_Ocioso'].max() * 1.1, color='#d62728', alpha=0.1, label='Saturação de Buffer/Queda')

    sns.scatterplot(
        x='Tempo_Ocioso', y='Jitter', hue='Status_IA', palette=paleta_ia, 
        data=df_real, s=80, alpha=0.9, edgecolor='white', linewidth=1, legend=False, ax=ax2
    )

    plt.title("Sonda Live (Fase 2): Análise de Jitter vs Tempo Ocioso", fontsize=15, fontweight='bold', pad=15)
    plt.xlabel("Tempo Ocioso da Interface Físíca (Segundos)", fontsize=12)
    plt.ylabel("Jitter - Variação de Inter-Chegada (Desvio Padrão)", fontsize=12)
    
    handles2, labels2 = ax2.get_legend_handles_labels()
    plt.legend(handles=handles2, labels=labels2, loc='upper left', frameon=True, shadow=True, fontsize=11)
    
    plt.tight_layout()
    plt.savefig('grafico_3_novas_metricas.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 3 criado com sucesso usando os dados do teste real!")
    
except FileNotFoundError:
    print("⚠️ O arquivo 'metricas_reais_relatorio.csv' não foi encontrado. O Gráfico 3 foi ignorado.")

print("✅ Todos os gráficos foram gerados. Verifique sua pasta!")
