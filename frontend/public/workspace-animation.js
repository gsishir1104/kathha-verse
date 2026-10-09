
window.startKathhaWorkspace=function(){var controller=new AbortController();function listen(name,fn){window.addEventListener(name,fn,{signal:controller.signal})}try{
var V=['ov','man','uni','que','aut','rel','set','bet','ria','msg','hlp'],cv=document.getElementById('writer-ambient'),R=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
R.setPixelRatio(Math.min(devicePixelRatio,2));var S=new THREE.Scene();S.fog=new THREE.Fog(0x111513,9,24);
var cam=new THREE.PerspectiveCamera(45,1,.1,60);
S.add(new THREE.AmbientLight(0x7a9a8c,.55));var L=new THREE.PointLight(0xffb48a,2.2,22);L.position.set(-3,4,3);S.add(L);
var G=new THREE.Group();S.add(G);
function lines(w,h,seed){var c=document.createElement('canvas');c.width=340;c.height=420;var x=c.getContext('2d');x.fillStyle='#efe3c8';x.fillRect(0,0,340,420);x.fillStyle='#6b5a38';x.fillRect(36,36,120,10);
for(var r=0;r<19;r++){var y=76+r*18,ww=200+((r*41+seed*67)%80);if(r===6+seed%3){x.fillStyle='rgba(201,96,106,.5)';x.fillRect(34,y-10,ww+4,15)}x.fillStyle='#b8a782';x.fillRect(36,y-4,ww,4)}
return new THREE.CanvasTexture(c)}
function mat(t){return new THREE.MeshStandardMaterial({map:t,roughness:.9,side:THREE.DoubleSide})}
var cover=new THREE.Mesh(new THREE.BoxGeometry(7.6,.28,4.8),new THREE.MeshStandardMaterial({color:0x3a2a24,roughness:.7}));cover.position.y=-.16;G.add(cover);
[-1,1].forEach(function(sd,i){var st=new THREE.Mesh(new THREE.BoxGeometry(3.5,.16,4.3),new THREE.MeshStandardMaterial({color:0xe9dfc5,roughness:.9}));st.position.set(sd*1.76,.06,0);st.rotation.z=-sd*.035;G.add(st);
var tp=new THREE.Mesh(new THREE.PlaneGeometry(3.4,4.2),mat(lines(0,0,i+1)));tp.rotation.x=-Math.PI/2;tp.rotation.z=0;tp.position.set(sd*1.76,.16+Math.abs(sd)*0,0);tp.position.y=.145;tp.rotation.order='YXZ';G.add(tp)});
var pv=new THREE.Group();pv.position.set(0,.2,0);G.add(pv);
var fp=new THREE.Mesh(new THREE.PlaneGeometry(3.4,4.2),mat(lines(0,0,5)));fp.rotation.x=-Math.PI/2;fp.position.x=1.72;pv.add(fp);
var ink=new THREE.Mesh(new THREE.CylinderGeometry(.38,.45,.55,24),new THREE.MeshStandardMaterial({color:0x1a2420,roughness:.2,metalness:.3}));ink.position.set(4.7,.1,1.3);G.add(ink);
var q=new THREE.Group();q.position.set(4.7,.35,1.3);q.rotation.z=-.55;q.rotation.y=.4;G.add(q);
var sh=new THREE.Mesh(new THREE.CylinderGeometry(.025,.02,3.2,8),new THREE.MeshStandardMaterial({color:0xd9cdb0}));sh.position.y=1.6;q.add(sh);
var fe=new THREE.Mesh(new THREE.ConeGeometry(.3,2.1,16),new THREE.MeshStandardMaterial({color:0xe9dfc5,roughness:.8}));fe.scale.z=.12;fe.position.y=2.3;q.add(fe);
var W=['once upon a time','chapter','reader','writer','beta reader','book','story','plot','page','ink','the end','imagine'],cl=['#ece6d6','#7fbfa9','#e59097'],ws=[];
W.forEach(function(w,i){var c=document.createElement('canvas');c.width=256;c.height=64;var x=c.getContext('2d');x.font='italic 32px Georgia,serif';x.textAlign='center';x.filter='blur(2px)';x.shadowColor=cl[i%3];x.shadowBlur=12;x.fillStyle=cl[i%3];x.fillText(w,128,42);
var sp=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),transparent:true,depthWrite:false,opacity:0}));sp.scale.set(2.2,.55,1);G.add(sp);ws.push({s:sp,o:i/W.length,x:(Math.random()-.5)*5,z:(Math.random()-.5)*2.5})});
var flipT=-1,last=0,tl=0,ang=0,ta=0,mx=0,my=0,reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
function flip(){if(flipT<0&&!reduce)flipT=0}
var aim=function(v){var n=V.indexOf(v);ta=(n-5)*.13;flip();if(reduce)draw(0)};
function size(){var w=innerWidth,h=innerHeight;R.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();G.position.x=w>900?3.6:0;G.position.y=-.6;G.scale.setScalar(w>900?1:.7)}
function draw(t){var s=t*.001,dt=s-last;last=s;if(s-tl>8){tl=s;flip()}
if(flipT>=0){flipT+=dt/1.5;var e=Math.min(flipT,1);e=e*e*(3-2*e);pv.rotation.z=Math.PI*e;fp.position.y=Math.sin(Math.PI*e)*.15;if(flipT>=1){flipT=-1;pv.rotation.z=0;fp.position.y=0}}
ws.forEach(function(w){var u=(s*.1+w.o)%1;w.s.position.set(w.x+Math.sin(s*.5+w.o*9)*.4,.5+u*4.8,w.z);w.s.material.opacity=reduce?.55:Math.sin(u*Math.PI)*.5});
ang+=(ta-ang)*(reduce?1:.04);cam.position.set(Math.sin(ang+mx*.3)*8.4,3.6-my*1.2,Math.cos(ang+mx*.3)*8.4);cam.lookAt(G.position.x*.5,.8,0);
L.intensity=2.1+Math.sin(s*2)*.15;R.render(S,cam)}
var frame;function loop(t){draw(t);frame=requestAnimationFrame(loop)}
listen('resize',function(){size();if(reduce)draw(0)});
listen('pointermove',function(e){mx=e.clientX/innerWidth-.5;my=e.clientY/innerHeight-.5;});
listen('kathha-workspace-view',function(e){aim(e.detail)});
size();if(reduce)draw(0);else frame=requestAnimationFrame(loop);
return function(){cancelAnimationFrame(frame);controller.abort();S.traverse(function(o){if(o.geometry)o.geometry.dispose();if(o.material){if(o.material.map)o.material.map.dispose();o.material.dispose()}});R.dispose()};
}catch(e){console.warn("Workspace animation unavailable",e)}};