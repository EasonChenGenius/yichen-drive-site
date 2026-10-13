export const clamp=(value,min=0,max=1)=>Math.min(max,Math.max(min,value));
const lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>t*t*(3-2*t);
export const STORY_KEYS=[
 {at:0,angle:.05,scale:1,explode:0,camera:[1,.40,-1.15],targetY:1.1,bg:'#efede7',ink:'#171715',muted:'#716f69'},
 {at:.20,angle:-.48,scale:1.02,explode:0,camera:[1,.30,-1.05],targetY:1.16,bg:'#fbfaf7',ink:'#171715',muted:'#716f69'},
 {at:.40,angle:-1.0,scale:1.04,explode:0,camera:[.55,.32,-1.25],targetY:1.22,bg:'#30342f',ink:'#fbfaf7',muted:'#d1cec4'},
 {at:.60,angle:-.54,scale:.89,explode:1,camera:[1,.48,-1.08],targetY:1.65,bg:'#252a26',ink:'#fbfaf7',muted:'#d1cec4'},
 {at:.80,angle:.34,scale:1,explode:0,camera:[1,.36,-1.10],targetY:1.18,bg:'#efede7',ink:'#171715',muted:'#716f69'},
 {at:1,angle:.05,scale:1,explode:0,camera:[1,.40,-1.15],targetY:1.1,bg:'#fbfaf7',ink:'#171715',muted:'#716f69'}
];
export function storyPose(progress,reduced=false){const p=clamp(progress);if(reduced)return {...STORY_KEYS[0],progress:p,explode:0,chapter:Math.min(5,Math.floor(p*5+.5)),from:STORY_KEYS[0],to:STORY_KEYS[0],mix:0};let i=0;while(i<STORY_KEYS.length-2&&p>STORY_KEYS[i+1].at)i++;const a=STORY_KEYS[i],b=STORY_KEYS[i+1],mix=ease(clamp((p-a.at)/(b.at-a.at)));return {progress:p,angle:lerp(a.angle,b.angle,mix),scale:lerp(a.scale,b.scale,mix),explode:lerp(a.explode,b.explode,mix),camera:a.camera.map((v,j)=>lerp(v,b.camera[j],mix)),targetY:lerp(a.targetY,b.targetY,mix),chapter:Math.min(5,Math.floor(p*5+.5)),from:a,to:b,mix};}
export function partPosition(base,direction,amount){return base.map((value,i)=>value+direction[i]*amount);}
export function fitCameraDistance(points,target,direction,fovDegrees,aspect,padding=1.12){const length=Math.hypot(...direction),d=direction.map(n=>n/length),r0=[d[2],0,-d[0]],rl=Math.hypot(...r0),r=r0.map(n=>n/rl),u=[d[1]*r[2]-d[2]*r[1],d[2]*r[0]-d[0]*r[2],d[0]*r[1]-d[1]*r[0]],tan=Math.tan(fovDegrees*Math.PI/360),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);let required=1;for(const point of points){const p=point.map((x,i)=>x-target[i]),depth=dot(p,d);required=Math.max(required,depth+Math.abs(dot(p,u))/tan,depth+Math.abs(dot(p,r))/(tan*aspect));}return required*padding;}
