"""Quick gateway test."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Reset singleton
from core.llm_gateway import gateway as gw
gw._gateway = None
gw.LLMGateway._instance = None

from core.llm_gateway import request, request_structured, request_embedding

print('=' * 50)
print('LLM Gateway Quick Test')
print('=' * 50)

# Test 1
print('\n1. Basic request...')
r = request(agent='Test', task_id='T1', prompt='What is 2+2? Reply with just the number.', config={'max_tokens': 50})
status = 'PASS' if r.success else 'FAIL'
content = (r.content or '').strip() if r.success else r.error
print(f'   [{status}] Content: {content}')

# Test 2
print('\n2. Structured request...')
r = request_structured(agent='Architect', task_id='T2', prompt='List 2 colors', schema={'colors': []})
status = 'PASS' if r.success else 'FAIL'
print(f'   [{status}] JSON: {r.parsed_json if r.success else r.error}')

# Test 3
print('\n3. Embedding request...')
r = request_embedding(agent='Knowledge', task_id='T3', texts='hello world')
status = 'PASS' if r.success else 'FAIL'
dims = r.metadata.get('dimensions', 0) if r.success else 0
print(f'   [{status}] Dimensions: {dims}')

# Test 4
print('\n4. Unauthorized agent blocked...')
r = request(agent='BadAgent', task_id='T4', prompt='test')
status = 'PASS' if (not r.success and r.error_code == 'POLICY_DENIED') else 'FAIL'
print(f'   [{status}] Correctly blocked: {not r.success}')

# Test 5
print('\n5. Budget tracking...')
from core.llm_gateway.gateway import _get_gateway
g = _get_gateway()
b = g.get_budget_status()
status = 'PASS' if b['within_budget'] else 'FAIL'
print(f'   [{status}] Within budget: {b["within_budget"]}')

print('\n' + '=' * 50)
print('Gateway tests complete!')
print('=' * 50)
