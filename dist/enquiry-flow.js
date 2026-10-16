let enquiryPhoneLibrary;
function loadEnquiryPhoneLibrary(){if(window.libphonenumber)return Promise.resolve();if(enquiryPhoneLibrary)return enquiryPhoneLibrary;enquiryPhoneLibrary=new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='./vendor/libphonenumber-max-1.13.15.js';script.onload=()=>window.libphonenumber?resolve():reject(new Error('电话校验未能加载'));script.onerror=()=>{enquiryPhoneLibrary=null;script.remove();reject(new Error('电话校验未能加载'))};document.head.append(script)});return enquiryPhoneLibrary}
/* v51: real enquiry handoff, session-only drafts and local international phone metadata. */
function enquiryRegions(){
 const names=new Intl.DisplayNames([state.lang==='en'?'en':'zh-CN'],{type:'region'});
 return libphonenumber.getCountries().map(code=>({code,label:(code==='CN'&&state.lang!=='en'?'中国大陆':names.of(code))+' (+'+libphonenumber.getCountryCallingCode(code)+') · '+code})).sort((a,b)=>a.code==='CN'?-1:b.code==='CN'?1:a.label.localeCompare(b.label));
}
function enquiryPhoneRegionHTML(){return `<div class="phone-region-picker"><label for="phone-region-choice">电话国家 / 地区<input id="phone-region-choice" name="phoneRegionChoice" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="phone-region-results" value="${esc(enquiryRegions().find(r=>r.code==='CN').label)}" required autocomplete="off" placeholder="搜索国家、地区或区号" onfocus="showEnquiryRegions(this)" oninput="showEnquiryRegions(this,true);validateEnquiryPhone(this.form)" onkeydown="enquiryRegionKey(event)" onchange="validateEnquiryPhone(this.form)"></label><div id="phone-region-results" role="listbox" aria-label="电话国家与地区" hidden></div><datalist id="enquiry-phone-regions">${enquiryRegions().map(r=>`<option value="${esc(r.label)}"></option>`).join('')}</datalist><input name="phoneRegion" type="hidden" value="CN"></div>`}
function showEnquiryRegions(input,typed=false){
 const all=enquiryRegions(),exact=all.some(r=>r.label===input.value),term=(typed||!exact?input.value:'').trim().toLocaleLowerCase(),preferred=['CN','HK','TW','MO','SG','US','GB','AU','JP','FR','DE','CA'];
 const matches=term?all.filter(r=>r.label.toLocaleLowerCase().includes(term)):preferred.map(code=>all.find(r=>r.code===code)).filter(Boolean);
 const panel=input.form.querySelector('#phone-region-results');panel.hidden=false;input.setAttribute('aria-expanded','true');
 panel.innerHTML=matches.length?matches.slice(0,30).map(r=>`<button type="button" role="option" aria-label="${esc(r.label)}" aria-selected="${input.value===r.label}" data-region="${r.code}" onclick="chooseEnquiryRegion(this,'${r.code}')" onkeydown="enquiryRegionOptionKey(event)">${esc(r.label)}</button>`).join(''):'<p role="status">没有匹配地区，请尝试名称或区号。</p>';
}
function closeEnquiryRegions(f){const panel=f?.querySelector('#phone-region-results');if(panel)panel.hidden=true;f?.elements.phoneRegionChoice?.setAttribute('aria-expanded','false')}
function chooseEnquiryRegion(button,code){const f=button.form,input=f.elements.phoneRegionChoice;input.value=enquiryRegions().find(r=>r.code===code).label;validateEnquiryPhone(f);input.focus();closeEnquiryRegions(f);saveEnquiryDraft(f)}
function enquiryRegionKey(event){const input=event.target;if(event.key==='Escape'){event.preventDefault();closeEnquiryRegions(input.form)}else if(event.key==='ArrowDown'){event.preventDefault();showEnquiryRegions(input);input.form.querySelector('#phone-region-results [role=option]')?.focus()}else if(event.key==='Enter'&&input.getAttribute('aria-expanded')==='true'){event.preventDefault();const options=input.form.querySelectorAll('#phone-region-results [role=option]');if(options.length===1)options[0].click()}}
function enquiryRegionOptionKey(event){if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();(event.key==='ArrowDown'?event.target.nextElementSibling:event.target.previousElementSibling)?.focus()}else if(event.key==='Escape'){event.preventDefault();const input=event.target.form.elements.phoneRegionChoice;input.focus();closeEnquiryRegions(input.form)}}
if(typeof document!=='undefined')document.addEventListener('click',event=>{if(!event.target.closest('.phone-region-picker'))closeEnquiryRegions(document.querySelector('.enquiry-form'))});
function validateEnquiryPhone(f){
 const choice=f.elements.phoneRegionChoice,phone=f.elements.phone,region=enquiryRegions().find(r=>r.label===choice.value);
 choice.setCustomValidity(region?'':'请从列表选择电话国家或地区。');phone.setCustomValidity('');
 if(!region)return '';f.elements.phoneRegion.value=region.code;if(!phone.value.trim())return '';
 const parsed=libphonenumber.parsePhoneNumberFromString(phone.value.trim(),region.code);
 const valid=parsed&&parsed.country===region.code&&parsed.isValid()&&!/^(\d)\1+$/.test(parsed.nationalNumber);
 phone.setCustomValidity(valid?'':'请输入所选国家或地区的有效联系电话。');return valid?parsed.number:'';
}
function enquiryContext(){const query=new URLSearchParams(state.route.split('?')[1]||'');return JSON.stringify([query.get('car')||'',query.get('service')||'自驾租车',state.booking?.start,state.booking?.end,state.booking?.pickupId,state.booking?.returnAt])}
function saveEnquiryDraft(f){if(f.dataset.submitted==='true')return;const values=Object.fromEntries(new FormData(f));delete values.consent;sessionStorage.setItem('yichen-enquiry-draft-v51',JSON.stringify({context:f.dataset.context,values,request:f.dataset.requestBody?{body:f.dataset.requestBody,id:f.dataset.requestId}:null}))}
function enquiryPlace(value){const places=matchPlaces();return places.find(p=>p.id===value)||places.find(p=>p.id==='place-'+value)||places.find(p=>p.name===value)}
function initEnquiryForm(f){
 f.dataset.context=enquiryContext();let draft;
 try{const saved=JSON.parse(sessionStorage.getItem('yichen-enquiry-draft-v51'));if(saved?.context===f.dataset.context){draft=saved.values;if(saved.request){f.dataset.requestBody=saved.request.body;f.dataset.requestId=saved.request.id}}}catch{}
 const b=state.booking||{},m=state.matchRequest||{};const place=enquiryPlace(b.pickupId)||enquiryPlace(b.pickup)||enquiryPlace(m.start);
 const city=SERVICE_CITIES.find(c=>c.id===place?.cityKey)?.name||'成都';
 const values=draft||{city,pickupId:place?.id,returnId:(enquiryPlace(b.returnAt)?.id)||(b.same!==false?place?.id:''),destinationId:enquiryPlace(m.destination)?.id||'city-chengdu',people:m.people||2,bags:m.bags??2,startDate:b.start?.slice(0,10),endDate:b.end?.slice(0,10),startTime:b.timeConfirmed?b.start?.slice(11,16):'10:00',endTime:b.timeConfirmed?b.end?.slice(11,16):(b.start?.slice(0,10)===b.end?.slice(0,10)?'18:00':'10:00')};
 function assign(key,value){const el=f.elements[key];if(!el||value==null)return;if(el.tagName==='SELECT'&&![...el.options].some(o=>o.value===String(value)))return;el.value=String(value)}
 assign('city',values.city);updateEnquiryOptions(f);
 for(const [key,value] of Object.entries(values))if(key!=='consent'&&key!=='city')assign(key,value);
 if(draft?.phoneRegion)assign('phoneRegionChoice',enquiryRegions().find(r=>r.code===draft.phoneRegion)?.label);
 syncEnquiryDates(f);validateEnquiryPhone(f);
 f.addEventListener('input',()=>{syncEnquiryDates(f);saveEnquiryDraft(f)});
 f.addEventListener('change',()=>{syncEnquiryDates(f);validateEnquiryPhone(f);saveEnquiryDraft(f)});
}
