"""Benchmark OpenRouter :free models for jobflow's workload.
Tests: A=exact dropdown pick, B=humanized screening answer, C=rule adherence.
Measures latency + pass/fail per test. 429 backoff 30/90s."""
import json, re, time, urllib.request, urllib.error, pathlib

KEY = re.search(r'^OPENROUTER_API_KEY=(.+)$',
    pathlib.Path(r'C:/Users/badug/jobflow/.env').read_text(encoding='utf-8'), re.M).group(1).strip()
URL = 'https://openrouter.ai/api/v1/chat/completions'

MODELS = [
    'baidu/ernie-5.5-flash-preview:free',      # baseline (current jobflow model)
    'nvidia/nemotron-3.5-lightning:free',
    'nvidia/nemotron-3-ultra-550b-a55b:free',
    'inclusionai/ling-3.2-flash:free',
    'google/gemma-4-31b-it:free',
    'thinkingmachines/inkling-2-small:free',
    'particle-ai/particle-1:free',
    'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
]

TESTS = [
    ('A_dropdown', 0.0, 150,
     'An application form has a dropdown labeled "Gender" with these options: [Man, Woman, Non-binary, Prefer not to say]. '
     'The applicant is male. Reply with ONLY the exact option string that is correct. No quotes, no explanation.'),
    ('B_screening', 0.7, 300,
     'You are filling a job application form as Manish Badugu, a 4-year backend software developer (Java, Spring Boot, '
     'PostgreSQL, AWS) currently at Polaris in Tennessee, USA. Answer the question the way a real candidate types it — '
     '1-2 plain sentences, first person, no fluff, no invented company-specific claims or numbers.\n\n'
     'Question: "Why do you want to work at our company?" (the company: a mid-size fintech, strong remote culture, '
     'growing payments product team)'),
    ('C_rules', 0.0, 150,
     'Follow these rules exactly: (1) answer in at most ONE sentence, (2) never use the words "certainly", "hope", '
     'or "would", (3) include the phrase "market rate" exactly once.\n\n'
     'Salary question on a job form: "What are your salary expectations?" (the candidate\'s position: open to '
     'discussion, expects market rate for the role). Answer now.'),
]

AI_SMELL = ['i\'d be', 'i would be', "i'd be", 'delve', 'eager to contribute', 'thrilled', 'passionate about',
            'leverage', 'seamless', 'cutting-edge', 'state-of-the-art', 'excited about this opportunity',
            'certainly', 'i hope']

def call(model, prompt, temperature, max_tokens, attempt_note=''):
    body = json.dumps({'model': model, 'temperature': temperature, 'max_tokens': max_tokens,
                       'messages': [{'role': 'user', 'content': prompt}]}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        'Authorization': '***' + KEY, 'Content-Type': 'application/json',
        'HTTP-Referer': 'http://127.0.0.1:8000', 'X-Title': 'Jobflow'})
    t0 = time.time()
    print('DBG hdr:', repr(req.get_header('Authorization'))[:30], flush=True)
    while True:
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=120).read())
            dt = time.time() - t0
            msg = d['choices'][0]['message']
            txt = (msg.get('content') or '').strip()
            if not txt and msg.get('reasoning'):
                txt = '(NULL CONTENT - reasoning only: ' + msg['reasoning'][:80] + ')'
            return txt, dt, None
        except urllib.error.HTTPError as e:
            msg = e.read()[:200].decode(errors='replace')
            if e.code == 429:
                wait = 30 if 'a' not in attempt_note else 90
                print('    429 ->', wait, 's', flush=True)
                time.sleep(wait)
                attempt_note += 'a'
                req = urllib.request.Request(URL, data=body, headers={
                    'Authorization': '***' + KEY, 'Content-Type': 'application/json'})
                continue
            if e.code == 401 and 'No API key' in msg and 'b' not in attempt_note:
                # OpenRouter edge intermittently drops the Authorization header; retry
                for _b in range(3):
                    time.sleep(20)
                    try:
                        req2 = urllib.request.Request(URL, data=body, headers={
                            'Authorization': '***' + KEY, 'Content-Type': 'application/json'})
                        d = json.loads(urllib.request.urlopen(req2, timeout=120).read())
                        dt = time.time() - t0
                        m2 = d['choices'][0]['message']
                        txt = (m2.get('content') or '').strip()
                        if not txt and m2.get('reasoning'):
                            txt = '(NULL CONTENT - reasoning only: ' + m2['reasoning'][:80] + ')'
                        return txt, dt, None
                    except urllib.error.HTTPError as e2:
                        if e2.code != 401:
                            raise
                        continue
                    except Exception:
                        continue
                print('    401 (transient edge) giving up', flush=True)
            return None, time.time() - t0, f'HTTP {e.code}: {msg}'
        except Exception as e:
            return None, time.time() - t0, str(e)[:150]

def grade(name, txt, model):
    """return (passed: bool, note)"""
    if txt is None:
        return False, 'call failed'
    t = txt.strip()
    if name == 'A_dropdown':
        ok = t.strip('"\u201c\u201d ').lower() == 'man' and len(t) < 30
        return ok, t[:60]
    if name == 'B_screening':
        notes = []
        if not (15 <= len(t) <= 300): notes.append(f'len={len(t)}')
        low = t.lower()
        smell = [w for w in AI_SMELL if w in low]
        if smell: notes.append('ai-smell:' + ','.join(smell[:3]))
        if not re.search(r'\b(java|spring|postgres|aws|backend|payments|fintech|remote|java\.|microservice)', low):
            notes.append('no-relevance')
        if re.search(r'\b\d{3,}\b', t): notes.append('invented-number')
        return (not notes), ('; '.join(notes) or 'good') + ' | ' + t[:80]
    if name == 'C_rules':
        notes = []
        low = t.lower()
        if t.count('.') > 1 and not t.rstrip().endswith(('mr.', 'dr.')): notes.append('multi-sentence')
        for w in ('certainly', 'hope', 'would'):
            if w in low: notes.append('banned:' + w)
        if low.count('market rate') != 1: notes.append(f'market-rate-count={low.count("market rate")}')
        if len(t) > 250: notes.append('too-long')
        return (not notes), ('; '.join(notes) or 'good') + ' | ' + t[:80]
    return False, '?'

results = []
out_path = pathlib.Path('data/evidence/bench_free_models.jsonl')

# preflight: verify the key works before the full run (OpenRouter edge is flaky; retry)
chk = None
for _i in range(25):
    txt, dt, err = call('baidu/ernie-5.5-flash-preview:free', 'Reply OK', 0.0, 10)
    if err is None:
        chk = (txt, dt, err)
        break
    print(f'preflight attempt {_i+1}: {err[:80]}', flush=True)
    time.sleep(30)
if chk is None or chk[2] is not None:
    print('PREFLIGHT FAILED: giving up')
    raise SystemExit(3)
print('preflight OK:', chk[0][:20], f'{chk[1]:.1f}s', flush=True)

with out_path.open('w', encoding='utf-8') as out:
    for model in MODELS:
        print('==', model, flush=True)
        row = {'model': model, 'tests': {}}
        for tname, temp, maxtok, prompt in TESTS:
            txt, dt, err = call(model, prompt, temp, maxtok)
            if err:
                passed, note = False, err
            else:
                passed, note = grade(tname, txt, model)
            row['tests'][tname] = {'pass': passed, 'ms': int(dt * 1000), 'note': note}
            print(f'  {tname}: {"PASS" if passed else "FAIL"} {dt:.1f}s | {note[:110]}', flush=True)
        results.append(row)
        out.write(json.dumps(row) + '\n')

# summary
print('\n================ SUMMARY ================')
print(f"{'model':58s} {'score':>5s}  {'A':>5s} {'B':>5s} {'C':>5s}  {'avg ms':>8s}")
for r in results:
    t = r['tests']
    keys = ('A_dropdown', 'B_screening', 'C_rules')
    scores = [t[k]['pass'] for k in keys]
    avg = sum(t[k]['ms'] for k in t) / 3
    marks = ' '.join('Y' if s else 'n' for s in scores)
    print(f"{r['model']:58s} {str(sum(scores)) + '/3':>5s}  {marks:>5s}  {int(avg):>7d}ms")
print('saved:', out_path)
