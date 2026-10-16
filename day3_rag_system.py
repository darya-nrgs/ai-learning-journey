import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings  # ✅ استفاده از مدل محلی

# Load environment variables
load_dotenv()

class RAGSystem:
    """
    RAG System: سیستم پرسش و پاسخ بر اساس اسناد
    
    مراحل:
    1. Load: خواندن PDF
    2. Split: تقسیم به بخش‌های کوچک
    3. Embed: تبدیل به vector (اعداد)
    4. Store: ذخیره در ChromaDB
    5. Retrieve: پیدا کردن مرتبط‌ترین بخش‌ها
    6. Generate: تولید جواب با LLM
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:20128/v1"):
        """
        Initialize RAG System
        
        Args:
            api_key: 9router API key
            base_url: 9router base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # Initialize embeddings (مدل محلی - رایگان)
        print("📥 Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("✅ Embedding model loaded")
        
        # Initialize LLM (برای تولید جواب)
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            openai_api_base=base_url,
            model_name="kr/claude-sonnet-4.5",
            temperature=0.3
        )
        
        self.vectorstore = None
        self.retriever = None
        self.rag_chain = None
    
    def load_pdf(self, pdf_path: str):
        """
        مرحله 1: خواندن PDF
        """
        print(f"📄 Loading PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"✅ Loaded {len(documents)} pages")
        return documents
    
    def split_documents(self, documents, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        مرحله 2: تقسیم به بخش‌های کوچک
        """
        print(f"✂️  Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        print(f"✅ Created {len(chunks)} chunks")
        return chunks
    
    def create_vectorstore(self, chunks, persist_directory: str = "./chroma_db"):
        """
        مرحله 3 و 4: تبدیل به vector و ذخیره
        """
        print(f"🧮 Creating embeddings and storing in ChromaDB...")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        
        # Create retriever
        self.retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 3}
        )
        
        print(f"✅ Vector store created and saved to {persist_directory}")
        return self.vectorstore
    
    def setup_rag_chain(self):
        """
        مرحله 5 و 6: ساخت زنجیره RAG
        """
        if self.retriever is None:
            raise ValueError("Retriever not created. Call create_vectorstore first.")
        
        # Custom prompt template
        template = """از اطلاعات زیر برای پاسخ به سوال استفاده کن. اگر جواب رو نمیدونی، بگو "نمیدونم"، جواب دروغ نده.

Context:
{context}

سوال: {question}

جواب (به فارسی):"""
        
        prompt = PromptTemplate.from_template(template)
        
        # Helper function
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Create RAG chain
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("✅ RAG chain ready!")
    
    def ask(self, question: str):
        """
        پرسیدن سوال از سیستم
        """
        if self.rag_chain is None:
            raise ValueError("RAG chain not setup. Call setup_rag_chain first.")
        
        print(f"\n❓ Question: {question}")
        
        # Get answer
        answer = self.rag_chain.invoke(question)
        
        # Get source documents
        source_docs = self.retriever.invoke(question)
        
        print(f"💡 Answer: {answer}\n")
        print(f"📚 Sources ({len(source_docs)} chunks used):")
        for i, doc in enumerate(source_docs, 1):
            print(f"   {i}. Page {doc.metadata.get('page', 'N/A')}: {doc.page_content[:100]}...")
        
        return answer, source_docs
    
    def process_pdf(self, pdf_path: str):
        """
        فرایند کامل: از PDF تا آماده شدن سیستم
        """
        print("=" * 60)
        print("🚀 Starting RAG System Pipeline")
        print("=" * 60)
        
        documents = self.load_pdf(pdf_path)
        chunks = self.split_documents(documents)
        self.create_vectorstore(chunks)
        self.setup_rag_chain()
        
        print("=" * 60)
        print("✅ RAG System Ready!")
        print("=" * 60)


def main():
    """
    تست سیستم RAG
    """
    api_key = os.getenv("NINE_ROUTER_API_KEY")
    if not api_key:
        raise ValueError("NINE_ROUTER_API_KEY not found in .env file")
    
    rag = RAGSystem(api_key=api_key)
    
    pdf_path = "blue_point.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"⚠️  PDF not found: {pdf_path}")
        return
    
    rag.process_pdf(pdf_path)
    
    questions = [
        "این سند درباره چیست؟",
        "نکات کلیدی کدامند؟"
    ]
    
    for question in questions:
        rag.ask(question)
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
