"""
Serviço de processamento de documentos para o RAG.

Fluxo:
1. Lê o arquivo (PDF, TXT, DOCX)
2. Divide em chunks menores (text splitting)
3. Gera embeddings via OpenAI
4. Armazena no ChromaDB (vector store)

Isso permite depois buscar os chunks mais relevantes para uma pergunta.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configurações do text splitting
# chunk_size: máximo de caracteres por chunk
# chunk_overlap: sobreposição entre chunks (evita perder contexto nas bordas)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def get_embeddings() -> OpenAIEmbeddings:
    """
    Retorna o modelo de embeddings da OpenAI.
    text-embedding-3-small é uma opção econômica e eficiente.
    """
    return OpenAIEmbeddings(
        openai_api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )


def get_vector_store(user_id: str) -> Chroma:
    """
    Retorna (ou cria) o vector store ChromaDB para um usuário específico.

    Cada usuário tem sua própria coleção no ChromaDB,
    garantindo isolamento dos documentos.

    Args:
        user_id: ID do usuário dono dos documentos

    Returns:
        Instância do Chroma pronta para uso
    """
    # Cria diretório de persistência se não existir
    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=f"user_{user_id}",  # coleção isolada por usuário
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )


def load_document(file_path: str, content_type: str) -> list:
    """
    Carrega um documento do sistema de arquivos usando o loader adequado.

    Args:
        file_path: Caminho absoluto do arquivo
        content_type: MIME type do arquivo

    Returns:
        Lista de Documents do LangChain
    """
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf" or content_type == "application/pdf":
        # PyPDFLoader extrai texto de cada página do PDF
        loader = PyPDFLoader(file_path)
    elif ext in (".docx", ".doc") or "word" in content_type:
        # Para arquivos Word
        loader = UnstructuredWordDocumentLoader(file_path)
    else:
        # Para TXT, MD e outros arquivos de texto
        loader = TextLoader(file_path, encoding="utf-8")

    return loader.load()


async def process_document(
    file_path: str,
    content_type: str,
    user_id: str,
    document_id: str,
) -> int:
    """
    Processa um documento e armazena seus embeddings no ChromaDB.

    Etapas:
    1. Carrega o documento com o loader adequado
    2. Divide em chunks usando RecursiveCharacterTextSplitter
    3. Adiciona metadados em cada chunk (user_id, document_id, filename)
    4. Gera embeddings e armazena no ChromaDB

    Args:
        file_path: Caminho do arquivo no sistema de arquivos
        content_type: MIME type do arquivo
        user_id: ID do usuário dono do documento
        document_id: ID do documento no banco de dados

    Returns:
        Número de chunks criados

    Raises:
        Exception: Em caso de erro no processamento
    """
    logger.info(f"Iniciando processamento do documento {document_id} para usuário {user_id}")

    # Passo 1: Carrega o documento
    documents = load_document(file_path, content_type)
    logger.info(f"Documento carregado: {len(documents)} páginas/partes")

    # Passo 2: Divide em chunks menores
    # RecursiveCharacterTextSplitter tenta dividir em parágrafos,
    # depois frases, depois palavras — mantendo o contexto
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    logger.info(f"Documento dividido em {len(chunks)} chunks")

    # Passo 3: Adiciona metadados para filtrar depois
    filename = Path(file_path).name
    for chunk in chunks:
        chunk.metadata.update({
            "user_id": user_id,
            "document_id": document_id,
            "source": filename,
        })

    # Passo 4: Gera embeddings e armazena no ChromaDB
    vector_store = get_vector_store(user_id)
    vector_store.add_documents(chunks)

    logger.info(f"Documento {document_id} processado com sucesso: {len(chunks)} chunks armazenados")
    return len(chunks)


async def search_relevant_context(
    query: str,
    user_id: str,
    k: int = 4,
) -> list[dict]:
    """
    Busca os chunks mais relevantes para uma pergunta no ChromaDB.

    Usa similarity search com embeddings para encontrar os trechos
    dos documentos do usuário mais relacionados à pergunta.

    Args:
        query: Pergunta do usuário
        user_id: ID do usuário (busca apenas nos documentos dele)
        k: Número máximo de chunks a retornar

    Returns:
        Lista de dicts com content e metadata de cada chunk relevante
    """
    try:
        vector_store = get_vector_store(user_id)

        # Busca os k chunks mais similares à query
        results = vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter={"user_id": user_id},  # filtra apenas docs do usuário
        )

        # Formata os resultados
        context_docs = []
        for doc, score in results:
            # LangChain normaliza os scores do ChromaDB para relevância (0=irrelevante, 1=idêntico).
            # Filtramos chunks com score baixo para remover resultados pouco relacionados.
            if score > 0.3:
                context_docs.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score,
                })

        logger.info(f"Encontrados {len(context_docs)} chunks relevantes para a query")
        return context_docs

    except Exception as e:
        logger.error(f"Erro ao buscar contexto no ChromaDB: {e}")
        return []


async def delete_user_documents(user_id: str) -> None:
    """Remove todos os documentos de um usuário do ChromaDB."""
    try:
        vector_store = get_vector_store(user_id)
        vector_store.delete_collection()
        logger.info(f"Coleção do usuário {user_id} removida do ChromaDB")
    except Exception as e:
        logger.error(f"Erro ao remover coleção do ChromaDB: {e}")
