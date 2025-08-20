const qs = (s) => document.querySelector(s);
const byId = (id) => document.getElementById(id);
const apiUrl = (path) => ((window.API_BASE || '') + path);

function makeDropzone({zone, input}){
  zone.addEventListener('click',()=> input.click());
  zone.addEventListener('dragover',(e)=>{e.preventDefault();zone.classList.add('dragover')});
  zone.addEventListener('dragleave',()=> zone.classList.remove('dragover'));
  zone.addEventListener('drop',(e)=>{e.preventDefault();zone.classList.remove('dragover');if(e.dataTransfer.files.length){input.files = e.dataTransfer.files;}});
}

function init(){
  const uniDrop = byId('uniDrop');
  const uniFile = byId('uniFile');
  if(uniDrop && uniFile){
    makeDropzone({ zone: uniDrop, input: uniFile });
  }
  const uniForm = byId('uniForm');
  if(uniForm){
    uniForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const file = byId('uniFile').files[0];
      if(!file) return;
      const btn = byId('uniBtn');
      const bar = byId('uniProgBar');
      const preview = byId('uniPreview');
      const dl = byId('uniDownload');
      btn.disabled = true; dl.classList.add('hidden'); preview.classList.add('hidden');
      bar.style.width = '5%';
      try{
        const fd = new FormData();
        fd.append('file', file);
        fd.append('aggressive', byId('uniAgg').checked ? 'true' : 'false');
        fd.append('desired_format', byId('uniFormat').value);
  const res = await fetch(apiUrl('/api/ingest-file'), { method:'POST', body: fd });
        const data = await res.json();
        if(data.error) throw new Error(data.error);
        const id = data.session_id;
        let done = false;
        while(!done){
          await new Promise(r=> setTimeout(r, 500));
          const pr = await fetch(apiUrl(`/api/progress/${id}`));
          const pj = await pr.json();
          if(pj.error) throw new Error(pj.error);
          bar.style.width = `${pj.progress||0}%`;
          if(pj.preview){ preview.textContent = pj.preview; preview.classList.remove('hidden'); }
          if(pj.status === 'completed'){ done = true; dl.dataset.sessionId = id; dl.classList.remove('hidden'); break; }
          if(pj.status === 'error'){ throw new Error(pj.error || 'Processing error'); }
        }
      }catch(err){
        alert('Error: ' + err.message);
      }finally{
        btn.disabled = false;
        setTimeout(()=> bar.style.width = '0%', 600);
      }
    });
    byId('uniDownload').addEventListener('click', ()=>{
      const id = byId('uniDownload').dataset.sessionId; if(!id) return;
      const fmt = byId('uniFormat').value;
      const a = document.createElement('a');
  a.href = apiUrl(`/api/download-file/${id}?format=${encodeURIComponent(fmt)}`);
      a.download = `translated.${fmt}`;
      document.body.appendChild(a); a.click(); a.remove();
    });
  }
}

document.addEventListener('DOMContentLoaded', init);