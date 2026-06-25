# Projeto-Avaliacao-de-Desempenho-em-Redes

# 📡 Monitoramento Preditivo de QoS com Machine Learning

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Conteinerizado-2496ED?logo=docker&logoColor=white)
![Zabbix](https://img.shields.io/badge/Zabbix-7.0-red?logo=zabbix&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-Visualiza%C3%A7%C3%A3o-orange?logo=grafana&logoColor=white)
![Machine Learning](https://img.shields.io/badge/IA-Random_Forest-green)

Este projeto implementa uma arquitetura de monitoramento de redes orientada a Inteligência Artificial (AIOps). O objetivo é prever a degradação de tráfego em plataformas de streaming (Netflix, YouTube, Amazon Prime) *antes* que ocorra o travamento (buffer) para o usuário final, utilizando métricas de Variação de Atraso (Jitter), Densidade de Pacotes e Tempos Ociosos.

---

## 🏗️ Arquitetura do Sistema

O projeto opera em um ecossistema conteinerizado (Docker) e é dividido em três camadas principais:
1. **Coleta (Sensores):** Scripts em Python atuando como agentes (`zabbix-sender` e `scapy`), extraindo métricas de tráfego de datasets ou diretamente da placa de rede física.
2. **Cérebro (IA):** Um modelo de Machine Learning (`modelo_qos_v2.pkl`) pré-treinado com algoritmo *Random Forest* para classificar as micro-rajadas de pacotes em Tempo Real (Status 0: Limpo | Status 1: Gargalo).
3. **NOC (Network Operations Center):** Zabbix como motor de alarmística e disparos de e-mail, espelhado em um Dashboard de alta performance no Grafana.

---

## 🛠️ Pré-requisitos

Para rodar este projeto, sua máquina (preferencialmente ambiente Linux/Ubuntu) precisará ter instalado:
* [Docker](https://docs.docker.com/engine/install/) e Docker Compose.
* Python 3.10 ou superior (com pacote `python3-venv`).
* Acesso root (sudo) para escuta de interfaces de rede.

---

## 🚀 Como Instalar e Rodar

### 1. Subindo a Infraestrutura (Zabbix + Grafana + MySQL)
Clone o repositório, entre na pasta do projeto e inicie os containers:

```bash
git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
cd SEU_REPOSITORIO
docker compose up -d
```

### ⚠️ Atenção (Permissões do Grafana): Se o container do Grafana entrar em loop de reinicialização (restarting), é necessário conceder a permissão correta (ID 472) à pasta de dados na sua máquina host:

sudo chown -R 472:472 grafana_data/

docker compose restart grafana

### Configurando o Ambiente Python (Cérebro e Agentes) Para evitar conflitos com pacotes do sistema operacional (PEP 668 do Ubuntu), crie um ambiente virtual isolado:
```bash
cd archive
python3 -m venv venv
source venv/bin/activate
pip install zabbix-utils scikit-learn pandas numpy scapy joblib matplotlib seaborn
```

### Acesse as interfaces web:

Zabbix: http://localhost:8081
Grafana: http://localhost:3000


### Cenário 1: Simulação Controlada (Múltiplos Hosts)
Utiliza datasets pré-processados para simular tráfego de três nós simultâneos e envia as métricas para o Zabbix. Ideal para testes de carga e validação dos painéis.

### Antes de executar o agente, deve alterar dentro do arquivo qual dataset você vai querer injetar para que seja alinhado com o zabbix.
vim/nano agente_global.py
./venv/bin/python3 agente_global.py

### Cenário 2: Inferência Ao Vivo (Teste Real)
Transforma a máquina em uma sonda SRE. O script escuta a placa de rede em tempo real (enp4s0 ou equivalente), calcula o Jitter, consulta a IA a cada segundo e reporta anomalias instantaneamente.
Nota: Requer privilégios de administrador para usar o módulo Scapy.

# O comando usa o Python do ambiente virtual com permissão sudo
sudo ./venv/bin/python3 agente_live.py

### Caso realize capturas externas via Wireshark (.pcapng exportado para .csv), utilize o script de refinamento para extrair as métricas exatas consolidadas por segundo (Vazão, Densidade, Jitter):
./venv/bin/python3 extrair_teste_real.py

Isso gerará o arquivo metricas_reais_relatorio.csv, pronto para ser plotado em gráficos acadêmicos.


### Autores
Hugo Antônio Fernandes dos Santos
//
Pedro Henrique Teixeira Cardoso de Paula
