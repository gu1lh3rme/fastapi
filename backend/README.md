# RAG Chatbot — Área do Aluno 🎓

Backend **FastAPI** com **RAG (Retrieval Augmented Generation)** para um chatbot educacional inteligente.
Integrado ao frontend Angular, permite que alunos conversem com um assistente IA que responde perguntas
baseadas nos documentos que eles mesmos fizeram upload.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Tecnologias](#-tecnologias)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Como o RAG Funciona](#-como-o-rag-funciona)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Rodando o Projeto](#-rodando-o-projeto)
- [Endpoints da API](#-endpoints-da-api)
- [Próximos Passos — Frontend Angular](#-próximos-passos--frontend-angular)

---

## 🌟 Visão Geral

Este projeto implementa um chatbot educacional que:

1. **Autentica** alunos com JWT
2. **Aceita upload** de documentos (PDF, TXT, DOCX) — materiais do curso, resumos, etc.
3. **Processa os documentos** automaticamente: extrai texto → divide em chunks → gera embeddings → armazena no ChromaDB
4. **Responde perguntas** usando RAG: busca os trechos mais relevantes dos documentos e enriquece o prompt do GPT-4o-mini

---

## 🛠 Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.11+ | Linguagem |
| FastAPI | 0.111 | Framework web async |
| SQLAlchemy | 2.x | ORM async |
| Alembic | 1.13 | Migrations |
| PostgreSQL | 15+ | Banco de dados |
| OpenAI | 1.30 | LLM + Embeddings |
| LangChain | 0.2 | Framework RAG |
| ChromaDB | 0.5 | Vector store |
| Pydantic | v2 | Validação de dados |
| JWT (jose) | 3.3 | Autenticação |

---

## 📁 Estrutura do Projeto

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py       # Configurações via .env (pydantic-settings)
│   │   ├── database.py     # SQLAlchemy 2.x async engine + sessão
│   │   └── security.py     # JWT + bcrypt
│   │
│   ├── models/
│   │   ├── user.py         # Model SQLAlchemy: usuário
│   │   ├── document.py     # Model SQLAlchemy: documento uploaded
│   │   └── chat_message.py # Model SQLAlchemy: histórico de chat
│   │
│   ├── schemas/
│   │   ├── auth.py         # Schemas Pydantic v2: registro/login
│   │   ├── document.py     # Schemas: upload/listagem documentos
│   │   └── chat.py         # Schemas: request/response do chat
│   │
│   ├── routers/
│   │   ├── auth.py         # Endpoints: /api/v1/auth/*
│   │   ├── documents.py    # Endpoints: /api/v1/documents/*
│   │   └── chat.py         # Endpoints: /api/v1/chat/*
│   │
│   ├── services/
│   │   ├── auth_service.py      # Lógica: registro e login
│   │   ├── document_service.py  # Lógica: upload + background processing
│   │   ├── rag_service.py       # RAG: chunking + embeddings + ChromaDB
│   │   └── openai_service.py    # LLM: prompt + chamada OpenAI
│   │
│   ├── repositories/
│   │   ├── user_repository.py      # CRUD users
│   │   ├── document_repository.py  # CRUD documents
│   │   └── chat_repository.py      # CRUD chat_messages
│   │
│   ├── utils/
│   │   ├── dependencies.py  # DI: get_current_user
│   │   └── helpers.py       # Funções auxiliares
│   │
│   └── main.py             # App FastAPI + CORS + routers
│
├── alembic/
│   ├── env.py              # Configuração async do Alembic
│   ├── script.py.mako      # Template de migration
│   └── versions/
│       └── 001_initial.py  # Migration inicial (3 tabelas)
│
├── alembic.ini             # Configuração do Alembic
├── .env.example            # Exemplo de variáveis de ambiente
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🧠 Como o RAG Funciona

**RAG (Retrieval Augmented Generation)** é uma técnica que melhora as respostas do LLM adicionando contexto relevante ao prompt. Assim:

```
┌─────────────────────────────────────────────────────────────────┐
│                         FLUXO DO RAG                            │
│                                                                  │
│  INDEXAÇÃO (ao fazer upload de documento)                        │
│  ──────────────────────────────────────                          │
│  PDF/TXT → Extração de Texto → Chunks (1000 chars)               │
│         → Embeddings (OpenAI text-embedding-3-small)             │
│         → ChromaDB (banco vetorial)                              │
│                                                                  │
│  CONSULTA (ao fazer uma pergunta)                                │
│  ─────────────────────────────────                               │
│  Pergunta → Embedding → Similarity Search no ChromaDB            │
│          → Top K chunks relevantes                               │
│          → Injeta no prompt do GPT-4o-mini                       │
│          → Resposta contextualizada ✓                            │
└─────────────────────────────────────────────────────────────────┘
```

### Por que RAG?

Sem RAG, o LLM não conhece seus documentos específicos (apostilas, resumos, PDFs do curso).
Com RAG, o LLM recebe os trechos mais relevantes como contexto e pode responder com precisão
sobre o conteúdo que você carregou.

### Embeddings

Embeddings são representações numéricas de texto em alta dimensão (1536 dimensões no caso do
`text-embedding-3-small`). Textos semanticamente similares têm embeddings próximos no espaço
vetorial, o que permite buscar por similaridade semântica (não apenas palavras-chave).

---

## ✅ Pré-requisitos

- Python **3.11+**
- PostgreSQL **15+** rodando localmente
- Conta na **OpenAI** com créditos (https://platform.openai.com)
- `pip` ou `uv` para gerenciar dependências

---

## ⚙️ Instalação e Configuração

### 1. Clone o repositório e entre na pasta

```bash
git clone https://github.com/gu1lh3rme/fastapi.git
cd fastapi/backend
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv

# Linux/Mac:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com seus dados:

```env
# Banco de dados PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:admin@localhost:5432/rag_chatbot

# Chave da API OpenAI — obtenha em https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...

# Chave secreta JWT — gere com: openssl rand -hex 32
JWT_SECRET=sua-chave-secreta-aqui-muito-longa-e-aleatoria

# Modelo OpenAI (gpt-4o-mini é mais barato, gpt-4o é mais poderoso)
OPENAI_CHAT_MODEL=gpt-4o-mini
```

### 5. Crie o banco de dados

Certifique-se que o PostgreSQL está rodando e crie o banco:

```bash
# Via psql
psql -U postgres -c "CREATE DATABASE rag_chatbot;"
```

### 6. Execute as migrations do Alembic

```bash
# Dentro da pasta backend/
alembic upgrade head
```

Isso cria as tabelas `users`, `documents` e `chat_messages`.

---

## 🚀 Rodando o Projeto

```bash
# Dentro da pasta backend/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em:
- **API**: http://localhost:8000
- **Swagger UI (docs interativos)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

---

## 📡 Endpoints da API

Todos os endpoints da API usam o prefixo `/api/v1`.

### Autenticação (`/api/v1/auth`)

| Método | Endpoint | Descrição | Auth |
|---|---|---|---|
| `POST` | `/auth/register` | Cadastro de novo usuário | ❌ |
| `POST` | `/auth/login` | Login → retorna JWT | ❌ |
| `GET` | `/auth/me` | Dados do usuário logado | ✅ |

**Exemplo de cadastro:**
```json
POST /api/v1/auth/register
{
  "email": "aluno@exemplo.com",
  "full_name": "João Silva",
  "password": "senha123"
}
```

**Exemplo de login:**
```json
POST /api/v1/auth/login
{
  "email": "aluno@exemplo.com",
  "password": "senha123"
}
// Retorna: { "access_token": "eyJ...", "token_type": "bearer", ... }
```

### Documentos (`/api/v1/documents`) — Requer JWT

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/documents/upload` | Upload de PDF/TXT/DOCX para o RAG |
| `GET` | `/documents` | Lista documentos do usuário |

**Exemplo de upload (multipart/form-data):**
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <seu-token>" \
  -F "file=@apostila.pdf"
```

### Chat (`/api/v1/chat`) — Requer JWT

| Método | Endpoint | Descrição |
|---|---|---|
| `POST` | `/chat` | Envia mensagem ao chatbot (RAG + LLM) |
| `GET` | `/chat/history/{session_id}` | Histórico de uma sessão |
| `GET` | `/chat/sessions` | Lista sessões do usuário |

**Exemplo de chat:**
```json
POST /api/v1/chat
{
  "message": "O que é aprendizado supervisionado?",
  "session_id": "uuid-opcional",
  "history": [],
  "use_rag": true
}

// Resposta:
{
  "message_id": "...",
  "response": "Aprendizado supervisionado é...",
  "session_id": "...",
  "sources": [
    {
      "filename": "apostila_ml.pdf",
      "content_preview": "Aprendizado supervisionado refere-se..."
    }
  ],
  "model_used": "gpt-4o-mini",
  "tokens_used": 342,
  "response_time_ms": 1250.5
}
```

---

## 🔄 Próximos Passos — Frontend Angular

Para integrar com um frontend Angular, siga estas sugestões:

### 1. Serviço de Autenticação

```typescript
// auth.service.ts
@Injectable({ providedIn: 'root' })
export class AuthService {
  private apiUrl = 'http://localhost:8000/api/v1';

  login(email: string, password: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.apiUrl}/auth/login`, { email, password })
      .pipe(tap(res => localStorage.setItem('token', res.access_token)));
  }
}
```

### 2. Interceptor JWT

```typescript
// jwt.interceptor.ts — adiciona o token em todas as requisições
export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem('token');
  if (token) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};
```

### 3. Upload de Documentos

```typescript
uploadDocument(file: File): Observable<any> {
  const formData = new FormData();
  formData.append('file', file);
  return this.http.post(`${this.apiUrl}/documents/upload`, formData);
}
```

### 4. Chat com Streaming (Futuro)

Para uma experiência mais fluida, implemente streaming de resposta com
`Server-Sent Events (SSE)` ou `WebSockets`. O FastAPI suporta ambos.

### 5. Variáveis de Ambiente Angular

```typescript
// environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1'
};
```

---

## 🔐 Segurança

- Senhas são hasheadas com **bcrypt** (nunca armazenadas em texto puro)
- Tokens JWT expiram após 30 minutos (configurável)
- Uploads são validados por extensão e MIME type
- Cada usuário acessa apenas seus próprios documentos (isolamento por `user_id`)
- Mensagens de erro de login são genéricas (evita enumeração de emails)

---

## 📊 Migrations com Alembic

```bash
# Criar nova migration após alterar um model:
alembic revision --autogenerate -m "add coluna xyz na tabela users"

# Aplicar todas as migrations pendentes:
alembic upgrade head

# Ver histórico de migrations:
alembic history

# Reverter última migration:
alembic downgrade -1
```

---

## 🐛 Solução de Problemas

### Erro de conexão com PostgreSQL
```
sqlalchemy.exc.OperationalError: could not connect to server
```
Verifique se o PostgreSQL está rodando e se a `DATABASE_URL` no `.env` está correta.

### Erro na API OpenAI
```
openai.AuthenticationError: Invalid API key
```
Verifique se a `OPENAI_API_KEY` no `.env` está correta e tem créditos.

### Documento com status "error"
Verifique os logs do servidor (`uvicorn`) para ver a mensagem de erro detalhada.
Causas comuns: PDF protegido por senha, arquivo corrompido, falta de memória.

---

## 📚 Conceitos de IA Implementados

| Conceito | Onde | Descrição |
|---|---|---|
| **Embeddings** | `rag_service.py` | Transformação de texto em vetores numéricos |
| **Similarity Search** | `rag_service.py` | Busca por similaridade semântica no ChromaDB |
| **Text Splitting** | `rag_service.py` | Divisão de documentos em chunks com sobreposição |
| **RAG** | `openai_service.py` | Injeção de contexto no prompt do LLM |
| **Prompt Engineering** | `openai_service.py` | System prompt + formatação do contexto |
| **Chat History** | `chat.py` (router) | Manutenção do histórico de conversa |
