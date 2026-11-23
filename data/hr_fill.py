import time, json, glob
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "highroller-careers.com" in p.url)

def fill(name, text):
    page.evaluate(
        """(a) => {
          const e = document.querySelector('input[name="' + a.n + '"]');
          if (!e) throw new Error("missing " + a.n);
          e.scrollIntoView({block: "center"});
          e.focus();
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
          setter.call(e, a.v);
          e.dispatchEvent(new Event("input", {bubbles: true}));
          e.dispatchEvent(new Event("change", {bubbles: true}));
        }""",
        {"n": name, "v": text},
    )
    time.sleep(0.3)

fill("candidate.name", "Manish Badugu")
fill("candidate.email", "badugu.m7@gmail.com")
fill("candidate.phone", "+1 940-843-6058")
fill("candidate.openQuestionAnswers.7685170.content", "Open to discussion - market rate")
fill("candidate.openQuestionAnswers.7685171.content", "1 month")

cv = glob.glob(r"C:/Users/badug/jobflow/data/exports/highroller/*.pdf")[0]
cv_el = page.locator('input[name="candidate.cv"]')
cv_el.set_input_files(cv)
time.sleep(4)

# radios: hybrid=Yes, malta work permit=No
page.evaluate(
    """() => {
      document.querySelector('input[name="candidate.openQuestionAnswers.7685172.flag"][value="true"]').click();
      document.querySelector('input[name="candidate.openQuestionAnswers.7685173.flag"][value="false"]').click();
    }"""
)
time.sleep(0.5)

vals = page.evaluate(
    """() => {
      const g = n => { const e = document.querySelector('input[name="' + n + '"]'); return e ? e.value : "?"; };
      return {
        name: g("candidate.name"), email: g("candidate.email"), phone: g("candidate.phone"),
        salary: g("candidate.openQuestionAnswers.7685170.content"), notice: g("candidate.openQuestionAnswers.7685171.content"),
        hybrid: document.querySelector('input[name="candidate.openQuestionAnswers.7685172.flag"]:checked') ? document.querySelector('input[name="candidate.openQuestionAnswers.7685172.flag"]:checked').value : "none",
        malta: document.querySelector('input[name="candidate.openQuestionAnswers.7685173.flag"]:checked') ? document.querySelector('input[name="candidate.openQuestionAnswers.7685173.flag"]:checked').value : "none",
      };
    }"""
)
print(json.dumps(vals, indent=1))
b.close()
