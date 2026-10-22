// Googoo Robo service worker. tools/build.py rewrites the two versions below on every build:
// a new page build = new shell cache, new/changed audio = new audio cache; old caches are deleted on activate.
const SHELL_V='39b727b810',AUDIO_V='92904cdb22',SHELL='googoo-shell-'+SHELL_V,AUDIO='googoo-audio-'+AUDIO_V;
const PRE=['./','manifest.webmanifest','icons/icon-192.png','icons/icon-512.png','icons/apple-touch-icon.png','audio/manifest.json','vocab/stories.json',
  'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
  'https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js',
  'https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&family=Vazirmatn:wght@600;800&display=swap'];
self.addEventListener('install',e=>e.waitUntil(caches.open(SHELL).then(c=>c.addAll(PRE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('googoo-')&&k!==SHELL&&k!==AUDIO).map(k=>caches.delete(k))))
  .then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url),mp3=/\.(mp3|glb)$/.test(u.pathname);
  const keep=res=>{if(res.ok){const c=res.clone();caches.open(mp3?AUDIO:SHELL).then(x=>x.put(r,c))}return res};
  if(mp3||u.origin!==location.origin)e.respondWith(caches.match(r).then(hit=>hit||fetch(r).then(keep))); // audio, three.js, fonts: cache first
  else e.respondWith(fetch(r).then(keep).catch(()=>caches.match(r,{ignoreSearch:true}))); // page + data: network first, so updates arrive
});
