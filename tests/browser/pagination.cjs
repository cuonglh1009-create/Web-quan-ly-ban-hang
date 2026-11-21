const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const { createInterface } = require("node:readline");
const path = require("node:path");
const fs = require("node:fs");

async function run() {
  const origin = "http://localhost:5000";
  const screenshots=path.resolve(process.cwd(),"artifacts/scope-review-20261121/ui");fs.mkdirSync(screenshots,{recursive:true});
  const database = path.join(require("node:os").tmpdir(), "kbh-scope-ui-" + Date.now() + ".db");
  const worker = spawn(process.env.KBH_PYTHON || "python", [path.join(__dirname,"pagination_bridge.py"),database], {
    env: {...process.env, PYTHONPATH:process.cwd(), PYTHONDONTWRITEBYTECODE:"1"},
  });
  const pending = new Map();
  let id = 0, browser;
  worker.stderr.pipe(process.stderr);
  createInterface({input:worker.stdout}).on("line", line=>{
    const result=JSON.parse(line);
    pending.get(result.id)?.(result);
    pending.delete(result.id);
  });
  try {
    browser=await chromium.launch({executablePath:"C:/Program Files/Google/Chrome/Application/chrome.exe",headless:true});
    const page=await browser.newPage({viewport:{width:1480,height:960}});
    const errors=[];
    let orderSubmits=0,paymentSubmits=0;
    page.on("request",request=>{
      if(request.method()!=="POST")return;
      if(request.url().endsWith("/api/ban-hang/don-hang"))orderSubmits++;
      if(request.url().endsWith("/thanh-toan"))paymentSubmits++;
    });
    page.on("pageerror",e=>errors.push(e.message));
    page.on("dialog",d=>d.accept());
    page.setDefaultTimeout(8000);
    await page.route("**/*",async route=>{
      const request=route.request(),url=new URL(request.url());
      if(url.origin!==origin)return route.abort();
      const call=id++,response=new Promise(resolve=>pending.set(call,resolve));
      const headers=await request.allHeaders();delete headers["content-length"];
      worker.stdin.write(JSON.stringify({id:call,path:url.pathname+url.search,method:request.method(),headers,
        body:request.postDataBuffer()?.toString("base64")||""})+"\n");
      const result=await response;
      await route.fulfill({status:result.status,headers:result.headers,body:Buffer.from(result.body,"base64")});
    });

    async function login(name){
      await page.goto(origin+"/dang-nhap");
      await page.locator('[name="ten_dang_nhap"]').fill(name);
      await page.locator('[name="mat_khau"]').fill("test-only-pass");
      await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();
      await page.waitForURL(url=>url.pathname!=="/dang-nhap");
    }
    async function ready(selector,count){await page.waitForFunction(({selector,count})=>document.querySelectorAll(selector).length===count,{selector,count});}
    async function noOverflow(label){
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1))throw Error("Overflow: "+label);
    }
    async function responsive(routes,role){
      for(const width of [360,390,768,1024,1440]){
        await page.setViewportSize({width,height:900});
        for(const route of routes){
          await page.goto(origin+route);
          await page.waitForLoadState("networkidle");
          await noOverflow(role+" "+route+" "+width);
        }
        if(width===360||width===1440)await page.screenshot({path:path.join(screenshots,role+"-"+width+"-final.png"),fullPage:true});
      }
    }
    await login("nv_kho");
    await page.goto(origin+"/kho/lo-hang");
    await ready("tbody tr",10);
    const first=await page.locator("tbody tr td:first-child").allTextContents();
    await page.locator("[data-next]").click();
    await page.locator("[data-page]").filter({hasText:"2 /"}).waitFor();
    if((await page.locator("tbody tr td:first-child").allTextContents()).some(x=>first.includes(x)))throw Error("Lot pages overlap");
    await page.reload();await page.locator("[data-page]").filter({hasText:"2 /"}).waitFor();
    await page.locator('[name="q"]').fill("IMPOSSIBLE-EMPTY");
    await page.getByRole("button",{name:"Tìm kiếm",exact:true}).click();
    await page.locator("[data-lot-summary]").filter({hasText:"Không tìm thấy lô hàng"}).waitFor();
    await page.getByRole("button",{name:"Xóa lọc",exact:true}).click();
    await page.locator("[data-page]").filter({hasText:"1 /"}).waitFor();
    await ready("tbody tr",10);
    await page.goto(origin+"/kho/phieu-nhap?page_size=10");
    await ready("tbody tr",10);
    await page.getByRole("link",{name:"Trang sau",exact:true}).click();
    await page.locator(".table-footer").filter({hasText:"Trang 2/4"}).waitFor();
    await responsive(["/kho","/kho/lo-hang","/kho/phieu-nhap","/kho/phieu-nhap/moi"],"warehouse");
    await page.goto(origin+"/kho/phieu-nhap/moi");
    await page.locator('[name="ma_ncc"]').selectOption("NCC01");
    await page.locator('[name="ma_sp"]').selectOption("SP01");
    await page.locator('[name="ma_lo"]').fill("FOOD-MISSING-DATES");
    await page.locator('[name="so_luong_nhap"]').fill("2");
    await page.locator('[name="gia_nhap"]').fill("55.000");
    await page.getByRole("button",{name:"Lưu phiếu nháp",exact:true}).click();
    if(await page.locator('[name="ngay_san_xuat"]').evaluate(n=>n.validity.valid))throw Error("Food date not required");
    if(!page.url().endsWith("/moi"))throw Error("Invalid food submitted");
    await page.locator('[name="ma_sp"]').selectOption("SP02");
    await page.locator('[name="ma_lo"]').fill("LO01");
    await page.getByRole("button",{name:"Lưu phiếu nháp",exact:true}).click();
    await page.getByRole("button",{name:"Xác nhận nhập kho",exact:true}).click();
    await page.locator("[data-error]:visible").waitFor();
    if(!(await page.locator("tbody").textContent()).includes("LO01"))throw Error("Receipt input erased");
    if(!(await page.locator("[data-status]").textContent()).includes("Nháp"))throw Error("Conflicting lot confirmed");
    await page.getByRole("button",{name:"Đăng xuất",exact:true}).click();
    await page.waitForURL("**/dang-nhap");
    await login("nv_ban_hang");
    await page.goto(origin+"/ban-hang/don-hang?page_size=10");
    await ready("#bang-don-hang tr",10);
    const orders=await page.locator("#bang-don-hang tr td:first-child").allTextContents();
    await page.getByRole("button",{name:"Trang sau",exact:true}).click();
    await page.locator(".table-footer").filter({hasText:"Trang 2/4"}).waitFor();
    if((await page.locator("#bang-don-hang tr td:first-child").allTextContents()).some(x=>orders.includes(x)))throw Error("Order pages overlap");
    await page.reload();await page.locator(".table-footer").filter({hasText:"Trang 2/4"}).waitFor();
    await page.goto(origin+"/ban-hang/khach-hang?page_size=10");
    await ready("#bang-khach-hang tr",10);
    await page.getByRole("button",{name:"Trang sau",exact:true}).click();
    await page.locator(".table-footer").filter({hasText:"Trang 2/5"}).waitFor();
    await page.locator("#tu-khoa-kh").fill("IMPOSSIBLE-EMPTY");
    await page.locator("#form-tra-cuu-kh").evaluate(f=>f.requestSubmit());
    await page.locator(".table-footer").filter({hasText:"Không có kết quả"}).waitFor();
    await page.locator("#tu-khoa-kh").fill("");
    await page.locator("#form-tra-cuu-kh").evaluate(f=>f.requestSubmit());
    await ready("#bang-khach-hang tr",10);
    await responsive(["/ban-hang/don-hang","/ban-hang/khach-hang","/ban-hang/thong-ke","/ban-hang/tra-cuu-kho","/ban-hang/don-hang/moi"],"sales");
    await page.setViewportSize({width:1440,height:960});
    const stockBefore=await page.evaluate(async()=> (await Api.get("/api/ban-hang/tra-cuu-kho")).find(x=>x.ma_sp==="SP02"));
    await page.goto(origin+"/ban-hang/don-hang/moi");
    await page.locator('#chon-khach-cu option[value="KH003"]').waitFor({state:"attached"});
    await page.locator("#chon-khach-cu").selectOption("KH003");
    await page.locator("#chon-sp-nhanh").selectOption("SP02");
    await page.locator("#nut-them-san-pham").click();
    await page.locator("#gui").click();
    await page.locator("#khu-thanh-toan").waitFor();
    await page.locator("#giam-khach").filter({hasText:"23.000"}).waitFor();
    await page.locator("#khu-km summary").click();
    await page.locator('[name="ma_km"]').fill("GIAM10");
    await page.locator("#form-km").evaluate(f=>f.requestSubmit());
    await page.locator("#giam-km").filter({hasText:"20.700"}).waitFor();
    await page.locator('[name="tien_khach_dua"]').fill("1");
    await page.getByRole("button",{name:"Thanh toán và xuất hóa đơn",exact:true}).click();
    await page.locator('[data-loi-truong="thong_tin.tien_khach_dua"]').filter({hasText:/thiếu|đủ/i}).waitFor();
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(screenshots,"vip-checkout-final.png"),fullPage:true});
    const orderPath=new URL(page.url()).pathname.replace("/ban-hang/","/api/ban-hang/");
    await page.locator("#nut-huy").click();
    await page.locator("#trang-thai").filter({hasText:/hủy/i}).waitFor();
    const canceled=await page.evaluate(async path=>await Api.get(path),orderPath);
    if(canceled.trang_thai!=="DA_HUY")throw Error("Cancellation failed");
    const stockAfter=await page.evaluate(async()=> (await Api.get("/api/ban-hang/tra-cuu-kho")).find(x=>x.ma_sp==="SP02"));
    if(JSON.stringify(stockAfter)!==JSON.stringify(stockBefore))throw Error("Cancellation did not release hold");
    const wrongRole=await page.evaluate(async()=> (await fetch("/api/kho/tong-quan")).status);
    if(wrongRole!==403)throw Error("Role access not blocked");
    await page.context().clearCookies();
    await page.evaluate(()=>Api.get("/api/ban-hang/khach-hang").catch(()=>{}));
    await page.waitForURL("**/dang-nhap");
    if(errors.length)throw Error(errors.join("\n"));
    console.log("PASS: real backend paging of lots/receipts/orders/customers, empty/reset/reload, 45 responsive page-width combinations, food required dates, duplicate lot, VIP+promo, insufficient cash, cancel releases stock, role and expired-session redirect.");
  } finally {
    await browser?.close();
    worker.stdin.end();
    await new Promise(resolve=>worker.once("exit",resolve));
    for(const suffix of ["","-wal","-shm"])fs.rmSync(database+suffix,{force:true});
  }
}
run().catch(e=>{console.error(e);process.exitCode=1;});
