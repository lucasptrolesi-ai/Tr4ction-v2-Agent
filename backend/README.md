# TR4CTION Agent Backend (Local)

Backend em FastAPI para:

- Painel admin de conhecimento (CRUD simples local)
- Upload e listagem de arquivos (PDF, PPTX etc.)
- Chat do founder em modo MOCK (sem OpenAI)

## Como rodar

Dentro da pasta `backend/`:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
