# API Integration Steering Document

## API Integration Philosophy & Standards

### Multi-Service Integration
- **Primary APIs**: Coinbase Advanced Trade, Google AI (Gemini), Google Cloud Storage
- **Error Handling**: Graceful degradation with fallback strategies
- **Rate Limiting**: Respect API limits with exponential backoff
- **Authentication**: Secure credential management and rotation support

### API Client Architecture

#### Coinbase Advanced Trade Integration
- **Library**: `coinbase-advanced-py` for official SDK support
- **Authentication**: EC private key with organization-scoped API keys
- **Rate Limits**: 10 requests/second with intelligent queuing
- **Error Recovery**: Automatic retry with exponential backoff

#### Google AI (Gemini) Integration
- **SDK**: Google AI SDK (`google-generativeai`), NOT Vertex AI SDK
- **Models**: `gemini-3-flash-preview` (primary), `gemini-3-pro-preview` (fallback)
- **Location**: `global` (required for preview models)
- **Authentication**: Service account with AI Platform permissions

### API Client Standards

#### Base Client Pattern
```python
class BaseAPIClient:
    """Base class for all API clients"""
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        
    def _make_request(self, method: str, url: str, **kwargs):
        """Make HTTP request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

#### Error Handling Standards
```python
class APIError(Exception):
    """Base API error class"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class RateLimitError(APIError):
    """Rate limit exceeded error"""
    pass

class AuthenticationError(APIError):
    """Authentication failed error"""
    pass
```

### Coinbase API Integration

#### Client Configuration
```python
from coinbase.rest import RESTClient

class CoinbaseClient:
    def __init__(self):
        self.api_key = config.COINBASE_API_KEY
        self.api_secret = config.COINBASE_API_SECRET
        
        # Validate credentials format
        if not self._validate_credentials():
            raise ValueError("Invalid Coinbase API credentials")
            
        self.client = RESTClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            base_url="https://api.coinbase.com"
        )
```

#### Rate Limiting Implementation
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests: int = 10, time_window: int = 1):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove old requests outside time window
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        # Wait if at rate limit
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.requests.append(now)
```

#### Trading Operations
```python
def create_market_order(self, product_id: str, side: str, amount: float) -> dict:
    """Create market order with comprehensive error handling"""
    try:
        self.rate_limiter.wait_if_needed()
        
        order_data = {
            "client_order_id": f"order_{int(time.time())}",
            "product_id": product_id,
            "side": side.upper(),
            "order_configuration": {
                "market_market_ioc": {
                    "quote_size" if side.upper() == "BUY" else "base_size": str(amount)
                }
            }
        }
        
        response = self.client.create_order(**order_data)
        return self._process_order_response(response)
        
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        raise APIError(f"Failed to create {side} order: {str(e)}")
```

### Google AI Integration

#### Client Configuration
```python
import google.generativeai as genai

class LLMAnalyzer:
    def __init__(self):
        # Configure Google AI SDK (NOT Vertex AI)
        api_key = os.getenv('GOOGLE_AI_API_KEY') or self._get_service_account_key()
        genai.configure(api_key=api_key)
        
        # Use preview models with global location
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
        self.fallback_model = genai.GenerativeModel('gemini-3-pro-preview')
```

#### AI Analysis with Fallback
```python
def analyze_market(self, market_data: dict, technical_indicators: dict) -> dict:
    """Analyze market with primary and fallback models"""
    try:
        # Try primary model first
        return self._analyze_with_model(self.model, market_data, technical_indicators)
    except Exception as e:
        logger.warning(f"Primary model failed: {e}, trying fallback")
        try:
            return self._analyze_with_model(self.fallback_model, market_data, technical_indicators)
        except Exception as fallback_error:
            logger.error(f"Both models failed: {fallback_error}")
            return self._generate_fallback_analysis()

def _generate_fallback_analysis(self) -> dict:
    """Generate safe fallback analysis when AI fails"""
    return {
        'decision': 'HOLD',
        'confidence': 0,
        'reasoning': 'AI analysis unavailable, defaulting to HOLD for safety',
        'risk_assessment': 'HIGH',
        'technical_indicators': {},
        'fallback_used': True
    }
```

### Google Cloud Storage Integration

#### Client Configuration
```python
from google.cloud import storage

class GCSBacktestSync:
    def __init__(self, bucket_name: str = None):
        self.client = storage.Client()
        self.bucket_name = bucket_name or f"{os.getenv('GOOGLE_CLOUD_PROJECT')}-backtest-data"
        
        try:
            self.bucket = self.client.bucket(self.bucket_name)
            # Test bucket access
            self.bucket.reload()
        except Exception as e:
            logger.error(f"GCS bucket access failed: {e}")
            raise
```

#### File Operations with Retry
```python
def upload_file(self, local_path: str, gcs_path: str, metadata: dict = None) -> bool:
    """Upload file to GCS with retry logic"""
    for attempt in range(3):
        try:
            blob = self.bucket.blob(gcs_path)
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
            
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded {local_path} to gs://{self.bucket_name}/{gcs_path}")
            return True
            
        except Exception as e:
            if attempt == 2:  # Last attempt
                logger.error(f"Failed to upload {local_path}: {e}")
                return False
            time.sleep(2 ** attempt)
    
    return False
```

### API Response Processing

#### Standardized Response Handling
```python
def process_api_response(response, expected_fields: list = None) -> dict:
    """Process API response with validation"""
    try:
        if hasattr(response, 'json'):
            data = response.json()
        else:
            data = response
        
        # Validate expected fields
        if expected_fields:
            missing_fields = [field for field in expected_fields if field not in data]
            if missing_fields:
                logger.warning(f"Missing expected fields: {missing_fields}")
        
        return data
        
    except Exception as e:
        logger.error(f"Failed to process API response: {e}")
        raise APIError(f"Invalid API response: {str(e)}")
```

#### Data Validation
```python
def validate_market_data(data: dict) -> bool:
    """Validate market data structure and values"""
    required_fields = ['price', 'volume', 'timestamp']
    
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate data types and ranges
    try:
        price = float(data['price'])
        volume = float(data['volume'])
        
        if price <= 0 or volume < 0:
            logger.error("Invalid price or volume values")
            return False
            
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid data types: {e}")
        return False
    
    return True
```

### Error Recovery Strategies

#### Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise APIError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

#### Graceful Degradation
```python
def get_market_data_with_fallback(self, product_id: str) -> dict:
    """Get market data with multiple fallback strategies"""
    
    # Try primary API
    try:
        return self.coinbase_client.get_product_ticker(product_id)
    except Exception as e:
        logger.warning(f"Primary API failed: {e}")
    
    # Try cached data
    try:
        cached_data = self.load_cached_market_data(product_id)
        if self.is_data_fresh(cached_data, max_age_minutes=5):
            logger.info("Using cached market data")
            return cached_data
    except Exception as e:
        logger.warning(f"Cached data unavailable: {e}")
    
    # Final fallback - return safe default
    logger.error("All market data sources failed, using safe defaults")
    return self.get_safe_default_data(product_id)
```

### API Monitoring & Alerting

#### Performance Monitoring
```python
class APIMonitor:
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_failed': 0,
            'response_times': [],
            'rate_limit_hits': 0
        }
    
    def record_request(self, duration: float, success: bool):
        """Record API request metrics"""
        self.metrics['requests_total'] += 1
        self.metrics['response_times'].append(duration)
        
        if not success:
            self.metrics['requests_failed'] += 1
        
        # Alert on high failure rate
        failure_rate = self.metrics['requests_failed'] / self.metrics['requests_total']
        if failure_rate > 0.1:  # 10% failure rate
            self.send_alert(f"High API failure rate: {failure_rate:.2%}")
```

#### Health Checks
```python
def check_api_health(self) -> dict:
    """Comprehensive API health check"""
    health_status = {}
    
    # Check Coinbase API
    try:
        self.coinbase_client.get_accounts()
        health_status['coinbase'] = 'healthy'
    except Exception as e:
        health_status['coinbase'] = f'unhealthy: {str(e)}'
    
    # Check Google AI API
    try:
        test_response = self.llm_analyzer.model.generate_content("test")
        health_status['google_ai'] = 'healthy'
    except Exception as e:
        health_status['google_ai'] = f'unhealthy: {str(e)}'
    
    # Check GCS API
    try:
        self.gcs_client.bucket(self.bucket_name).reload()
        health_status['gcs'] = 'healthy'
    except Exception as e:
        health_status['gcs'] = f'unhealthy: {str(e)}'
    
    return health_status
```

### Best Practices

#### Security
- **Never Log Credentials**: Sanitize logs to remove API keys and secrets
- **Credential Rotation**: Support for updating credentials without restart
- **Least Privilege**: Use minimal required permissions for service accounts
- **Secure Storage**: Store credentials in environment variables, not code

#### Performance
- **Connection Pooling**: Reuse HTTP connections for better performance
- **Caching**: Cache frequently accessed data with appropriate TTL
- **Async Operations**: Use async/await for non-blocking API calls where possible
- **Batch Operations**: Group multiple API calls when supported

#### Reliability
- **Idempotency**: Ensure operations can be safely retried
- **Timeout Handling**: Set appropriate timeouts for all API calls
- **Graceful Degradation**: Provide fallback behavior when APIs fail
- **Circuit Breakers**: Prevent cascade failures with circuit breaker pattern

This API integration framework ensures robust, secure, and maintainable external service integration.