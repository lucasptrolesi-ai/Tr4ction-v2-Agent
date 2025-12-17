# 🚀 Deploy Automático para Vercel - Instruções Finais

## ⚡ Forma Rápida (Recomendada)

### Passo 1: Fazer Push
Execute em um terminal PowerShell:

```powershell
cd C:\Users\Micro\Desktop\Tr4ction_Agent_V2
git add .
git commit -m "Deploy v1 - Sistema pronto para produção"
git push origin main
```

### Passo 2: Conectar Vercel
1. Acesse: https://vercel.com/dashboard
2. Clique em "Add New Project"
3. Selecione "lucasptrolesi-ai/Tr4ction-v2-Agent"
4. Deixar configurações padrão (auto-detecta Next.js)
5. Clicar "Deploy"

### Passo 3: Configurar Variáveis
No Vercel Dashboard → Project Settings → Environment Variables:

```
Nome: NEXT_PUBLIC_API_BASE_URL
Valor: https://54.144.92.71.sslip.io
Ambientes: Production, Preview, Development
```

### Passo 4: Deploy Completo
- Push para main = deploy automático
- Ou clique "Redeploy" no Vercel para forçar

---

## 📊 Status Atual

### ✅ Frontend Pronto
- [x] Next.js configurado
- [x] API client com retry
- [x] CORS headers
- [x] vercel.json criado
- [x] .env.production configurado
- [x] Git pronto

### ✅ Backend Rodando
- [x] FastAPI em 54.144.92.71.sslip.io
- [x] CORS configurado com Vercel URL
- [x] Autenticação funcional
- [x] Banco de dados OK

### ⏳ Faltando
1. Push para GitHub
2. Conectar Vercel
3. Configurar variáveis
4. Deploy finalizado

---

## 🔗 URLs Importantes

| Serviço | URL |
|---------|-----|
| GitHub | https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent |
| Vercel Dashboard | https://vercel.com/dashboard |
| Backend | https://54.144.92.71.sslip.io |
| Frontend Local | http://localhost:3000 |
| Frontend Produção | https://tr4ction-v2-agent.vercel.app |

---

## 🧪 Testes Recomendados

Após deploy, testar:

1. **Login**: admin@tr4ction.com / admin
2. **Chat**: Enviar mensagem e receber resposta
3. **Dashboard**: Carregar informações
4. **Upload**: Enviar documento
5. **Console**: F12 → verificar erros CORS

---

## 🆘 Troubleshooting

### CORS Error
```
Access to XMLHttpRequest from origin 'https://seu-app.vercel.app' 
has been blocked by CORS policy
```
**Solução**: Verificar se backend tem Vercel URL nas CORS_ORIGINS

### Build Falha
- Executar `npm run build` localmente
- Verificar logs no Vercel
- Atualizar Node version se necessário

### API não conecta
- Verificar `NEXT_PUBLIC_API_BASE_URL`
- Confirmar backend está rodando
- Testar URL diretamente no navegador

---

## 📝 Próximas Ações

1. ✅ Executar push para GitHub
2. ✅ Conectar repositório no Vercel
3. ✅ Configurar variáveis de ambiente
4. ✅ Monitorar build
5. ✅ Testar em produção
6. ✅ Documentar issues
7. ✅ Configurar monitoramento

---

## 💡 Dica Final

Após o primeiro deploy bem-sucedido:
- Todo push para `main` = deploy automático
- Vercel cria preview URLs para PRs
- Rolls back automático se build falhar

**Pronto para começar? Execute o passo 1 acima!** 🚀
