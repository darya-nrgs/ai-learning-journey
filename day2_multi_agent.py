"""
روز 2: Multi-Agent System
یک تیم از Agent ها که با هم کار می‌کنن
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()

class BaseAgent:
    """کلاس پایه برای همه Agent ها"""
    
    def __init__(self, name, role, system_prompt):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.client = OpenAI(
            api_key=os.getenv("NINE_ROUTER_API_KEY"),
            base_url="http://localhost:20128/v1"
        )
        self.model = "kr/claude-sonnet-4.5"
    
    def process(self, user_input, context=""):
        """پردازش input و برگرداندن output"""
        
        print(f"\n{'='*60}")
        print(f"🤖 {self.name} در حال کار...")
        print(f"   نقش: {self.role}")
        print(f"{'='*60}\n")
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # اضافه کردن context اگه وجود داشته باشه
        if context:
            messages.append({
                "role": "user", 
                "content": f"\n\nContext از مراحل قبل:\n{context}"
            })
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4
        )
        
        output = response.choices[0].message.content
        
        print(output)
        print(f"\n{'='*60}\n")
        
        return output


class ArchitectAgent(BaseAgent):
    """Agent طراح معماری"""
    
    def __init__(self):
        super().__init__(
            name="Architect",
            role="معمار سیستم",
            system_prompt="""تو یک معمار نرم‌افزار با تجربه هستی.
وقتی یک feature request می‌گیری:
1. آن را به components تقسیم کن
2. ساختار داده‌ها را طراحی کن
3. توابع و کلاس‌های مورد نیاز را مشخص کن
4. Edge cases را در نظر بگیر

خروجی‌ات باید واضح و قابل implement باشه."""
        )


class DeveloperAgent(BaseAgent):
    """Agent برنامه‌نویس"""
    
    def __init__(self):
        super().__init__(
            name="Developer",
            role="برنامه‌نویس",
            system_prompt="""تو یک برنامه‌نویس Python حرفه‌ای هستی.
بر اساس طراحی معماری، کد بنویس که:
- تمیز و خوانا باشه
- docstring و type hints داشته باشه
- error handling درست داشته باشه
- کامنت برای قسمت‌های پیچیده

فقط کد Python بنویس، بدون markdown."""
        )
    
    def extract_code(self, text):
        """استخراج کد از خروجی"""
        code_blocks = re.findall(r'```python\n(.*?)```', text, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        return text.strip()


class ReviewerAgent(BaseAgent):
    """Agent بازبین کد"""
    
    def __init__(self):
        super().__init__(
            name="Reviewer",
            role="بازبین کد",
            system_prompt="""تو یک code reviewer با تجربه هستی.
کد را از این جنبه‌ها بررسی کن:
1. باگ‌ها و خطاهای منطقی
2. مشکلات امنیتی
3. مشکلات performance
4. نقض best practices
5. کد تکراری

نقدت سازنده و مشخص باشه."""
        )


class ImproverAgent(BaseAgent):
    """Agent بهبود دهنده"""
    
    def __init__(self):
        super().__init__(
            name="Improver",
            role="بهبود دهنده کد",
            system_prompt="""تو یک برنامه‌نویس senior هستی.
بر اساس نظرات reviewer، کد را بهبود بده.
فقط کد بهبود یافته را بنویس، بدون توضیحات اضافی."""
        )


class MultiAgentSystem:
    """سیستم مدیریت چند Agent"""
    
    def __init__(self):
        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent()
        self.reviewer = ReviewerAgent()
        self.improver = ImproverAgent()
        
        self.results = {}
    
    def run_workflow(self, user_request):
        """اجرای کامل workflow"""
        
        print("\n" + "🚀" * 30)
        print("🚀 شروع Multi-Agent Workflow")
        print("🚀" * 30)
        print(f"\n📝 درخواست: {user_request}\n")
        
        # مرحله 1: طراحی معماری
        print("\n" + "📐" * 30)
        print("مرحله 1: طراحی معماری")
        print("📐" * 30)
        
        design = self.architect.process(
            f"طراحی کن: {user_request}"
        )
        self.results['design'] = design
        
        # مرحله 2: پیاده‌سازی
        print("\n" + "💻" * 30)
        print("مرحله 2: پیاده‌سازی")
        print("💻" * 30)
        
        code = self.developer.process(
            f"پیاده‌سازی کن: {user_request}",
            context=f"طراحی:\n{design}"
        )
        clean_code = self.developer.extract_code(code)
        self.results['code_v1'] = clean_code
        
        # مرحله 3: بررسی کد
        print("\n" + "🔍" * 30)
        print("مرحله 3: بررسی کد")
        print("🔍" * 30)
        
        review = self.reviewer.process(
            f"این کد را بررسی کن:\n\n{clean_code}"
        )
        self.results['review'] = review
        
        # مرحله 4: بهبود کد
        print("\n" + "⚡" * 30)
        print("مرحله 4: بهبود کد")
        print("⚡" * 30)
        
        improved = self.improver.process(
            f"این کد را بر اساس نظرات بهبود بده:\n\nکد:\n{clean_code}\n\nنظرات:\n{review}"
        )
        clean_improved = self.developer.extract_code(improved)
        self.results['code_final'] = clean_improved
        
        print("\n" + "✅" * 30)
        print("✅ Workflow تمام شد!")
        print("✅" * 30)
        
        return self.results
    
    def save_results(self, filename="workflow_results"):
        """ذخیره نتایج"""
        
        # ذخیره کد نهایی
        code_file = f"{filename}_final.py"
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("# Generated by Multi-Agent System\n")
            f.write("# Final improved version\n\n")
            f.write(self.results.get('code_final', ''))
        
        # ذخیره گزارش کامل
        report_file = f"{filename}_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Multi-Agent Workflow Report\n\n")
            
            f.write("## 1. Architecture Design\n\n")
            f.write(self.results.get('design', '') + "\n\n")
            
            f.write("## 2. Initial Implementation\n\n")
            f.write("```python\n")
            f.write(self.results.get('code_v1', ''))
            f.write("\n```\n\n")
            
            f.write("## 3. Code Review\n\n")
            f.write(self.results.get('review', '') + "\n\n")
            
            f.write("## 4. Final Improved Code\n\n")
            f.write("```python\n")
            f.write(self.results.get('code_final', ''))
            f.write("\n```\n")
        
        print(f"\n💾 نتایج ذخیره شد:")
        print(f"   📄 کد نهایی: {code_file}")
        print(f"   📋 گزارش کامل: {report_file}")


def main():
    print("=" * 60)
    print("🤖 Multi-Agent Development System")
    print("=" * 60)
    
    # مثال‌ها
    examples = [
        "تابعی برای validation کردن email",
        "کلاسی برای مدیریت to-do list",
        "تابعی برای پردازش و تمیز کردن متن فارسی"
    ]
    
    print("\n📋 مثال‌ها:")
    for i, ex in enumerate(examples, 1):
        print(f"   {i}. {ex}")
    
    choice = input("\nانتخاب (1-3) یا درخواست خودت: ")
    
    if choice.isdigit() and 1 <= int(choice) <= 3:
        request = examples[int(choice) - 1]
    else:
        request = choice
    
    # اجرای workflow
    system = MultiAgentSystem()
    results = system.run_workflow(request)
    
    # ذخیره نتایج
    system.save_results("day2_output")
    
    print("\n" + "=" * 60)
    print("🎉 تمام! حالا می‌تونی فایل‌های output رو چک کنی")
    print("=" * 60)


if __name__ == "__main__":
    main()
