from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'site')
index = root / 'index.html'
app = root / 'app.js'
sw = root / 'sw.js'
version = root / 'src' / 'version.js'

html = index.read_text(encoding='utf-8')
js = app.read_text(encoding='utf-8')

CSS = r'''
.next-step{margin-top:18px;background:linear-gradient(145deg,#10213a,#0b1728);border:1px solid #2b4364;border-radius:18px;padding:18px}.next-step h2{margin:0 0 6px}.choice-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}.choice-btn{flex:1 1 220px;padding:14px 16px;text-align:left;background:#12243c;color:#e8f0ff;border:1px solid #35527a}.choice-btn strong{display:block;font-size:15px}.choice-btn span{display:block;color:#aebed6;font-size:12px;font-weight:500;margin-top:3px}.action-card{display:none;margin-top:14px;background:#081322;border:1px solid #2a3e5d;border-radius:14px;padding:15px}.action-card.show{display:block}.action-card h3{margin:0 0 7px;font-size:17px}.action-copy{white-space:pre-wrap;background:#0d1a2c;border:1px solid #223753;border-radius:11px;padding:13px;line-height:1.55;color:#dce7fa;font-size:14px}.action-note{font-size:12px;color:#9fb0c8;line-height:1.5;margin:10px 0}.rights-box{display:grid;gap:10px}.rights-item{background:#0d1a2c;border:1px solid #223753;border-radius:11px;padding:12px}.rights-item strong{display:block;margin-bottom:4px}.rights-source{display:inline-flex;align-items:center;gap:5px;color:#9dbaff;font-size:12px}.scenario-row{display:flex;gap:7px;flex-wrap:wrap;margin:10px 0 4px}.scenario-row button{font-size:12px;padding:8px 10px}.scenario-row button.active{background:#dbe7ff;color:#091221}.legal-guard{border-left:3px solid #ffc760;padding-left:10px;color:#c7d3e6;font-size:12px;line-height:1.5;margin-top:12px}
'''.strip()
if '.next-step{' not in html:
    html = html.replace('</style>', CSS + '\n  </style>', 1)

NEXT_HTML = r'''
  <section id="nextStep" class="next-step" hidden>
    <h2>4. Hvad vil du gÃ¸re?</h2>
    <p class="sub">VÃ¦lg om du vil starte venligt eller se, hvilke forbrugerregler der kan vÃ¦re relevante.</p>
    <div class="choice-row">
      <button id="friendlyActionBtn" class="choice-btn"><strong>ğŸ™‚ Venlig forespÃ¸rgsel</strong><span>FÃ¥ en rolig besked, du kan sende til virksomheden.</span></button>
      <button id="rightsActionBtn" class="choice-btn"><strong>âš–ï¸ Dine rettigheder som kunde</strong><span>Se relevante regler, officielle kilder og et mere fast svar.</span></button>
    </div>
    <div id="actionCard" class="action-card"></div>
  </section>
'''.strip()
if 'id="nextStep"' not in html:
    marker = '  <section id="how" class="how">'
    if marker not in html:
        raise SystemExit('Could not find insertion marker for step 4')
    html = html.replace(marker, NEXT_HTML + '\n\n' + marker, 1)

index.write_text(html, encoding='utf-8')

HELPERS = r'''

const RIGHTS_SOURCE_CHECKED='17.08.2026';
const RIGHTS_GUIDES={
  handvaerker:{
    title:'HÃ¥ndvÃ¦rker',
    source:'Forbrug.dk â€” HÃ¥ndvÃ¦rkere: aftaler, tilbud og klager',
    url:'https://forbrug.dk/emner/bolig-og-byggeri/haandvaerkere-aftaler-tilbud-og-klager',
    extraUrl:'https://forbrug.dk/emner/bolig-og-byggeri/haandvaerkere-aftaler-tilbud-og-klager/forsinkelser-fejl-og-skader-ved-byggeri'
  },
  vaerksted:{
    title:'VÃ¦rksted / reparation',
    source:'Forbrug.dk â€” AutovÃ¦rksteder og bilsyn',
    url:'https://forbrug.dk/emner/biler/autovaerksteder-og-bilsyn',
    extraUrl:'https://forbrug.dk/regler/opslagsvaerk-forbrugerleksikon/reparationer-du-selv-skal-betale'
  },
  webshop:{
    title:'Webshop / levering',
    source:'Forbrug.dk â€” Problemer med fragt og levering',
    url:'https://forbrug.dk/emner/nethandel-og-digitale-tjenester/sikker-handel-paa-nettet/problemer-med-fragt-og-levering',
    extraUrl:'https://forbrug.dk/emner/nethandel-og-digitale-tjenester/sikker-handel-paa-nettet/problemer-med-varen'
  },
  abonnement:{
    title:'Abonnement',
    source:'Forbrug.dk â€” AbonnementsvilkÃ¥r',
    url:'https://forbrug.dk/emner/aftaler-og-abonnementer/abonnementsvilkaar',
    extraUrl:'https://forbrug.dk/emner/penge-og-forsikring/priser-tilbud-og-gebyrer/regler-gebyrer'
  },
  andet:{title:'Andet',source:'',url:'',extraUrl:''}
};

function relevantFindings(){
  const r=refreshReport();
  if(!r)return [];
  const reviewed=(r.findings||[]).filter(f=>f.userReview!=='wrong-match');
  const issues=reviewed.filter(f=>['changed','contradiction'].includes(f.status));
  return issues.length?issues:reviewed.filter(f=>['unverified','review'].includes(f.status));
}
function compactFinding(f){
  if(f.after) return `â€¢ Det lovede: â€œ${f.before}â€\n  Det der skete: â€œ${f.after}â€`;
  return `â€¢ Det lovede: â€œ${f.before}â€\n  Jeg kan ikke se dokumentation for resultatet i det materiale, jeg har samlet.`;
}
function buildFriendlyDraft(){
  const findings=relevantFindings().slice(0,3);
  const lines=['Hej.','','Jeg har gennemgÃ¥et det, vi aftalte, og det materiale jeg har bagefter. Jeg vil gerne have hjÃ¦lp til at afklare fÃ¸lgende:',''];
  if(findings.length) lines.push(...findings.map(compactFinding));
  else lines.push('â€¢ Jeg vil gerne have bekrÃ¦ftet, at det leverede og den endelige pris stemmer med vores aftale.');
  lines.push('','Vil I hjÃ¦lpe med at forklare forskellen og oplyse, hvordan I foreslÃ¥r, at vi fÃ¥r det afklaret?','','PÃ¥ forhÃ¥nd tak.');
  return lines.join('\n');
}
function allCaseText(){
  const parts=[];
  for(const e of [...(state.caseData?.before||[]),...(state.caseData?.after||[])]) parts.push(e.text||'');
  parts.push($('caseTitle')?.value||'');
  return parts.join(' ').toLowerCase();
}
function detectRightsScenario(){
  const t=allCaseText();
  const score={handvaerker:0,vaerksted:0,webshop:0,abonnement:0};
  for(const w of ['hÃ¥ndvÃ¦rker','tÃ¸mrer','murer','elektriker','vvs','maler','byggeri','renovering','svend','lÃ¦rling','tillÃ¦gsarbejde']) if(t.includes(w))score.handvaerker+=3;
  for(const w of ['autovÃ¦rksted','vÃ¦rksted','mekaniker','bilreparation','reparation','reservedele']) if(t.includes(w))score.vaerksted+=3;
  for(const w of ['webshop','ordrebekrÃ¦ftelse','pakke','forsendelse','levering','returret','vare','ordre']) if(t.includes(w))score.webshop+=2;
  for(const w of ['abonnement','medlemskab','mÃ¥nedligt','pr. mÃ¥ned','prisÃ¦ndring','prisstigning','opsigelse']) if(t.includes(w))score.abonnement+=3;
  const ranked=Object.entries(score).sort((a,b)=>b[1]-a[1]);
  return ranked[0][1]>=3?ranked[0][0]:'andet';
}
function contractSignal(){
  const t=allCaseText();
  if(/maksimumpris|maxpris/.test(t))return 'maksimumpris';
  if(/overslag|prisoverslag|estimat/.test(t))return 'overslag';
  if(/fast pris|fastpris/.test(t))return 'tilbud';
  if(/tilbud/.test(t))return 'tilbud';
  if(/efter regning|timepris|timelÃ¸n/.test(t))return 'regning';
  return 'uklar';
}
function rightsDetails(type){
  const signal=contractSignal();
  const findings=relevantFindings();
  const hasMoney=findings.some(f=>f.kind==='money'||(f.diffs||[]).some(d=>d.type==='money'));
  const hasDelivery=findings.some(f=>f.kind==='delivery'||(f.diffs||[]).some(d=>d.type==='date'));
  if(type==='handvaerker'){
    if(signal==='maksimumpris') return ['En aftalt maksimumpris mÃ¥ ifÃ¸lge Forbrug.dk ikke overskrides uden din accept af, at arbejdet bliver dyrere.','Ã†ndringer og tillÃ¦gsarbejde bÃ¸r aftales med betydningen for pris og tid, gerne skriftligt.'];
    if(signal==='overslag') return ['Et overslag er en cirkapris â€” ikke det samme som et bindende tilbud.','Hvis hÃ¥ndvÃ¦rkeren kan se, at overslaget ikke holder, bÃ¸r du blive orienteret, sÃ¥ I kan aftale, hvad der videre skal ske.'];
    if(signal==='tilbud') return ['Et tilbud er bindende for det arbejde og de leverancer, som tilbuddet faktisk omfatter.','Uforudsete forhold og aftalte Ã¦pdringer kan have betydning, sÃ¥ AsPromised kan ikke ud fra en prisforskel alene afgÃ¸re, at fakturaen er forkert.'];
    if(signal==='regning') return ['Ved arbejde efter regning skal prisen vÃ¦re rimelig i forhold til det udfÃ¸rte arbejde.','Du kan have brug for en specificeret regning for at kunne kontrollere time- og materialforbrug.'];
    return ['Det afgÃ¸rende er fÃ¸rst, om jeres pris var et tilbud, et overslag, en maksimumpris eller arbejde efter regning.','AsPromised kan ikke se det sikkert i materialet, sÃ¥ et fast juridisk svar ville vÃ¦re et gÃ¦t.'];
  }
  if(type==='vaerksted'){
    if(signal==='maksimumpris') return ['En aftalt maksimumpris mÃ¥ normalt ikke overskrides.','Hvis prisen Ã¦ndres, er skriftlig dokumentation for den nye prisaftale vigtig.'];
    if(signal==='overslag') return ['Et prisoverslag binder ikke som et fast tilbud, men hvis prisen vÃ¦sentligt vil overskride overslaget, skal reparatÃ¸ren ifÃ¸lge Forbrug.dk kontakte dig og fÃ¥ accept af den hÃ¸jere pris.','Hvis du har aftalt, at vÃ¦rkstedet ikke mÃ¥ reparere fÃ¸r du accepterer prisen, er dokumentationen for den aftale vigtig.'];
    if(signal==='tilbud') return ['En skriftlig aftale om fast pris stÃ¥r stÃ¦rkere end et lÃ¸st overslag.','Ved senere prisÃ¦ndringer er det vigtigt at kunne dokumentere, hvad der faktisk blev aftalt.'];
    return ['Det afgÎ¸rende er, om der var fast pris, prisoverslag, maksimumpris eller ingen prisaftale.','AsPromised viser derfor kilden og beder dig afklare aftaletypen frem for at gÃ¦tte.'];
  }
  if(type==='webshop'){
    const out=[];
    if(hasDelivery) out.push('Hvis der ikke var aftalt en anden leveringsfrist, skal en dansk/EU-webshop normalt levere inden 30 dage. Ved forsinkelse van du normalt give en ny rimelig frist; levereres der stadig ikke, kan kÃ¸bet i visse tilÃ¤lde h™ÙÙ\Ë‰ÊNÂˆİ]œ\Ú
	Òš\È[ˆ˜\™HZÚÙHÛÛ[Y\ˆœ™[H[\ˆ\ˆ›ÜšÙ\[˜™Y˜[\ˆ›Ü˜œYË™Ë]H°îœİÛÛZİ\ˆÙXœÚÜ[ˆÚÜšYYİğéHHØ[ˆÚİ[Y[\™H›ÜœğîÙ]0éH]0îÙHØYÙ[‹‰ÊNÂˆİ]œ\Ú
	ĞÚ\™ÙX˜XÚÈØ[ˆ°éœ™H™[]˜[Hš\ÜÙH[°é›KY[ˆ\Ô›ÛZ\ÙYØ[ˆZÚÙHYœ˜H[™HÚİ[Y[\ˆ[[™HY™ğî™KÛH[ˆ˜[šÈÚØ[[˜YÙY°î™H™[0î™]‰ÊNÂˆ™]\›ˆİ]ÂˆBˆYŠ\OOOIØX›Û›™[Y[	Ê^Âˆ™]\›ˆÉÑ]š[ğé\ˆÛH0é›™š[™Ù\ˆÚØ[°éœ™HÛ\ÙÈ0é›™š[™Ù\ˆÚØ[˜\œÛ\ÈHš[Y[YÈY‰Ë	Õ™Y°éœÙ[YÙH0é›™š[™Ù\‹ˆ[ˆ°éœÙ[YÈš\ÜİYÛš[™ËÚØ[H›Ü›X[İ[›™HÛÛ[YHYYˆX›Û›™[Y[]°îˆ0é›™š[™Ù[ˆ°é\ˆš\šÛš[™Ë‰Ë	Òš\ÈH\ˆİ™][ˆ˜\İš\ÈH[ˆ™\İ[]\š[ÙKÜ\Ù\ˆ›Ü˜œYË™Ë]š\šÜÛÛZY[ˆ›Ü›X[ZÚÙHØ[ˆ0é™Hš\Ù[ˆH[ˆ\š[ÙK‰×NÂˆBˆ™]\›ˆÉÒ™YÈØ[ˆZÚÙHÚZÚÙ\XÙ\™HØYÙ[ˆH[ˆYˆH\\‹›Üˆ\Ô›ÛZ\ÙY\ˆÚ[ZÛÛ›Û\™YH›Ü˜œYÙ\œ™YÛ\ˆ[™K‰Ë	ĞœYÈ8 '™[›YÈ›Ü™\Ü0î™ÜÙ[8 'HKˆ[ˆ\šY\ÚÈÛÛšÛ\Ú[Ûˆ\ˆšH°éœ™HY\™HÙ[œÚZÚÙ\ˆ[™X]\šX[][Y\‹‰×NÂŸB™[˜İ[ÛˆZ[šYÚÑ˜Y
\J^ÂˆÛÛœİÚYÛ˜[XÛÛ˜XİÚYÛ˜[

NÂˆÛÛœİš[™[™ÜÏ\™[]˜[š[™[™ÜÊ
KœÛXÙJŠNÂˆÛÛœİ[™\ÏVÉÒZ‹‰Ë	ÉË	Ò™YÈš[Ù\›™H]™HYšÛ\™][ˆ›ÜœÚÙ[Y[[H›Ü™\ÈY[HÙÈ]Y\™°îÙ[™HX]\šX[N‰Ë	É×NÂˆYŠš[™[™ÜË›[™İ
[[™\Ëœ\Ú
‹‹™š[™[™ÜË›X\
ÛÛ\Xİš[™[™ÊJNÂˆ[™\Ëœ\Ú
	ÉÊNÂˆYŠ\OOOIÚ[™˜Y\šÙ\‰É‰œÚYÛ˜[OOIÛXZÜÚ[][\š\ÉÊH[™\Ëœ\Ú
	Ñ›Ü˜œYË™ÈÜ\Ù\‹][ˆY[XZÜÚ[][\š\ÈZÚÙHpéHİ™\œÚÜšY\ÈY[ˆİ[™[œÈXØÙ\ˆH]X]\šX[K™YÈ\ˆØ[[]Ø[ˆ™YÈZÚÙHÙK›Üˆ[ˆ0î™\™Hš\È›]ˆXØÙ\\™]ˆš[HÙ[™HÚİ[Y[][Û™[ˆ›Üˆ[ˆY[H[\ˆÛÜœšYÙ\™H™[0î™]ÉÊNÂˆ[ÙHYŠ\OOOIÚ[™˜Y\šÙ\‰É‰œÚYÛ˜[OOIİ[Y	ÊH[™\Ëœ\Ú
	Ñ›Ü˜œYË™ÈÜ\Ù\‹]][Y\ˆš[™[™H›Üˆ]\˜™Z™K[Y]ÛY˜]\‹ˆš[H\™›Üˆ›ÜšÛ\™K˜Yš\Ù›ÜœÚÙ[[ˆÚŞ[\ËÙÈ›Üˆ]™[Y[H0éœš[™Ù\ˆ[\ˆ[0é™ÜØ\˜™Z™\ˆ›]ˆY[ÉÊNÂˆ[ÙHYŠ\OOOIÚ[™˜Y\šÙ\‰É‰œÚYÛ˜[OOIÛİ™\œÛYÉÊH[™\Ëœ\Ú
	Ò™YÈ\ˆÜpéœšÜÛÛH0éK]]İ™\œÛYÈZÚÙH\ˆ]Ø[[YHÛÛH]˜\İ[Yˆ›Ü˜œYË™ÈÜ\Ù\ˆÙË]İ[™[ˆ°îˆÜšY[\™\Ëš\Èİ™\œÛYÙ]ZÚÙHÛ\‹ˆš[HÜ\ÙK›Ü›°é\ˆ[ˆ0î™\™Hš\È›]ˆYY[ÙÈY[ÉÊNÂˆ[ÙHYŠ\OOOIİ˜Y\šÜİY	É‰œÚYÛ˜[OOIÛİ™\œÛYÉÊH[™\Ëœ\Ú
	Ñ›Ü˜œYË™ÈÜ\Ù\‹]š\È[ˆ™\\˜]0îˆØ[ˆÙK]]š\Ûİ™\œÛYÈ°éœÙ[Yİš[›]™Hİ™\œÚÜ™Y]ÚØ[İ[™[ˆÛÛZİ\™\ÈÙÈXØÙ\\™H[ˆYHš\Ëˆš[HÜ\ÙK›Ü›°é\ˆ[ˆ0î™\™Hš\È›]ˆY[ÉÊNÂˆ[ÙHYŠ\OOOIİ˜Y\šÜİY	É‰œÚYÛ˜[OOIÛXZÜÚ[][\š\ÉÊH[™\Ëœ\Ú
	Ñ›Ü˜œYË™ÈÜ\Ù\‹][ˆY[XZÜÚ[][\š\È›Ü›X[ZÚÙHpéHİ™\œÚÜšY\Ëˆš[HÙ[™HÚİ[Y[][Ûˆ›Üˆ[ˆ]™[Y[Ù[™\™HY[HÛH[ˆ0î™\™Hš\ÏÉÊNÂˆ[ÙHYŠ\OOOIİÙXœÚÜ	ÊH[™\Ëœ\Ú
	Ò™YÈ™Y\ˆ™\ˆ\™›ÜˆÛH]™ZÜ°é™K›Ü™[ˆHš[0îÙHØYÙ[‹ÙÈ›Ü›°é\ˆ™YÈØ[ˆ›Ü™[H]ˆ™YÈš[Ù\›™H]™Hİ˜\™]ÚÜšYYİ‰ÊNÂˆ[ÙHYŠ\OOOIØX›Û›™[Y[	ÊH[™\Ëœ\Ú
	Ñ›Ü˜œYË™ÈÜ\Ù\‹]0éœš[™Ù\ˆHX›Û›™[Y[\ˆÚØ[˜\œÛ\ÈÛ\ÙÈHš[Y[YÈYÙÈ]°éœÙ[YÙH0éœš[™Ù\ˆ›Ü›X[ÚØ[Ú]™H][YÚY›Üˆ]ÛÛ[YHYYˆY[[ˆ°îˆ0é›™š[™Ù[ˆ°é\ˆš\šÛš[™Ëˆš[HÜ\ÙK›Ü›°é\ˆÙÈ›Ü™[ˆ[›™H0é›™š[™È›]ˆ˜\œÛ]ÙÈš[Ù]Y[]š[ğé\ˆHİ0î\ˆ[ˆ0éOÉÊNÂˆ[ÙH[™\Ëœ\Ú
	Õš[H›ÜšÛ\™H›ÜœÚÙ[[ˆÙÈÙ[™H[ˆÚİ[Y[][Ûˆ[\ˆY[KÛÛHHY[™\ˆ™YÜ[™\ˆ0éœš[™Ù[ÉÊNÂˆ[™\Ëœ\Ú
	ÉË	ÓYY™[›YÈ[Ù[‰ÊNÂˆ™]\›ˆ[™\Ëš›Ú[Š	×‰ÊNÂŸB™[˜İ[ÛˆÛÜPXİ[Û•^
^
^Âˆ˜]šYØ]Ü‹˜Û\›Ø\™ËÜš]U^
^
K[Š

OOØ\İ
	ÕZÜİ[ˆ\ˆÛÜY\™]‰ÊJK˜Ø]Ú


OO™İÛ›ØY
	Ø\Ü›ÛZ\ÙYX™\ÚÙY^	İ^ÜZ[‰ÊJNÂŸB™[˜İ[Ûˆ™[™\‘œšY[™PXİ[ÛŠ
^ÂˆÛÛœİØ\™I
	ØXİ[ÛØ\™	ÊNÈÛÛœİ^XZ[œšY[™Q˜Y

NÂˆØ\™š[›™\’SXÏ¼'æ`ˆ™[›YÈ›Ü™\Ü0î™ÜÙ[ÚÏÛ\ÜÏH˜Xİ[Û‹[›İH”İ\\ˆ›ÛYİÙÈ™Y\ˆš\šÜÛÛZY[ˆ›ÜšÛ\™H›ÜœÚÙ[[ˆY[ˆ]0é\İ0éK]›ÙÙ[ˆ\ˆÚ›Ü›ÙÙ]›ÜšÙ\Ü]ˆÛ\ÜÏH˜Xİ[Û‹XÛÜHˆYH™œšY[™Q˜YÙ]]ˆÛ\ÜÏHÛÛ˜\ˆ]ÛˆYH˜ÛÜQœšY[™Pˆ’ÛÜpê\ˆ™\ÚÙYØ]ÛÙ]˜Âˆ	
	ÙœšY[™Q˜Y	ÊK^ÛÛ[]^ÈØ\™˜Û\ÜÓ\İ˜Y
	ÜÚİÉÊNÈ	
	ØÛÜQœšY[™P‰ÊK˜Y]™[\İ[™\Š	ØÛXÚÉË

OO˜ÛÜPXİ[Û•^
^
JNÂŸB™[˜İ[Ûˆ™[™\”šYÚĞXİ[ÛŠ\OY]XİšYÚÔØÙ[˜\š[Ê
^ÂˆÛÛœİØ\™I
	ØXİ[ÛØ\™	ÊNÈÛÛœİİZYOT’QÒ×ÑÕRQTÖİ\W_’QÒ×ÑÕRQTË˜[™]ÈÛÛœİ]Z[Ï\šYÚÑ]Z[Ê\JNÈÛÛœİ˜YXZ[šYÚÑ˜Y
\JNÂˆÛÛœİ\\ÏVÖÉÚ[™˜Y\šÙ\‰Ë	Ò0é[™°éœšÙ\‰×KÉİ˜Y\šÜİY	Ë	Õ°éœšÜİY	×KÉİÙXœÚÜ	Ë	ÕÙXœÚÜ	×KÉØX›Û›™[Y[	Ë	ĞX›Û›™[Y[	×KÉØ[™]	Ë	Ğ[™]	×WNÂˆØ\™š[›™\’SXÏ¸¦¥»î#È[™H™]YÚY\ˆÛÛHİ[™OÚÏÛ\ÜÏH˜Xİ[Û‹[›İH\Ô›ÛZ\ÙY›Ü‹ØYÙ[ˆ[™\ˆÛHİ›Û™Ï‰ÜØY™JİZYK]J_OÜİ›Û™Ï‹ˆ™]]YY0ê]ÛZËš\È]\ˆ›ÜšÙ\Ü]ˆÛ\ÜÏHœØÙ[˜\š[Ë\›İÈˆYHœØÙ[˜\š[Ô›İÈÙ]]ˆÛ\ÜÏHœšYÚËX›Ş‰Ù]Z[Ë›X\
O˜]ˆÛ\ÜÏHœšYÚËZ][H‰ÜØY™J
_OÙ]˜
Kš›Ú[Š	ÉÊ_OÙ]‰ÙİZYK\›ØÛ\ÜÏH˜Xİ[Û‹[›İH’Ú[HÛÛ›Û\™]	Ô’QÒ×ÔÓÕTÑWĞÒPÒÑQNˆHÛ\ÜÏHœšYÚË\Ûİ\˜ÙHˆ\™Ù]H—Ø›[šÈˆ™[H››ÛÜ[™\ˆ›Ü™Y™\œ™\ˆˆ™YH‰ÙİZYK\›H‰ÜØY™JİZYKœÛİ\˜ÙJ_H8¡¥ÏØO‰ÙİZYK™^˜U\›Ø0­ÈHÛ\ÜÏHœšYÚË\Ûİ\˜ÙHˆ\™Ù]H—Ø›[šÈˆ™[H››ÛÜ[™\ˆ›Ü™Y™\œ™\ˆˆ™YH‰ÙİZYK™^˜U\›H‘ZÜİ˜HÙ™šXÚY[™Z›Yš[™È8¡¥ÏØO˜‰ÉßOÜ˜‰ÉßO]ˆÛ\ÜÏH›YØ[YİX\™‘]\ˆ\ˆÙ[™\™[›Ü˜œYÙ\š[™›Ü›X][Û‹ZÚÙH[ˆY™ğî™[ÙHYˆ[ˆØYËˆ\Ô›ÛZ\ÙYØ[ˆZÚÙHÙH][™YÙHY[\‹›ÜšÛY[ˆ›Üˆ[™Hš[\ˆ[\ˆ[H\šY\ÚÙH[™YÙ[Ù\‹Ù]Èİ[OH›X\™Ú[‹]ÜŒMœ‘›ÜœÛYÈ[İ˜\ÚÏ]ˆÛ\ÜÏH˜Xİ[Û‹XÛÜHˆYHœšYÚÑ˜YÙ]]ˆÛ\ÜÏHÛÛ˜\ˆ]ÛˆYH˜ÛÜTšYÚĞˆ’ÛÜpê\ˆİ˜\Ø]ÛÙ]˜ÂˆÛÛœİ›İÏI
	ÜØÙ[˜\š[Ô›İÉÊNÂˆ›ÜŠÛÛœİÚÙ^KX™[HÙˆ\\Ê^ØÛÛœİYØİ[Y[˜Ü™X]Q[[Y[
	Ø]Û‰ÊNØ‹˜Û\ÜÓ˜[YOXÙXÛÛ™\H	ÚÙ^OOO]\OÉØXİ]™IÎ‰ÉßXØ‹^ÛÛ[[X™[Ø‹˜Y]™[\İ[™\Š	ØÛXÚÉË

OOœ™[™\”šYÚĞXİ[ÛŠÙ^JJNÜ›İË˜\[™
ŠNßBˆ	
	ÜšYÚÑ˜Y	ÊK^ÛÛ[Y˜YÈØ\™˜Û\ÜÓ\İ˜Y
	ÜÚİÉÊNÈ	
	ØÛÜTšYÚĞ‰ÊK˜Y]™[\İ[™\Š	ØÛXÚÉË

OO˜ÛÜPXİ[Û•^
˜Y
JNÂŸB™[˜İ[Ûˆ™\Ù]Xİ[Û”İ\

^ÂˆÛÛœİİ\I
	Û™^İ\	ÊKØ\™I
	ØXİ[ÛØ\™	ÊNÈYŠİ\
\İ\šY[]YNÈYŠØ\™
^ØØ\™˜Û\ÜÓ\İœ™[[İ™J	ÜÚİÉÊNØØ\™š[›™\’SIÉÎßBŸB™[˜İ[ÛˆÚİĞXİ[Û”İ\

^ØÛÛœİİ\I
	Û™^İ\	ÊNÚYŠİ\
\İ\šY[Y˜[ÙNßB‰ÉÉËœœİš\

B‚šYˆ	ØÛÛœİ’QÒ×ÔÓÕTÑWĞÒPÒÑQIÈ›İ[ˆœÎ‚ˆX\šÙ\ˆH™[˜İ[ÛˆØY[[Ê
^È‚ˆYˆX\šÙ\ˆ›İ[ˆœÎ‚ˆ˜Z\ÙHŞ\İ[Q^]
	ĞÛİ[›İš[™”È[œÙ\[ÛˆX\šÙ\‰ÊBˆœÈHœËœ™\XÙJX\šÙ\‹ST”È
È	×—‰È
ÈX\šÙ\‹JB‚ˆÈÛÚÈ[È™\İ[Y™XŞXÛK‚šœÈHœËœ™\XÙJˆ	
	Ü™\İ[ÉÊK˜Û\ÜÓ\İ˜Y
	ÜÚİÉÊNÈ	
	ÜØ]™P‰ÊK™\ØX›YY˜[ÙNÈ	
	Ù^ÜØ\ÙP‰ÊK™\ØX›YY˜[ÙNÈ‹ˆ	
	Ü™\İ[ÉÊK˜Û\ÜÓ\İ˜Y
	ÜÚİÉÊNÈ	
	ÜØ]™P‰ÊK™\ØX›YY˜[ÙNÈ	
	Ù^ÜØ\ÙP‰ÊK™\ØX›YY˜[ÙNÈÚİĞXİ[Û”İ\

NÈŠBšœÈHœËœ™\XÙJ™[˜İ[Ûˆ[˜[Y]P[˜[\Ú\Ê
^Èİ]K˜[˜[\Ú\Ï[[Èİ]K˜Ø\ÙQ]O[[Èİ]Kœ™\Ü[[Èİ]K™š[™[™Ô™]šY]ÜÏ^ßNÈ	
	Ü™\İ[ÉÊK˜Û\ÜÓ\İœ™[[İ™J	ÜÚİÉÊNÈ	
	ÜØ]™P‰ÊK™\ØX›Y]YNÈ	
	Ù^ÜØ\ÙP‰ÊK™\ØX›Y]YNÈH‹™[˜İ[Ûˆ[˜[Y]P[˜[\Ú\Ê
^Èİ]K˜[˜[\Ú\Ï[[Èİ]K˜Ø\ÙQ]O[[Èİ]Kœ™\Ü[[Èİ]K™š[™[™Ô™]šY]ÜÏ^ßNÈ	
	Ü™\İ[ÉÊK˜Û\ÜÓ\İœ™[[İ™J	ÜÚİÉÊNÈ	
	ÜØ]™P‰ÊK™\ØX›Y]YNÈ	
	Ù^ÜØ\ÙP‰ÊK™\ØX›Y]YNÈ™\Ù]Xİ[Û”İ\

NÈHŠBšœÈHœËœ™\XÙJ™[˜İ[ÛˆÛX\[
Ü™\Ù\™TØ]™YYY˜[Ù_O^ßJ^Èİ]K˜™Y›Ü™OV×NÜİ]K˜Y\V×NÜİ]K˜[˜[\Ú\Ï[[Üİ]K˜Ø\ÙQ]O[[Üİ]Kœ™\Ü[[Üİ]K™š[™[™Ô™]šY]ÜÏ^ßNÚYŠ\™\Ù\™TØ]™YY
\İ]KœØ]™YØ\ÙRY[[É
	Ø™Y›Ü™U^	ÊK˜[YOIÉÎÉ
	ØY\•^	ÊK˜[YOIÉÎÉ
	ØØ\ÙU]IÊK˜[YOIÓZ[ˆØ[[Y[›YÛš[™ÉÎÙ]šY[˜ÙT›İÜÊ	Ø™Y›Ü™IÊNÙ]šY[˜ÙT›İÜÊ	ØY\‰ÊNÉ
	Ü™\İ[ÉÊK˜Û\ÜÓ\İœ™[[İ™J	ÜÚİÉÊNÉ
	ÜØ]™P‰ÊK™\ØX›Y]YNÉ
	Ù^ÜØ\ÙP‰ÊK™\ØX›Y]YNÜİ]\Ê	ÒÛ\‹‰Ë	ÉÊNÈH‹™[˜İ[ÛˆÛX\[
Ü™\Ù\™TØ]™YYY˜[Ù_O^ßJ^Èİ]K˜™Y›Ü™OV×NÜİ]K˜Y\V×NÜİ]K˜[˜[\Ú\Ï[[Üİ]K˜Ø\ÙQ]O[[Üİ]Kœ™\Ü[[Üİ]K™š[™[™Ô™]šY]ÜÏ^ßNÚYŠ\™\Ù\™TØ]™YY
\İ]KœØ]™YØ\ÙRY[[É
	Ø™Y›Ü™U^	ÊK˜[YOIÉÎÉ
	ØY\•^	ÊK˜[YOIÉÎÉ
	ØØ\ÙU]IÊK˜[YOIÓZ[ˆØ[[Y[›YÛš[™ÉÎÙ]šY[˜ÙT›İÜÊ	Ø™Y›Ü™IÊNÙ]šY[˜ÙT›İÜÊ	ØY\‰ÊNÉ
	Ü™\İ[ÉÊK˜Û\ÜÓ\İœ™[[İ™J	ÜÚİÉÊNÉ
	ÜØ]™P‰ÊK™\ØX›Y]YNÉ
	Ù^ÜØ\ÙP‰ÊK™\ØX›Y]YNÜ™\Ù]Xİ[Û”İ\

NÜİ]\Ê	ÒÛ\‹‰Ë	ÉÊNÈHŠB‚“TÕS‘T—ÓPT’ÑTˆH‰
	Ø[˜[^™P‰ÊK˜Y]™[\İ[™\Š	ØÛXÚÉË[˜[^™JNÈ‚šYˆ‰
	ÙœšY[™PXİ[Û‰ÊK˜Y]™[\İ[™\ˆˆ›İ[ˆœÎ‚ˆYˆTÕS‘T—ÓPT’ÑTˆ›İ[ˆœÎ‚ˆ˜Z\ÙHŞ\İ[Q^]
	ĞÛİ[›İš[™\İ[™\ˆX\šÙ\‰ÊBˆœÈHœËœ™\XÙJTÕS‘T—ÓPT’ÑT‹‰
	ÙœšY[™PXİ[Û‰ÊK˜Y]™[\İ[™\Š	ØÛXÚÉË™[™\‘œšY[™PXİ[ÛŠNÈ	
	ÜšYÚĞXİ[Û‰ÊK˜Y]™[\İ[™\Š	ØÛXÚÉË

OOœ™[™\”šYÚĞXİ[ÛŠ
JN×ˆˆ
ÈTÕS‘T—ÓPT’ÑT‹JB‚˜\Üš]Wİ^
œË[˜ÛÙ[™ÏIİ]‹N	ÊB‚ˆÈš^Hİ[K\Ú[YÎˆØ[YK[ÜšYÚ[ˆ˜]šYØ][Ûˆ[™\ÜÙ]È™Y™\ˆH™]ÛÜšËˆÈ]ÙY\HØXÚH\È[ˆÙ™›[™H˜[˜XÚËˆ\ÈXZÙ\È™]ÈRH™[X\Ù\Èš\ÚX›BˆÈÈ™]\›š[™È\Ù\œÈÚ]İ]X[X[ØXÚKX\İ[™Ë‚œİ×İ^HİËœ™XYİ^
[˜ÛÙ[™ÏIİ]‹N	ÊBœİ×İ^H™KœİXŠˆ˜ÛÛœİĞPÒOIÖ×‰×JÉÎÈ‹˜ÛÛœİĞPÒOIØ\Ü›ÛZ\ÙY\Ú[]ŒKŒLŒ	ÎÈ‹İ×İ^Ûİ[LJB›ÛÙ™]ÚHœÙ[‹˜Y]™[\İ[™\Š	Ù™]Ú	ËOOÚYŠKœ™\]Y\İ›Y]ÙOOIÑÑU	ß™]ÈT“
Kœ™\]Y\İ\›
K›ÜšYÚ[ˆOO[ØØ][Û‹›ÜšYÚ[Š\™]\›ÙKœ™\ÜÛ™Ú]
ØXÚ\Ë›X]Ú
Kœ™\]Y\İ
K[ŠOœŸ™]Ú
Kœ™\]Y\İ
JJNßJNÈ‚›™]×Ù™]ÚHœÙ[‹˜Y]™[\İ[™\Š	Ù™]Ú	ËOOÚYŠKœ™\]Y\İ›Y]ÙOOIÑÑU	ß™]ÈT“
Kœ™\]Y\İ\›
K›ÜšYÚ[ˆOO[ØØ][Û‹›ÜšYÚ[Š\™]\›ÙKœ™\ÜÛ™Ú]
™]Ú
Kœ™\]Y\İ
K[ŠOØÛÛœİÛÜO\‹˜ÛÛ™J
NØØXÚ\Ë›Ü[ŠĞPÒJK[ŠÏO˜Ëœ]
Kœ™\]Y\İÛÜJJK˜Ø]Ú


OOßJNÜ™]\›ˆßJK˜Ø]Ú


OO˜ØXÚ\Ë›X]Ú
Kœ™\]Y\İ
JJNßJNÈ‚šYˆÛÙ™]Ú[ˆİ×İ^ˆİ×İ^Hİ×İ^œ™\XÙJÛÙ™]Ú™]×Ù™]Ú
B™[Yˆ	Ù™]Ú
Kœ™\]Y\İ
K[‰È›İ[ˆİ×İ^ˆ˜Z\ÙHŞ\İ[Q^]
	Õ[™^XİYÙ\šXÙHÛÜšÙ\ˆ™]Úİ˜]YŞIÊBœİËÜš]Wİ^
İ×İ^[˜ÛÙ[™ÏIİ]‹N	ÊB‚ˆH™\œÚ[Û‹œ™XYİ^
[˜ÛÙ[™ÏIİ]‹N	ÊBˆH™KœİXŠˆTÕ‘T”ÒSÓˆH	Ö×‰×JÉÈ‹TÕ‘T”ÒSÓˆH	ÌKŒLŒ	È‹‹Ûİ[LJB™\œÚ[Û‹Üš]Wİ^
‹[˜ÛÙ[™ÏIİ]‹N	ÊB‚ˆÈ™[X\ÙHØ]\È›Üˆ\È™X]\™K‚™š[˜[Ú[Z[™^œ™XYİ^
[˜ÛÙ[™ÏIİ]‹N	ÊB™š[˜[ÚœÏX\œ™XYİ^
[˜ÛÙ[™ÏIİ]‹N	ÊB™š[˜[ÜİÏ\İËœ™XYİ^
[˜ÛÙ[™ÏIİ]‹N	ÊB™›Üˆ™\]Z\™Y[ˆÉÍˆ˜Yš[Hğî™OÉË	Õ™[›YÈ›Ü™\Ü0î™ÜÙ[	Ë	Ñ[™H™]YÚY\ˆÛÛHİ[™IË	ÚYH˜Xİ[ÛØ\™‰×N‚ˆYˆ™\]Z\™Y›İ[ˆš[˜[Ú[ˆ˜Z\ÙHŞ\İ[Q^]
‰ÓZ\ÜÚ[™ÈXİ[ÛˆRNˆÜ™\]Z\™YIÊB™›Üˆ™\]Z\™Y[ˆÉÔ’QÒ×ÔÓÕTÑWĞÒPÒÑQ	Ë	ØZ[œšY[™Q˜Y	Ë	Ü™[™\”šYÚĞXİ[Û‰Ë	Ù›Ü˜œYË™ËÙ[[™\‹Ø›ÛYË[ÙËXYÙÙ\šIË	Ù›Ü˜œYË™ËÙ[[™\‹ØY[\‹[ÙËXX›Û›™[Y[\‰×N‚ˆYˆ™\]Z\™Y›İ[ˆš[˜[ÚœÎˆ˜Z\ÙHŞ\İ[Q^]
‰ÓZ\ÜÚ[™ÈXİ[ÛˆÙÚXÎˆÜ™\]Z\™YIÊBšYˆ	ØØXÚ\Ë›X]Ú
Kœ™\]Y\İ
K[ŠOœŸ™]Ú
Kœ™\]Y\İ
JIÈ[ˆš[˜[ÜİÎˆ˜Z\ÙHŞ\İ[Q^]
	ÓÛØXÚKYš\œİİ˜]YŞHİ[™\Ù[	ÊBœš[
	Ôİ\Xİ[ÛœÈ
ÈšYÚÈİZY[˜ÙH
È™]ÛÜšËYš\œİÙ\šXÙHÛÜšÙ\ˆ\YY	ÊB