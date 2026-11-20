(() => {
  const shell=document.querySelector(".shell"), sidebar=document.querySelector(".sidebar");
  const workspace=document.querySelector(".workspace");
  const menu=document.querySelector("[data-workspace-menu],[data-toggle-menu]");
  const mobile=window.matchMedia("(max-width:760px)");
  let previousFocus=null;
  if(sidebar && menu){
    const close=document.createElement("button");close.type="button";close.className="drawer-close";close.textContent="Đóng menu";sidebar.prepend(close);
    const backdrop=document.createElement("button");backdrop.type="button";backdrop.className="nav-backdrop";backdrop.tabIndex=-1;
    backdrop.setAttribute("aria-label","Đóng menu điều hướng");shell.after(backdrop);
    function setOpen(open){
      if(open && !mobile.matches)return;
      if(open)previousFocus=document.activeElement;
      shell.classList.toggle("menu-open",open);document.body.classList.toggle("navigation-open",open);
      menu.setAttribute("aria-expanded",String(open));workspace.inert=open;
      if(open)close.focus();
      else if(previousFocus?.isConnected){previousFocus.focus();previousFocus=null;}
    }
    menu.addEventListener("click",()=>setOpen(!shell.classList.contains("menu-open")));
    close.addEventListener("click",()=>setOpen(false));backdrop.addEventListener("click",()=>setOpen(false));
    document.addEventListener("workspace:navigated",()=>setOpen(false));mobile.addEventListener("change",()=>setOpen(false));
    document.addEventListener("keydown",event=>{
      if(!shell.classList.contains("menu-open"))return;
      if(event.key==="Escape"){event.preventDefault();setOpen(false);}
      if(event.key==="Tab"){
        const items=[...sidebar.querySelectorAll("a[href],button:not([disabled])")],first=items[0],last=items.at(-1);
        if(event.shiftKey && document.activeElement===first){event.preventDefault();last.focus();}
        else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first.focus();}
      }
    });
  }
  document.querySelectorAll(".table-wrap").forEach((wrap,index)=>{
    const hint=document.createElement("p");hint.className="table-scroll-hint";hint.textContent="Cuộn ngang để xem đầy đủ các cột.";
    hint.id="table-scroll-hint-"+index;hint.hidden=true;wrap.after(hint);
    const update=()=>{
      const scrollable=wrap.clientWidth>0 && wrap.scrollWidth>wrap.clientWidth+1;
      hint.hidden=!scrollable;
      if(scrollable){wrap.tabIndex=0;wrap.setAttribute("role","region");wrap.setAttribute("aria-label","Bảng dữ liệu có thể cuộn ngang");wrap.setAttribute("aria-describedby",hint.id);}
      else{wrap.removeAttribute("tabindex");wrap.removeAttribute("role");wrap.removeAttribute("aria-label");wrap.removeAttribute("aria-describedby");}
    };
    const observer=new ResizeObserver(update);observer.observe(wrap);if(wrap.querySelector("table"))observer.observe(wrap.querySelector("table"));update();
  });
  const dialog=document.querySelector("#workspace-shortcuts");if(!dialog)return;
  const search=dialog.querySelector("input"),results=dialog.querySelector("[data-jump-results]");
  const normalize=value=>value.toLowerCase().replaceAll("đ","d").normalize("NFD").replace(/[\u0300-\u036f]/g,"").trim();
  function render(){
    results.replaceChildren();
    for(const source of document.querySelectorAll(".sidebar nav a")){
      if(!normalize(source.textContent).includes(normalize(search.value)))continue;
      const link=document.createElement("a");link.href=source.href;link.textContent=source.textContent;results.append(link);
    }
    dialog.querySelector("[data-jump-empty]").hidden=Boolean(results.children.length);
  }
  function open(){search.value="";render();if(!dialog.open)dialog.showModal();search.focus();}
  document.querySelector("[data-open-shortcuts]")?.addEventListener("click",open);
  dialog.querySelector("[data-close-shortcuts]").addEventListener("click",()=>dialog.close());
  search.addEventListener("input",render);search.addEventListener("keydown",event=>{
    if(event.key==="Enter" && results.firstElementChild){event.preventDefault();results.firstElementChild.click();}
    if(event.key==="ArrowDown" && results.firstElementChild){event.preventDefault();results.firstElementChild.focus();}
  });
  dialog.addEventListener("click",event=>{
    if(event.target!==dialog)return;
    const box=dialog.getBoundingClientRect();
    if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)dialog.close();
  });
  document.addEventListener("keydown",event=>{
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"&&!shell?.classList.contains("menu-open")){event.preventDefault();open();}
  });
})();
