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
2. **Cérebro (IA):** Um modelo de Machine Learning (`modelo_qos_v2.pkl`) pré-treinado com algoritmo *Random Forest* para classificar as micro-rajadas de pacotes em Tempo Real (Status 0: Limpo | Status 1: Gargalo | Status 2: Queda).
3. **NOC (Network Operations Center):** Zabbix como motor de alarmística relacional, espelhado em um Dashboard de alta performance e mapeamento visual no Grafana.

---

## 🛠️ Pré-requisitos

Para rodar este projeto, sua máquina (preferencialmente ambiente Linux/Ubuntu) precisará ter instalado:
* [Docker](https://docs.docker.com/engine/install/) e Docker Compose.
* Python 3.10 ou superior (com pacote `python3-venv`).
* Acesso root (`sudo`) para escuta profunda de interfaces de rede.

---

## 🚀 Como Instalar e Rodar

### 1. Subindo a Infraestrutura (Zabbix + Grafana + MySQL)
Clone o repositório, entre na pasta do projeto e inicie os containers:

```bash
git clone [https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git](https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git)
cd projeto-qos-ml
docker compose up -d
```

> ⚠️ **Atenção (Permissões do Grafana):** Se o container do Grafana entrar em loop de reinicialização (*CrashLoopBackOff*), é necessário conceder a permissão correta (UID 472) à pasta de dados na sua máquina host antes de reiniciar:
> ```bash
> sudo chown -R 472:472 grafana_data/
> docker compose restart grafana
> ```

### 2. Configurando o Ambiente Python (Cérebro e Agentes)
Para evitar conflitos com pacotes do sistema operacional (PEP 668 do Ubuntu), crie um ambiente virtual isolado:

```bash
python3 -m venv venv
source venv/bin/activate
pip install zabbix-utils scikit-learn pandas numpy scapy joblib matplotlib seaborn
```

### 3. Acesso às Interfaces Web
Após a inicialização, o seu Centro de Operações de Rede estará disponível em:
* **Zabbix:** http://localhost:8081
* **Grafana:** http://localhost:3000

---

## 🧪 Cenários de Execução

### Cenário 1: Simulação Controlada (Múltiplos Hosts)
Utiliza datasets pré-processados para simular tráfego de três nós simultâneos e envia as métricas para o Zabbix. Ideal para testes de carga e validação da escalabilidade dos painéis.

*Antes de executar, edite o arquivo `agente_global.py` para alinhar os datasets com os hosts do Zabbix.*
```bash
cd projeto-qos-ml/Fase\ 2/archive
vim/nano agente_global.py
./venv/bin/python3 agente_global.py
```

### Cenário 2: Inferência Ao Vivo (Sonda Live)
Transforma a máquina em uma sonda SRE. O script escuta a placa de rede em tempo real, calcula a matemática vetorial do tráfego (Jitter, Vazão, Ociosidade) e consulta a IA a cada 1 segundo, reportando anomalias instantaneamente.

**A Inteligência do DASH:** O script possui uma tolerância heurística de 5 segundos. Ele sabe diferenciar quando o tráfego está zerado porque a rede caiu (Status 2: Vermelho) ou apenas porque o protocolo de vídeo DASH preencheu o buffer e está descansando (Status 0: Verde).

*Nota: Requer privilégios de administrador para acoplar o Scapy ao driver de rede.*
```bash
sudo ./venv/bin/python3 agente_live.py
```

---

## 💥 Engenharia do Caos (Testes de Estresse e Ataques)

Para validar a eficácia da IA de forma prática, o ambiente foi projetado para resistir e alertar sobre anomalias extremas. Recomendamos o uso de uma máquina virtual atacante com **Kali Linux** para reproduzir os cenários abaixo contra o host que está rodando a *Sonda Live* assistindo a um vídeo no YouTube (porta 443).

### Teste A: Queda de Infraestrutura (Cabo Desconectado)
Desative a interface de rede do host alvo enquanto o vídeo toca. O player de vídeo continuará rodando graças à memória buffer, mas a IA perceberá o silêncio absoluto. Após 5 segundos de tolerância do DASH, o Grafana mudará para `❌ Rede Inativa`.

### Teste B: Ataque de Inundação (DDoS / UDP Flood)
Simula um estrangulamento brutal de banda. Para que os pacotes maliciosos sejam capturados pela Sonda Live (que filtra apenas a porta 443 de streaming), execute no Kali Linux:
```bash
sudo hping3 --udp -p 443 --flood <IP_DO_ALVO>
```
**Resultado Esperado:** A Sonda registrará milhares de pacotes por segundo. A IA perceberá a eliminação da variação humana do tráfego e alertará `🚨 Degradação` instantânea.

### Teste C: Estrangulamento Furtivo (Man-in-the-Middle)
O teste de predição definitivo. O Kali Linux se posiciona silenciosamente entre o roteador e o host alvo, repassando a internet perfeitamente, mas injetando atrasos imperceptíveis à camada de aplicação. O vídeo continuará rodando sem travar, mas a rede estará matematicamente envenenada.

1. **Ative o roteamento invisível no Kali:**
   ```bash
   sudo sysctl -w net.ipv4.ip_forward=1
   ```
2. **Sequestre a rota (ARP Spoofing):**
   ```bash
   sudo arpspoof -i <SUA_INTERFACE_KALI> -t <IP_DO_ALVO> <IP_DO_ROTEADOR>
   ```
3. **Injete o caos na rede (Atraso e Jitter):** Abra um novo terminal no Kali e injete 80ms de atraso e 30ms de variação:
   ```bash
   sudo tc qdisc add dev <SUA_INTERFACE_KALI> root netem delay 80ms 30ms
   ```
**Resultado Esperado:** A IA calculará a arritmia exata dos pacotes atrasados pelo Kali e disparará o alarme preventivo muito antes de o buffer do vídeo esvaziar.

---

## 🗄️ Bases de Dados (Datasets) de Referência
Os modelos de Machine Learning deste projeto foram treinados e validados utilizando os seguintes datasets públicos:

* **[Aggregated Gaming e Video Streaming Traffic for 5G](https://www.kaggle.com/datasets/ahassanein/aggregated-gaming-and-video-streaming-traffic-for-5g)**
  * **Autor:** Ahmed Hassanein
* **[VPN and Non-VPN Application Traffic (CIC-VPN2016)](https://www.kaggle.com/datasets/noobbcoder2/vpn-and-non-vpn-application-traffic-cic-vpn2016)**
  * **Autor:** Krish Agarwal

---

## 👥 Autores
* **Hugo Antônio Fernandes dos Santos**
* **Pedro Henrique Teixeira Cardoso de Paula**
