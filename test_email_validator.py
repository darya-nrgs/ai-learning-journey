"""
تست Email Validator تولید شده توسط Multi-Agent System
"""

from day2_output_final import validate_email, EmailValidator, ValidationOptions

def test_basic_emails():
    """تست ایمیل‌های ساده"""
    
    print("=" * 60)
    print("🧪 تست ایمیل‌های معتبر")
    print("=" * 60)
    
    valid_emails = [
        "user@example.com",
        "test.user@example.com",
        "user+tag@example.com",
        "user123@test.co.uk",
    ]
    
    for email in valid_emails:
        result = validate_email(email)
        status = "✅" if result.is_valid else "❌"
        print(f"{status} {email}")
        if result.warnings:
            print(f"   ⚠️  هشدارها: {result.warnings}")
    
    print("\n" + "=" * 60)
    print("🧪 تست ایمیل‌های نامعتبر")
    print("=" * 60)
    
    invalid_emails = [
        "user@",
        "@example.com",
        "user..name@example.com",
        "user name@example.com",
        "user@domain",
        ".user@example.com",
    ]
    
    for email in invalid_emails:
        result = validate_email(email)
        status = "✅" if not result.is_valid else "❌"
        print(f"{status} {email}")
        if result.errors:
            print(f"   🔴 خطاها: {result.errors[0]}")


def test_with_options():
    """تست با تنظیمات مختلف"""
    
    print("\n" + "=" * 60)
    print("🧪 تست با strict mode")
    print("=" * 60)
    
    strict_validator = EmailValidator(
        ValidationOptions(strict_mode=True, allow_disposable=False)
    )
    
    email = "user@tempmail.com"
    result = strict_validator.validate(email)
    
    print(f"ایمیل: {email}")
    print(f"معتبر: {result.is_valid}")
    if result.warnings:
        print(f"هشدارها: {result.warnings}")


def test_edge_cases():
    """تست edge cases"""
    
    print("\n" + "=" * 60)
    print("🧪 تست Edge Cases")
    print("=" * 60)
    
    edge_cases = [
        ("a@b.c", "ایمیل کوتاه"),
        ("test@localhost", "بدون TLD"),
        ("user+tag+more@example.com", "چند plus"),
        ('"user name"@example.com', "quoted local part"),
    ]
    
    for email, description in edge_cases:
        result = validate_email(email)
        status = "✅" if result.is_valid else "❌"
        print(f"{status} {description}: {email}")
        if result.errors:
            print(f"   خطا: {result.errors[0]}")


if __name__ == "__main__":
    test_basic_emails()
    test_with_options()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("✅ تست‌ها تمام شد!")
    print("=" * 60)
