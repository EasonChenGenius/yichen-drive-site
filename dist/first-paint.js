/* Route styles and optional motion never block the parser-painted home hero. */
const routeStyleJobs=new Map();
function ensureRouteStyles(route,resume){
 const sheets=[];
 if(route==='/search'||route.startsWith('/car/')||route==='/garage'||route==='/match')sheets.push('vehicle');
 if(route==='/match')sheets.push('match');
 const pending=sheets.filter(name=>routeStyleJobs.get(name)!=='ready');
 if(!pending.length)return true;
 for(const name of pending)if(!routeStyleJobs.has(name)){
  const link=document.createElement('link');link.rel='stylesheet';link.href='./'+name+'.css?v=20261017-auth-v57';
  const job=new Promise((resolve,reject)=>{link.onload=()=>{routeStyleJobs.set(name,'ready');resolve()};link.onerror=()=>{routeStyleJobs.delete(name);link.remove();reject(new Error('页面样式加载失败'))}});
  routeStyleJobs.set(name,job);document.head.append(link);
 }
 const expected=location.hash;
 Promise.all(pending.map(name=>routeStyleJobs.get(name))).then(()=>{if(location.hash===expected)resume()}).catch(()=>{
  if(location.hash!==expected)return;
  document.getElementById('app').innerHTML='<main class="page wrap"><h1>页面暂时无法加载</h1><p role="alert">请检查网络后重试。</p><button class="btn" onclick="render()">重新加载</button></main>';
 });
 return false;
}
let optionalMotionJob;
function loadOptionalMotion(){
 if(optionalMotionJob)return optionalMotionJob;
 const script=src=>new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>{s.remove();reject(new Error('Optional motion unavailable'))};document.head.append(s)});
 optionalMotionJob=script('./gsap.min.js').then(()=>script('./ScrollTrigger.min.js'));
 return optionalMotionJob;
}
let motionRevision=0;
function schedulePageMotion(route,isNewRoute){
 const revision=++motionRevision;
 if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 // Two frames allow the useful content to paint before animation work begins.
 requestAnimationFrame(()=>requestAnimationFrame(()=>{
  const run=()=>{if(revision!==motionRevision)return;loadOptionalMotion().then(()=>{if(revision===motionRevision)initMotion(route,isNewRoute)}).catch(()=>{})};
  if(window.requestIdleCallback)requestIdleCallback(run,{timeout:2500});else setTimeout(run,150);
 }));
}
