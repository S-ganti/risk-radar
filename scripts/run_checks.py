"""Run every repository test suite without masking an earlier failure."""
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
commands=[['node','--test',*[str(p.relative_to(ROOT)) for p in sorted((ROOT/'tests').glob('*.test.js'))]],
 [sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'],
 [sys.executable,'tests/test_engine.py'],[sys.executable,'tests/test_mcp_servers.py'],
 [sys.executable,'scripts/validate.py']]
results=[];failed=False
for command in commands:
    result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
    failed|=result.returncode!=0
    results.append('## '+' '.join(command)+'\n\nExit: '+str(result.returncode)+'\n\n```text\n'+result.stdout+'\n```\n')
    print(('PASS' if result.returncode==0 else 'FAIL')+' '+' '.join(command))
(ROOT/'docs/TEST-RESULTS.md').write_text('# Test run\n\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+'\n'.join(results),encoding='utf-8')
sys.exit(1 if failed else 0)
