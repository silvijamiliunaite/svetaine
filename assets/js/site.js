/* Titulinio puslapio efektai: nuotrauka lieka vietoje, skrolinant tamsėja, o viršutinė juosta tampa vientisa. */
(function(){var r=document.documentElement;function f(){var y=scrollY,h=innerHeight;r.style.setProperty('--dark',Math.min(.8,y/h*.8).toFixed(3));document.querySelectorAll('.top.on-photo').forEach(function(t){t.classList.toggle('solid',y>h*.5)})}addEventListener('scroll',f,{passive:true});addEventListener('resize',f);f()})();

/* Žinutės langelis ir formos siuntimas (Web3Forms) */
document.addEventListener('click',function(e){var o=e.target.closest('[data-open]');if(o){var d=(o.closest('.pg')||document).querySelector('dialog.mdlg');if(d&&d.showModal){e.preventDefault();var sj=d.querySelector('[name=subject]');if(sj&&o.dataset.subject)sj.value=o.dataset.subject;d.showModal()}return}
if(e.target.matches('dialog.mdlg')||e.target.closest('[data-close]')){e.target.closest('dialog').close()}});
document.addEventListener('submit',function(e){var f=e.target.closest('form.mform');if(!f)return;e.preventDefault();
var n=f.querySelector('.fnote'),b=f.querySelector('button.btn'),k=f.dataset.key;if(f.querySelector('[name=botcheck]').checked)return;
function bad(){b.disabled=false;n.className='fnote bad';n.textContent=f.dataset.err+f.dataset.mail}
function ok(){f.reset();b.disabled=false;n.className='fnote ok';n.textContent=f.dataset.ok}
if(!k){bad();return}b.disabled=true;n.className='fnote';n.textContent=f.dataset.sending;
if(k==='demo'){setTimeout(ok,700);return}
fetch('https://api.web3forms.com/submit',{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(f)))})
.then(function(r){return r.json()}).then(function(x){if(!x.success)throw 0;ok()}).catch(bad)});

/* Muzika: ištraukų grotuvas, paieška ir filtrai */
(function(){var au=new Audio(),cur=null,pl=null;au.preload='none';
function R(el){return el.closest('.pg')||document}
function fmt(s){s=Math.floor(s||0);return Math.floor(s/60)+':'+('0'+s%60).slice(-2)}
function ui(){document.querySelectorAll('.play').forEach(function(b){b.classList.toggle('on',b===cur&&!au.paused)});if(pl)pl.querySelector('.pp').className='pp'+(au.paused?'':' on')}
function norm(s){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}
function filter(r){var q=norm(r.querySelector('.wsearch').value.trim()),c=r.querySelector('.chip.on').dataset.cat,n=0;r.querySelectorAll('.work').forEach(function(w){var ok=(c==='all'||(' '+w.dataset.cat+' ').indexOf(' '+c+' ')>-1)&&(!q||w.dataset.q.indexOf(q)>-1);w.hidden=!ok;if(ok)n++});r.querySelector('.nores').hidden=n>0}
document.addEventListener('click',function(e){var b=e.target.closest('.play:not(.none)');
if(b){pl=R(b).querySelector('.player');if(cur===b){au.paused?au.play():au.pause()}else{cur=b;au.src=b.dataset.src;au.play()}pl.hidden=false;pl.querySelector('.ptitle').textContent=b.dataset.title;pl.querySelector('.ptime').textContent='';document.body.classList.add('hasplayer');ui();return}
if(e.target.closest('.pp')){au.paused?au.play():au.pause();return}
if(e.target.closest('.px')){au.pause();e.target.closest('.player').hidden=true;document.body.classList.remove('hasplayer');cur=null;ui();return}
var c=e.target.closest('.chip');if(c){var r=R(c);r.querySelectorAll('.chip').forEach(function(x){x.classList.toggle('on',x===c)});filter(r)}});
document.addEventListener('input',function(e){if(e.target.matches('.pbar')&&au.duration)au.currentTime=e.target.value/1000*au.duration;if(e.target.matches('.wsearch'))filter(R(e.target))});
au.addEventListener('play',ui);au.addEventListener('pause',ui);au.addEventListener('ended',ui);
au.addEventListener('timeupdate',function(){if(!pl)return;pl.querySelector('.pbar').value=au.duration?au.currentTime/au.duration*1000:0;pl.querySelector('.ptime').textContent=fmt(au.currentTime)+' / '+fmt(au.duration)});
au.addEventListener('error',function(){if(pl)pl.querySelector('.ptime').textContent=pl.dataset.err})})();

/* Vaizdo įrašai: iframe įkeliamas tik paspaudus (greitesnis puslapis, mažiau sekimo) */
document.addEventListener('click',function(e){var m=e.target.closest('.media[data-embed]');if(!m)return;var f=document.createElement('iframe');f.src=m.dataset.embed;f.allow='autoplay; fullscreen; picture-in-picture';f.allowFullscreen=true;f.title=m.getAttribute('aria-label')||'';f.referrerPolicy='strict-origin-when-cross-origin';m.replaceWith(f);f.className='media live'});

/* Galerija: filtrai ir peržiūra per visą ekraną (rodyklės, Esc, braukimas) */
(function(){var d,items=[],i=0,x0=null;
function root(el){return el.closest('.pg')||document}
function vis(g){return [].slice.call(g.querySelectorAll('.gi')).filter(function(b){return !b.parentNode.hidden})}
function show(n){var b=items[n];if(!b)return;i=n;var s=b.dataset.full;if(window.PVMAP&&PVMAP[s])s=PVMAP[s];d.querySelector('img').src=s;d.querySelector('.cap').textContent=b.dataset.cap||'';d.querySelector('.cnt').textContent=(n+1)+' / '+items.length}
function go(k){if(items.length)show((i+k+items.length)%items.length)}
document.addEventListener('click',function(e){var b=e.target.closest('.gi');
if(b){d=root(b).querySelector('dialog.lbx');items=vis(b.closest('.gal'));show(items.indexOf(b));d.showModal();return}
var c=e.target.closest('.gchip');if(c){var r=root(c);r.querySelectorAll('.gchip').forEach(function(z){z.classList.toggle('on',z===c)});r.querySelectorAll('.gal li').forEach(function(li){li.hidden=!(c.dataset.cat==='all'||(' '+li.dataset.cat+' ').indexOf(' '+c.dataset.cat+' ')>-1)});return}
if(e.target.closest('.lnext')){go(1);return}if(e.target.closest('.lprev')){go(-1);return}
if(e.target.closest('.lclose')||e.target.matches('dialog.lbx')){e.target.closest('dialog').close()}});
document.addEventListener('keydown',function(e){if(!d||!d.open)return;if(e.key==='ArrowRight')go(1);if(e.key==='ArrowLeft')go(-1)});
document.addEventListener('touchstart',function(e){if(e.target.closest('dialog.lbx'))x0=e.touches[0].clientX},{passive:true});
document.addEventListener('touchend',function(e){if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;x0=null;if(Math.abs(dx)>50)go(dx<0?1:-1)},{passive:true})})();

/* Press kit: tekstų kopijavimas */
document.addEventListener('click',function(e){var b=e.target.closest('.copy');if(!b)return;var box=b.closest('.biobox,details'),el=box.querySelector('.biotxt'),o=b.textContent;
function ok(){b.textContent=b.dataset.ok;setTimeout(function(){b.textContent=o},1800)}
function sel(){var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r)}
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(el.innerText.trim()).then(ok).catch(sel)}else sel()});
/* Galerija: vienodo aukščio eilutės. Eilučių lūžiai parenkami taip, kad visų eilučių aukštis būtų kuo panašesnis (dinaminis programavimas); kiekviena eilutė tiksliai užpildo plotį, nuotraukos nesikarpo */
(function(){var ul=document.querySelector('.gal');if(!ul)return;
function lay(){var W=ul.clientWidth;if(!W)return;var gap=W<820?6:10;var H=W<560?135:W<820?170:W<1100?210:230;
var li=[].filter.call(ul.children,function(x){return x.tagName==='LI'&&!x.hidden});ul.classList.add('jl');
var A=li.map(function(el){return parseFloat(el.style.getPropertyValue('--a'))||1.5}),N=A.length;if(!N){ul.style.height='0px';return}
var pre=[0];A.forEach(function(a,i){pre.push(pre[i]+a)});
function rowH(i,j){return (W-gap*(j-i-1))/(pre[j]-pre[i])}
var best=[0],from=[0],MAXN=W<560?3:W<820?4:6;
for(var j=1;j<=N;j++){best[j]=Infinity;for(var n=1;n<=MAXN&&n<=j;n++){var i=j-n,h=rowH(i,j),c;
 if(j===N&&h>H*1.25)c=0;else c=Math.pow(Math.log(h/H),2);
 if(best[i]+c<best[j]){best[j]=best[i]+c;from[j]=i}}}
var rows=[],j2=N;while(j2>0){rows.unshift([from[j2],j2]);j2=from[j2]}
var top=0;rows.forEach(function(r,ri){var i=r[0],j=r[1],n=j-i,h=rowH(i,j),last=ri===rows.length-1,full=true;if(last&&h>H*1.25){h=H;full=false}
 var x=0;for(var k=i;k<j;k++){var w=(full&&k===j-1)?W-x:A[k]*h,st=li[k].style;st.left=x+'px';st.top=top+'px';st.width=w+'px';st.height=h+'px';x+=w+gap}top+=h+gap});
ul.style.height=Math.max(top-gap,0)+'px'}
lay();var t;window.addEventListener('resize',function(){clearTimeout(t);t=setTimeout(lay,80)});
document.addEventListener('click',function(e){if(e.target.closest('.gchip'))setTimeout(lay,0)});window.addEventListener('load',lay)})();
