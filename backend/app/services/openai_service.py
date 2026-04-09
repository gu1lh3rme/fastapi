"""
Serviço de integração com a OpenAI.

Responsável por:
1. Montar o prompt com o contexto RAG
2. Chamar o LLM (GPT-4o-mini/GPT-4o)
3. Retornar a resposta formatada

A técnica RAG (Retrieval Augmented Generation) funciona assim:
1. Usuário faz uma pergunta
2. Buscamos os trechos relevantes nos documentos (retrieval)
3. Adicionamos esses trechos como contexto no prompt
4. O LLM gera uma resposta baseada nesse contexto (augmented generation)
"""

import logging
import time
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.rag_service import search_relevant_context

logger = logging.getLogger(__name__)

# Prompt do sistema — define o papel do assistente
SYSTEM_PROMPT = """Você é um assistente inteligente de uma plataforma de estudos online.
Seu papel é ajudar os alunos a entender os conteúdos dos cursos e responder
dúvidas sobre os materiais que eles fizeram upload.

Diretrizes:
- Seja claro, didático e encorajador
- Use o contexto fornecido para embasar suas respostas
- Se o contexto não contiver informação suficiente, diga honestamente
- Cite os trechos relevantes quando apropriado
- Responda sempre em português do Brasil
- Use formatação Markdown quando útil (listas, negrito, código)"""


def get_openai_client() -> AsyncOpenAI:
    """Retorna o cliente assíncrono da OpenAI."""
    return AsyncOpenAI(api_key=settings.openai_api_key)


def build_rag_prompt(question: str, context_docs: list[dict]) -> str:
    """
    Monta o prompt com o contexto RAG.

    Injeta os trechos dos documentos no prompt para que o LLM
    possa usar essas informações para responder.

    Args:
        question: Pergunta do usuário
        context_docs: Lista de chunks relevantes do ChromaDB

    Returns:
        Prompt completo com contexto injetado
    """
    if not context_docs:
        return question

    # Formata os trechos dos documentos como contexto
    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        source = doc["metadata"].get("source", "documento")
        context_parts.append(f"[Trecho {i} de '{source}']:\n{doc['content']}")

    context_text = "\n\n".join(context_parts)

    return f"""Com base nos seguintes trechos dos materiais de estudo do aluno:

---
{context_text}
---

Pergunta do aluno: {question}

Por favor, responda baseando-se principalmente no contexto acima."""


async def generate_chat_response(
    user_id: str,
    message: str,
    history: list[dict],
    use_rag: bool = True,
) -> dict:
    """
    Gera uma resposta do chatbot usando RAG + LLM.

    Fluxo completo:
    1. Se use_rag=True, busca contexto nos documentos do usuário
    2. Monta o prompt com o contexto
    3. Chama o GPT-4o-mini com o histórico de conversa
    4. Retorna a resposta com metadados

    Args:
        user_id: ID do usuário (para buscar documentos no RAG)
        message: Mensagem atual do usuário
        history: Histórico de mensagens anteriores
        use_rag: Se deve buscar contexto nos documentos

    Returns:
        Dict com resposta, fontes, tokens usados e tempo de resposta
    """
    start_time = time.time()
    context_docs = []

    # Passo 1: Busca contexto no RAG (se habilitado)
    if use_rag:
        logger.info(f"Buscando contexto RAG para usuário {user_id}")
        context_docs = await search_relevant_context(
            query=message,
            user_id=user_id,
            k=4,
        )
        logger.info(f"Encontrados {len(context_docs)} documentos de contexto")

    # Passo 2: Monta o prompt com contexto (se encontrou docs)
    user_prompt = build_rag_prompt(message, context_docs) if context_docs else message

    # Passo 3: Monta as mensagens para a API (histórico + nova mensagem)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Adiciona histórico de conversa (máximo de 10 pares)
    for hist_msg in history[-10:]:
        messages.append({
            "role": hist_msg["role"],
            "content": hist_msg["content"],
        })

    # Adiciona a mensagem atual com contexto RAG
    messages.append({"role": "user", "content": user_prompt})

    # Passo 4: Chama a API da OpenAI
    client = get_openai_client()

    try:
        logger.info(f"Chamando OpenAI {settings.openai_chat_model}...")
        response = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=messages,
            temperature=0.7,
            max_tokens=1500,
        )

        # Extrai a resposta
        assistant_message = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else None

        # Calcula tempo de resposta
        response_time_ms = (time.time() - start_time) * 1000

        # Formata as fontes para o response
        sources = []
        for doc in context_docs:
            sources.append({
                "filename": doc["metadata"].get("source", "documento"),
                "content_preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "relevance_score": doc.get("score"),
            })

        # Contexto usado (para salvar no banco)
        rag_context = "\n\n".join([d["content"] for d in context_docs]) if context_docs else None

        logger.info(f"Resposta gerada em {response_time_ms:.0f}ms, {tokens_used} tokens")

        return {
            "response": assistant_message,
            "sources": sources,
            "tokens_used": tokens_used,
            "model_used": settings.openai_chat_model,
            "response_time_ms": response_time_ms,
            "rag_context": rag_context,
        }

    except Exception as e:
        logger.error(f"Erro ao chamar OpenAI: {e}")
        raise
