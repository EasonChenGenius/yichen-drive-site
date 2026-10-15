/* v51: real enquiry handoff, session-only drafts and local international phone metadata. */
function enquiryRegions(){
 const names=new Intl.DisplayNames([state.lang==='en'?'en':'zh-CN'],{type:'region'});
 return libphonenumber.getCountries().map(code=>({code,label:(code==='CN'&&state.lang!=='en'?'中国大陆':names.of(code))+' (+'+libphonenumber.getCountryCallingCode(code)+') · '+code})).sort((a,b)=>a.code==='CN'?-1:b.code==='CN'?1:a.label.localeCompare(b.label));
}
function enquiryPhoneRegionHTML(){return `<label>电话国家 / 地区<input name="phoneRegionChoice" list="enquiry-phone-regions" value="${esc(enquiryRegions().find(r=>r.code==='CN').label)}" required autocomplete="off" placeholder="搜索国家、地区或区号" onchange="validateEnquiryPhone(this.form)"><datalist id="enquiry-phone-regions">${enquiryRegions().map(r=>`<option value="${esc(r.label)}"></option>`).join('')}</datalist><input name="phoneRegion" type="hidden" value="CN"></label>`}
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
