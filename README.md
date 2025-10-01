# LibraAI: A Lightweight Conversational AI System for Book Consultation in E-Commerce

Author: Phan Thanh Duy, Nguyen Truong Son and Dinh Bao Minh

LibraAI is an AI-powered chatbot that automatically crawls book information from **Tiki** on a scheduled basis and builds an intelligent knowledge base.  
Users can then query LibraAI in natural language to explore book details and receive suggestions to make better purchasing decisions.

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/stavidphan/LibraAI.git
cd LibraAI/
```

### 2. Backend Setup (LightRAG + Ollama)
- Create a Python environment (Python 3.11 recommended) and install dependencies:
  ```bash
  conda create -n libraai python=3.11 -y
  conda activate libraai
  pip install -e .
  ```
- Install [Ollama](https://ollama.com) and pull required models:
  ```bash
  ollama pull nomic-embed-text
  ollama pull gemma2:2b
  ```
- Configure environment variables in a `.env` file (example included in repo).
- Start Ollama service:
  ```bash
  ollama serve
  ```
- Run backend API:
  ```bash
  python src/main/lightrag_ollama_api.py
  ```

### 3. Frontend Setup (Web UI)
The frontend is a lightweight static app located in `LibraAI_webui/`.  
Run it with any local server, for example:
```bash
cd LibraAI_webui
python3 -m http.server 3000
```
Then open: [http://localhost:3000](http://localhost:3000)

*(Make sure the backend API is running at `http://localhost:8000`.)*

### 4. Automated Updates
You can schedule automatic crawling and updating of book data with `cron`.  
Example (run daily at 18:51):
```bash
51 18 * * * cd /path/to/LibraAI && python ./src/main/automate_update_data.py >> ./logs/cron_log.txt 2>&1
```

---

## System Flow

The overall LibraAI workflow:

![LibraAI System Flowchart](docs/LibraAI_structure.svg)

1. **Data Crawling**  
   - A Python-based crawler connects to the Tiki API to periodically collect book metadata.  

2. **Data Preprocessing**  
   - The collected records are normalized and compared with existing data.  
   - Only new or updated books are processed further for knowledge base updates.  

3. **Knowledge Processing**  
   - Valid book data is embedded using an embedding model.  
   - Data is stored in LightRAG with entity–relation graphs for efficient retrieval.  

4. **Query & Response Generation**  
   - When a user sends a query, the system combines vector search with graph-based retrieval at two levels.  
   - A large language model generates natural language answers.
     
---

## References
[1]	Zirui Guo, Lianghao Xia, Yanhua Yu, Tu Ao, and Chao Huang, ”LightRAG: Simple and Fast Retrieval-Augmented Generation”
[2] Minh DinhBao, Viet DangAnh and Loc NguyenThe, “Xây dựng Đồ thị tri thức Thương mại điện tử Tiếng Việt dựa trên Trích xuất thông tin ngữ nghĩa với BERT”, The 26th National Conference on Electronics, Communications and Information Technology, 2023.

