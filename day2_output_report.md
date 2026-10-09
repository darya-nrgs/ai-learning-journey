# Multi-Agent Workflow Report

## 1. Architecture Design

# طراحی تابع Validation ایمیل

## 1. تقسیم‌بندی Components

```
EmailValidator
├── Format Validation (ساختار کلی)
├── Syntax Rules (قوانین RFC)
├── Domain Validation (بررسی دامنه)
└── Security Checks (بررسی‌های امنیتی)
```

## 2. ساختار داده‌ها

```typescript
interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
  metadata?: {
    localPart: string;
    domain: string;
    hasValidMX?: boolean;
  };
}

interface ValidationOptions {
  allowDisposable?: boolean;
  checkMX?: boolean;
  allowSubaddressing?: boolean; // plus addressing: user+tag@domain
  maxLength?: number;
  strictMode?: boolean;
}
```

## 3. توابع و کلاس‌های مورد نیاز

### کلاس اصلی
```typescript
class EmailValidator {
  private options: ValidationOptions;
  private disposableDomains: Set<string>;
  
  constructor(options?: ValidationOptions);
  
  // متد اصلی
  validate(email: string): ValidationResult;
  
  // متدهای کمکی
  private validateFormat(email: string): boolean;
  private validateLocalPart(localPart: string): boolean;
  private validateDomain(domain: string): boolean;
  private checkDisposable(domain: string): boolean;
  private checkMXRecords(domain: string): Promise<boolean>;
  private sanitizeInput(email: string): string;
}
```

### توابع Utility

```typescript
// بررسی‌های پایه
function isValidLength(email: string, max: number): boolean;
function hasValidCharacters(part: string, allowed: RegExp): boolean;
function splitEmail(email: string): { local: string; domain: string } | null;

// بررسی‌های پیشرفته
function validateDomainSyntax(domain: string): boolean;
function hasConsecutiveDots(str: string): boolean;
function isQuotedString(str: string): boolean;
```

## 4. Edge Cases

### موارد معتبر اما غیرمعمول
- `"user name"@example.com` (quoted local part)
- `user+tag@example.com` (plus addressing)
- `user@subdomain.example.com` (subdomain)
- `user@[192.168.1.1]` (IP literal)
- `user@example.co.uk` (multiple TLD parts)

### موارد نامعتبر
- `user@` (بدون domain)
- `@example.com` (بدون local part)
- `user..name@example.com` (نقطه‌های متوالی)
- `user@.example.com` (شروع domain با نقطه)
- `.user@example.com` (شروع local با نقطه)
- `user@domain` (بدون TLD در حالت strict)
- `user name@example.com` (فاصله بدون quote)
- `user@domain-.com` (dash در انتهای label)

### موارد امنیتی
- ایمیل‌های خیلی طولانی (DoS)
- کاراکترهای Unicode مشکوک (homograph attack)
- Multiple @ symbols
- Null bytes یا کاراکترهای control

## 5. پیاده‌سازی نمونه

```typescript
class EmailValidator {
  private readonly MAX_LENGTH = 320; // 64 + @ + 255
  private readonly MAX_LOCAL_LENGTH = 64;
  private readonly MAX_DOMAIN_LENGTH = 255;
  
  private options: ValidationOptions;

  constructor(options: ValidationOptions = {}) {
    this.options = {
      allowDisposable: false,
      checkMX: false,
      allowSubaddressing: true,
      maxLength: this.MAX_LENGTH,
      strictMode: true,
      ...options
    };
  }

  validate(email: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // 1. Sanitize
    const sanitized = this.sanitizeInput(email);
    
    // 2. Length check
    if (sanitized.length > this.options.maxLength!) {
      errors.push(`Email exceeds maximum length of ${this.options.maxLength}`);
      return { isValid: false, errors };
    }

    // 3. Split email
    const parts = this.splitEmail(sanitized);
    if (!parts) {
      errors.push('Invalid email format');
      return { isValid: false, errors };
    }

    // 4. Validate local part
    if (!this.validateLocalPart(parts.local)) {
      errors.push('Invalid local part');
    }

    // 5. Validate domain
    if (!this.validateDomain(parts.domain)) {
      errors.push('Invalid domain');
    }

    // 6. Additional checks
    if (!this.options.allowDisposable && this.checkDisposable(parts.domain)) {
      warnings.push('Disposable email detected');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings: warnings.length > 0 ? warnings : undefined,
      metadata: errors.length === 0 ? {
        localPart: parts.local,
        domain: parts.domain
      } : undefined
    };
  }

  private sanitizeInput(email: string): string {
    return email.trim().toLowerCase();
  }

  private splitEmail(email: string): { local: string; domain: string } | null {
    const atIndex = email.lastIndexOf('@');
    if (atIndex === -1 || atIndex === 0 || atIndex === email.length - 1) {
      return null;
    }

    return {
      local: email.substring(0, atIndex),
      domain: email.substring(atIndex + 1)
    };
  }

  private validateLocalPart(local: string): boolean {
    if (local.length === 0 || local.length > this.MAX_LOCAL_LENGTH) {
      return false;
    }

    // Check for consecutive dots
    if (local.includes('..')) return false;
    
    // Check start/end
    if (local.startsWith('.') || local.endsWith('.')) return false;

    // Quoted string handling
    if (local.startsWith('"') && local.endsWith('"')) {
      return this.validateQuotedString(local);
    }

    // Regular validation
    const validChars = /^[a-z0-9!#$%&'*+\/=?^_`{|}~.-]+$/;
    return validChars.test(local);
  }

  private validateDomain(domain: string): boolean {
    if (domain.length === 0 || domain.length > this.MAX_DOMAIN_LENGTH) {
      return false;
    }

    // IP literal check
    if (domain.startsWith('[') && domain.endsWith(']')) {
      return this.validateIPLiteral(domain);
    }

    // Domain label validation
    const labels = domain.split('.');
    
    if (this.options.strictMode && labels.length < 2) {
      return false; // Require TLD
    }

    for (const label of labels) {
      if (label.length === 0 || label.length > 63) return false;
      if (label.startsWith('-') || label.endsWith('-')) return false;
      if (!/^[a-z0-9-]+$/.test(label)) return false;
    }

    return true;
  }

  private validateQuotedString(local: string): boolean {
    // Simplified: allow any character between quotes
    const content = local.slice(1, -1);
    return content.length > 0;
  }

  private validateIPLiteral(domain: string): boolean {
    const ip = domain.slice(1, -1);
    // IPv4 basic check
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    return ipv4Regex.test(ip);
  }

  private checkDisposable(domain: string): boolean {
    const disposable = ['tempmail.com', 'throwaway.email', '10minutemail.com'];
    return disposable.includes(domain);
  }

  async validateAsync(email: string): Promise<ValidationResult> {
    const result = this.validate(email);
    
    if (result.isValid && this.options.checkMX && result.metadata) {
      const hasMX = await this.checkMXRecords(result.metadata.domain);
      result.metadata.hasValidMX = hasMX;
      
      if (!hasMX) {
        result.warnings = result.warnings || [];
        result.warnings.push('No MX records found');
      }
    }

    return result;
  }

  private async checkMXRecords(domain: string): Promise<boolean> {
    // Implementation depends on environment (Node.js dns module, etc.)
    return true; // Placeholder
  }
}
```

## 6. استفاده

```typescript
// Basic usage
const validator = new EmailValidator();
const result = validator.validate('user@example.com');

if (result.isValid) {
  console.log('Valid email:', result.metadata);
} else {
  console.log('Errors:', result.errors);
}

// With options
const strictValidator = new EmailValidator({
  strictMode: true,
  allowDisposable: false,
  maxLength: 254
});

// Async with MX check
const advancedValidator = new EmailValidator({ checkMX: true });
const asyncResult = await advancedValidator.validateAsync('user@example.com');
```

## نکات پیاده‌سازی

1. **Performance**: برای لیست disposable domains از Set استفاده کن
2. **Security**: همیشه input را sanitize کن
3. **RFC Compliance**: برای production از کتابخانه‌های تست‌شده استفاده کن
4. **Async Operations**: MX lookup را جدا نگه دار تا blocking نباشه
5. **Internationalization**: برای ایمیل‌های non-ASCII باید IDN encoding رو ساپورت کنی

## 2. Initial Implementation

```python
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import ipaddress


@dataclass
class ValidationResult:
    """نتیجه اعتبارسنجی ایمیل
    
    Attributes:
        is_valid: آیا ایمیل معتبر است
        errors: لیست خطاها
        warnings: لیست هشدارها (اختیاری)
        metadata: اطلاعات اضافی درباره ایمیل (اختیاری)
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, str]] = None


@dataclass
class ValidationOptions:
    """تنظیمات اعتبارسنجی ایمیل
    
    Attributes:
        allow_disposable: اجازه به ایمیل‌های موقت
        allow_subaddressing: اجازه به plus addressing (user+tag@domain)
        max_length: حداکثر طول ایمیل
        strict_mode: حالت سخت‌گیرانه (نیاز به TLD)
    """
    allow_disposable: bool = False
    allow_subaddressing: bool = True
    max_length: int = 320  # 64 + @ + 255
    strict_mode: bool = True


class EmailValidator:
    """کلاس اعتبارسنجی ایمیل
    
    این کلاس بر اساس RFC 5322 و RFC 5321 ایمیل‌ها را اعتبارسنجی می‌کند.
    """
    
    MAX_LOCAL_LENGTH = 64
    MAX_DOMAIN_LENGTH = 255
    
    # دامنه‌های ایمیل موقت شناخته شده
    DISPOSABLE_DOMAINS: Set[str] = {
        'tempmail.com',
        'throwaway.email',
        '10minutemail.com',
        'guerrillamail.com',
        'mailinator.com',
    }
    
    def __init__(self, options: Optional[ValidationOptions] = None) -> None:
        """مقداردهی اولیه validator
        
        Args:
            options: تنظیمات اعتبارسنجی (پیش‌فرض: None)
        """
        self.options = options or ValidationOptions()
    
    def validate(self, email: str) -> ValidationResult:
        """اعتبارسنجی ایمیل
        
        Args:
            email: آدرس ایمیل برای بررسی
            
        Returns:
            ValidationResult: نتیجه اعتبارسنجی شامل وضعیت، خطاها و هشدارها
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # ۱. پاکسازی ورودی
        try:
            sanitized = self._sanitize_input(email)
        except ValueError as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors)
        
        # ۲. بررسی طول
        if len(sanitized) > self.options.max_length:
            errors.append(
                f'طول ایمیل بیش از حد مجاز است (حداکثر {self.options.max_length} کاراکتر)'
            )
            return ValidationResult(is_valid=False, errors=errors)
        
        # ۳. جداسازی local و domain
        parts = self._split_email(sanitized)
        if not parts:
            errors.append('فرمت ایمیل نامعتبر است')
            return ValidationResult(is_valid=False, errors=errors)
        
        local_part, domain = parts
        
        # ۴. اعتبارسنجی local part
        local_errors = self._validate_local_part(local_part)
        errors.extend(local_errors)
        
        # ۵. اعتبارسنجی domain
        domain_errors = self._validate_domain(domain)
        errors.extend(domain_errors)
        
        # ۶. بررسی‌های اضافی
        if not self.options.allow_disposable and self._check_disposable(domain):
            warnings.append('ایمیل موقت شناسایی شد')
        
        # ۷. بررسی subaddressing
        if not self.options.allow_subaddressing and '+' in local_part:
            warnings.append('استفاده از plus addressing (+) شناسایی شد')
        
        # ساخت نتیجه
        is_valid = len(errors) == 0
        metadata = None
        if is_valid:
            metadata = {
                'local_part': local_part,
                'domain': domain,
            }
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings if warnings else [],
            metadata=metadata
        )
    
    def _sanitize_input(self, email: str) -> str:
        """پاکسازی و نرمال‌سازی ورودی
        
        Args:
            email: ایمیل خام
            
        Returns:
            str: ایمیل پاک‌شده
            
        Raises:
            ValueError: اگر ایمیل حاوی کاراکترهای غیرمجاز باشد
        """
        # حذف فاصله‌های ابتدا و انتها
        sanitized = email.strip()
        
        # بررسی کاراکترهای کنترلی و null byte
        if any(ord(c) < 32 for c in sanitized) or '\x00' in sanitized:
            raise ValueError('ایمیل حاوی کاراکترهای غیرمجاز است')
        
        # بررسی تعداد @
        if sanitized.count('@') != 1:
            raise ValueError('ایمیل باید دقیقاً یک @ داشته باشد')
        
        # تبدیل domain به حروف کوچک (local part case-sensitive است)
        at_index = sanitized.rfind('@')
        if at_index != -1:
            local = sanitized[:at_index]
            domain = sanitized[at_index + 1:].lower()
            sanitized = f"{local}@{domain}"
        
        return sanitized
    
    def _split_email(self, email: str) -> Optional[tuple[str, str]]:
        """جداسازی local part و domain
        
        Args:
            email: آدرس ایمیل
            
        Returns:
            Optional[tuple[str, str]]: تاپل (local, domain) یا None در صورت خطا
        """
        at_index = email.rfind('@')
        
        # بررسی وجود و موقعیت @
        if at_index == -1 or at_index == 0 or at_index == len(email) - 1:
            return None
        
        local = email[:at_index]
        domain = email[at_index + 1:]
        
        return (local, domain)
    
    def _validate_local_part(self, local: str) -> List[str]:
        """اعتبارسنجی local part
        
        Args:
            local: قسمت local از ایمیل (قبل از @)
            
        Returns:
            List[str]: لیست خطاها
        """
        errors: List[str] = []
        
        # بررسی طول
        if len(local) == 0:
            errors.append('local part نمی‌تواند خالی باشد')
            return errors
        
        if len(local) > self.MAX_LOCAL_LENGTH:
            errors.append(
                f'طول local part بیش از حد مجاز است (حداکثر {self.MAX_LOCAL_LENGTH})'
            )
            return errors
        
        # اگر quoted string است
        if local.startswith('"') and local.endswith('"'):
            if not self._validate_quoted_string(local):
                errors.append('quoted string نامعتبر است')
            return errors
        
        # بررسی نقطه‌های متوالی
        if '..' in local:
            errors.append('local part نمی‌تواند نقطه‌های متوالی داشته باشد')
        
        # بررسی شروع و پایان با نقطه
        if local.startswith('.') or local.endswith('.'):
            errors.append('local part نمی‌تواند با نقطه شروع یا پایان یابد')
        
        # بررسی کاراکترهای مجاز
        # طبق RFC: a-z, 0-9 و !#$%&'*+-/=?^_`{|}~.
        valid_chars_pattern = re.compile(r'^[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~.-]+$')
        if not valid_chars_pattern.match(local):
            errors.append('local part حاوی کاراکترهای غیرمجاز است')
        
        return errors
    
    def _validate_quoted_string(self, local: str) -> bool:
        """اعتبارسنجی quoted string
        
        Args:
            local: local part به صورت quoted
            
        Returns:
            bool: آیا معتبر است
        """
        # محتوای بین گیومه‌ها
        content = local[1:-1]
        
        # نباید خالی باشد
        if len(content) == 0:
            return False
        
        # در quoted string کاراکترهای بیشتری مجاز هستند
        # اما backslash باید escape شده باشد
        i = 0
        while i < len(content):
            if content[i] == '\\':
                # کاراکتر بعدی باید escape شده باشد
                if i + 1 >= len(content):
                    return False
                i += 2
            else:
                i += 1
        
        return True
    
    def _validate_domain(self, domain: str) -> List[str]:
        """اعتبارسنجی domain
        
        Args:
            domain: قسمت domain از ایمیل (بعد از @)
            
        Returns:
            List[str]: لیست خطاها
        """
        errors: List[str] = []
        
        # بررسی طول
        if len(domain) == 0:
            errors.append('domain نمی‌تواند خالی باشد')
            return errors
        
        if len(domain) > self.MAX_DOMAIN_LENGTH:
            errors.append(
                f'طول domain بیش از حد مجاز است (حداکثر {self.MAX_DOMAIN_LENGTH})'
            )
            return errors
        
        # بررسی IP literal
        if domain.startswith('[') and domain.endswith(']'):
            if not self._validate_ip_literal(domain):
                errors.append('IP literal نامعتبر است')
            return errors
        
        # جداسازی labels
        labels = domain.split('.')
        
        # در حالت strict باید حداقل دو label داشته باشد (domain + TLD)
        if self.options.strict_mode and len(labels) < 2:
            errors.append('domain باید شامل TLD باشد')
        
        # اعتبارسنجی هر label
        for label in labels:
            if len(label) == 0:
                errors.append('domain label نمی‌تواند خالی باشد')
                continue
            
            if len(label) > 63:
                errors.append('طول domain label بیش از ۶۳ کاراکتر است')
                continue
            
            # نباید با dash شروع یا پایان یابد
            if label.startswith('-') or label.endswith('-'):
                errors.append('domain label نمی‌تواند با - شروع یا پایان یابد')
            
            # فقط a-z، 0-9 و - مجاز است
            if not re.match(r'^[a-z0-9-]+$', label):
                errors.append('domain label حاوی کاراکترهای غیرمجاز است')
        
        return errors
    
    def _validate_ip_literal(self, domain: str) -> bool:
        """اعتبارسنجی IP literal
        
        Args:
            domain: domain به صورت [IP]
            
        Returns:
            bool: آیا معتبر است
        """
        # استخراج IP از بین براکت‌ها
        ip_str = domain[1:-1]
        
        try:
            # تلاش برای parse کردن به عنوان IPv4 یا IPv6
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    def _check_disposable(self, domain: str) -> bool:
        """بررسی اینکه domain جزو ایمیل‌های موقت است یا نه
        
        Args:
            domain: دامنه برای بررسی
            
        Returns:
            bool: آیا موقت است
        """
        return domain in self.DISPOSABLE_DOMAINS


def validate_email(
    email: str,
    options: Optional[ValidationOptions] = None
) -> ValidationResult:
    """تابع helper برای اعتبارسنجی سریع ایمیل
    
    Args:
        email: آدرس ایمیل برای بررسی
        options: تنظیمات اعتبارسنجی (اختیاری)
        
    Returns:
        ValidationResult: نتیجه اعتبارسنجی
        
    Example:
        >>> result = validate_email('user@example.com')
        >>> if result.is_valid:
        ...     print(f"ایمیل معتبر است: {result.metadata}")
        ... else:
        ...     print(f"خطاها: {result.errors}")
    """
    validator = EmailValidator(options)
    return validator.validate(email)
```

## 3. Code Review

# بررسی کد - Email Validator

این یک پیاده‌سازی خوب و جامع است، اما چند نکته قابل بهبود دارد:

## 1. باگ‌ها و خطاهای منطقی

### باگ در `_validate_domain`:
```python
# مشکل: labels خالی از split نادیده گرفته می‌شوند
labels = domain.split('.')  # 'example..com' → ['example', '', 'com']
```
دامنه‌هایی مثل `user@example..com` باید رد شوند اما ممکن است از بین بخش‌های بررسی بگذرند.

**راه حل:**
```python
# بررسی نقطه‌های متوالی قبل از split
if '..' in domain:
    errors.append('domain نمی‌تواند نقطه‌های متوالی داشته باشد')
    return errors
```

### باگ در `_sanitize_input`:
```python
# مشکل: rfind ممکن است آخرین @ را پیدا کند
at_index = sanitized.rfind('@')
```
اگر در local part کاراکتر @ وجود داشته باشد (در quoted string)، این کد اشتباه عمل می‌کند:
- `"user@internal"@example.com` به اشتباه split می‌شود

**راه حل:** در `_split_email` باید quoted string را در نظر بگیری:
```python
def _split_email(self, email: str) -> Optional[tuple[str, str]]:
    # اگر با " شروع شود، @ بعد از " بسته باید پیدا شود
    if email.startswith('"'):
        quote_end = email.find('"', 1)
        if quote_end != -1:
            at_index = email.find('@', quote_end)
            if at_index != -1:
                return (email[:at_index], email[at_index + 1:])
    
    at_index = email.rfind('@')
    # ...
```

## 2. مشکلات امنیتی

### ReDoS Vulnerability:
```python
valid_chars_pattern = re.compile(r'^[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~.-]+$')
```
این regex امن است، اما در `_validate_quoted_string` یک حلقه دستی وجود دارد که می‌تواند با ورودی‌های بزرگ کُند شود.

**راه حل:** محدود کردن طول قبل از پردازش:
```python
def _validate_quoted_string(self, local: str) -> bool:
    if len(local) > 100:  # حد معقول
        return False
    # ...
```

### Domain Confusion Attack:
```python
sanitized = f"{local}@{domain}"
```
بهتر است IDN/Punycode را هم بررسی کنی. دامنه‌هایی مثل `аррӏе.com` (با حروف سیریلیک) می‌توانند گمراه‌کننده باشند.

## 3. مشکلات Performance

### مشکل: هر بار validator ساخته می‌شود
```python
def validate_email(email: str, options: Optional[ValidationOptions] = None):
    validator = EmailValidator(options)  # ایجاد جدید در هر فراخوانی
    return validator.validate(email)
```

**بهبود:**
```python
# یک instance سراسری برای استفاده مجدد
_default_validator = EmailValidator()

def validate_email(email: str, options: Optional[ValidationOptions] = None):
    if options is None:
        return _default_validator.validate(email)
    return EmailValidator(options).validate(email)
```

### Regex Compilation:
```python
def _validate_local_part(self, local: str):
    valid_chars_pattern = re.compile(...)  # در هر فراخوانی compile می‌شود
```

**بهبود:**
```python
class EmailValidator:
    _LOCAL_PATTERN = re.compile(r'^[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~.-]+$')
    _DOMAIN_LABEL_PATTERN = re.compile(r'^[a-z0-9-]+$')
    
    def _validate_local_part(self, local: str):
        if not self._LOCAL_PATTERN.match(local):
            errors.append('...')
```

## 4. نقض Best Practices

### Type Hints:
```python
def _split_email(self, email: str) -> Optional[tuple[str, str]]:
```
در Python 3.9+ باید از `tuple` استفاده کنی، نه `tuple`:
```python
from typing import Optional, Tuple  # یا typing.Tuple

def _split_email(self, email: str) -> Optional[Tuple[str, str]]:
```

### Magic Numbers:
```python
if any(ord(c) < 32 for c in sanitized):  # 32 چیست؟
```

**بهتر:**
```python
ASCII_CONTROL_THRESHOLD = 32

if any(ord(c) < ASCII_CONTROL_THRESHOLD for c in sanitized):
```

### Hardcoded Domain List:
```python
DISPOSABLE_DOMAINS: Set[str] = {
    'tempmail.com',
    # ...
}
```
این لیست خیلی محدود است و سریع منسوخ می‌شود.

**پیشنهاد:** از یک فایل خارجی یا API استفاده کن:
```python
def __init__(self, options: Optional[ValidationOptions] = None,
             disposable_domains: Optional[Set[str]] = None):
    self.options = options or ValidationOptions()
    self.disposable_domains = disposable_domains or self.DISPOSABLE_DOMAINS
```

## 5. کد تکراری

### بررسی‌های طول:
```python
if len(local) > self.MAX_LOCAL_LENGTH:
    errors.append(f'طول local part بیش از حد مجاز است...')

if len(domain) > self.MAX_DOMAIN_LENGTH:
    errors.append(f'طول domain بیش از حد مجاز است...')
```

**Refactor:**
```python
def _check_length(self, value: str, max_len: int, name: str) -> Optional[str]:
    if len(value) > max_len:
        return f'طول {name} بیش از حد مجاز است (حداکثر {max_len})'
    return None

# استفاده:
if error := self._check_length(local, self.MAX_LOCAL_LENGTH, 'local part'):
    errors.append(error)
```

## سایر نکات

### Missing: DNS Validation
برای اعتبارسنجی واقعی، بررسی MX record هم لازم است:
```python
import dns.resolver

def _check_mx_records(self, domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False
```

### Normalization:
برای consistency، local part را هم normalize کن (اگر case-insensitive باشد):
```python
if self.options.normalize_local:
    local = local.lower()
```

---

## خلاصه اولویت‌ها:
1. **بالا**: رفع باگ split با quoted strings
2. **بالا**: ReDoS protection با محدود کردن طول
3. **متوسط**: بهینه‌سازی regex compilation
4. **متوسط**: بهبود مدیریت disposable domains
5. **پایین**: refactor کردن تکرارها

کلیت کد خوب است و RFC-aware هست، فقط نیاز به تقویت در edge cases دارد.

## 4. Final Improved Code

```python
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import ipaddress


@dataclass
class ValidationResult:
    """نتیجه اعتبارسنجی ایمیل
    
    Attributes:
        is_valid: آیا ایمیل معتبر است
        errors: لیست خطاها
        warnings: لیست هشدارها (اختیاری)
        metadata: اطلاعات اضافی درباره ایمیل (اختیاری)
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, str]] = None


@dataclass
class ValidationOptions:
    """تنظیمات اعتبارسنجی ایمیل
    
    Attributes:
        allow_disposable: اجازه به ایمیل‌های موقت
        allow_subaddressing: اجازه به plus addressing (user+tag@domain)
        max_length: حداکثر طول ایمیل
        strict_mode: حالت سخت‌گیرانه (نیاز به TLD)
    """
    allow_disposable: bool = False
    allow_subaddressing: bool = True
    max_length: int = 320  # 64 + @ + 255
    strict_mode: bool = True


class EmailValidator:
    """کلاس اعتبارسنجی ایمیل
    
    این کلاس بر اساس RFC 5322 و RFC 5321 ایمیل‌ها را اعتبارسنجی می‌کند.
    """
    
    MAX_LOCAL_LENGTH = 64
    MAX_DOMAIN_LENGTH = 255
    MAX_DOMAIN_LABEL_LENGTH = 63
    MAX_QUOTED_STRING_LENGTH = 100
    ASCII_CONTROL_THRESHOLD = 32
    
    _LOCAL_PATTERN = re.compile(r'^[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~.-]+$')
    _DOMAIN_LABEL_PATTERN = re.compile(r'^[a-z0-9-]+$')
    
    DISPOSABLE_DOMAINS: Set[str] = {
        'tempmail.com',
        'throwaway.email',
        '10minutemail.com',
        'guerrillamail.com',
        'mailinator.com',
    }
    
    def __init__(
        self,
        options: Optional[ValidationOptions] = None,
        disposable_domains: Optional[Set[str]] = None
    ) -> None:
        """مقداردهی اولیه validator
        
        Args:
            options: تنظیمات اعتبارسنجی (پیش‌فرض: None)
            disposable_domains: لیست سفارشی دامنه‌های موقت (پیش‌فرض: None)
        """
        self.options = options or ValidationOptions()
        self.disposable_domains = disposable_domains or self.DISPOSABLE_DOMAINS
    
    def validate(self, email: str) -> ValidationResult:
        """اعتبارسنجی ایمیل
        
        Args:
            email: آدرس ایمیل برای بررسی
            
        Returns:
            ValidationResult: نتیجه اعتبارسنجی شامل وضعیت، خطاها و هشدارها
        """
        errors: List[str] = []
        warnings: List[str] = []
        
        # ۱. پاکسازی ورودی
        try:
            sanitized = self._sanitize_input(email)
        except ValueError as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors)
        
        # ۲. بررسی طول
        if error := self._check_length(sanitized, self.options.max_length, 'ایمیل'):
            errors.append(error)
            return ValidationResult(is_valid=False, errors=errors)
        
        # ۳. جداسازی local و domain
        parts = self._split_email(sanitized)
        if not parts:
            errors.append('فرمت ایمیل نامعتبر است')
            return ValidationResult(is_valid=False, errors=errors)
        
        local_part, domain = parts
        
        # ۴. اعتبارسنجی local part
        local_errors = self._validate_local_part(local_part)
        errors.extend(local_errors)
        
        # ۵. اعتبارسنجی domain
        domain_errors = self._validate_domain(domain)
        errors.extend(domain_errors)
        
        # ۶. بررسی‌های اضافی
        if not self.options.allow_disposable and self._check_disposable(domain):
            warnings.append('ایمیل موقت شناسایی شد')
        
        # ۷. بررسی subaddressing
        if not self.options.allow_subaddressing and '+' in local_part:
            warnings.append('استفاده از plus addressing (+) شناسایی شد')
        
        # ساخت نتیجه
        is_valid = len(errors) == 0
        metadata = None
        if is_valid:
            metadata = {
                'local_part': local_part,
                'domain': domain,
            }
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings if warnings else [],
            metadata=metadata
        )
    
    def _sanitize_input(self, email: str) -> str:
        """پاکسازی و نرمال‌سازی ورودی
        
        Args:
            email: ایمیل خام
            
        Returns:
            str: ایمیل پاک‌شده
            
        Raises:
            ValueError: اگر ایمیل حاوی کاراکترهای غیرمجاز باشد
        """
        sanitized = email.strip()
        
        if any(ord(c) < self.ASCII_CONTROL_THRESHOLD for c in sanitized) or '\x00' in sanitized:
            raise ValueError('ایمیل حاوی کاراکترهای غیرمجاز است')
        
        if sanitized.count('@') != 1:
            raise ValueError('ایمیل باید دقیقاً یک @ داشته باشد')
        
        return sanitized
    
    def _split_email(self, email: str) -> Optional[Tuple[str, str]]:
        """جداسازی local part و domain
        
        Args:
            email: آدرس ایمیل
            
        Returns:
            Optional[Tuple[str, str]]: تاپل (local, domain) یا None در صورت خطا
        """
        if email.startswith('"'):
            quote_end = email.find('"', 1)
            if quote_end != -1:
                at_index = email.find('@', quote_end)
                if at_index != -1 and at_index > 0 and at_index < len(email) - 1:
                    local = email[:at_index]
                    domain = email[at_index + 1:].lower()
                    return (local, domain)
            return None
        
        at_index = email.rfind('@')
        
        if at_index == -1 or at_index == 0 or at_index == len(email) - 1:
            return None
        
        local = email[:at_index]
        domain = email[at_index + 1:].lower()
        
        return (local, domain)
    
    def _check_length(self, value: str, max_len: int, name: str) -> Optional[str]:
        """بررسی طول یک مقدار
        
        Args:
            value: مقدار برای بررسی
            max_len: حداکثر طول مجاز
            name: نام فیلد برای پیام خطا
            
        Returns:
            Optional[str]: پیام خطا یا None
        """
        if len(value) > max_len:
            return f'طول {name} بیش از حد مجاز است (حداکثر {max_len} کاراکتر)'
        return None
    
    def _validate_local_part(self, local: str) -> List[str]:
        """اعتبارسنجی local part
        
        Args:
            local: قسمت local از ایمیل (قبل از @)
            
        Returns:
            List[str]: لیست خطاها
        """
        errors: List[str] = []
        
        if len(local) == 0:
            errors.append('local part نمی‌تواند خالی باشد')
            return errors
        
        if error := self._check_length(local, self.MAX_LOCAL_LENGTH, 'local part'):
            errors.append(error)
            return errors
        
        if local.startswith('"') and local.endswith('"'):
            if not self._validate_quoted_string(local):
                errors.append('quoted string نامعتبر است')
            return errors
        
        if '..' in local:
            errors.append('local part نمی‌تواند نقطه‌های متوالی داشته باشد')
        
        if local.startswith('.') or local.endswith('.'):
            errors.append('local part نمی‌تواند با نقطه شروع یا پایان یابد')
        
        if not self._LOCAL_PATTERN.match(local):
            errors.append('local part حاوی کاراکترهای غیرمجاز است')
        
        return errors
    
    def _validate_quoted_string(self, local: str) -> bool:
        """اعتبارسنجی quoted string
        
        Args:
            local: local part به صورت quoted
            
        Returns:
            bool: آیا معتبر است
        """
        if len(local) > self.MAX_QUOTED_STRING_LENGTH:
            return False
        
        content = local[1:-1]
        
        if len(content) == 0:
            return False
        
        i = 0
        while i < len(content):
            if content[i] == '\\':
                if i + 1 >= len(content):
                    return False
                i += 2
            else:
                i += 1
        
        return True
    
    def _validate_domain(self, domain: str) -> List[str]:
        """اعتبارسنجی domain
        
        Args:
            domain: قسمت domain از ایمیل (بعد از @)
            
        Returns:
            List[str]: لیست خطاها
        """
        errors: List[str] = []
        
        if len(domain) == 0:
            errors.append('domain نمی‌تواند خالی باشد')
            return errors
        
        if error := self._check_length(domain, self.MAX_DOMAIN_LENGTH, 'domain'):
            errors.append(error)
            return errors
        
        if domain.startswith('[') and domain.endswith(']'):
            if not self._validate_ip_literal(domain):
                errors.append('IP literal نامعتبر است')
            return errors
        
        if '..' in domain:
            errors.append('domain نمی‌تواند نقطه‌های متوالی داشته باشد')
            return errors
        
        labels = domain.split('.')
        
        if self.options.strict_mode and len(labels) < 2:
            errors.append('domain باید شامل TLD باشد')
        
        for label in labels:
            if len(label) == 0:
                errors.append('domain label نمی‌تواند خالی باشد')
                continue
            
            if error := self._check_length(label, self.MAX_DOMAIN_LABEL_LENGTH, 'domain label'):
                errors.append(error)
                continue
            
            if label.startswith('-') or label.endswith('-'):
                errors.append('domain label نمی‌تواند با - شروع یا پایان یابد')
            
            if not self._DOMAIN_LABEL_PATTERN.match(label):
                errors.append('domain label حاوی کاراکترهای غیرمجاز است')
        
        return errors
    
    def _validate_ip_literal(self, domain: str) -> bool:
        """اعتبارسنجی IP literal
        
        Args:
            domain: domain به صورت [IP]
            
        Returns:
            bool: آیا معتبر است
        """
        ip_str = domain[1:-1]
        
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    def _check_disposable(self, domain: str) -> bool:
        """بررسی اینکه domain جزو ایمیل‌های موقت است یا نه
        
        Args:
            domain: دامنه برای بررسی
            
        Returns:
            bool: آیا موقت است
        """
        return domain in self.disposable_domains


_default_validator = EmailValidator()


def validate_email(
    email: str,
    options: Optional[ValidationOptions] = None
) -> ValidationResult:
    """تابع helper برای اعتبارسنجی سریع ایمیل
    
    Args:
        email: آدرس ایمیل برای بررسی
        options: تنظیمات اعتبارسنجی (اختیاری)
        
    Returns:
        ValidationResult: نتیجه اعتبارسنجی
        
    Example:
        >>> result = validate_email('user@example.com')
        >>> if result.is_valid:
        ...     print(f"ایمیل معتبر است: {result.metadata}")
        ... else:
        ...     print(f"خطاها: {result.errors}")
    """
    if options is None:
        return _default_validator.validate(email)
    return EmailValidator(options).validate(email)
```
