document.querySelector("[data-workspace-menu]")?.addEventListener("click", event => {
 const open = document.querySelector(".shell").classList.toggle("menu-open");
 event.currentTarget.setAttribute("aria-expanded", String(open));
});
