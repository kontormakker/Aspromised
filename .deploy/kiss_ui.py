from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
index = root / 'index.html'
app = root / 'app.js'
version = root / 'src' / 'version.js'
sw = root / 'sw.js'

s = index.read_text(encoding='utf-8')
# Idempotent: if the KISS UI is already present, only make sure version/cache are current.
if '3. Se forskellen' not in s:
    s=s.replace('.hero{display:grid;grid-template-columns:1.25fr .75fr;gap:24px;align-items:end;margin-bottom:26px}', '.hero{margin-bottom:26px}.hero.simple{max-width:820px}')
    s=s.replace('.privacy{background:linear-gradient(145deg,#10223a,#0c1728);border:1px solid #28405f;padding:17px;border-radius:16px;color:#c8d5e9;font-size:14px;line-height:1.5}', '.privacy-line{display:inline-flex;align-items:center;gap:7px;margin-top:14px!important;color:#aebed6!important;font-size:14px!important}.advanced{margin-top:16px;border:1px solid var(--line);border-radius:14px;background:#091525}.advanced>summary{cursor:pointer;padding:13px 15px;color:#c6d3e7;font-weight:700}.advanced-body{padding:0 15px 15px}.advanced .panel{box-shadow:none}.result-more{margin-top:12px}.result-more>summary{cursor:pointer;color:#9dbaff;font-size:13px}.how{margin-top:26px}.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.step{background:#0d1a2c;border:1px solid var(--line);border-radius:14px;padding:14px}.step strong{display:block;margin-bottom:4px}')
    s=s.replace('@media(max-width:800px){.hero,.grid2{grid-template-columns:1fr}', '@media(max-width:800px){.grid2{grid-template-columns:1fr}.steps{grid-template-columns:1fr}')
    start=s.index('  <nav>')
    res=s.index('  <section id="results"')
    new_top='''  <nav><div class="brand">AsPromised</div><a class="pill" style="text-decoration:none" href="#how">Sådan virker det</a></nav>
  <section class="hero simple">
    <h1>Fik du det, du blev lovet?</h1>
    <p>Upload det, du blev lovet, og det der skete. AsPromised viser forskellene.</p>
    <p class="privacy-line">🔒 Dine filer bliver på din enhed.</p>
  </section>

  <div class="grid2">
    <section class="panel"><h2>1. Det du blev lovet</h2><p class="sub">Fx tilbud, annonce, ordrebekræftelse eller besked</p><div class="drop" id="beforeDrop"><input id="beforeFiles" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md,.html,.htm,text/*,image/*,application/pdf"><p class="tiny">Vælg filer eller træk dem hertil</p></div><textarea id="beforeText" placeholder="Eller indsæt teksten her…"></textarea><div id="beforeList" class="files"></div></section>
    <section class="panel"><h2>2. Det der skete</h2><p class="sub">Fx faktura, levering, foto eller besked</p><div class="drop" id="afterDrop"><input id="afterFiles" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.md,.html,.htm,text/*,image/*,application/pdf"><p class="tiny">Vælg filer eller træk dem hertil</p></div><textarea id="afterText" placeholder="Eller indsæt teksten her…"></textarea><div id="afterList" class="files"></div></section>
  </div>

  <div class="toolbar"><button id="analyzeBtn" class="run">3. Se forskellen</button><button id="demoBtn" class="secondary">Prøv et eksempel</button><button id="clearBtn" class="ghost">Start forfra</button></div>
  <div class="statusbar"><span id="statusDot" class="dot"></span><span id="statusText">Klar.</span></div>

  <details class="advanced">
    <summary>Flere muligheder</summary>
    <div class="advanced-body">
      <label class="sub" for="caseTitle">Navn på sag</label><input id="caseTitle" type="text" value="Min sammenligning" autocomplete="off">
      <div class="toolbar"><button id="saveBtn" class="secondary" disabled>Gem på denne enhed</button><button id="exportCaseBtn" class="ghost" disabled>Eksportér sag</button><label class="ghost" style="border-radius:11px;padding:10px 14px;cursor:pointer">Importér sag<input id="importCaseInput" type="file" accept="application/json,.json" hidden></label></div>
      <section class="ai-box"><div class="ai-row"><div><strong>Bedre tekstforståelse (valgfri)</strong><div id="aiStatus" class="tiny">Slået fra. Den almindelige sammenligning virker uden.</div></div><button id="enableAi" class="secondary">Slå til</button></div><div class="progress"><span id="aiProgress"></span></div></section>
      <details style="margin-top:12px"><summary class="tiny" style="cursor:pointer">Fejlsøgning</summary><section class="panel device-check"><div class="section-title"><div><h2>Enhedstjek</h2></div><button id="deviceCheckBtn" class="ghost mini">Kør tjek</button></div><div id="deviceCheckResults" class="check-grid"><p class="tiny">Ikke kørt endnu.</p></div></section></details>
      <section class="panel" style="margin-top:14px"><div class="section-title"><div><h2>Gemte sager</h2></div><button id="refreshSavedBtn" class="ghost mini">Opdatér</button></div><div id="savedCases" style="margin-top:12px"></div></section>
    </div>
  </details>

'''
    s=s[:start]+new_top+s[res:]
    old='''  <section id="results" class="results"><div class="summary"><div class="metric"><strong id="metricMismatch">0</strong><span>mulige afvigelser</span></div><div class="metric"><strong id="metricSupported">0</strong><span>understøttet</span></div><div class="metric"><strong id="metricUnverified">0</strong><span>ikke verificeret</span></div><div class="metric"><strong id="metricEvidence">0</strong><span>beviser</span></div></div><section class="panel"><div class="ai-row"><div><h2 style="margin:0">Sammenligning af beviser</h2><p class="sub" style="margin:4px 0 0">Hvert fund peger tilbage på det materiale, du har givet AsPromised.</p></div><div class="toolbar" style="margin:0"><button id="copySummaryBtn" class="secondary">Kopiér resumé</button><button id="downloadHtmlBtn" class="secondary">HTML-rapport</button><button id="downloadJsonBtn" class="ghost">JSON-rapport</button></div></div><div id="findings"></div><p class="notice">AsPromised sammenligner kun det materiale, du har givet værktøjet. Det afgør ikke juridisk ansvar, beviser ikke hvad der skete uden for materialet og fastslår ikke ret til refundering eller erstatning.</p></section></section>'''
    new='''  <section id="results" class="results"><div class="summary"><div class="metric"><strong id="metricMismatch">0</strong><span>forskelle</span></div><div class="metric"><strong id="metricSupported">0</strong><span>stemmer overens</span></div><div class="metric"><strong id="metricUnverified">0</strong><span>mangler dokumentation</span></div><div class="metric"><strong id="metricEvidence">0</strong><span>materialer</span></div></div><section class="panel"><div class="section-title"><div><h2 style="margin:0">3. Forskellene</h2><p class="sub" style="margin:4px 0 0">Her er det, AsPromised fandt i dit materiale.</p></div><button id="copySummaryBtn" class="secondary">Kopiér resumé</button></div><div id="findings"></div><details class="result-more"><summary>Rapport og eksport</summary><div class="toolbar"><button id="downloadHtmlBtn" class="secondary">Gem rapport</button><button id="downloadJsonBtn" class="ghost">Gem data</button></div></details><p class="notice">AsPromised sammenligner dit materiale. Det er ikke juridisk rådgivning.</p></section></section>'''
    if old not in s:
        raise SystemExit('Expected results block not found')
    s=s.replace(old,new)
    s=s.replace('<h2>Typiske problemer AsPromised kan sammenligne</h2>\n    <p class="sub">Problemguiderne forklarer kun, hvordan du samler og sammenligner materialet — ikke hvad du juridisk har krav på.</p>', '<h2>Typiske situationer</h2>\n    <p class="sub">Se eksempler på, hvad du kan sammenligne.</p>')
    needle='  <section class="panel" style="margin-top:22px">\n    <h2>Typiske situationer</h2>'
    how='''  <section id="how" class="how"><h2>Sådan virker det</h2><div class="steps"><div class="step"><strong>1. Tilføj det lovede</strong><span class="tiny">Tilbud, annonce, besked eller andet.</span></div><div class="step"><strong>2. Tilføj det der skete</strong><span class="tiny">Faktura, levering, foto eller besked.</span></div><div class="step"><strong>3. Se forskellene</strong><span class="tiny">AsPromised sammenligner de to sider.</span></div></div></section>\n\n'''
    s=s.replace(needle,how+needle)
    s=re.sub(r'  <footer style="margin-top:28px;[\s\S]*?</footer>', '''  <footer style="margin-top:28px;padding:18px 0;border-top:1px solid var(--line);color:var(--muted);font-size:12px;line-height:1.6">\n    🔒 Dine filer bliver på din enhed. · <a style="color:#9dbaff" href="./privatliv/">Privatliv</a> · Feedback: <a id="contactLink" style="color:#9dbaff" href="#">contact not configured</a> · Ikke juridisk rådgivning.\n  </footer>''', s, count=1)
    index.write_text(s, encoding='utf-8')

    a=app.read_text(encoding='utf-8')
    repl={
      "const STATUS_DA={changed:'ændret',contradiction:'modstrid',supported:'understøttet',unverified:'ikke verificeret',review:'gennemgå'};":"const STATUS_DA={changed:'forskel',contradiction:'modstrid',supported:'stemmer',unverified:'mangler dokumentation',review:'tjek'};",
      "'No sufficiently similar outcome statement was found.':'Der blev ikke fundet et tilstrækkeligt lignende udsagn i resultatmaterialet.',":"'No sufficiently similar outcome statement was found.':'Der blev ikke fundet noget tilsvarende på den anden side.',",
      "'A matched statement contains a changed numeric value.':'Det matchede bevis indeholder en ændret talværdi.',":"'A matched statement contains a changed numeric value.':'Tallet er forskelligt.',",
      "'The wording is strongly aligned.':'Ordlyden stemmer tydeligt overens.',":"'The wording is strongly aligned.':'Det stemmer tydeligt overens.',",
      "'A related statement was found, but lexical evidence is not strong enough for a firm conclusion.':'Der blev fundet et relateret udsagn, men tekstmatchningen er ikke stærk nok til en fast konklusion.',":"'A related statement was found, but lexical evidence is not strong enough for a firm conclusion.':'Der er noget lignende, men ikke nok til at konkludere sikkert.',",
      "'No matching outcome evidence found.':'Der blev ikke fundet et matchende bevis for resultatet.',":"'No matching outcome evidence found.':'Der blev ikke fundet noget tilsvarende på den anden side.',",
      "'Matched evidence contains a changed numeric value.':'Det matchede bevis indeholder en ændret talværdi.',":"'Matched evidence contains a changed numeric value.':'Tallet er forskelligt.',",
      "'Outcome evidence closely matches the promise.':'Resultatmaterialet matcher det lovede tæt.',":"'Outcome evidence closely matches the promise.':'Det stemmer tæt overens.',",
      "'Related evidence found; semantic review is still required.':'Der blev fundet relateret materiale; semantisk gennemgang er stadig nødvendig.',":"'Related evidence found; semantic review is still required.':'Der er noget lignende, men det bør tjekkes.',",
      "'Local semantic model found strong support in outcome evidence.':'Den lokale semantiske model fandt stærk støtte i resultatmaterialet.'":"'Local semantic model found strong support in outcome evidence.':'Det stemmer tydeligt overens.'",
      "main.innerHTML=`<strong>${safe(e.label)}</strong><small>${safe(e.type)} · ${Math.max(1,Math.round((e.size||e.text.length)/1024))} KB${e.sha256?` · ${safe(e.sha256.slice(0,10))}…`:''}${e.extraction?` · ${safe(e.extraction)}`:''}</small>${e.warnings?.length?`<small class=\"warning-text\">${safe(e.warnings.join(' '))}</small>`:''}`;":"main.innerHTML=`<strong>${safe(e.label)}</strong><small>${safe(e.type)} · ${Math.max(1,Math.round((e.size||e.text.length)/1024))} KB</small>${e.warnings?.length?`<small class=\"warning-text\">${safe(e.warnings.join(' '))}</small>`:''}`;",
      "rename.title='Navn på bevis'":"rename.title='Navn på fil'",
      "rename.setAttribute('aria-label','Navn på bevis')":"rename.setAttribute('aria-label','Navn på fil')",
      "date.title='Valgfri dato/tid for bevis'":"date.title='Dato (valgfri)'",
      "status('Bevismaterialet er klar. Intet er blevet uploadet.','good');":"status('Materialet er klar.','good');",
      "el.innerHTML=`<div class=\"fhead\"><span>${safe(statusDa(f.status))} · ${safe(kindDa(f.kind))}</span><span>${Math.round((f.confidence||0)*100)}% · ${safe(f.decisionSource==='deterministic'?'regelbaseret':(f.decisionSource||'regelbaseret'))}</span></div>":"el.innerHTML=`<div class=\"fhead\"><span>${safe(statusDa(f.status))} · ${safe(kindDa(f.kind))}</span></div>",
      "label.textContent=review==='right-match'?'Gennemgået: matchet ser rigtigt ud':review==='wrong-match'?'Gennemgået: forkert match':'Menneskelig kontrol: er det de rigtige beviser, der er parret?';":"label.textContent=review==='right-match'?'Tjekket: ser rigtigt ud':review==='wrong-match'?'Tjekket: forkert match':'Er det de rigtige tekststykker?';",
      "yes.textContent='Rigtigt match'":"yes.textContent='Ja'",
      "no.textContent='Forkert match'":"no.textContent='Nej'",
      "toast('Tilføj beviser på begge sider først.');":"toast('Tilføj noget på begge sider først.');",
      "status('Sammenligner beviser…','warn');":"status('Sammenligner…','warn');",
      "status(issues?`Sammenligningen er færdig: ${issues} mulig${issues===1?'':'e'} afvigelse${issues===1?'':'r'} fundet.`:'Sammenligningen er færdig. Ingen dokumenteret afvigelse blev fundet.','good');":"status(issues?`${issues} forskel${issues===1?'':'le'} fundet.`:'Ingen tydelige forskelle fundet.','good');",
      "status('Demo indlæst. Tryk “Sammenlign beviser”.','good');":"status('Eksemplet er klar. Tryk “Se forskellen”.','good');",
      "status('Ryddet. Intet gemmes, medmindre du selv trykker “Gem lokalt”.','');":"status('Klar.','');",
      "else status('Gemt sag åbnet. Tilføj beviser på begge sider før sammenligning.','good');":"else status('Sagen er åbnet. Tilføj noget på begge sider.','good');",
      "else status('Sagen er importeret lokalt. Tilføj beviser på begge sider før sammenligning.','good');":"else status('Sagen er importeret. Tilføj noget på begge sider.','good');",
      "} else status(`Klar · intern regelbaseret sikkerhedstest ${gate.passedCount}/${gate.total}. Intet gemmes automatisk.`,'good');":"} else status('Klar.','good');",
    }
    for old,new in repl.items():
        if old not in a:
            raise SystemExit(f'Expected app pattern not found: {old[:80]}')
        a=a.replace(old,new)
    app.write_text(a, encoding='utf-8')

v=version.read_text(encoding='utf-8').replace("APP_VERSION = '1.9.0'", "APP_VERSION = '1.9.1'")
version.write_text(v, encoding='utf-8')
c=sw.read_text(encoding='utf-8').replace("aspromised-shell-v1.9'", "aspromised-shell-v1.9.1'")
sw.write_text(c, encoding='utf-8')

# Build gate for the simplification itself.
final = index.read_text(encoding='utf-8')
for required in ['1. Det du blev lovet','2. Det der skete','3. Se forskellen','Flere muligheder']:
    if required not in final:
        raise SystemExit(f'Missing KISS UI marker: {required}')
if 'lokalt · ingen betalt API' in final or 'Valgfri lokal semantisk AI' in final:
    raise SystemExit('Technical copy leaked back into the primary UI')
print('KISS UI patch applied')
