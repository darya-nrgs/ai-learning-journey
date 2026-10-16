import requests
import json
import time

# Base URL
BASE_URL = "http://localhost:8000"
API_KEY = "demo-key-123"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def print_section(title):
    """چاپ عنوان قسمت"""
    print("\n" + "=" * 60)
    print(f"🧪 {title}")
    print("=" * 60)


def test_health():
    """تست 1: بررسی سلامت سرویس"""
    print_section("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_code_generation():
    """تست 2: تولید کد"""
    print_section("Test 2: Code Generation")
    
    try:
        payload = {
            "prompt": "یک تابع برای بررسی عدد اول بنویس با تست‌های کامل",
            "language": "python"
        }
        
        print(f"Request:\n{json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/generate-code",
            headers=headers,
            json=payload
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Language: {result['language']}")
            print(f"Status: {result['status']}")
            print(f"\nGenerated Code:")
            print("-" * 60)
            print(result['code'])
            print("-" * 60)
            print("✅ Code generation passed!")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_rag_upload():
    """تست 3: آپلود PDF"""
    print_section("Test 3: RAG Upload PDF")
    
    pdf_path = "blue_point.pdf"
    
    # بررسی فایل
    import os
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        print("⚠️  Please make sure blue_point.pdf exists in the current directory")
        return False
    
    try:
        print(f"Uploading: {pdf_path}")
        
        files = {
            'file': ('blue_point.pdf', open(pdf_path, 'rb'), 'application/pdf')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/upload?session_id=test_session",
            headers={"X-API-Key": API_KEY},
            files=files
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ PDF upload passed!")
            time.sleep(2)  # صبر برای پردازش
            return True
        else:
            print(f"❌ Upload failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_rag_ask():
    """تست 4: پرسیدن سوال از PDF"""
    print_section("Test 4: RAG Ask Question")
    
    try:
        questions = [
            "این سند درباره چیست؟",
            "چه موضوعاتی در این سند بررسی شده؟"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n📝 Question {i}: {question}")
            
            payload = {
                "question": question,
                "session_id": "test_session"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/rag/ask",
                headers=headers,
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n🤖 Answer:")
                print(result['answer'])
                print(f"\n📚 Sources: {len(result['sources'])} chunks used")
                for j, source in enumerate(result['sources'], 1):
                    print(f"   {j}. Page {source['page']}: {source['content'][:100]}...")
                print("✅ Question answered!")
            else:
                print(f"❌ Error: {response.text}")
                return False
            
            print("-" * 60)
            time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_invalid_api_key():
    """تست 5: API Key نامعتبر"""
    print_section("Test 5: Invalid API Key")
    
    try:
        bad_headers = {
            "X-API-Key": "wrong-key-999",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/generate-code",
            headers=bad_headers,
            json={"prompt": "test", "language": "python"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ API key validation works!")
            return True
        else:
            print("❌ API key validation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_rate_limit():
    """تست 6: Rate Limiting"""
    print_section("Test 6: Rate Limiting")
    
    try:
        print("Sending 12 requests (limit is 10/minute)...")
        
        for i in range(12):
            response = requests.post(
                f"{BASE_URL}/api/v1/generate-code",
                headers=headers,
                json={"prompt": f"test {i}", "language": "python"}
            )
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"Request {i+1:2d}: {status} Status {response.status_code}")
            
            if response.status_code == 429:
                print("\n✅ Rate limit triggered! (This is expected)")
                return True
            
            time.sleep(0.2)
        
        print("⚠️  Rate limit not triggered (might need more requests)")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """اجرای تمام تست‌ها"""
    print("=" * 60)
    print("🚀 AI Services API - Test Suite")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = test_health()
    
    if not results['health']:
        print("\n❌ Server is not healthy. Stopping tests.")
        return
    
    # Test 2: Code Generation
    results['code_gen'] = test_code_generation()
    
    # Test 3 & 4: RAG System
    if test_rag_upload():
        results['rag'] = test_rag_ask()
    else:
        results['rag'] = False
        print("⚠️  Skipping RAG questions (upload failed)")
    
    # Test 5: Invalid API Key
    results['auth'] = test_invalid_api_key()
    
    # Test 6: Rate Limiting (optional)
    # results['rate_limit'] = test_rate_limit()
    
    # خلاصه نتایج
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:15s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")


if __name__ == "__main__":
    # بررسی اینکه سرور در حال اجراست
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except:
        print("❌ Error: Server is not running!")
        print(f"Please start the server first: python day4_api.py")
        exit(1)
    
    main()
