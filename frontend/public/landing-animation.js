window.startKathhaPages=function(){var controller=new AbortController();function listen(name,fn,options){window.addEventListener(name,fn,Object.assign({},options,{signal:controller.signal}))}
try{
var cv=document.getElementById('c'),R=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
R.setPixelRatio(Math.min(devicePixelRatio,2));
var S=new THREE.Scene();S.fog=new THREE.Fog(0x111513,9,26);
var cam=new THREE.PerspectiveCamera(45,1,.1,60);cam.position.set(0,0,11);
S.add(new THREE.AmbientLight(0x7a9a8c,.55));
var L=new THREE.PointLight(0xffb48a,1.6,40);L.position.set(0,1,7);S.add(L);
var G=new THREE.Group();S.add(G);
function tex(i){var c=document.createElement('canvas');c.width=256;c.height=340;var x=c.getContext('2d');
x.fillStyle='#efe3c8';x.fillRect(0,0,256,340);x.fillStyle='#6b5a38';x.fillRect(28,30,110,9);
for(var r=0;r<17;r++){var y=62+r*15,w=150+((r*37+i*53)%60);
if(i%3===0&&(r===5||r===6)){x.fillStyle='rgba(201,96,106,.55)';x.fillRect(26,y-8,w+4,13)}
if(i%4===1&&r===10){x.fillStyle='rgba(127,191,169,.6)';x.fillRect(26,y-8,w+4,13)}
x.fillStyle='#b8a782';x.fillRect(28,y-4,w,4)}
var t=new THREE.CanvasTexture(c);return t}
var N=18,pg=[];
for(var i=0;i<N;i++){var m=new THREE.Mesh(new THREE.PlaneGeometry(2.2,2.9),new THREE.MeshStandardMaterial({map:tex(i),side:THREE.DoubleSide,roughness:.9}));
var a=i*.6;m.position.set(Math.cos(a)*4.2,(i-N/2)*.7,Math.sin(a)*4.2);m.rotation.y=Math.PI/2-a;m.rotation.z=Math.sin(i)*.08;G.add(m);pg.push(m)}
var pn=300,pp=new Float32Array(pn*3);for(var k=0;k<pn*3;k++)pp[k]=(Math.random()-.5)*22;
var pb=new THREE.BufferGeometry();pb.setAttribute('position',new THREE.BufferAttribute(pp,3));
var dust=new THREE.Points(pb,new THREE.PointsMaterial({color:0xd9cdb0,size:.05,transparent:true,opacity:.6}));S.add(dust);
var mx=0,my=0,prog=0,reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
function size(){var w=innerWidth,h=innerHeight;R.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();G.position.x=w>900?3:0;G.scale.setScalar(w>900?1:.7)}
function scroll(){var d=document.documentElement.scrollHeight-innerHeight;prog=d>0?scrollY/d:0}
function draw(t){G.rotation.y=prog*Math.PI*2.4+(reduce?0:t*.00006);G.position.y=prog*6-3;
cam.position.x+=(mx*.8-cam.position.x)*.05;cam.position.y+=(-my*.5-cam.position.y)*.05;cam.lookAt(G.position.x*.4,0,0);
dust.rotation.y=t*.00003;L.intensity=1.5+Math.sin(t*.002)*.12;R.render(S,cam)}
var frame;function loop(t){draw(t);frame=requestAnimationFrame(loop)}
listen('resize',function(){size();if(reduce)draw(0)});
listen('scroll',function(){scroll();if(reduce)draw(0)},{passive:true});
listen('pointermove',function(e){mx=e.clientX/innerWidth-.5;my=e.clientY/innerHeight-.5});
size();scroll();if(reduce)draw(0);else frame=requestAnimationFrame(loop);
return function(){cancelAnimationFrame(frame);controller.abort();S.traverse(function(o){if(o.geometry)o.geometry.dispose();if(o.material){if(o.material.map)o.material.map.dispose();o.material.dispose()}});R.dispose()};
}catch(e){}
};