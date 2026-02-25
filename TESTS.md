# Voice Chat v2 - Test Suite

Comprehensive test coverage for both backend and frontend.

## 📊 Test Coverage

### Backend Tests (pytest)
- **test_weather.py** - Weather service with location parsing
- **test_memory.py** - Redis conversation memory
- **test_whisper.py** - OpenAI Whisper transcription
- **test_gpt.py** - GPT chat completion
- **test_tts.py** - Text-to-speech generation
- **test_voice_endpoint.py** - API endpoint integration

### Frontend Tests (Vitest + React Testing Library)
- **useAudio.test.ts** - Web Audio API hook
- **VoiceOrb.test.tsx** - Recording button component
- **AudioVisualizer.test.tsx** - Audio visualization
- **api.test.ts** - API client
- **ChatInterface.test.tsx** - Chat display component

## 🚀 Running Tests

### Backend Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_weather.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Install dependencies (if not done)
npm install

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run with coverage
npm run coverage

# Run in watch mode
npm test -- --watch
```

## 📝 Test Examples

### Backend: Testing Weather Service

```python
# Test location parsing
@pytest.mark.parametrize("query,expected", [
    ("weather in Mumbai", "Mumbai"),
    ("What's the weather in Delhi?", "Delhi"),
])
def test_parse_location(weather_service, query, expected):
    result = weather_service._parse_location(query)
    assert result == expected
```

### Frontend: Testing Component

```typescript
// Test VoiceOrb click
it('calls onClick when clicked', () => {
  const handleClick = vi.fn()
  render(<VoiceOrb isRecording={false} audioLevel={0} onClick={handleClick} />)
  
  fireEvent.click(screen.getByRole('button'))
  expect(handleClick).toHaveBeenCalledTimes(1)
})
```

## 🎯 What Tests Cover

### Backend
- ✅ Service logic (weather, memory, whisper, gpt, tts)
- ✅ API endpoints (voice chat, skills, health)
- ✅ Error handling (timeouts, API errors)
- ✅ Mocking external APIs (OpenAI, ElevenLabs, Open-Meteo)
- ✅ Redis operations

### Frontend
- ✅ Hook behavior (useAudio)
- ✅ Component rendering and interaction
- ✅ API client requests
- ✅ User events (clicks, inputs)
- ✅ Loading and error states

## 🔧 Test Configuration

### Backend (pytest.ini)
- Async test support
- Auto-discovery of test files
- Short traceback format

### Frontend (vitest.config.ts)
- jsdom environment
- React Testing Library integration
- Coverage reporting
- Global test utilities

## 🛠️ Mocking Strategy

### Backend
- **HTTP requests** - Mocked with `httpx.AsyncClient` patches
- **Redis** - Mocked with `unittest.mock.Mock`
- **Environment** - Fixtures provide test settings

### Frontend
- **fetch/API** - Mocked with `global.fetch`
- **MediaRecorder** - Mocked class implementation
- **navigator.mediaDevices** - Mocked getUserMedia

## 📈 Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Backend Services | 90% | 🔄 |
| API Endpoints | 85% | 🔄 |
| Frontend Components | 80% | 🔄 |
| Hooks | 90% | 🔄 |

## 🐛 Debugging Tests

### Backend
```bash
# Run with PDB
pytest --pdb

# Stop on first failure
pytest -x

# Show local variables
pytest -l
```

### Frontend
```bash
# Debug specific test
npm test -- useAudio.test.ts

# Show console output
npm test -- --reporter=verbose
```

## ✅ Continuous Integration

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    
    - name: Test Backend
      run: |
        cd backend
        pip install -r requirements.txt
        pytest
    
    - name: Test Frontend
      run: |
        cd frontend
        npm install
        npm test
```

## 🎓 Writing New Tests

### Backend Pattern

```python
# 1. Create test file: tests/test_new_feature.py
# 2. Import and create test class
# 3. Use fixtures from conftest.py
# 4. Mock external dependencies
# 5. Test both success and error cases

class TestNewFeature:
    @pytest.fixture
    def service(self):
        return NewFeatureService()
    
    @pytest.mark.asyncio
    async def test_success_case(self, service):
        with patch('external.api') as mock:
            mock.return_value = {'success': True}
            result = await service.do_something()
            assert result == expected
```

### Frontend Pattern

```typescript
// 1. Create test file: Component.test.tsx
// 2. Import and setup
// 3. Render with test utilities
// 4. Query and interact
// 5. Assert on outcomes

it('does something', () => {
  render(<Component prop="value" />)
  
  // Query
  const button = screen.getByRole('button')
  
  // Interact
  fireEvent.click(button)
  
  // Assert
  expect(screen.getByText('Result')).toBeInTheDocument()
})
```

## 🤝 Contributing

When adding features:
1. Write tests FIRST (TDD)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Document edge cases

## 📄 License

Tests are part of the project and follow the same MIT license.
