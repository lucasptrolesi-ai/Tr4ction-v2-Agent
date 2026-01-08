# 🔐 AWS EC2 - Guia de Configuração de Security Group

## 📋 Objetivo
Liberar a porta 8000 no AWS Security Group para permitir acesso externo ao backend TR4CTION Agent V2.

---

## 🎯 Passo a Passo Completo

### Passo 1: Acessar AWS Console
1. Fazer login em: https://console.aws.amazon.com
2. Navegar para **EC2 Dashboard**
3. No menu lateral, clicar em **"Instances"**

### Passo 2: Identificar sua Instância
1. Localizar a instância onde o backend está rodando
2. Anotar o **Instance ID** (ex: i-0123456789abcdef)
3. Anotar o **Public IPv4 address** (ex: 54.144.92.71)

### Passo 3: Acessar Security Group
1. Clicar na instância para ver detalhes
2. Na aba **"Security"**, localizar o Security Group
3. Clicar no link do Security Group (ex: sg-0123456789abcdef)

### Passo 4: Editar Regras de Entrada
1. Clicar no botão **"Edit inbound rules"**
2. Clicar em **"Add rule"**

### Passo 5: Configurar Regra para Porta 8000
Preencher os campos:

```
Type: Custom TCP
Protocol: TCP
Port Range: 8000
Source Type: Anywhere-IPv4
Source: 0.0.0.0/0
Description: TR4CTION Backend API
```

**Explicação dos campos:**
- **Type**: Custom TCP (permite tráfego TCP personalizado)
- **Port Range**: 8000 (porta onde o backend roda)
- **Source**: 0.0.0.0/0 (permite acesso de qualquer IP)
- **Description**: Descrição para identificar a regra

### Passo 6: (Opcional) Configurar para IPv6
Se quiser suportar IPv6, adicionar outra regra:

```
Type: Custom TCP
Protocol: TCP
Port Range: 8000
Source Type: Anywhere-IPv6
Source: ::/0
Description: TR4CTION Backend API (IPv6)
```

### Passo 7: Salvar Configurações
1. Revisar as regras adicionadas
2. Clicar em **"Save rules"**
3. Aguardar a confirmação

---

## ✅ Verificação

### Teste Interno (dentro da EC2)
```bash
# SSH na instância EC2
ssh -i sua-chave.pem ubuntu@SEU_IP_PUBLICO

# Testar localmente
curl http://localhost:8000/health
```

Resposta esperada:
```json
{"status":"ok"}
```

### Teste Externo (do seu computador)
```bash
# Substituir SEU_IP_PUBLICO pelo IP da EC2
curl http://SEU_IP_PUBLICO:8000/health
```

Resposta esperada:
```json
{"status":"ok"}
```

### Teste pelo Browser
Abrir no navegador:
- `http://SEU_IP_PUBLICO:8000/`
- `http://SEU_IP_PUBLICO:8000/docs`
- `http://SEU_IP_PUBLICO:8000/health`

---

## 🔐 Segurança Adicional

### Opção 1: Restringir por IP Específico
Se quiser permitir acesso apenas do seu IP ou do frontend:

```
Source Type: My IP
Source: (será preenchido automaticamente)
```

Ou para um IP específico:
```
Source Type: Custom
Source: 203.0.113.0/32 (IP específico)
```

### Opção 2: Restringir por Range de IPs
Para permitir uma faixa de IPs:

```
Source Type: Custom
Source: 203.0.113.0/24 (faixa de IPs)
```

### Opção 3: Permitir Apenas Frontend (Vercel)
Vercel usa IPs dinâmicos, então você precisaria:

1. **Opção A**: Usar domínio customizado com CloudFlare
2. **Opção B**: Manter 0.0.0.0/0 e usar autenticação JWT
3. **Opção C**: Consultar ranges de IP do Vercel

---

## 🛡️ Regras de Security Group Recomendadas

### Configuração Completa para Produção

#### Inbound Rules (Entrada)

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | My IP | SSH Access |
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP (redirect to HTTPS) |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS Web Traffic |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | TR4CTION Backend API |

#### Outbound Rules (Saída)
Manter configuração padrão (All traffic para 0.0.0.0/0) para permitir:
- Chamadas à API do Groq
- Chamadas à API do HuggingFace
- Atualizações do sistema
- Downloads de dependências

---

## 🔍 Troubleshooting

### Problema 1: Não consigo acessar de fora da EC2
**Causas possíveis:**
1. Security Group não configurado corretamente
2. Backend não está rodando
3. Firewall local (UFW) bloqueando porta

**Solução:**
```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Verificar firewall local
sudo ufw status

# Se UFW estiver ativo, permitir porta 8000
sudo ufw allow 8000/tcp
```

### Problema 2: Consigo acessar de dentro, mas não de fora
**Causa:** Security Group não configurado

**Solução:**
1. Verificar regras de entrada no Security Group
2. Garantir que porta 8000 está liberada para 0.0.0.0/0
3. Aguardar 1-2 minutos para propagação

### Problema 3: Acesso intermitente
**Causa:** IP público da EC2 mudou (instância parada e reiniciada)

**Solução:**
- Usar Elastic IP (IP fixo) na AWS:
  1. EC2 > Elastic IPs > Allocate Elastic IP
  2. Associate Elastic IP com sua instância
  3. Atualizar DNS e configurações com novo IP fixo

### Problema 4: "Connection refused"
**Causas possíveis:**
1. Backend não está rodando
2. Backend rodando em 127.0.0.1 em vez de 0.0.0.0

**Solução:**
```bash
# Verificar se está rodando
ps aux | grep uvicorn

# Iniciar com host correto
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Problema 5: "Connection timeout"
**Causa:** Firewall ou Security Group bloqueando

**Solução:**
```bash
# Testar conectividade de dentro da EC2
curl http://localhost:8000/health

# Se funcionar internamente, problema é Security Group
# Revisar regras de entrada no AWS Console
```

---

## 📊 Checklist de Segurança

### Obrigatório
- [ ] Porta 22 (SSH) restrita ao seu IP
- [ ] Porta 8000 liberada para 0.0.0.0/0 ou IPs específicos
- [ ] JWT_SECRET_KEY alterado do padrão
- [ ] .env com credenciais reais (não example)

### Recomendado
- [ ] Elastic IP configurado (IP fixo)
- [ ] UFW (firewall local) configurado
- [ ] SSL/TLS configurado (HTTPS)
- [ ] CloudFlare como proxy reverso
- [ ] Backups automáticos configurados
- [ ] Monitoramento de logs ativo

### Avançado
- [ ] VPC com subnets privadas
- [ ] Load Balancer (ALB)
- [ ] Auto Scaling configurado
- [ ] CloudWatch Alarms
- [ ] S3 para backup de dados
- [ ] RDS em vez de SQLite

---

## 🔗 Recursos Úteis

### AWS Documentation
- [EC2 Security Groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
- [Elastic IP Addresses](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html)
- [EC2 Best Practices](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-best-practices.html)

### Ferramentas de Teste
```bash
# Verificar portas abertas
nmap -p 8000 SEU_IP_PUBLICO

# Testar conectividade HTTP
curl -v http://SEU_IP_PUBLICO:8000/health

# Verificar DNS
dig SEU_DOMINIO.com

# Verificar SSL/TLS (se configurado)
openssl s_client -connect SEU_IP_PUBLICO:443
```

---

## ✨ Resumo

**O que você precisa fazer:**
1. ✅ Acessar AWS Console → EC2 → Security Groups
2. ✅ Editar Inbound Rules
3. ✅ Adicionar regra: TCP porta 8000, source 0.0.0.0/0
4. ✅ Salvar e testar: `curl http://SEU_IP:8000/health`

**Tempo estimado:** 2-3 minutos

**Após configurar:**
- Backend acessível externamente
- Frontend pode se conectar ao backend
- API Docs disponível em /docs
- Pronto para produção! 🚀
