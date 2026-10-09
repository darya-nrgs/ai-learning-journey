"""
تست اتصال به API با 9router
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# بارگذاری environment variables
load_dotenv()

def test_api_connection():
    """تست اتصال به 9router"""
    
    print("=" * 60)
    print("🚀 تست اتصال به API با 9router")
    print("=" * 60)
    print()
    
    # چک کردن API key
    api_key = os.getenv("NINE_ROUTER_API_KEY")
    
    if not api_key:
        print("❌ خطا: NINE_ROUTER_API_KEY در فایل .env پیدا نشد!")
        print("لطفاً فایل .env رو چک کن.")
        return False
    
    print(f"✅ API Key پیدا شد (طول: {len(api_key)} کاراکتر)")
    print(f"🔌 در حال اتصال به: http://localhost:20128/v1")
    print(f"🤖 مدل: kr/claude-sonnet-4.5")
    print()
    
    try:
        # ساخت client
        client = OpenAI(
            api_key=api_key,
            base_url="http://localhost:20128/v1"
        )
        
        print("📤 در حال ارسال request...")
        
        # ارسال request
        response = client.chat.completions.create(
            model="kr/claude-sonnet-4.5",
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API is working!' in Persian"
                }
            ],
            temperature=0.7
        )
        
        # نمایش پاسخ
        print("\n" + "-" * 60)
        print("✅ پاسخ دریافت شد:")
        print("-" * 60)
        print(response.choices[0].message.content)
        print("-" * 60)
        
        # نمایش اطلاعات بیشتر
        print("\n📊 جزئیات:")
        print(f"   مدل استفاده شده: {response.model}")
        if hasattr(response, 'usage') and response.usage:
            print(f"   Tokens مصرف شده: {response.usage.total_tokens}")
        
        print("\n" + "=" * 60)
        print("🎉 اتصال موفقیت‌آمیز بود!")
        print("=" * 60)
        
        return True
        
    except ConnectionError as e:
        print(f"\n❌ خطای اتصال: {e}")
        print("\n💡 راهنمایی:")
        print("   1. مطمئن شو 9router در حال اجراست")
        print("   2. چک کن که روی port 20128 گوش می‌ده")
        print("   3. تنظیمات firewall رو بررسی کن")
        return False
        
    except Exception as e:
        print(f"\n❌ خطا: {e}")
        print(f"   نوع خطا: {type(e).__name__}")
        print("\n💡 راهنمایی:")
        print("   1. API key رو چک کن")
        print("   2. مدل 'kr/claude-sonnet-4.5' در دسترسه؟")
        print("   3. 9router به‌روز هست؟")
        return False

if __name__ == "__main__":
    test_api_connection()
