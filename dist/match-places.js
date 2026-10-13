/* Curated real places; no arbitrary text, synthetic POIs or fabricated live routes. */
let matchPickerOpen=null,matchPickerIndex=-1;
function matchPlaces(){
 const cities=SERVICE_CITIES.map(c=>({id:'city-'+c.id,name:c.name,en:c.nameEn,cityKey:c.id,kind:'city',detail:c.summary,detailEn:c.summaryEn}));
 const landmarks=PLACES.filter(p=>p.id!=='panda').map(p=>({...p,id:'place-'+p.id,cityKey:'chengdu',kind:'city',detailEn:p.en}));
 const sights=TOUR_DESTINATIONS.map(d=>({id:'sight-'+d.id,name:d.name,en:d.nameEn,cityKey:d.group==='city'||['dujiangyan','qingcheng'].includes(d.id)?'chengdu':null,kind:d.group,destinationId:d.id,detail:DESTINATION_CATEGORIES.find(c=>d.categories.includes(c.id))?.name||'',detailEn:DESTINATION_CATEGORIES.find(c=>d.categories.includes(c.id))?.nameEn||''}));
 const unique=[];for(const p of [...cities,...sights,...landmarks])if(!unique.some(x=>x.name===p.name))unique.push(p);return unique;
}
function matchPlaceById(id){return matchPlaces().find(p=>p.id===id)}
function matchPlaceName(p){return p?(state.lang==='en'?p.en:p.name):''}
function matchPlaceOptions(role,query=''){
 const term=query.trim().toLowerCase(),all=matchPlaces();
 const ordered=role==='destination'?[...all.filter(p=>p.destinationId),...all.filter(p=>!p.destinationId)]:[...all.filter(p=>p.id==='city-chengdu'),...all.filter(p=>p.id.startsWith('place-')),...all.filter(p=>p.id!=='city-chengdu'&&!p.id.startsWith('place-'))];
 return ordered.filter(p=>!term||`${p.name} ${p.en} ${p.detail} ${p.keywords||''}`.toLowerCase().includes(term));
}
function matchPlacePickerHTML(role,n){
 const key=role==='start'?'startId':'destinationId',id=role==='start'?'m-start':'m-dest',p=matchPlaceById(n[key]),value=p?matchPlaceName(p):(role==='start'?n.start:n.destination)||'';
 return `<div class="formfield match-place-field" data-match-picker="${role}"><label for="${id}">${matchCopy(role==='start'?'起点':'目的地',role==='start'?'Starting point':'Destination')}</label><div class="match-place-input"><input id="${id}" role="combobox" aria-autocomplete="list" aria-haspopup="listbox" aria-expanded="false" aria-controls="${id}-options" aria-describedby="${id}-error" autocomplete="off" maxlength="80" data-place-id="${p?.id||''}" value="${esc(value)}" placeholder="${matchCopy('搜索并选择地点','Search and select a place')}" onfocus="openMatchPlace('${role}')" oninput="searchMatchPlace('${role}')" onkeydown="matchPlaceKey(event,'${role}')"/><button type="button" aria-label="${matchCopy(role==='start'?'选择起点':'选择目的地',role==='start'?'Select starting point':'Select destination')}" onclick="openMatchPlace('${role}',true)">⌄</button></div><div class="match-place-panel" id="${id}-panel" hidden><div class="match-place-panel-title">${matchCopy('请选择列表中的真实地点','Select a listed place')}</div><div role="listbox" aria-label="${matchCopy('地点选项','Place options')}" id="${id}-options"></div></div><small class="match-place-error" id="${id}-error" role="status"></small></div>`;
}
function matchPlaceInput(role){return q(role==='start'?'m-start':'m-dest')}
function closeMatchPlaces(){for(const role of ['start','destination']){const input=matchPlaceInput(role);if(input){q(input.id+'-panel').hidden=true;input.setAttribute('aria-expanded','false');input.removeAttribute('aria-activedescendant')}}matchPickerOpen=null;matchPickerIndex=-1}
function openMatchPlace(role,focus=false){
 const input=matchPlaceInput(role);if(!input)return;closeMatchPlaces();matchPickerOpen=role;
 const options=matchPlaceOptions(role,input.dataset.placeId?'':input.value),box=q(input.id+'-options');
 box.innerHTML=options.length?options.map(p=>`<button type="button" role="option" aria-selected="false" id="${input.id}-option-${p.id}" data-place-id="${p.id}" onpointerdown="event.preventDefault()" onclick="chooseMatchPlace('${role}','${p.id}')"><strong>${esc(matchPlaceName(p))}</strong><small>${esc(state.lang==='en'?p.detailEn:p.detail)}</small></button>`).join(''):`<p class="match-place-no-result">${matchCopy('没有找到这个地点，请换个关键词；不能直接用输入文字推荐。','No listed place found. Try another keyword and select an option.')}</p>`;
 q(input.id+'-panel').hidden=false;input.setAttribute('aria-expanded','true');if(focus)input.focus();
}
function matchTripChanged(){state.match=null;q('match-result')?.remove();q('match-empty')?.remove();if(q('m-people'))state.matchRequest={...matchRequest(),people:+q('m-people').value,bags:+q('m-bags').value,budget:+q('m-budget').value,type:q('m-type').value,priority:q('m-priority').value}}
function searchMatchPlace(role){const input=matchPlaceInput(role);input.dataset.placeId='';input.removeAttribute('aria-invalid');q(input.id+'-error').textContent='';const n=matchRequest();state.matchRequest={...n,[role==='start'?'startId':'destinationId']:'',[role==='start'?'start':'destination']:input.value};matchTripChanged();openMatchPlace(role)}
function chooseMatchPlace(role,id){
 const p=matchPlaceById(id),input=matchPlaceInput(role);if(!p||!input)return;
 input.value=matchPlaceName(p);input.dataset.placeId=p.id;input.removeAttribute('aria-invalid');q(input.id+'-error').textContent='';
 state.matchRequest={...matchRequest(),[role==='start'?'startId':'destinationId']:p.id,[role==='start'?'start':'destination']:p.name};matchTripChanged();closeMatchPlaces();
}
function matchPlaceKey(e,role){
 if(e.key==='Escape'){closeMatchPlaces();return}
 if(e.key==='Tab'){closeMatchPlaces();return}
 if(!['ArrowDown','ArrowUp','Enter'].includes(e.key))return;
 if(matchPickerOpen!==role&&e.key!=='Enter')openMatchPlace(role);
 const input=matchPlaceInput(role),buttons=[...(q(input.id+'-options')?.querySelectorAll('button[role="option"]')||[])];
 if(e.key==='Enter'){if(matchPickerOpen===role){e.preventDefault();if(matchPickerIndex>=0&&buttons[matchPickerIndex])chooseMatchPlace(role,buttons[matchPickerIndex].dataset.placeId)}return}
 e.preventDefault();if(!buttons.length)return;matchPickerIndex=(matchPickerIndex+(e.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;
 buttons.forEach((b,i)=>b.setAttribute('aria-selected',String(i===matchPickerIndex)));input.setAttribute('aria-activedescendant',buttons[matchPickerIndex].id);buttons[matchPickerIndex].scrollIntoView({block:'nearest'});
}
document.addEventListener('pointerdown',e=>{if(!e.target.closest('[data-match-picker]'))closeMatchPlaces()});
function validateMatchPlaces(startId,destinationId,startText,destinationText){
 const start=matchPlaceById(startId),destination=matchPlaceById(destinationId),matches=(p,s)=>p&&(s===p.name||s===p.en);
 if(!matches(start,startText))return {field:'start',error:matchCopy('请从下方选项中选择起点。','Select your starting point from the options.')};
 if(!matches(destination,destinationText))return {field:'destination',error:matchCopy('请从下方选项中选择目的地。','Select your destination from the options.')};
 if(start.id===destination.id)return {field:'destination',error:matchCopy('目的地不能与起点相同，请重新选择。','Choose a destination different from the starting point.')};
 return {start,destination};
}
function matchRouteContext(n){
 const start=matchPlaceById(n.startId),end=matchPlaceById(n.destinationId),d=TOUR_DESTINATIONS.find(x=>x.id===end?.destinationId),startD=TOUR_DESTINATIONS.find(x=>x.id===start?.destinationId);
 const ids=[d?.id,startD?.id];
 return {start,end,d,startD,kind:ids.includes('siguniang')?'highland':ids.includes('jiuzhai')?'long-mountain':d?.group==='nature'||startD?.group==='nature'?'scenic':start?.cityKey&&end?.cityKey&&start.cityKey!==end.cityKey?'intercity':'city'};
}
const MATCH_MODEL_POSITIONING={h7:{luxury:true,labelZh:'高级商务轿车',labelEn:'Executive saloon',sourceUrl:'https://www.faw.com.cn/fawcn/373692/5133331/yfcg/index.html',sourceTitleZh:'一汽车型定位资料',sourceTitleEn:'FAW model positioning'}};
function matchesMatchPriority(car,n){
 if(n.priority==='豪华感')return car.type.includes('豪华')||MATCH_MODEL_POSITIONING[car.id]?.luxury===true;
 if(n.priority==='环保')return car.type.includes('新能源');
 if(n.priority==='驾驶乐趣')return car.type.includes('跑车');
 if(n.priority==='空间')return /SUV|MPV|中巴/.test(car.type);
 return true;
}
function matchPreferenceReason(car,n){
 const p=MATCH_MODEL_POSITIONING[car.id];
 if(n.priority==='豪华感')return {label:matchCopy('对应你的豪华感偏好','For your luxury preference'),text:matchCopy(`你最在意“豪华感”，本次优先比较高级或豪华定位的车型。这辆车以${p?.labelZh||car.type}定位进入预算内候选，适合继续比较外观风格与座舱体验；具体内饰用料、座椅与配置仍以实车资料为准。`,`Your luxury preference selects executive or luxury-positioned models within budget. This ${p?.labelEn||'luxury-category vehicle'} is a candidate for comparing styling and cabin experience; confirm the actual materials, seating and equipment.`),sourceUrl:p?.sourceUrl};
 if(n.priority==='价格')return {label:matchCopy('按价格优先排列','Price comes first'),text:matchCopy('在符合行程与同行人数所需类别的候选中，按演示日租价由低到高排序，方便你控制选车预算。','Among the body-type candidates for this journey and group, demo daily rates are ordered from lowest to highest.')};
 if(n.priority==='空间')return {label:matchCopy('先比较空间取向的车型类别','Compare space-oriented body types'),text:matchCopy('按你的空间偏好，先比较 MPV、SUV 或中巴类别。具体座位布局、行李容量与同行人数的适配，需要结合这辆实车确认。','Your space preference compares MPV, SUV or minibus categories. Confirm actual seat layout, luggage capacity and group capacity for this vehicle.')};
 if(n.priority==='驾驶乐趣')return {label:matchCopy('优先比较跑车类别','Sports-car category first'),text:matchCopy('按你的驾驶乐趣偏好，本次筛选跑车类别供你比较外观与出行方式。驾驶感受和具体性能需结合实车版本了解。','Your driving-enjoyment preference selects sports-car categories to compare styling and journey style. Assess driving feel and performance against the actual version.')};
 if(n.priority==='环保')return {label:matchCopy('对应新能源出行偏好','For your electric-mobility preference'),text:matchCopy('按你的环保偏好，本次先查看新能源分类的车型。具体动力版本、续航与沿途补能安排需在出发前确认。','Your environmental preference selects the catalogue’s electric/hybrid category. Confirm the actual powertrain, range and charging arrangements before travel.')};
 if(n.priority==='舒适')return {label:matchCopy('舒适体验待实车确认','Confirm the actual comfort experience'),text:matchCopy('这次先结合行程、预算和车型类别比较候选。实车座椅、隔音等舒适信息尚未核实，因此舒适项暂未参与排序，确认资料后再进一步比较。','These candidates compare journey, budget and body type. Actual seating and other comfort details are not yet verified, so comfort is not used in ranking until the vehicle information is confirmed.')};
 return null;
}
function routeMatchCandidates(n,options={}){
 const route=matchRouteContext(n),mountain=['highland','long-mountain'].includes(route.kind),relaxPriority=options.relaxPriority===true;
 return CARS.filter(car=>{
  const cfg=configFor(car);if(car.price==null||car.price>n.budget)return false;
  if(!relaxPriority&&!matchesMatchPriority(car,n))return false;
  if(cfg.verified&&((cfg.seats!=null&&cfg.seats<n.people)||(cfg.bags!=null&&cfg.bags<n.bags)))return false;
  const knownSeats=carSeats(car);if(knownSeats!=null&&knownSeats<n.people)return false;
  if(knownSeats==null&&n.people>7&&!car.type.includes('中巴'))return false;
  if(knownSeats==null&&n.people>5&&!/MPV|中巴/.test(car.type))return false;
  if(n.people>2&&car.type.includes('敞篷'))return false;
  const knownBags=carBags(car);
  if(knownBags!=null&&knownBags<n.bags)return false;
  if(knownBags==null&&n.bags>=3&&!/MPV|中巴/.test(car.type))return false;
  if(mountain&&n.people<=5)return car.type.includes('SUV')&&!car.type.includes('新能源');
  if(n.people<=5&&n.bags<6&&car.type.includes('中巴'))return false;
  return true;
 }).map(car=>{
  const body=car.type.includes('SUV')?'SUV':car.type.includes('MPV')?'MPV':car.type.includes('轿车')?'saloon':'other';
  const routeRank=n.priority==='空间'?({MPV:3,SUV:2}[body]||0):route.kind==='scenic'?({SUV:3,MPV:2,saloon:1}[body]||0):n.type==='家庭出游'||n.bags>=3?({MPV:3,SUV:2,saloon:1}[body]||0):0;
  return {...car,routeRank,sceneMatch:car.scene===n.type};
 }).sort((a,b)=>n.priority==='价格'?a.price-b.price||b.routeRank-a.routeRank:b.routeRank-a.routeRank||Number(b.sceneMatch)-Number(a.sceneMatch)||a.price-b.price).slice(0,3);
}
function matchApplyBudget(value){const el=q('m-budget');if(!el)return;el.value=String(value);matchTripChanged();submitRouteMatch({preventDefault(){}})}
function matchEmptyResultHTML(n){
 const broader=routeMatchCandidates({...n,budget:Infinity},{relaxPriority:true}),cheapest=broader.length?Math.min(...broader.map(c=>c.price)):null;
 const suggestion=cheapest!=null?[700,1000,1500].find(b=>b>=cheapest)||null:null;
 const knownPreference=['豪华感','空间','驾驶乐趣','环保'].includes(n.priority),title=knownPreference?matchCopy(`当前预算内暂无符合“${n.priority}”的候选车型`,`No within-budget candidates for “${t(n.priority)}”`):matchCopy('当前条件下暂无合适类别的候选车型','No candidates in the requested categories');
 const text=cheapest!=null?matchCopy(`保持你的行程与偏好条件，当前对应类别的演示日租价最低为 ${money(cheapest)}，超过 ${money(n.budget)} 日预算。可以手动调整预算，或联系确认其他车型报价。`,`Keeping your journey and preference, the lowest matching demo daily rate is ${money(cheapest)}, above your ${money(n.budget)} limit. Adjust the budget manually or enquire about other quotes.`):matchCopy('当前行程、同行人数与偏好组合没有对应的已报价车型。可联系确认其他车型或调整偏好条件。','No quoted model category matches this journey, group and preference combination. Enquire about other models or adjust the preference.');
 return `<div class="match-result match-empty" id="match-empty">${matchRoutePlanHTML(n)}<h2>${esc(title)}</h2><p>${esc(text)}</p><div class="match-empty-actions">${suggestion?`<button class="btn" onclick="matchApplyBudget(${suggestion})">${matchCopy(`把日预算调到 ${money(suggestion)} 再看`,`Retry with a ${money(suggestion)} daily budget`)}</button>`:''}<a class="btn ghost" href="#/search">${matchCopy('查看全部车型','View all cars')}</a></div></div>`;
}
function matchRouteReason(car,n){
 if(!matchPlaceById(n.startId)||!matchPlaceById(n.destinationId)){const s=matchVehicleStory(car);return {label:matchCopy(s[0],s[2]),text:matchCopy(s[1],s[3])}}
 const {kind,end,d,startD}=matchRouteContext(n),label=matchPlaceName(end),mountain=[d,startD].find(x=>x?.id===(kind==='highland'?'siguniang':'jiuzhai')),scenic=[d,startD].find(x=>x?.group==='nature'),body=car.type.includes('SUV')?'SUV':car.type.includes('MPV')?'MPV':car.type.includes('中巴')?matchCopy('中巴','minibus'):matchCopy('轿车','saloon');
 let text=n.people>7?matchCopy(`这次有 ${n.people} 人同行，先比较中巴类别，再核对实车核载人数和驾驶资格，让团队集中出发的安排更清晰。`,`For ${n.people} travellers, compare minibus options and confirm the actual permitted capacity and licence requirements.`):n.people>5?matchCopy(`这次有 ${n.people} 人同行，优先比较 MPV 类别，把座位布局和行李安排一起确认，方便规划共同出发的旅程。`,`For ${n.people} travellers, compare MPV options and confirm the actual seat layout and luggage arrangement.`):['highland','long-mountain'].includes(kind)?matchCopy(`本次行程涉及${mountain?tourText(mountain,'name'):label}，先比较预算内的 SUV 类别。沿途安排休息与补给，再核对实车状态和出行日道路信息。`,`This journey includes ${mountain?tourText(mountain,'name'):label}. Compare SUV categories within budget, plan stops and supplies, and confirm the actual vehicle and roads for your travel day.`):kind==='scenic'?matchCopy(`行程涉及${scenic?tourText(scenic,'name'):label}，这次先比较 SUV、MPV 等类别，兼顾沿途停留和游览安排。这辆${body}可作为预算内的车型参考，实际空间和配置以实车确认。`,`For the journey involving ${scenic?tourText(scenic,'name'):label}, SUV and MPV categories are shown first to support planning stops and sightseeing. This ${body} is a within-budget model reference; confirm its actual space and equipment.`):matchCopy(`从${matchPlaceName(matchRouteContext(n).start)}出发去${label}，结合你选择的“${n.type}”安排车型。到达后按现场停车条件游览，让用车与行程衔接更顺畅。`,`For ${matchPlaceName(matchRouteContext(n).start)} to ${label}, consider your ${t(n.type)} category and the parking arrangements at the destination.`);
 return {label:matchCopy('结合你的目的地','For your selected destination'),text};
}
function matchRoutePlanHTML(n){
 const {start,end,d,startD,kind}=matchRouteContext(n);if(!start||!end)return '';
 const guide=['highland','long-mountain'].includes(kind)?[d,startD].find(x=>x?.id===(kind==='highland'?'siguniang':'jiuzhai')):d||startD;
 const route=TOUR_ROUTES.find(r=>r.destination===d?.id),originChengdu=start.cityKey==='chengdu';
 const labels={city:['城市行程','City journey'],intercity:['跨城行程','Intercity journey'],scenic:['近郊山水','Nearby scenery'],highland:['高海拔山地','Highland destination'],'long-mountain':['长途山地','Mountain destination']};
 const note=guide?tourText(guide,['highland','long-mountain'].includes(kind)||originChengdu?'terrain':'tip'):matchCopy('按已选择的真实地点规划，出发前确认取还车点和实际道路安排。','Plan around the selected places and confirm pickup, return and actual road arrangements.');
 const official=guide?.id==='siguniang'?{zh:'双桥沟内以景区观光车游览；自驾到达与园内游览分开安排。',en:'Shuangqiao Valley uses sightseeing vehicles; plan the drive to the destination separately from the visit inside.',url:'https://www.sgns.cn/understand/sqg'}:null;
 return `<aside class="match-route-plan"><div><span class="eyebrow">YOUR ROUTE</span><h3>${esc(matchPlaceName(start))} → ${esc(matchPlaceName(end))}</h3><span class="match-route-kind">${matchCopy(...labels[kind])}</span></div><p>${esc(note)}</p>${official?`<p>${matchCopy(official.zh,official.en)} <a href="${official.url}" target="_blank" rel="noopener">${matchCopy('景区官方说明','Official visitor information')} ↗</a></p>`:''}${route&&originChengdu?`<a href="#/route/${route.id}">${matchCopy('参考行程','Itinerary idea')} · ${esc(tourText(route,'name'))} ↗</a>`:d?`<a href="#/destination/${d.id}">${matchCopy('查看目的地资料','View destination information')} ↗</a>`:''}<small>${matchCopy('实际里程、车程与路况请按出行日导航确认。','Confirm driving distance, time and road conditions with navigation for your travel day.')}</small></aside>`;
}
function submitRouteMatch(e){
 e.preventDefault();const a=matchPlaceInput('start'),b=matchPlaceInput('destination'),result=validateMatchPlaces(a.dataset.placeId,b.dataset.placeId,a.value.trim(),b.value.trim());
 if(result.error){const input=matchPlaceInput(result.field);input.setAttribute('aria-invalid','true');q(input.id+'-error').textContent=result.error;matchTripChanged();openMatchPlace(result.field,true);return}
 const n={startId:result.start.id,destinationId:result.destination.id,start:result.start.name,destination:result.destination.name,people:+q('m-people').value,bags:+q('m-bags').value,budget:+q('m-budget').value,type:q('m-type').value,priority:q('m-priority').value};
 if(!(n.people>=1&&n.people<=30)||![1,2,3,4,5,6,7,8].includes(n.bags)||![700,1000,1500].includes(n.budget)){return}
 closeMatchPlaces();state.matchRequest=n;let list=routeMatchCandidates(n);state.matchPriorityRelaxed=false;if(!list.length){list=routeMatchCandidates(n,{relaxPriority:true});state.matchPriorityRelaxed=list.length>0}state.match=list;state.matchNeeds={people:n.people,bags:n.bags};render();(q('match-result')||q('match-empty'))?.scrollIntoView({block:'start',behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
}
