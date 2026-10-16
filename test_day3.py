# import os
# from dotenv import load_dotenv

# # Test 1: Load environment
# print("🧪 Test 1: Loading environment...")
# load_dotenv()
# api_key = os.getenv("NINE_ROUTER_API_KEY")
# if api_key:
#     print(f"✅ API Key found: {api_key[:10]}...")
# else:
#     print("❌ API Key not found!")
#     exit(1)

# # Test 2: Import RAG System
# print("\n🧪 Test 2: Importing RAG System...")
# try:
#     from day3_rag_system import RAGSystem
#     print("✅ RAG System imported successfully")
# except Exception as e:
#     print(f"❌ Import failed: {e}")
#     exit(1)

# # Test 3: Check PDF exists
# print("\n🧪 Test 3: Checking PDF file...")
# pdf_path = "blue_point.pdf"
# if os.path.exists(pdf_path):
#     print(f"✅ PDF found: {pdf_path}")
# else:
#     print(f"❌ PDF not found: {pdf_path}")
#     exit(1)

# # Test 4: Initialize RAG
# print("\n🧪 Test 4: Initializing RAG System...")
# try:
#     rag = RAGSystem(api_key=api_key)
#     print("✅ RAG System initialized")
# except Exception as e:
#     print(f"❌ Initialization failed: {e}")
#     exit(1)

# # Test 5: Process PDF
# print("\n🧪 Test 5: Processing PDF...")
# try:
#     rag.process_pdf(pdf_path)
#     print("✅ PDF processed successfully")
# except Exception as e:
#     print(f"❌ Processing failed: {e}")
#     import traceback
#     traceback.print_exc()
#     exit(1)

# # Test 6: Ask a question
# print("\n🧪 Test 6: Asking a question...")
# try:
#     answer, sources = rag.ask("این سند درباره چیست؟")
#     print(f"✅ Question answered successfully")
#     print(f"\n📝 Answer: {answer}")
# except Exception as e:
#     print(f"❌ Question failed: {e}")
#     import traceback
#     traceback.print_exc()
#     exit(1)

# print("\n" + "="*60)
# print("🎉 All tests passed!")
# print("="*60)
import os
from dotenv import load_dotenv

# Test 1: Load environment
print("🧪 Test 1: Loading environment...")
load_dotenv()
api_key = os.getenv("NINE_ROUTER_API_KEY")
if api_key:
    print(f"✅ API Key found: {api_key[:10]}...")
else:
    print("❌ API Key not found!")
    exit(1)

# Test 2: Import RAG System
print("\n🧪 Test 2: Importing RAG System...")
try:
    from day3_rag_system import RAGSystem
    print("✅ RAG System imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 3: Check PDF exists
print("\n🧪 Test 3: Checking PDF file...")
pdf_path = "blue_point.pdf"
if os.path.exists(pdf_path):
    print(f"✅ PDF found: {pdf_path}")
else:
    print(f"❌ PDF not found: {pdf_path}")
    exit(1)

# Test 4: Initialize RAG
print("\n🧪 Test 4: Initializing RAG System...")
try:
    rag = RAGSystem(api_key=api_key)
    print("✅ RAG System initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    exit(1)

# Test 5: Process PDF
print("\n🧪 Test 5: Processing PDF...")
try:
    rag.process_pdf(pdf_path)
    print("✅ PDF processed successfully")
except Exception as e:
    print(f"❌ Processing failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 6: Ask a question
print("\n🧪 Test 6: Asking a question...")
try:
    answer, sources = rag.ask("این سند درباره چیست؟")
    print(f"✅ Question answered successfully")
    print(f"\n📝 Answer: {answer}")
except Exception as e:
    print(f"❌ Question failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("🎉 All tests passed!")
print("="*60)
