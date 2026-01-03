"""Validate the enhanced loop test prompt."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.command_trigger import trigger

output = trigger('full arcyn os loop test')

checks = [
    ('Persona confidence/assumptions', 'confidence' in output and 'assumptions' in output and 'missing_info' in output and 'risk_flags' in output),
    ('Architect decisions/rejected', 'decisions' in output and 'rejected_options' in output and 'architectural_constraints' in output),
    ('Forge F-1 (Builder)', 'STEP 3A: Forge F-1' in output),
    ('Forge F-2 (System Designer)', 'STEP 3B: Forge F-2' in output),
    ('Forge F-3 (Integrator)', 'STEP 3C: Forge F-3' in output),
    ('Knowledge embeddings/decay', 'embeddings' in output and 'decay' in output and 'reuse_score' in output),
    ('Evolution strategic critique', 'architectural_concerns' in output and 'scalability_limits' in output and 'maintenance_forecast' in output),
    ('Failure handling section', 'FAILURE HANDLING' in output),
    ('Persona failure path', 'On Persona Failure' in output),
    ('Builder failure path', 'On Builder (F-1) Failure' in output),
    ('Knowledge conflict path', 'On Knowledge Engine Conflict' in output),
]

print('Loop Test Validation:')
print('-' * 50)
for name, passed in checks:
    status = 'OK' if passed else 'MISSING'
    print(f'  [{status}] {name}')

all_passed = all(p for _, p in checks)
print('-' * 50)
if all_passed:
    print('Result: ALL CHECKS PASSED')
else:
    print('Result: SOME CHECKS FAILED')
