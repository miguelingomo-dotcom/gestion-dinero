"""Comparador de estilos calculados, para refactorizar CSS sin cambios visuales. Opcional: no forma parte de pytest.

Compara todos los elementos y pseudoelementos de dos versiones de la app, con Notion simulado, en muchos estados
(pestañas, modales, toasts, modo privado, idioma), los dos temas, movimiento normal y reducido, y :active/:focus/:hover.
Las capturas no ven lo que solo aparece en esos estados.

    tests/.venv/bin/python tests/comparar_estilos.py [REF_GIT] [ARCHIVO] [--rapido] [--max=N]

REF_GIT: versión de partida (por defecto HEAD). ARCHIVO: versión nueva (por defecto index-nuevo.html).
Termina con código 0 si no hay diferencias y 1 si las hay. Ignora lo que depende del tiempo: animaciones en curso y
las clases que ponen los temporizadores. No compara @keyframes ni barras de desplazamiento."""
import json,os,re,subprocess,sys
from pathlib import Path
AQUI=Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(AQUI/'.browsers'))
from playwright.sync_api import sync_playwright
import datos
from notion_mock import FakeNotion,APP_ORIGIN
_args=[x for x in sys.argv[1:] if not x.startswith('--')]
RAPIDO='--rapido' in sys.argv
MAX=next((int(x[6:]) for x in sys.argv if x.startswith('--max=')),60)
REF=_args[0] if _args else 'HEAD'
ARCHIVO=Path(_args[1]) if len(_args)>1 else datos.RAIZ/'index-nuevo.html'
A=subprocess.run(['git','show',REF+':index-nuevo.html'],cwd=datos.RAIZ,capture_output=True,text=True,check=True,encoding='utf-8').stdout
B=ARCHIVO.read_text(encoding='utf-8')
FORZAR={':active':'.__fa',':focus-visible':'.__ffv',':focus':'.__ff',':hover':'.__fh'}
def forzado(h):
    def cambia(m):
        c=m.group(2)
        for k,v in FORZAR.items(): c=c.replace(k,v)
        return m.group(1)+c+'</style>'
    return re.sub(r'(<style[^>]*>)(.*?)</style>',cambia,h,flags=re.S)
SNAP="""(n)=>{const p=['','::before','::after','::placeholder'];const out={};const conteo={};window.__s=window.__s||{};const det={};
 const h=s=>{let x=2166136261;for(let i=0;i<s.length;i++){x^=s.charCodeAt(i);x=Math.imul(x,16777619);}return x>>>0;};
 document.querySelectorAll('.count-pop').forEach(e=>e.classList.remove('count-pop'));
 try{clearTimeout(toastTimer)}catch(e){}
 document.querySelectorAll('*').forEach(e=>{if(e.classList.contains('__fa'))e.classList.add('ya-animada');else e.classList.remove('ya-animada');});
 document.querySelectorAll('.count-pop').forEach(e=>e.classList.remove('count-pop'));
 document.body.offsetHeight;
 document.getAnimations().forEach(a=>{try{a.cancel()}catch(e){}});
 document.body.offsetHeight;
 document.getAnimations().forEach(a=>{try{a.cancel()}catch(e){}});
 document.body.offsetHeight;
 document.getAnimations().forEach(a=>{try{a.cancel()}catch(e){}});
 document.body.offsetHeight;
 document.getAnimations().forEach(a=>{try{a.cancel()}catch(e){}});
 for(const el of document.querySelectorAll('*')){if(['SCRIPT','STYLE','META','TITLE','HEAD','LINK','DEFS','STOP'].includes(el.tagName.toUpperCase()))continue;
  let k=el.tagName+(el.id?'#'+el.id:'')+'.'+(el.getAttribute('class')||'').trim().split(/\\s+/).filter(c=>!c.startsWith('__f')&&c!=='ya-animada').join('.');
  if(el.parentElement&&!el.id){const pk=el.parentElement.id||(el.parentElement.getAttribute('class')||'').trim().split(/\\s+/).filter(c=>!c.startsWith('__f')&&c!=='count-pop'&&c!=='ya-animada').join('.');k=String(pk).slice(0,30)+'>'+k;}
  conteo[k]=(conteo[k]||0)+1;k+='['+conteo[k]+']';
  for(const ps of p){const cs=getComputedStyle(el,ps||undefined);if(ps&&cs.content==='none'&&ps!=='::placeholder')continue;if(ps==='::placeholder'&&!/INPUT|TEXTAREA/.test(el.tagName))continue;
   let s='';for(let i=0;i<cs.length;i++){const q=cs[i];s+=q+':'+cs.getPropertyValue(q)+';';}
   out[k+ps]=h(s);det[k+ps]=s;}}
 window.__s[n]=det;return out;}"""
def sembrar(n):
    datos.sembrar(n)
    n.anadir('cuentas',{'Nombre':datos.titulo('Vacaciones'),'Cuenta o Meta':{'select':{'name':'Meta'}},'Objetivo':{'number':1000},'AhorradoActual':{'number':250},'Emoji':{'rich_text':[{'plain_text':'🎯'}]}})
    n.anadir('cuentas',{'Nombre':datos.titulo('Bici'),'Tipo':{'select':{'name':'Wish List'}},'Precio':{'number':300},'Emoji':{'rich_text':[{'plain_text':'🚲'}]}})
PASOS=[
 ('inicio',"showSec('inicio',0)"),('desglose',"togglePatBreakdown()"),('movs',"showSec('movimientos',1)"),
 ('editmov',"openEditMovement('%s')"%datos.MOV_MERCADONA),('cierraedit',"closeEdit()"),
 ('editrans',"openEditTransfer('%s')"%datos.TR_REVOLUT),('cierratr',"closeEditTransfer()"),
 ('registrar',"showSec('registrar',-1)"),('ingreso',"setType('ingreso')"),('gasto',"setType('gasto')"),
 ('cuentas',"showSec('cuentas',2)"),('inactivas',"toggleInactivas()"),
 ('expandida',"document.querySelector('#accountCards .account-card-head').click()"),
 ('transfer',"showTransfer('%s','Ibercaja','%s',150)"%(datos.IBERCAJA,datos.REMUNERADA)),('cierrat',"closeTransfer()"),
 ('inversion',"showSec('inversion',3)"),('valor',"openInvModal('Valor Cartera')"),('cierrai',"closeInvModal()"),
 ('stats',"showSec('stats',-1)"),
 ('toast',"showToast('hola','success')"),('toasterr',"showToast('mal','error')"),('toastacc',"showToast('x','',{texto:'Deshacer',fn:()=>{}})"),
 ('accion',"hojaAccion({titulo:'t',texto:'x',confirmar:'y',peligro:true})"),('cierraacc',"cerrarAccion(false)"),
 ('burst',"showSuccessBurst()"),('privado',"window.kashyPrivacy()"),('sinprivado',"window.kashyPrivacy()"),
 ('clave',"document.getElementById('claveScreen').classList.add('show')"),('sinclave',"document.getElementById('claveScreen').classList.remove('show')"),
 ('esqueleto',"document.getElementById('recentMovs').innerHTML=skeletonRowsInner(2)+skeletonCards(1)+emptyState('x','y','z')"),
 ('en',"setLang('en')"),('es',"setLang('es')"),
]
def abrir(b,html,tema,red,hoy,forz):
    ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True,locale='es-ES',timezone_id='Europe/Madrid',service_workers='block',reduced_motion=red)
    p=ctx.new_page();n=FakeNotion(datos.BASES);sembrar(n)
    def r(route):
        q=route.request
        if not q.url.startswith(APP_ORIGIN+'/'):return route.abort()
        ru=q.url[len(APP_ORIGIN):].split('?')[0]
        if ru=='/':return route.fulfill(status=200,content_type='text/html; charset=utf-8',body=forzado(html) if forz else html)
        if ru in ('/icon.png','/kashy-vencimientos.js'):return route.fulfill(status=200,content_type='image/png' if ru.endswith('.png') else 'text/javascript',path=str(datos.RAIZ/ru[1:]))
        if ru.startswith('/api/'):
            x=n.responder(q.method,q.url,json.loads(q.post_data) if q.post_data else None) or (500,{})
            return route.fulfill(status=x[0],content_type='application/json',body=json.dumps(x[1]))
        return route.fulfill(status=404,body='')
    ctx.route('**/*',r);p.clock.set_fixed_time(hoy+'T12:00:00+01:00')
    p.add_init_script("try{localStorage.setItem('kashy-theme',%s);localStorage.setItem('kashy-lang','es');localStorage.setItem('kashy-key','k')}catch(e){}"%json.dumps(tema))
    p.goto(APP_ORIGIN+'/');p.wait_for_timeout(1800)
    if forz:p.evaluate("()=>document.querySelectorAll('*').forEach(e=>e.classList.add('__fa','__ff','__ffv','__fh'))")
    return ctx,p
PROP=re.compile(r'([\w-]+):([^;]*);')
# (tema, movimiento, fecha, estados forzados)
MODOS=[('dark','reduce','2026-11-15',False),('light','reduce','2026-11-15',False),('dark','no-preference','2026-11-05',False),('light','no-preference','2026-11-23',False),('dark','reduce','2026-11-15',True),('light','reduce','2026-11-15',True)]
MODOS_RAPIDO=[('dark','reduce','2026-11-15',False),('light','reduce','2026-11-05',True)]
def main():
    res={};total=0
    with sync_playwright() as pw:
        b=pw.chromium.launch()
        for tema,red,hoy,forz in (MODOS_RAPIDO if RAPIDO else MODOS):
            c1,p1=abrir(b,A,tema,red,hoy,forz);c2,p2=abrir(b,B,tema,red,hoy,forz)
            for nombre,js in PASOS:
                for p in (p1,p2):
                    try:p.evaluate("()=>{"+js+"}")
                    except Exception as e:res['ERROR paso %s: %s'%(nombre,str(e)[:60])]=1
                    p.wait_for_timeout(60 if not nombre in('inicio','movs','cuentas','inversion','stats','registrar') else 350)
                    if forz:p.evaluate("()=>document.querySelectorAll('*').forEach(e=>e.classList.add('__fa','__ff','__ffv','__fh'))")
                a=p1.evaluate(SNAP,nombre);d=p2.evaluate(SNAP,nombre);total+=len(a)
                for k in set(a)|set(d):
                    if a.get(k)==d.get(k):continue
                    if k not in a or k not in d:res['SOLO EN UNO '+k[:70]]=res.get('SOLO EN UNO '+k[:70],0)+1;continue
                    sa=dict(PROP.findall(p1.evaluate("([n,k])=>window.__s[n][k]",[nombre,k])));sd=dict(PROP.findall(p2.evaluate("([n,k])=>window.__s[n][k]",[nombre,k])))
                    for q in set(sa)|set(sd):
                        if sa.get(q)!=sd.get(q):
                            cl=re.sub(r'\[\d+\]','',k)[:60];cl=(cl+' | '+q+' | '+str(sa.get(q))[:38]+' -> '+str(sd.get(q))[:38])
                            res[cl]=res.get(cl,0)+1
                p1.evaluate("()=>{window.__s={}}");p2.evaluate("()=>{window.__s={}}")
            c1.close();c2.close()
        b.close()
    print('Nodos comparados:',total,'| diferencias distintas:',len(res))
    for k,v in sorted(res.items())[:MAX]:print(v,k)
    return 1 if res else 0
sys.exit(main())
