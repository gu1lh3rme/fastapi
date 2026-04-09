# RAG Chatbot — FastAPI Backend 🎓

Backend **FastAPI** com RAG (Retrieval Augmented Generation) para chatbot educacional.

📖 **Documentação completa**: [backend/README.md](./backend/README.md)

## Início rápido

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edite com suas chaves
alembic upgrade head
uvicorn app.main:app --reload
```

Acesse a documentação interativa em: http://localhost:8000/docs