/* Ka$hy · vencimientos
   Pagos, cuotas y transferencias recurrentes, y la lógica de «qué vence hoy». La usan la app (index-nuevo.html,
   como script clásico) y el servidor (api/cron-avisos.js, con import), así que el aviso de Inicio y la
   notificación diaria no pueden discrepar. Sin dependencias ni red: las consultas a Notion llegan como
   consultar(dbId, body), que devuelve la respuesta de Notion ({results: [...]}). Las fechas son 'AAAA-MM-DD'. */
(function(raiz){
'use strict';
const IDS={IBERCAJA:'31621c54013f811ebd49f65e2776d28e',MYINVESTOR_REM:'3d821c54013f81eab324f5174d95ade2',REVOLUT_PERSONAL:'31621c54013f817f9f00fc6acc160c26',MYINVESTOR:'3b821c54013f817088e9fe2e7a0a3707'};
const BASES={MOVS:'25e21c54013f817481d6cd37b0daa2b5',TRANSFER:'25e21c54013f813faceae0152856368e',CUENTAS:'25e21c54013f817e959ee75351072a94'};
const SUSCRIPCIONES=[
  {name:'Spotify',emoji:'🎵',amount:20.99,cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f8130bd7ddbf775f0f1bd',dia:3,anim:{familia:'balanceo',origen:'50% 100%'}},
  {name:'Letra Coche',emoji:'🚗',amount:432.35,cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f81689c53c344e9ce8987',dia:5,fechaInicio:'2026-05-05',fechaFin:'2028-01-05',cuotasTotales:24,cuotasIniciales:3,pagadoInicial:1297.05,anim:{familia:'avance'}},
  {name:'iCloud',emoji:'☁️',amount:1.50,cuentaId:'38621c54013f818ead8be5ec81d47356',catId:'31621c54013f8130bd7ddbf775f0f1bd',dia:30,anim:{familia:'flote'}},
  {name:'DAZN Basket',emoji:'🏀',amount:4.99,cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f8130bd7ddbf775f0f1bd',dia:27,fechaInicio:'2026-08-01',fechaFin:'2027-04-27',cuotasTotales:12,cuotasIniciales:4,pagadoInicial:19.96,anim:{familia:'salto'}},
  {name:'Claude Pro',emoji:'🤖',amount:21.78,cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f8130bd7ddbf775f0f1bd',dia:11,anim:{familia:'zumbido'}},
  {name:'DAZN Fútbol',emoji:'⚽',amount:2.99,cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f8130bd7ddbf775f0f1bd',dia:28,fechaInicio:'2026-08-28',fechaFin:'2027-08-28',cuotasTotales:12,cuotasIniciales:0,pagadoInicial:0,anim:{familia:'salto'}},
  {name:'Mueble Ikea',emoji:'🛋️',amount:28.93,cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f816d85afc5277c4e2c08',dia:27,fechaInicio:'2026-10-27',fechaFin:'2026-12-27',cuotasTotales:3,cuotasIniciales:0,pagadoInicial:0,anim:{familia:'latido'}},
  {name:'Vinilos',emoji:'💿',amount:28.85,importes:[28.85,28.86,28.85],cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f8196b8d4dc7c51c738b2',dia:29,fechaInicio:'2026-10-29',fechaFin:'2026-12-29',cuotasTotales:3,cuotasIniciales:0,pagadoInicial:0,anim:{familia:'giro'}},
  {name:'Revisiones Coche',emoji:'🔧',amount:55,cuentaId:'31621c54013f811ebd49f65e2776d28e',catId:'31621c54013f81689c53c344e9ce8987',dia:5,fechaInicio:'2026-12-05',fechaFin:'2027-11-05',cuotasTotales:12,cuotasIniciales:0,pagadoInicial:0,anim:{familia:'giro'}},
];
/* Sin amount: la hoja se abre con el importe vacío y cualquier importe cuenta como «ya registrada» este mes */
const TRANSF_RECURRENTES=[
  {fromId:IDS.IBERCAJA,toId:IDS.MYINVESTOR_REM,amount:150,dia:23},
  {fromId:IDS.IBERCAJA,toId:IDS.REVOLUT_PERSONAL,dia:26},
];
/* Aportación mensual a los fondos: cuenta como hecha cualquier transferencia Remunerada → MyInvestor del mes */
const APORTACION={fromId:IDS.MYINVESTOR_REM,toId:IDS.MYINVESTOR,importe:150,dia:26};
const NOMBRES={[IDS.MYINVESTOR_REM]:'MyInvestor Remunerada',[IDS.REVOLUT_PERSONAL]:'Revolut Personal',[IDS.MYINVESTOR]:'MyInvestor'};
const DIAS_CARTERA=35; // más días sin actualizar el valor de la cartera: recordatorio

const pad=n=>String(n).padStart(2,'0');
const diaDe=hoy=>Number(hoy.slice(8,10));
function mesDe(hoy){
  const a=Number(hoy.slice(0,4)),m=Number(hoy.slice(5,7));
  return{ini:a+'-'+pad(m)+'-01',fin:a+'-'+pad(m)+'-'+pad(new Date(Date.UTC(a,m,0)).getUTCDate())};
}
const diasEntre=(desde,hasta)=>Math.round((Date.UTC(+hasta.slice(0,4),+hasta.slice(5,7)-1,+hasta.slice(8,10))-Date.UTC(+desde.slice(0,4),+desde.slice(5,7)-1,+desde.slice(8,10)))/86400000);
const hayFilas=d=>!!(d&&d.results&&d.results.length);

/* Pago a plazos cuya primera cuota aún no ha llegado */
function pagoPorEmpezar(s,hoy){return !!s.fechaInicio&&hoy<s.fechaInicio;}
/* Total e importe de cada cuota: con importes (cuotas distintas) se usa la lista; si no, amount */
function totalCuotas(s){return s.importes?Math.round(s.importes.reduce((a,b)=>a+b,0)*100)/100:s.cuotasTotales*s.amount;}
function importeCuota(s,cuotasPagadas){return s.importes?(s.importes[cuotasPagadas]??s.amount):s.amount;}
/* Cuotas pagadas: movimientos reales con el nombre exacto («emoji nombre») desde el inicio. Si Notion falla no se da por terminado */
async function progresoCuotas(s,consultar){
  const base=s.cuotasIniciales||0,basePagado=s.pagadoInicial||0;
  try{
    const d=await consultar(BASES.MOVS,{filter:{and:[
      {property:'Nombre',title:{equals:s.emoji+' '+s.name}},
      {property:'Fecha',date:{on_or_after:s.fechaInicio}}
    ]},sorts:[{property:'Fecha',direction:'ascending'}]});
    const filas=(d&&d.results)||[];
    const cuotasPagadas=Math.min(s.cuotasTotales,base+filas.length);
    const pagado=basePagado+filas.reduce((t,r)=>t+((r.properties&&r.properties.Gasto&&r.properties.Gasto.number)||0),0);
    return{cuotasPagadas,pagado,total:totalCuotas(s),terminado:cuotasPagadas>=s.cuotasTotales};
  }catch(e){return{cuotasPagadas:base,pagado:basePagado,total:totalCuotas(s),terminado:false};}
}
/* ¿Ya hay un movimiento de este pago este mes? Si Notion falla, se avisa igualmente */
async function pagoRegistrado(s,hoy,consultar){
  const m=mesDe(hoy);
  try{
    return hayFilas(await consultar(BASES.MOVS,{filter:{and:[
      {property:'Nombre',title:{equals:s.emoji+' '+s.name}},
      {property:'Fecha',date:{on_or_after:m.ini}},{property:'Fecha',date:{on_or_before:m.fin}}
    ]},page_size:1}));
  }catch(e){return false;}
}
/* ¿Ya hay esta transferencia este mes? Con importe, solo si coincide. Si Notion falla, se avisa igualmente */
async function transferRegistrada(x,hoy,consultar){
  const m=mesDe(hoy);
  const conds=[
    {property:'Transferir Desde',relation:{contains:x.fromId}},
    {property:'Transferir a',relation:{contains:x.toId}},
    {property:'Fecha',date:{on_or_after:m.ini}},{property:'Fecha',date:{on_or_before:m.fin}}
  ];
  if(x.amount)conds.push({property:'Monto',number:{equals:x.amount}});
  try{return hayFilas(await consultar(BASES.TRANSFER,{filter:{and:conds},page_size:1}));}
  catch(e){return false;}
}
/* Lo que vence hoy y aún no está registrado.
   pagos: [{s, importe}] · transferencias: [{toId, destino, importe|null, aportacion}] */
async function vencenHoy(hoy,consultar){
  const dia=diaDe(hoy);
  const [pagos,transferencias,aportacion]=await Promise.all([
    Promise.all(SUSCRIPCIONES.filter(s=>s.dia===dia&&!pagoPorEmpezar(s,hoy)).map(async s=>{
      if(await pagoRegistrado(s,hoy,consultar))return null;
      if(!s.cuotasTotales)return{s,importe:s.amount};
      const p=await progresoCuotas(s,consultar);
      return p.terminado?null:{s,importe:importeCuota(s,p.cuotasPagadas)};
    })),
    Promise.all(TRANSF_RECURRENTES.filter(x=>x.dia===dia).map(async x=>
      await transferRegistrada(x,hoy,consultar)?null:{toId:x.toId,destino:NOMBRES[x.toId],importe:x.amount||null,aportacion:false})),
    dia===APORTACION.dia&&!(await transferRegistrada({fromId:APORTACION.fromId,toId:APORTACION.toId},hoy,consultar))
      ?{toId:APORTACION.toId,destino:NOMBRES[APORTACION.toId],importe:APORTACION.importe,aportacion:true}:null,
  ]);
  return{pagos:pagos.filter(Boolean),transferencias:transferencias.filter(Boolean).concat(aportacion?[aportacion]:[])};
}
/* Recordatorio de actualizar el valor de la cartera: más de 35 días (o ninguno registrado). clave identifica el
   último valor, para avisar una sola vez por cada uno. Lanza si Notion falla */
async function recordatorioCartera(hoy,consultar){
  const d=await consultar(BASES.CUENTAS,{filter:{property:'InvTipo',select:{equals:'Valor Cartera'}},
    sorts:[{property:'InvFecha',direction:'descending'}],page_size:1});
  if(!d||!d.results)throw new Error('consulta fallida');
  const fecha=(((d.results[0]||{}).properties||{}).InvFecha||{}).date;
  const ultima=fecha&&fecha.start?fecha.start.slice(0,10):null;
  const dias=ultima?diasEntre(ultima,hoy):null;
  return{clave:ultima||'ninguno',dias,debeAvisar:dias===null||dias>DIAS_CARTERA};
}
const euros=n=>n.toLocaleString('es-ES',{minimumFractionDigits:2,maximumFractionDigits:2})+' €';
/* Texto de la notificación diaria: null si no hay nada */
function textoNotificacion(v){
  const lineas=[];
  (v.pagos||[]).forEach(x=>lineas.push(x.s.emoji+' '+x.s.name+' '+euros(x.importe)));
  (v.transferencias||[]).forEach(x=>lineas.push(x.aportacion?'📈 Aportación mensual '+euros(x.importe):'⇄ '+x.destino+(x.importe?' '+euros(x.importe):'')));
  if(v.cartera)lineas.push(v.cartera.dias===null?'📊 Registra el valor de tu cartera':'📊 Actualiza el valor de la cartera ('+v.cartera.dias+' días)');
  if(!lineas.length)return null;
  const solo=lineas.length===1&&v.cartera;
  return{titulo:solo?'Ka$hy · Recordatorio':'Ka$hy · Hoy vence',cuerpo:lineas.join('\n')};
}
raiz.KashyVencimientos={IDS,BASES,SUSCRIPCIONES,TRANSF_RECURRENTES,APORTACION,NOMBRES,DIAS_CARTERA,
  mesDe,pagoPorEmpezar,totalCuotas,importeCuota,progresoCuotas,pagoRegistrado,transferRegistrada,vencenHoy,recordatorioCartera,textoNotificacion};
})(typeof globalThis!=='undefined'?globalThis:window);
