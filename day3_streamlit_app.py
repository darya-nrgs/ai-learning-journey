import streamlit as st
import os
from dotenv import load_dotenv
from day3_rag_system import RAGSystem
import tempfile
import shutil
import hashlib

# Load environment
load_dotenv()

# Page config
st.set_page_config(
    page_title="RAG System - سیستم پرسش و پاسخ هوشمند",
    page_icon="📚",
    layout="wide"
)

# Title
st.title("📚 سیستم پرسش و پاسخ هوشمند (RAG)")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ تنظیمات")
    
    # API Key
    api_key = os.getenv("NINE_ROUTER_API_KEY")
    if not api_key:
        st.error("❌ NINE_ROUTER_API_KEY not found in .env")
        st.stop()
    else:
        st.success("✅ API Key loaded")
    
    st.markdown("---")
    st.markdown("### 📖 راهنما")
    st.markdown("""
    1. یک فایل PDF آپلود کنید
    2. منتظر بمانید تا پردازش شود
    3. سوالات خود را بپرسید!
    4. برای تغییر فایل، PDF جدید آپلود کنید
    """)
    
    # Reset button
    if st.button("🔄 شروع مجدد", help="پاک کردن همه دیتاها"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Clear all chroma_db folders
        for folder in os.listdir('.'):
            if folder.startswith('chroma_db_'):
                try:
                    shutil.rmtree(folder)
                except:
                    pass
        
        st.success("✅ دیتاها پاک شدند")
        st.rerun()

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'pdf_processed' not in st.session_state:
    st.session_state.pdf_processed = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_pdf_name' not in st.session_state:
    st.session_state.current_pdf_name = None
if 'current_db_path' not in st.session_state:
    st.session_state.current_db_path = None

# Main area
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📤 آپلود فایل")
    
    # Show current file
    if st.session_state.current_pdf_name:
        st.info(f"📄 فایل فعلی: **{st.session_state.current_pdf_name}**")
    
    uploaded_file = st.file_uploader(
        "فایل PDF خود را انتخاب کنید",
        type=['pdf'],
        help="یک فایل PDF حاوی اطلاعاتی که میخواهید از آن سوال بپرسید"
    )
    
    if uploaded_file is not None:
        # Check if it's a new file
        is_new_file = (st.session_state.current_pdf_name != uploaded_file.name)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        st.success(f"✅ فایل آپلود شد: {uploaded_file.name}")
        
        if is_new_file and st.session_state.pdf_processed:
            st.warning("⚠️ این فایل جدید است. لطفاً دکمه 'پردازش فایل' را بزنید.")
        
        # Process button
        if st.button("🚀 پردازش فایل", type="primary"):
            with st.spinner("در حال پردازش... لطفاً صبر کنید"):
                try:
                    # Create unique database path for this file
                    file_hash = hashlib.md5(uploaded_file.name.encode()).hexdigest()[:8]
                    db_path = f"./chroma_db_{file_hash}"
                    
                    # If processing a new file, clear old database
                    if is_new_file and st.session_state.current_db_path:
                        if os.path.exists(st.session_state.current_db_path):
                            shutil.rmtree(st.session_state.current_db_path)
                            st.info("🗑️ دیتابیس قبلی پاک شد")
                    
                    # Initialize RAG system
                    rag = RAGSystem(api_key=api_key)
                    
                    # Check if this file was already processed
                    if os.path.exists(db_path) and not is_new_file:
                        st.info("📂 از دیتابیس موجود استفاده می‌شود...")
                        from langchain_community.vectorstores import Chroma
                        
                        rag.vectorstore = Chroma(
                            persist_directory=db_path,
                            embedding_function=rag.embeddings
                        )
                        rag.retriever = rag.vectorstore.as_retriever(search_kwargs={"k": 3})
                        rag.setup_rag_chain()
                    else:
                        # Process PDF
                        if os.path.exists(db_path):
                            shutil.rmtree(db_path)
                        
                        # Modify process_pdf to use custom db_path
                        documents = rag.load_pdf(tmp_path)
                        chunks = rag.split_documents(documents)
                        rag.create_vectorstore(chunks, persist_directory=db_path)
                        rag.setup_rag_chain()
                    
                    # Save to session state
                    st.session_state.rag_system = rag
                    st.session_state.pdf_processed = True
                    st.session_state.current_pdf_name = uploaded_file.name
                    st.session_state.current_db_path = db_path
                    
                    # Clear chat history for new file
                    if is_new_file:
                        st.session_state.chat_history = []
                    
                    st.success("✅ فایل پردازش شد! حالا میتوانید سوال بپرسید.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ خطا در پردازش: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Clean up temp file
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except:
            pass
    
    # Info box
    if st.session_state.pdf_processed:
        st.info("🟢 سیستم آماده است")
    else:
        st.warning("🟡 لطفاً ابتدا یک PDF آپلود و پردازش کنید")

with col2:
    st.header("💬 پرسش و پاسخ")
    
    if st.session_state.pdf_processed:
        # Question input
        question = st.text_input(
            "سوال خود را بپرسید:",
            placeholder="مثال: این سند درباره چیست؟",
            key="question_input"
        )
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            ask_button = st.button("🔍 جستجو", type="primary")
        with col_btn2:
            clear_button = st.button("🗑️ پاک کردن تاریخچه")
        
        if clear_button:
            st.session_state.chat_history = []
            st.rerun()
        
        if ask_button and question:
            with st.spinner("در حال جستجو..."):
                try:
                    # Get answer
                    answer, sources = st.session_state.rag_system.ask(question)
                    
                    # Add to history
                    st.session_state.chat_history.append({
                        'question': question,
                        'answer': answer,
                        'sources': sources
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ خطا: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Display chat history
        if st.session_state.chat_history:
            st.markdown("---")
            st.subheader("📝 تاریخچه گفتگو")
            
            for i, chat in enumerate(reversed(st.session_state.chat_history), 1):
                with st.expander(f"💬 سوال {len(st.session_state.chat_history) - i + 1}: {chat['question']}", expanded=(i==1)):
                    st.markdown(f"**🤖 پاسخ:**")
                    st.write(chat['answer'])
                    
                    st.markdown("**📚 منابع:**")
                    for j, doc in enumerate(chat['sources'], 1):
                        page = doc.metadata.get('page', 'N/A')
                        content = doc.page_content[:200] + "..."
                        st.text(f"{j}. صفحه {page}:\n{content}\n")
    else:
        st.info("👆 لطفاً ابتدا یک PDF در بخش سمت چپ آپلود کنید")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    🚀 Day 3: RAG System | AI Learning Journey
</div>
""", unsafe_allow_html=True)
