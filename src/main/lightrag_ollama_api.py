import asyncio
import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.operate import chunking_by_token_size
from lightrag.prompt import PROMPTS
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
from src.data_preprocessing.insert_custom_kg import create_custom_kg_for_batch

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
INSERT_BATCH_SIZE = int(os.getenv("INSERT_BATCH_SIZE", 20))
DEFAULT_QUERY_MODE = os.getenv("DEFAULT_QUERY_MODE", "local")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemma2:9b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
TOP_K = int(os.getenv("TOP_K", 5))
LOG_FILE_MODE = os.getenv("LOG_FILE_MODE", "a")


LOG_FILE = "./logs/api_logs.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format log
    datefmt="%Y-%m-%d %H:%M:%S",
    filemode=LOG_FILE_MODE
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Accept all domains
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, DELETE,...)
    allow_headers=["*"],  # Allow all headers
)

WORKING_DIR = "./dickens_ollama"
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)

def custom_chunking_wrapper(
    content,
    split_by_character=None,
    split_by_character_only=False,
    chunk_token_size=250,
    chunk_overlap_token_size=0,
    tiktoken_model_name="gpt-4o"
):
    return chunking_by_token_size(
        content=content,
        split_by_character="\n\n",
        split_by_character_only=False,  
        overlap_token_size=50,         
        max_token_size=512,         
        tiktoken_model="gpt-4o" 
    )

# init RAG instance
rag = None

async def initialize_rag():
    global rag
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=ollama_model_complete,
        llm_model_name=LLM_MODEL_NAME,
        enable_llm_cache=False,
        llm_model_max_async=4,
        llm_model_max_token_size=8192,
        llm_model_kwargs={"host": "http://localhost:11434", "options": {"num_ctx": 32768}},
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=lambda texts: ollama_embed(
                texts, embed_model=EMBED_MODEL, host="http://localhost:11434"
            ),
        ),
        chunking_func=custom_chunking_wrapper,
        max_parallel_insert = INSERT_BATCH_SIZE
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()
    logging.info("✅ LightRAG is ready with: " + LLM_MODEL_NAME)


class InsertRequest(BaseModel):
    content: str

class InsertCustomtRequest(BaseModel):
    path: str
    batch_size: int = 100

class DeleteRequest(BaseModel):
    doc_id: str

class QueryRequest(BaseModel):
    query: str
    mode: str = DEFAULT_QUERY_MODE
    conversation_history: list[dict[str, str]] = []
    top_k: int = TOP_K
    
is_just_updated_KG = False

# API insert document to LightRAG
@app.post("/insert")
async def insert_document(request: InsertRequest):
    if rag is None:
        raise HTTPException(status_code=500, detail="LightRAG is not initialized")
    
    await rag.ainsert(request.content)
    return {"message": "✅ Document inserted!"}

@app.post("/insert_custom_kg")
async def insert_custom_kg(request: InsertCustomtRequest):
    global is_just_updated_KG

    try:
        # Create custom_kg batches
        custom_kgs, df = create_custom_kg_for_batch(request.path, batch_size=request.batch_size)
        total_batches = len(custom_kgs)
        
        # Insert each batch into LightRAG
        for idx, custom_kg in enumerate(custom_kgs):
            try:
                await rag.ainsert_custom_kg(custom_kg)
                logging.info(f"Successfully inserted batch {idx + 1}/{total_batches}")
            except Exception as e:
                logging.error(f"Failed to insert batch {idx + 1}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error inserting batch {idx + 1}: {str(e)}")

        await rag.aclear_cache()
        is_just_updated_KG = True
        
        return JSONResponse(
            status_code=200,
            content={"message": f"Successfully inserted {len(df)} books in {total_batches} batches"}
        )

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    

# API to insert batch of documents with IDs
@app.post("/insert_batch")
async def insert_documents_batch(texts: list[str], ids: list[str] | None = None):
    if rag is None:
        raise HTTPException(status_code=500, detail="LightRAG is not initialized")
    if len(texts) != len(ids):
        raise HTTPException(status_code=400, detail="Length of texts and ids must match")
    
    # Step 1: Delete existing documents with the provided IDs
    for doc_id in ids:
        try:
            await rag.adelete_by_doc_id(doc_id)
            # logging.info(f"Deleted existing document with ID: {doc_id}")
        except Exception as e:
            # Ignore if the document doesn't exist or deletion fails
            # logging.warning(f"Failed to delete document ID {doc_id}: {e}")
            continue
    
    # Step 2: Insert batch of new documents
    logging.info(f"START inserting {len(texts)} documents")
    await rag.ainsert(texts, ids=ids)
    logging.info(f"END inserting {len(texts)} documents")

    return {"message": f"✅ Inserted {len(texts)} documents after deleting existing ones!"}


# API delete document from LightRAG
@app.delete("/delete")
async def delete_document(request: DeleteRequest):
    if rag is None:
        raise HTTPException(status_code=500, detail="LightRAG is not initialized")

    await rag.adelete_by_doc_id(request.doc_id)
    return {"message": "✅ Document deleted!"}


# API query from LightRAG
@app.post("/query")
async def query_rag(request: QueryRequest):
    global is_just_updated_KG
    
    if rag is None:
        raise HTTPException(status_code=500, detail="LightRAG is not initialized")

    # cache file empty <=> just updated KG
    if is_just_updated_KG:
        request.conversation_history = []
        is_just_updated_KG = False
        
    response = await rag.aquery(
        request.query,
        param=QueryParam(
            mode=request.mode, 
            top_k=request.top_k, 
            conversation_history=request.conversation_history, 
            history_turns=3 
        ),
        system_prompt=PROMPTS["think_response"]
    )
    
    return {"query": request.query, "response": response}


if __name__ == "__main__":
    import uvicorn
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize_rag())
    uvicorn.run(app, host="0.0.0.0", port=8000)