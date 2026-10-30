// Launch rocket built from clean shapes (crisp edges, plastic/metal look, bulged black glass). Units: Googoo is ~4 tall; this is ~3.55.
function makeRocket(){
  const g=new THREE.Group(),SEG=72,C=h=>new THREE.Color(h).convertSRGBToLinear();
  const white=new THREE.MeshPhysicalMaterial({color:C(0xeeeae2),roughness:.3,metalness:.12,clearcoat:.7,clearcoatRoughness:.2});
  const orange=new THREE.MeshPhysicalMaterial({color:C(0xd2501a),roughness:.36,metalness:.08,clearcoat:.5,clearcoatRoughness:.25});
  const dark=new THREE.MeshStandardMaterial({color:C(0x3a1a0a),roughness:.7});
  const glass=new THREE.MeshPhysicalMaterial({color:C(0x07080c),roughness:.05,metalness:0,clearcoat:1,clearcoatRoughness:.03});
  const glint=new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:.85});
  // body profile (radius, height): rounded base, widest at ~1.3, ogive nose with a softly rounded tip
  const pts=new THREE.SplineCurve([[.6,.42],[.8,.52],[.93,.8],[.98,1.2],[.97,1.7],[.9,2.15],[.75,2.6],[.52,3.0],[.27,3.32],[.1,3.5],[.0,3.54]].map(p=>new THREE.Vector2(...p))).getPoints(90);
  const rAt=y=>{for(let i=1;i<pts.length;i++)if(pts[i].y>=y){const a=pts[i-1],b=pts[i],t=(y-a.y)/(b.y-a.y||1);return a.x+(b.x-a.x)*t}return 0};
  g.add(new THREE.Mesh(new THREE.LatheGeometry([new THREE.Vector2(0,.42),...pts],SEG),white));
  // orange bands: a slightly proud copy of the body between two heights, square edges
  const band=(y0,y1,o=.025)=>{const p=[new THREE.Vector2(rAt(y0)-.01,y0)];for(let i=0;i<=12;i++){const y=y0+(y1-y0)*i/12;p.push(new THREE.Vector2(rAt(y)+o,y))}p.push(new THREE.Vector2(rAt(y1)-.01,y1));
    return new THREE.Mesh(new THREE.LatheGeometry(p,SEG),orange)};
  g.add(band(2.42,2.6),band(.6,.78));
  // bell nozzle with a dark throat
  const nz=new THREE.Mesh(new THREE.LatheGeometry([[.24,.47],[.36,.42],[.4,.3],[.47,.12],[.52,.03],[.47,.03],[.39,.14],[.22,.3]].map(p=>new THREE.Vector2(...p)),SEG),orange);nz.material.side=THREE.DoubleSide;g.add(nz);
  const th=new THREE.Mesh(new THREE.CircleGeometry(.46,SEG),dark);th.rotation.x=Math.PI/2;th.position.y=.06;g.add(th);
  // three fins (one faces the viewer, under the window): thick flat shape with a small bevel = crisp but finished edges
  const fs=new THREE.Shape();fs.moveTo(0,1.25);fs.quadraticCurveTo(.4,.95,.72,.48);fs.quadraticCurveTo(.82,.3,.78,.0);fs.lineTo(.52,.0);fs.quadraticCurveTo(.44,.3,.0,.48);fs.closePath();
  const fg=new THREE.ExtrudeGeometry(fs,{depth:.13,bevelEnabled:true,bevelThickness:.03,bevelSize:.03,bevelSegments:3,curveSegments:24});fg.translate(0,0,-.065);
  for(let i=0;i<3;i++){const f=new THREE.Mesh(fg,orange),piv=new THREE.Group();piv.rotation.y=-Math.PI/2+i*2*Math.PI/3;f.position.x=.78;piv.add(f);g.add(piv)}
  // porthole: orange ring + bulged glossy black glass + a little highlight
  const wy=1.88,wr=rAt(wy),R=.36,capR=.52,ha=Math.asin(R/capR),z0=wr-.03;
  const ring=new THREE.Mesh(new THREE.TorusGeometry(R+.02,.075,24,72),orange);ring.position.set(0,wy,z0);g.add(ring);
  const cap=new THREE.Mesh(new THREE.SphereGeometry(capR,48,24,0,Math.PI*2,0,ha),glass);cap.rotation.x=Math.PI/2;cap.position.set(0,wy,z0-capR*Math.cos(ha));g.add(cap);
  const gl=new THREE.Mesh(new THREE.TorusGeometry(R*.62,.022,8,32,Math.PI*.42),glint);gl.position.set(0,wy,z0+capR*(1-Math.cos(ha))*.82);gl.rotation.z=Math.PI*.55;g.add(gl);
  g.traverse(o=>{if(o.isMesh){o.castShadow=o.material!==glint;o.receiveShadow=true}});
  return g}
