import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)

def set_ta(tid, val):
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
    }""", [tid, val])

ans = {
 '123:_txtArea': "I keep resources consistent and names predictable, use the right HTTP verbs and status codes, and keep responses structured and machine-readable. I document the contract up front with the team, keep payloads focused on what the consumer actually needs, and version things early so the API can evolve without breaking clients. In practice that means clear error formats, sane pagination, and idempotent writes for anything that gets retried.",
 '127:_txtArea': "Most of my career has been in virtualized and cloud environments — I deploy and debug applications on AWS and work day to day with VMs and containers in shared development setups. I have not done hands-on vSphere administration, but I understand the core concepts (guests, clusters, resource orchestration) and I pick up the tooling quickly when a project needs it.",
 '131:_txtArea': "Spring Boot is my primary framework — I have built and maintained REST services, data access layers, and integration modules on top of it. I am comfortable with JPA and Hibernate for persistence, PostgreSQL for the database layer, Maven for builds, and Git for version control, plus JUnit and REST-level testing for validation.",
 '135:_txtArea': "At Verizon I integrated backend services with RESTful and API-based enterprise systems, including orchestrating provisioning workflows that span multiple downstream services. I handled the request and response contracts, retries and idempotency, and basic monitoring for those integrations, running in AWS. I would bring the same approach to managing and orchestrating cloud APIs.",
 '139:_txtArea': "AWS — that is where I have done the most work, including deployment, troubleshooting, and integration of backend services in AWS environments.",
}
for k, v in ans.items():
    print(k, ':', set_ta(k, v))
b.close()
