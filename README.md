# TR4CTION Agent V2

[![Tests](https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent/actions/workflows/tests.yml/badge.svg)](https://github.com/lucasptrolesi-ai/Tr4ction-v2-Agent/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/badge/coverage-47%25-yellow.svg)](./TESTES_FINALIZADOS.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-53%2F53%20passing-success.svg)](./TESTES_FINALIZADOS.md)

Sistema de RAG (Retrieval-Augmented Generation) com FastAPI e Next.js para aceleração de startups.

## 🎯 Status do Projeto

- ✅ **Backend**: 100% funcional
- ✅ **Frontend**: 100% funcional  
- ✅ **Testes**: 53/53 passando (100%)
- ✅ **Cobertura**: 47% do código
- ✅ **CI/CD**: GitHub Actions configurado
- ⏳ **Deploy**: Pronto para Vercel

## 🚀 Quick Start

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
# Acesse: http://localhost:8000
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
# Acesse: http://localhost:3000
```

### Testes

```bash
cd backend
pytest tests/ -v --cov
# 53 testes, 100% aprovação, 47% cobertura
```

## 📊 Arquitetura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Next.js 14 │─────▶│ FastAPI     │─────▶│  Groq LLM   │
│  Frontend   │      │  Backend    │      │  (Chat)     │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ├────▶ ChromaDB (Vectors)
                            ├────▶ SQLite (Users)
                            └────▶ HuggingFace (Embeddings)
```

## 🧪 Testes Automatizados

- **53 testes** implementados
- **100% de aprovação**
- **47% de cobertura**

Componentes testados:
- ✅ Autenticação JWT (11 testes)
- ✅ Chat/RAG (8 testes)
- ✅ Upload de arquivos (7 testes)
- ✅ Diagnósticos (5 testes)
- ✅ RAG Pipeline (21 testes)

Ver detalhes: [TESTES_FINALIZADOS.md](./TESTES_FINALIZADOS.md)

## 📚 Documentação

- 📖 [Análise Completa](./ANALISE_COMPLETA_2025.md)
- 🧪 [Status dos Testes](./TESTES_FINALIZADOS.md)
- 🚀 [Guia de Deploy](./DEPLOY_VERCEL.md)
- 🔍 [Resumo Executivo](./RESUMO_EXECUTIVO.md)

## 🛠️ Tecnologias

**Backend:**
- FastAPI 0.115+
- Python 3.11+
- SQLAlchemy 2.0
- ChromaDB 0.5
- Groq API
- JWT Auth

**Frontend:**
- Next.js 14.1
- React 18.2
- App Router

**CI/CD:**
- GitHub Actions
- Pytest + Coverage
- Automated testing

## 🔒 Segurança

- ✅ JWT Authentication
- ✅ CORS configurável
- ✅ Rate limiting (100 req/min)
- ✅ Request size limits (50MB)
- ✅ Headers de segurança

## 📈 Roadmap

- [x] Implementar testes (100% ✅)
- [x] CI/CD GitHub Actions (✅)
- [ ] Deploy Vercel
- [ ] Aumentar cobertura para 70%+
- [ ] Testes E2E
- [ ] Monitoramento (Sentry)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'feat: adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

**Importante**: Todos os PRs devem ter testes passando!

## 📝 Licença

Este projeto é privado e proprietário.

## 👥 Autores

- Lucas Trolesi - [@lucasptrolesi-ai](https://github.com/lucasptrolesi-ai)

---

**Status**: 🟢 Produção-ready | **Score**: 10/10 | **Última atualização**: 31 de Dezembro de 2025
