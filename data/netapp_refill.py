import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)

def set_input(id, val):
    return page.evaluate("""(a) => {
      const e = document.getElementById(a[0]);
      if (!e) return 'no el';
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      e.blur();
      return 'ok';
    }""", [id, val])

def set_ta(id, val):
    return page.evaluate("""(a) => {
      const e = document.getElementById(a[0]);
      if (!e) return 'no el';
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      e.blur();
      return 'ok';
    }""", [id, val])

# --- text fields
texts = {
    '411:_txtFld': 'Almond Willow CV',
    '419:_txtFld': 'Collierville',
    '430:_txtFld': '38017',
    '510:_txtFld': 'Polaris',
    '514:_txtFld': 'Senior Software Engineer',
    '522:_txtFld': 'Christian Brothers University',
    '526:_txtFld': 'Memphis',
    '530:_txtFld': 'Tennessee',
    '463:_txtFld': 'Yes',
}
for k, v in texts.items():
    print(k, set_input(k, v))
time.sleep(1)

# --- textareas
ans = {
 '443:_txtArea': "I keep resources consistent and names predictable, use the right HTTP verbs and status codes, and keep responses structured and machine-readable. I document the contract up front with the team, keep payloads focused on what the consumer actually needs, and version things early so the API can evolve without breaking clients. In practice that means clear error formats, sane pagination, and idempotent writes for anything that gets retried.",
 '447:_txtArea': "Most of my career has been in virtualized and cloud environments — I deploy and debug applications on AWS and work day to day with VMs and containers in shared development setups. I have not done hands-on vSphere administration, but I understand the core concepts (guests, clusters, resource orchestration) and I pick up the tooling quickly when a project needs it.",
 '451:_txtArea': "Spring Boot is my primary framework — I have built and maintained REST services, data access layers, and integration modules on top of it. I am comfortable with JPA and Hibernate for persistence, PostgreSQL for the database layer, Maven for builds, and Git for version control, plus JUnit and REST-level testing for validation.",
 '455:_txtArea': "At Verizon I integrated backend services with RESTful and API-based enterprise systems, including orchestrating provisioning workflows that span multiple downstream services. I handled the request and response contracts, retries and idempotency, and basic monitoring for those integrations, running in AWS. I would bring the same approach to managing and orchestrating cloud APIs.",
 '459:_txtArea': "AWS — that is where I have done the most work, including deployment, troubleshooting, and integration of backend services in AWS environments.",
}
for k, v in ans.items():
    print(k, set_ta(k, v))
time.sleep(1)

# --- radio groups: identify question text first
rad = page.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('.radioGroup').forEach(g => {
    let q = '';
    let node = g;
    for (let i = 0; i < 8 && node; i++) {
      node = node.parentElement;
      if (!node) break;
      const lab = node.querySelector('label');
      if (lab && lab.innerText && lab.innerText.length > 10) { q = lab.innerText.replace(/\n+/g, ' ').trim().slice(0, 90); break; }
    }
    res.push({id: g.id, q});
  });
  return res;
}""")
print('RADIOS:', json.dumps(rad, indent=1))

# radio answers by question
def click_radio(gid, text):
    return page.evaluate(r"""(args) => {
      const g = document.getElementById(args[0]);
      if (!g) return 'no group';
      const labels = [...g.querySelectorAll('.radioLabel')];
      const hit = labels.find(l => l.innerText.trim() === args[1]);
      if (!hit) return 'no radio';
      const radio = hit.closest('.globalRadio').querySelector('[id*="_radio"]');
      radio.click();
      return 'clicked ' + args[1];
    }""", [gid, text])

time.sleep(1)
for r in rad:
    q = r['q'].lower()
    if 'relocate' in q or 'hybrid' in q or 'san jose' in q or 'bay area' in q:
        print(r['id'], '-> No :', click_radio(r['id'], 'No'))
    elif 'in office' in q or 'in-office' in q or 'days per week' in q or '3 days' in q:
        print(r['id'], '-> Yes :', click_radio(r['id'], 'Yes'))
    elif 'sponsorship' in q or 'visa' in q:
        print(r['id'], '-> Yes :', click_radio(r['id'], 'Yes'))
    else:
        print(r['id'], 'UNKNOWN Q:', r['q'])
b.close()
