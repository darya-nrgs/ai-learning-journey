from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import os
from dotenv import load_dotenv
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import tempfile
import shutil
from openai import OpenAI
import re

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="AI Services API",
    description="Backend API for AI-powered code generation and RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# API Key validation
API_KEYS = {
    "demo-key-123": "demo_user",
    os.getenv("API_KEY", "your-secret-key"): "admin"
}

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return API_KEYS[x_api_key]


# ============================================================
# Helper Functions
# ============================================================

def extract_python_code(text: str) -> str:
    """استخراج کد Python از markdown"""
    pattern = r'```python\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[0]
    return text


def generate_code_with_ai(prompt: str, language: str = "python") -> str:
    """تولید کد با AI"""
    api_key = os.getenv("NINE_ROUTER_API_KEY")
    client = OpenAI(api_key=api_key, base_url="http://localhost:20128/v1")
    
    system_prompt = f"""You are an expert {language} programmer.
Generate clean, well-documented, production-ready code.
Include docstrings and comments.
Only return the code, no explanations."""
    
    response = client.chat.completions.create(
        model="kr/claude-sonnet-4.5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    
    code = response.choices[0].message.content
    
    # استخراج کد از markdown
    if "```" in code:
        code = extract_python_code(code)
    
    return code


# ============================================================
# Import RAG System (if available)
# ============================================================

try:
    from day3_rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("⚠️  Warning: RAG System not available (day3_rag_system.py not found)")


# ============================================================
# Pydantic Models
# ============================================================

class CodeGenerationRequest(BaseModel):
    prompt: str = Field(..., description="توضیحات کدی که میخوای تولید بشه")
    language: str = Field(default="python", description="زبان برنامه‌نویسی")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "یک تابع برای محاسبه فیبوناچی بنویس",
                "language": "python"
            }
        }


class CodeGenerationResponse(BaseModel):
    code: str
    language: str
    status: str


class RAGAskRequest(BaseModel):
    question: str = Field(..., description="سوال از PDF")
    session_id: Optional[str] = Field(default="default", description="شناسه session")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "این سند درباره چیست؟",
                "session_id": "user123"
            }
        }


class RAGAskResponse(BaseModel):
    answer: str
    sources: List[dict]
    session_id: str


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict


# ============================================================
# Global storage
# ============================================================

rag_sessions = {}


# ============================================================
# Endpoints
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Services API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "code_generation": "active",
            "rag_system": "active" if RAG_AVAILABLE else "unavailable"
        }
    }


@app.post("/api/v1/generate-code", response_model=CodeGenerationResponse, tags=["Code Generation"])
@limiter.limit("10/minute")
async def api_generate_code(
    request: Request,
    req: CodeGenerationRequest,
    user: str = Depends(verify_api_key)
):
    """
    تولید کد با AI Agent
    
    - **prompt**: توضیحات کدی که میخوای
    - **language**: زبان برنامه‌نویسی (پیش‌فرض: python)
    """
    try:
        code = generate_code_with_ai(req.prompt, req.language)
        
        return CodeGenerationResponse(
            code=code,
            language=req.language,
            status="success"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")


@app.post("/api/v1/rag/upload", tags=["RAG System"])
@limiter.limit("5/minute")
async def api_rag_upload(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = "default",
    user: str = Depends(verify_api_key)
):
    """
    آپلود PDF برای سیستم RAG
    """
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG System not available")
    
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # ذخیره موقت
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # ساخت RAG System
        api_key = os.getenv("NINE_ROUTER_API_KEY")
        rag = RAGSystem(api_key=api_key)
        
        # پردازش PDF
        rag.process_pdf(tmp_path)
        
        # ذخیره در session
        rag_sessions[session_id] = rag
        
        # پاک کردن فایل موقت
        os.unlink(tmp_path)
        
        return {
            "status": "success",
            "message": "PDF processed successfully",
            "filename": file.filename,
            "session_id": session_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF upload failed: {str(e)}")


@app.post("/api/v1/rag/ask", response_model=RAGAskResponse, tags=["RAG System"])
@limiter.limit("20/minute")
async def api_rag_ask(
    request: Request,
    req: RAGAskRequest,
    user: str = Depends(verify_api_key)
):
    """
    پرسیدن سوال از PDF
    """
    if not RAG_AVAILABLE:
        raise HTTPException(status_code=503, detail="RAG System not available")
    
    try:
        if req.session_id not in rag_sessions:
            raise HTTPException(
                status_code=404,
                detail="Session not found. Please upload a PDF first."
            )
        
        rag = rag_sessions[req.session_id]
        answer, sources = rag.ask(req.question)
        
        formatted_sources = [
            {
                "page": doc.metadata.get('page', 'N/A'),
                "content": doc.page_content[:200]
            }
            for doc in sources
        ]
        
        return RAGAskResponse(
            answer=answer,
            sources=formatted_sources,
            session_id=req.session_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question failed: {str(e)}")


# ============================================================
# Run server
# ============================================================

if __name__ == "__main__":
    print("🚀 Starting AI Services API...")
    print(f"📚 RAG System: {'Available' if RAG_AVAILABLE else 'Not Available'}")
    print(f"🔑 Demo API Key: demo-key-123")
    print(f"📖 Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "day4_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
