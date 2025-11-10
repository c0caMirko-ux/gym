// frontend/static/js/app.js
// Intenta cargar datos estáticos si los creas en frontend/static/data/{tree.txt,ddl.sql}
// De lo contrario deja los textos por defecto y puedes pegar manualmente.
async function loadIfExists(id, url){
  try{
    const r = await fetch(url);
    if(r.ok){
      const txt = await r.text();
      document.getElementById(id).textContent = txt;
    }
  }catch(e){
    // no hay archivo o fallo de CORS/FS; silencioso
    // console.log('no file', url, e);
  }
}

loadIfExists('file-tree', '/static/data/tree.txt');
loadIfExists('db-ddl', '/static/data/ddl.sql');
