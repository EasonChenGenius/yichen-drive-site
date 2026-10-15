const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=path.join(__dirname,'../dist');const ctx={console,Intl,state:{lang:'zh'},libphonenumber:require(path.join(root,'vendor/libphonenumber-max-1.13.15.js'))};vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(root,'enquiry-flow.js'),'utf8'),ctx);
function form(region,phone){const field=()=>({value:'',setCustomValidity(m){this.error=m}});const f={elements:{phoneRegionChoice:field(),phone:field(),phoneRegion:field()}};f.elements.phoneRegionChoice.value=ctx.enquiryRegions().find(r=>r.code===region).label;f.elements.phone.value=phone;return f}
for(const [region,input,result] of [['CN','13800138000','+8613800138000'],['US','2025550123','+12025550123'],['HK','61234567','+85261234567'],['CN','00000000000',''],['US','1111111111',''],['CN','+12025550123','']])assert.equal(ctx.validateEnquiryPhone(form(region,input)),result);
const op=fs.readFileSync(path.join(root,'operator.js'),'utf8');vm.runInContext(op.slice(op.indexOf('function inquiryDurationLabel'),op.indexOf('async function loadUsers')),ctx);
assert.equal(ctx.inquiryDurationLabel({startAt:'2026-10-16T10:00',endAt:'2026-10-21T10:00',durationDays:6}),'5 天（按24小时估算）');
assert.equal(ctx.inquiryDurationLabel({durationDays:6}),'6 天（原记录，时刻不完整）');
console.log('PASS v51 UI: international metadata validation and historical duration rendering; no records rewritten.');
