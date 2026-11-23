import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(2)

JS_LI = r"""(a) => {
  const name = a[0], q = a[1];
  const ul = document.querySelector('[id="' + name + '_dropdown-results"]');
  if (!ul) return 'no ul';
  const lis = [...ul.querySelectorAll('li')];
  if (!lis.length) return 'no lis';
  let hit = lis.find(li => li.innerText.trim().toLowerCase() === q.toLowerCase());
  if (!hit) hit = lis.find(li => li.innerText.toLowerCase().includes(q.toLowerCase()));
  if (!hit) return 'no match';
  hit.click();
  return 'clicked: ' + hit.innerText.trim();
}"""
JS_FOCUS = r"""(n) => {
  const i = document.querySelector('[id="' + n + '_icimsDropdown_ctnr"] input.dropdown-search');
  if (!i) return 'no input';
  i.focus();
  return 'focused';
}"""
f.evaluate(r"""() => { const a = document.activeElement; if (a && a.blur) a.blur(); }""")
time.sleep(0.4)
f.locator('a[id="-1_CandProfileFields.Major_icimsDropdown"]').first.click()
time.sleep(1.0)
print('focus:', f.evaluate(JS_FOCUS, '-1_CandProfileFields.Major'))
time.sleep(0.5)
page.keyboard.type('Computer Info', delay=60)
time.sleep(3.0)
print('major:', f.evaluate(JS_LI, ['-1_CandProfileFields.Major', 'Computer Info. Sys.']))
time.sleep(1.0)

# full final verification dump
dump = f.evaluate(r"""() => {
  const res = {};
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  const s = (n) => { const e = document.querySelector("select[name='" + n + "']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; };
  res.first = t('PersonProfileFields.FirstName');
  res.last = t('PersonProfileFields.LastName');
  res.email = t('PersonProfileFields.Email');
  res.source = s('rcf3048');
  res.source9 = s('rcf3049');
  res.phone = t('-1_PersonProfileFields.PhoneNumber');
  res.consent = s('rcf3553');
  res.street = t('-1_PersonProfileFields.AddressStreet1');
  res.city = t('-1_PersonProfileFields.AddressCity');
  res.zip = t('-1_PersonProfileFields.AddressZip');
  res.country = s('-1_PersonProfileFields.AddressCountry');
  res.state = s('-1_PersonProfileFields.AddressState');
  res.login = t('PersonProfileFields.Login');
  res.pw = t('PersonProfileFields.Password') ? '***' : null;
  res.pwc = t('PersonProfileFields.Password_Confirm') ? '***' : null;
  const fi = document.querySelector("input[type='file']");
  res.resume = fi && fi.files && fi.files.length ? fi.files[0].name : null;
  res.school = s('-1_CandProfileFields.School');
  res.degree = s('-1_CandProfileFields.Degree');
  res.major = s('-1_CandProfileFields.Major');
  res.grad = s('-1_CandProfileFields.IsGraduated');
  return res;
}""")
print(json.dumps(dump, indent=1))
b.close()
