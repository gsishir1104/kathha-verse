
window.startKathhaBeta=function(){var controller=new AbortController();function listen(name,fn){window.addEventListener(name,fn,{signal:controller.signal})}try{
var V=['hm','lib','rd','rq','fb','ins','inv','prof','msg','dis','hlp'],cv=document.getElementById('beta-ambient'),R=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
R.setPixelRatio(Math.min(devicePixelRatio,2));var S=new THREE.Scene();S.fog=new THREE.Fog(0x111513,10,26);
var cam=new THREE.PerspectiveCamera(45,1,.1,60);
S.add(new THREE.AmbientLight(0x6f8a7e,.5));
var sp=new THREE.SpotLight(0xffc89a,2.6,22,.9,.6,1);sp.position.set(-3.1,3.2,-1.2);S.add(sp,sp.target);sp.target.position.set(0,1,0);
var G=new THREE.Group();S.add(G);
var desk=new THREE.Mesh(new THREE.BoxGeometry(40,.4,18),new THREE.MeshStandardMaterial({color:0x1a1613,roughness:.85}));desk.position.y=-.2;G.add(desk);
var st=new THREE.Group();G.add(st);var y=0;
[[3.8,.45,2.8,0x27382f],[3.4,.4,2.6,0x4a2a2e],[3.6,.5,2.7,0x3a3a2a],[3.1,.38,2.4,0x2d3d3a],[3.3,.42,2.5,0x5a4630]].forEach(function(b){var g=new THREE.Group();
g.add(new THREE.Mesh(new THREE.BoxGeometry(b[0],b[1],b[2]),new THREE.MeshStandardMaterial({color:b[3],roughness:.7})));
g.add(new THREE.Mesh(new THREE.BoxGeometry(b[0]-.14,b[1]-.1,b[2]+.1),new THREE.MeshStandardMaterial({color:0xe9dfc5,roughness:.9})));
g.position.y=y+b[1]/2;g.rotation.y=(Math.random()-.5)*.35;st.add(g);y+=b[1]});
var gl=new THREE.Group(),br=new THREE.MeshStandardMaterial({color:0xc7b27a,metalness:.6,roughness:.3});
[-.42,.42].forEach(function(x){var l=new THREE.Mesh(new THREE.TorusGeometry(.3,.035,12,32),br);l.rotation.x=-Math.PI/2;l.position.x=x;gl.add(l);var t=new THREE.Mesh(new THREE.CylinderGeometry(.02,.02,1.2,8),br);t.rotation.x=Math.PI/2;t.position.set(x*1.7,0,-.6);gl.add(t)});
var bg=new THREE.Mesh(new THREE.CylinderGeometry(.025,.025,.24,8),br);bg.rotation.z=Math.PI/2;gl.add(bg);gl.position.set(0,y+.06,.3);gl.rotation.y=.35;st.add(gl);var gy=y+.06;
var mug=new THREE.Mesh(new THREE.CylinderGeometry(.45,.4,.75,32),new THREE.MeshStandardMaterial({color:0xd9cdb0,roughness:.5}));mug.position.set(3.4,.375,1.4);G.add(mug);
var cf=new THREE.Mesh(new THREE.CircleGeometry(.4,32),new THREE.MeshStandardMaterial({color:0x2a1a12}));cf.rotation.x=-Math.PI/2;cf.position.set(3.4,.74,1.4);G.add(cf);
var hd=new THREE.Mesh(new THREE.TorusGeometry(.22,.05,10,20,Math.PI),new THREE.MeshStandardMaterial({color:0xd9cdb0,roughness:.5}));hd.rotation.z=-Math.PI/2;hd.position.set(3.85,.38,1.4);G.add(hd);
var lm=new THREE.MeshStandardMaterial({color:0x2a2f2c,roughness:.5,metalness:.4});
var lb=new THREE.Mesh(new THREE.CylinderGeometry(.6,.7,.15,24),lm);lb.position.set(-3.6,.075,-1.2);G.add(lb);
var ls=new THREE.Mesh(new THREE.CylinderGeometry(.05,.05,3.2,10),lm);ls.position.set(-3.6,1.7,-1.2);G.add(ls);
var sh=new THREE.Mesh(new THREE.ConeGeometry(.75,.9,28,1,true),new THREE.MeshStandardMaterial({color:0x7fbfa9,emissive:0x3a2a14,roughness:.5,side:THREE.DoubleSide}));sh.position.set(-3.4,3.35,-1.2);sh.rotation.z=.8;G.add(sh);
function sprTex(){var c=document.createElement('canvas');c.width=c.height=64;var x=c.getContext('2d'),g=x.createRadialGradient(32,32,0,32,32,32);g.addColorStop(0,'rgba(236,230,214,.9)');g.addColorStop(1,'rgba(236,230,214,0)');x.fillStyle=g;x.fillRect(0,0,64,64);return new THREE.CanvasTexture(c)}
var stx=sprTex(),steam=[];for(var i=0;i<12;i++){var q=new THREE.Sprite(new THREE.SpriteMaterial({map:stx,transparent:true,depthWrite:false,opacity:0}));G.add(q);steam.push({s:q,o:i/12})}
function noteTex(c1){var c=document.createElement('canvas');c.width=128;c.height=96;var x=c.getContext('2d');x.fillStyle='#efe3c8';x.fillRect(0,0,128,96);x.fillStyle=c1;x.fillRect(0,0,128,14);x.fillStyle='#b8a782';for(var r=0;r<4;r++)x.fillRect(12,32+r*16,90-r*10,4);return new THREE.CanvasTexture(c)}
var notes=[];['#7fbfa9','#c9606a','#7fbfa9','#c9606a','#7fbfa9','#c9606a'].forEach(function(c,i){var m=new THREE.Mesh(new THREE.PlaneGeometry(.9,.68),new THREE.MeshStandardMaterial({map:noteTex(c),transparent:true,opacity:.85,side:THREE.DoubleSide}));var a=i*1.05+.3;G.add(m);notes.push({m:m,a:a,r:3.4+(i%3)*.5,h:1.8+(i%4)*.55,t:(i%2?.15:-.15)})});
var pp=new Float32Array(450);for(var k=0;k<450;k++)pp[k]=(Math.random()-.5)*18;var pb=new THREE.BufferGeometry();pb.setAttribute('position',new THREE.BufferAttribute(pp,3));
var dust=new THREE.Points(pb,new THREE.PointsMaterial({color:0xd9cdb0,size:.04,transparent:true,opacity:.5}));dust.position.y=3;S.add(dust);
var ang=0,ta=0,sy=0,tsy=0,bob=0,mx=0,my=0,reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
var aim=function(v){var n=V.indexOf(v);ta=(n-5)*.13;tsy=n*.09;bob=reduce?0:1;if(reduce)draw(0)};
function size(){var w=innerWidth,h=innerHeight;R.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();G.position.x=w>900?3.2:0;G.position.y=-.8;G.scale.setScalar(w>900?1:.7)}
function draw(t){var s=t*.001;ang+=(ta-ang)*(reduce?1:.04);sy+=(tsy-sy)*(reduce?1:.05);st.rotation.y=sy;bob*=.95;gl.position.y=gy+Math.abs(Math.sin(bob*8))*.18*bob;
steam.forEach(function(p){var u=(s*.12+p.o)%1;p.s.position.set(3.4+Math.sin(s+p.o*6)*.25*u,1+u*2.4,1.4);p.s.scale.setScalar(.5+u*1.1);p.s.material.opacity=reduce?.12:Math.sin(u*Math.PI)*.22});
notes.forEach(function(n){n.m.position.set(Math.cos(n.a+s*.04)*n.r,n.h+Math.sin(s*.6+n.a)*.15,Math.sin(n.a+s*.04)*n.r);n.m.lookAt(cam.position);n.m.rotateZ(n.t)});
cam.position.set(Math.sin(ang+mx*.3)*9.2,3.8-my*1.2,Math.cos(ang+mx*.3)*9.2);cam.lookAt(G.position.x*.5,.4,0);
sp.intensity=2.5+Math.sin(s*2)*.1;R.render(S,cam)}
var frame;function loop(t){draw(t);frame=requestAnimationFrame(loop)}
listen('resize',function(){size();if(reduce)draw(0)});
listen('pointermove',function(e){mx=e.clientX/innerWidth-.5;my=e.clientY/innerHeight-.5});
listen('kathha-beta-view',function(e){aim(e.detail)});
size();if(reduce)draw(0);else frame=requestAnimationFrame(loop);
return function(){cancelAnimationFrame(frame);controller.abort();S.traverse(function(o){if(o.geometry)o.geometry.dispose();if(o.material){if(o.material.map)o.material.map.dispose();o.material.dispose()}});R.dispose()};
}catch(e){console.warn("Beta background unavailable",e)}};
