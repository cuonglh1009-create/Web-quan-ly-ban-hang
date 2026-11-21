const { chromium } = require("playwright");
const { spawn } = require("node:child_process");
const { createInterface } = require("node:readline");
const path = require("node:path");
const fs = require("node:fs");

async function run() {
  const origin = "http://localhost:5000";
  const screenshots=path.resolve(process.cwd(),"artifacts/upgrade-20261121/ui");fs.mkdirSync(screenshots,{recursive:true});
  const database = path.join(require("node:os").tmpdir(), "kbh-ui-check-" + Date.now() + ".db");
  const worker = spawn(process.env.KBH_PYTHON || "python", [path.join(__dirname,"tv1_integrated_bridge.py"),database], {
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
    await page.goto(origin+"/dang-nhap");
    await page.getByRole("button",{name:"Đăng nhập",exact:true}).waitFor();
    await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished)));
    await page.screenshot({path:path.join(screenshots,"login-desktop.png"),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(screenshots,"login-mobile.png"),fullPage:true});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error("Login mobile overflow");
    await page.setViewportSize({width:1480,height:960});
    await page.locator('[name="ten_dang_nhap"]').fill("nv_kho");
    await page.locator('[name="mat_khau"]').fill("wrong-password");
    await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();
    await page.locator("#loi").filter({hasText:"không hợp lệ"}).waitFor();
    await page.locator('[name="mat_khau"]').fill("test-only-pass");
    await page.getByRole("button",{name:"Hiện mật khẩu",exact:true}).click();
    if(await page.locator('[name="mat_khau"]').getAttribute("type")!=="text")throw Error("Password toggle failed");
    await page.getByRole("button",{name:"Ẩn mật khẩu",exact:true}).click();
    await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();
    await page.locator("[data-lots]").filter({hasText:/^\d+$/}).waitFor();
    const expected=await page.evaluate(async()=>{
      const lots=await Api.get("/api/kho/lo-hang");
      return new Set(lots.filter(l=>l.kha_dung>0).map(l=>l.ma_sp)).size;
    });
    if(Number(await page.locator("[data-available]").textContent())!==expected)throw Error("Dashboard counts mixed units");
    await page.locator("[data-dashboard-refresh]").click();
    await page.getByRole("button",{name:"Làm mới số liệu",exact:true}).waitFor();
    await page.locator("[data-reserved-lots]").evaluate(node=>node.remove());
    await page.locator("[data-dashboard-refresh]").click();
    await page.getByRole("button",{name:"Làm mới số liệu",exact:true}).waitFor();
    if(await page.locator("[data-error]:visible").count())throw Error("Optional dashboard widget caused an error");
    await page.keyboard.press("Control+k");
    await page.locator("#jump-search").fill("san pham");
    await page.locator("[data-jump-results] a").click();
    await page.locator("[data-product-available]").first().filter({hasText:/^\d+$/}).waitFor();
    await page.locator("[data-product-category]").selectOption("THOI_TRANG");
    if(await page.locator("[data-product-row]:visible").count()!==1)throw Error("Category filter failed");
    await page.locator("[data-product-category]").selectOption("");
    await page.screenshot({path:path.join(screenshots,"products-v3.png"),fullPage:true});
    await page.goto(origin+"/kho");
    await page.locator("[data-lots]").filter({hasText:/^\d+$/}).waitFor();
    if(await page.locator(".metric-danger").count())throw Error("Red warehouse alert remains");
    await page.screenshot({path:path.join(screenshots,"tv1-overview.png"),fullPage:true});
    await page.getByRole("link",{name:"Lập phiếu nhập",exact:true}).click();
    await page.locator('[name="ma_ncc"]').selectOption("NCC01");
    await page.locator('[name="ma_sp"]').selectOption("SP02");
    await page.locator('[name="ma_lo"]').fill("LO-UI-REVIEW");
    await page.locator('[name="so_luong_nhap"]').fill("7");
    await page.locator('[name="gia_nhap"]').fill("135.000");
    const total=await page.locator("[data-receipt-total]").textContent();
    if(!total.includes("945"))throw Error("Receipt total incorrect: "+total);
    await page.screenshot({path:path.join(screenshots,"tv1-receipt-form.png"),fullPage:true});
    await page.getByRole("button",{name:"Lưu phiếu nháp",exact:true}).click();
    await page.getByRole("button",{name:"Xác nhận nhập kho",exact:true}).click();
    await page.locator("[data-status].success").waitFor();
    if(!(await page.locator("[data-supplier]").textContent()).includes("An Phú"))throw Error("Receipt supplier not hydrated");
    if(!(await page.locator("tbody").textContent()).includes("Đèn bàn LED"))throw Error("Receipt product name not hydrated");
    if((await page.title()).includes("script"))throw Error("Data leaked into title");
    await page.locator('nav a[href="/kho/phieu-nhap"]').click();
    await page.locator("tbody tr").filter({hasText:"945.000"}).waitFor();
    await page.locator('nav a[href="/kho/lo-hang"]').click();
    await page.locator('[name="q"]').fill("Den ban");
    await page.getByRole("button",{name:"Tìm kiếm",exact:true}).click();
    await page.locator("tbody tr").filter({hasText:"LO-UI-REVIEW"}).filter({hasText:"Đèn bàn LED"}).waitFor();
    const confirmed=page.locator("tbody tr").filter({hasText:"LO-UI-REVIEW"});
    if(!(await confirmed.textContent()).includes("Nhà cung cấp An Phú"))throw Error("Supplier missing");
    await page.screenshot({path:path.join(screenshots,"tv1-lots.png"),fullPage:true});
    await page.locator('nav a[href="/kho/san-pham"]').click();
    await page.locator("[data-product-available]").first().filter({hasText:/^\d+$/}).waitFor();
    await page.locator("[data-product-search]").fill("ao thun");
    if(await page.locator("[data-product-row]:visible").count()!==1)throw Error("Product search failed");
    await page.locator('nav a[href="/kho/canh-bao"]').click();
    await page.locator("[data-low-count]").filter({hasText:/^\d+$/}).waitFor();
    await page.setViewportSize({width:390,height:844});
    await page.getByRole("button",{name:"Mở menu",exact:true}).click();
    await page.locator('nav a[href="/kho"]').click();
    await page.locator("[data-lots]").filter({hasText:/^\d+$/}).waitFor();
    await page.screenshot({path:path.join(screenshots,"tv1-mobile.png"),fullPage:true});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error("Mobile overflow");
    await page.getByRole("button",{name:"Đăng xuất",exact:true}).click();
    await page.locator('[name="ten_dang_nhap"]').fill("nv_ban_hang");
    await page.locator('[name="mat_khau"]').fill("test-only-pass");
    await page.getByRole("button",{name:"Đăng nhập",exact:true}).click();
    await page.waitForURL("**/ban-hang**");
    for(const [tab,title] of [["khach-hang","Khách hàng"],["thong-ke","Thống kê doanh thu"],["tra-cuu-kho","Tra cứu kho"],["don-hang","Đơn hàng"]]){
      await page.locator('.nav-tabs [data-tab="'+tab+'"]').click();
      await page.locator("[data-sales-heading]").filter({hasText:title}).waitFor();
      await page.locator('#panel-'+tab).waitFor();
    }

    if(await page.locator('link[href*="kho/kho.css"]').count())throw Error("Warehouse stylesheet leaked to sales");
    await page.setViewportSize({width:1480,height:960});
    await page.screenshot({path:path.join(screenshots,"sales-overview-v2.png"),fullPage:true});
    for (const [route, selector] of [["/ban-hang/khach-hang","#bang-khach-hang"],["/ban-hang/thong-ke","#bang-thong-ke-doanh-thu"],["/ban-hang/tra-cuu-kho","#bang-tra-cuu-kho"]]) {
      await page.goto(origin+route);
      await page.locator(selector).waitFor();
      await page.waitForTimeout(150);
      await page.setViewportSize({width:390,height:844});
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error("Overflow: "+route);
      await page.getByRole("button",{name:"Menu",exact:true}).click();
      await page.locator("#menu a").first().waitFor();
      await page.setViewportSize({width:1480,height:960});
    }
    await page.goto(origin+"/ban-hang/don-hang/moi");
    await page.locator('#chon-sp-nhanh option[value="SP02"]').waitFor({state:"attached"});
    for(const width of [320,390,768,1024,1480]){
      await page.setViewportSize({width,height:960});
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error("Order form overflow "+width);
    }
    await page.locator("#chon-sp-nhanh").selectOption("SP02");
    await page.locator("#nut-them-san-pham").click();
    await page.locator("#chon-khach-cu").selectOption("KH001");
    await page.screenshot({path:path.join(screenshots,"sales-order-v2.png"),fullPage:true});
    await page.evaluate(()=>{const form=document.querySelector("#form-don");form.requestSubmit();form.requestSubmit();});
    await page.locator("#khu-thanh-toan").waitFor();
    for(const width of [320,390,768,1480]){
      await page.setViewportSize({width,height:960});
      if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error("Payment overflow "+width);
    }
    await page.locator('[name="tien_khach_dua"]').fill("500.000");
    await page.locator("#du-kien-tien-thoi").filter({hasText:"270.000"}).waitFor();
    await page.locator("#chi-tiet-don-body").filter({hasText:"Đèn bàn LED"}).waitFor();
    await page.screenshot({path:path.join(screenshots,"checkout-natural.png"),fullPage:true});
    await page.evaluate(()=>{const form=document.querySelector("#form-tt");form.requestSubmit();form.requestSubmit();});
    await page.waitForURL("**/hoa-don");
    await page.locator("#loi").waitFor({state:"hidden"});
    await page.goto(origin+"/ban-hang/khach-hang");
    await page.locator("#tab-khach-hang[aria-current=page]").waitFor({state:"attached"});
    const hostile='<img src=x onerror="window.__xss=1">';
    await page.evaluate(async name=>{await Api.post("/api/ban-hang/khach-hang",{ma_kh:"XSS-TEST",ho_ten:name,so_dien_thoai:"0900123123",dia_chi:"QA only"});},hostile);
    await page.reload();
    await page.locator("#bang-khach-hang tr").filter({hasText:"XSS-TEST"}).waitFor();
    if(await page.locator("#bang-khach-hang img").count() || await page.evaluate(()=>window.__xss))throw Error("HTML injection in customer list");
    await page.locator('#menu a[href="/ban-hang/thong-ke"]').click();
    await page.locator("#tab-thong-ke[aria-current=page]").waitFor({state:"attached"});
    await page.locator(".revenue-bar").first().waitFor();
    await page.goBack();
    await page.locator("[data-sales-heading]").filter({hasText:"Khách hàng"}).waitFor();
    await page.goForward();
    await page.locator("[data-sales-heading]").filter({hasText:"Thống kê doanh thu"}).waitFor();
    await page.screenshot({path:path.join(screenshots,"sales-statistics-v3.png"),fullPage:true});
    await page.locator('#menu a[href="/ban-hang/thong-ke"][aria-current=page]').waitFor();
    await page.goto(origin+"/ban-hang/don-hang/moi");
    await page.locator('#chon-khach-cu option[value="XSS-TEST"]').waitFor({state:"attached"});
    await page.locator("#nhap-tim-khach").fill("XSS-TEST");
    await page.locator("#danh-sach-goi-y-khach").filter({hasText:"XSS-TEST"}).waitFor();
    if(await page.locator("#danh-sach-goi-y-khach img").count() || await page.evaluate(()=>window.__xss))throw Error("HTML injection in suggestion");
    await page.goto(origin+"/ban-hang/khach-hang");
    await page.locator("#nut-mo-them-kh").click();
    await page.locator('#form-them-kh-moi [name="ho_ten"]').fill("Khách kiểm tra nút");
    await page.locator('#form-them-kh-moi [name="so_dien_thoai"]').fill("0912348877");
    await page.locator('#form-them-kh-moi [name="dia_chi"]').fill("Hà Nội");
    await page.getByRole("button",{name:"Lưu khách hàng",exact:true}).click();
    const newCustomer=page.locator("#bang-khach-hang tr").filter({hasText:"Khách kiểm tra nút"});
    await newCustomer.waitFor();
    await newCustomer.getByRole("button",{name:"Xem đơn",exact:true}).click();
    await page.locator("#khoi-lich-su-kh[open]").waitFor();
    await page.locator("#bang-lich-su-kh").filter({hasText:"chưa có đơn"}).waitFor();
    await page.locator("#nut-dong-lich-su").click();
    await page.locator("#bang-khach-hang tr").filter({hasText:"KH001"}).getByRole("button",{name:"Xem đơn",exact:true}).click();
    await page.locator("#bang-lich-su-kh").filter({hasText:"230.000"}).waitFor();
    await page.locator("#bang-lich-su-kh").getByRole("link",{name:"Chi tiết",exact:true}).first().click();
    await page.locator("#phai-tra").filter({hasText:"230.000"}).waitFor();
    await page.goto(origin+"/ban-hang/thong-ke");
    for(const [name,key] of [["Theo ngày","ngay"],["Theo tháng","thang"],["Theo năm","nam"]]){
      await Promise.all([page.waitForResponse(r=>r.url().includes("/thong-ke/doanh-thu?kieu="+key)&&r.status()===200),page.getByRole("button",{name,exact:true}).click()]);
      await page.locator("#tk-tong-doanh-thu").filter({hasText:"230.000"}).waitFor();
    }
    await page.goto(origin+"/ban-hang/tra-cuu-kho");
    await page.locator("#bang-tra-cuu-kho tr").filter({hasText:"SP02"}).getByRole("button",{name:"Lập đơn",exact:true}).click();
    await page.waitForURL("**/ban-hang/don-hang/moi");
    await page.locator("#chi-tiet-sp-chon").waitFor();
    if(await page.locator("#chon-sp-nhanh").inputValue()!=="SP02")throw Error("Selected product not carried into order");
    await page.locator("#nut-them-san-pham").click();
    await page.locator("#hien-thi-tam-tinh").filter({hasText:"230.000"}).waitFor();
    await page.locator(".quick-catalog summary").click();
    await page.locator("#danh-muc-nhanh > div").filter({hasText:"Cà phê rang"}).getByRole("button",{name:"+ Chọn vào đơn",exact:true}).click();
    if(await page.locator("#dong tr").count()!==2)throw Error("Quick catalog action failed");
    await page.locator("#nut-bat-them-kh").click();
    await page.locator("#ten-kh-moi").fill("Khách thêm nhanh");
    await page.locator("#sdt-kh-moi").fill("0912348866");
    await page.locator("#nut-luu-khach-nhanh").click();
    await page.locator("#ten-kh-hien-thi").filter({hasText:"Khách thêm nhanh"}).waitFor();
    if(orderSubmits!==1 || paymentSubmits!==1)throw Error("Duplicate submission: "+orderSubmits+"/"+paymentSubmits);
    await page.goto(origin+"/ban-hang/khach-hang");
    await page.locator("#bang-khach-hang tr").filter({hasText:"KH001"}).waitFor();
    await page.evaluate(()=>{
      window.__originalFetch=window.fetch;
      window.fetch=(input,options)=>{
        const url=String(input);
        if(url.includes("tu_khoa=SLOW") || url.includes("tu_khoa=FAST")){
          const slow=url.includes("tu_khoa=SLOW");
          return new Promise(resolve=>setTimeout(()=>resolve(new Response(JSON.stringify({du_lieu:[{ma_kh:slow?"OLD":"NEW",ho_ten:slow?"Old result":"New result",hang:"THUONG"}]}),{status:200,headers:{"Content-Type":"application/json"}})),slow?600:20));
        }
        return window.__originalFetch(input,options);
      };
    });
    await page.locator("#tu-khoa-kh").fill("SLOW");
    await page.locator("#form-tra-cuu-kh").evaluate(form=>form.requestSubmit());
    await page.locator("#tu-khoa-kh").fill("FAST");
    await page.locator("#form-tra-cuu-kh").evaluate(form=>form.requestSubmit());
    await page.locator("#bang-khach-hang").filter({hasText:"New result"}).waitFor();
    await page.waitForTimeout(700);
    if((await page.locator("#bang-khach-hang").textContent()).includes("Old result"))throw Error("Stale search overwrote latest result");
    await page.evaluate(()=>{window.fetch=(input,options)=>String(input).includes("tu_khoa=OFFLINE")?Promise.reject(new TypeError("Failed to fetch")):window.__originalFetch(input,options);});
    await page.locator("#tu-khoa-kh").fill("OFFLINE");
    await page.locator("#form-tra-cuu-kh").evaluate(form=>form.requestSubmit());
    await page.locator("#bang-khach-hang").filter({hasText:"Không kết nối được máy chủ"}).waitFor();
    await page.evaluate(()=>window.fetch=window.__originalFetch);
    await page.setViewportSize({width:390,height:844});
    await page.getByRole("button",{name:"Menu",exact:true}).click();
    await page.getByRole("button",{name:"Đóng menu",exact:true}).waitFor();
    await page.screenshot({path:path.join(screenshots,"navigation-mobile-fixed.png"),fullPage:false});
    await page.keyboard.press("Escape");
    if(await page.locator(".workspace").evaluate(node=>node.inert))throw Error("Workspace stayed inert");
    await page.getByRole("button",{name:"Menu",exact:true}).click();
    await page.locator('#menu a[href="/ban-hang/tra-cuu-kho"]').click();
    if(await page.locator(".workspace").evaluate(node=>node.inert))throw Error("Navigation did not close drawer");
    await page.locator("[data-sales-heading]").filter({hasText:"Tra cứu kho"}).waitFor();
    await page.goto(origin+"/ban-hang/don-hang/moi");
    await page.locator('#chon-sp-nhanh option[value="SP02"]').waitFor({state:"attached"});
    await page.locator("#chon-sp-nhanh").selectOption("SP02");
    await page.locator("#nut-them-san-pham").click();
    await page.locator("#gui").click();
    await page.locator("#khu-thanh-toan").waitFor();
    await page.locator("#ten-kh").filter({hasText:"Khách lẻ"}).waitFor();
    await page.locator('[data-cash="exact"]').click();
    if(await page.locator('[name="tien_khach_dua"]').inputValue()!=="230.000")throw Error("Exact cash button failed");
    await page.locator("#du-kien-tien-thoi").filter({hasText:"0 ₫"}).waitFor().catch(async()=>{
      if(!(await page.locator("#du-kien-tien-thoi").textContent()).includes("0 đ"))throw Error("Exact cash change incorrect");
    });
    const paymentsBeforeInvalid=paymentSubmits;
    await page.locator('[name="tien_khach_dua"]').fill("500.50");
    await page.getByRole("button",{name:"Thanh toán và xuất hóa đơn",exact:true}).click();
    await page.locator('[data-loi-truong="thong_tin.tien_khach_dua"]').filter({hasText:"hợp lệ"}).waitFor();
    if(paymentSubmits!==paymentsBeforeInvalid)throw Error("Invalid currency submitted");
    await page.locator('[name="phuong_thuc"]').selectOption("CHUYEN_KHOAN");
    if(await page.locator('[name="so_tien_doi_soat"]').inputValue()!=="230.000")throw Error("Bank amount not filled");
    await page.locator('[name="ten_ngan_hang"]').fill("MB Bank");
    await page.locator('[name="ma_giao_dich_ngan_hang"]').fill("UI-BANK-TEST");
    await page.getByRole("button",{name:"Thanh toán và xuất hóa đơn",exact:true}).click();
    await page.waitForURL("**/hoa-don");
    await page.locator("#phuong-thuc").filter({hasText:"Chuyển khoản"}).waitFor();
    // Mã chuyển khoản trùng phải bị chặn và giữ nguyên tồn đang giữ.
    await page.goto(origin+"/ban-hang/don-hang/moi");
    await page.locator('#chon-sp-nhanh option[value="SP02"]').waitFor({state:"attached"});
    await page.locator("#chon-sp-nhanh").selectOption("SP02");
    await page.locator("#nut-them-san-pham").click();
    await page.locator("#gui").click();
    await page.locator("#khu-thanh-toan").waitFor();
    await page.locator('[name="phuong_thuc"]').selectOption("CHUYEN_KHOAN");
    await page.locator('[name="ten_ngan_hang"]').fill("MB Bank");
    await page.locator('[name="ma_giao_dich_ngan_hang"]').fill("UI-BANK-TEST");
    await page.getByRole("button",{name:"Thanh toán và xuất hóa đơn",exact:true}).click();
    await page.locator('[data-loi-truong="thong_tin.ma_giao_dich_ngan_hang"]').filter({hasText:/đã|trùng/i}).waitFor();
    const duplicateStatus=await page.evaluate(async()=> (await Api.get(location.pathname.replace("/ban-hang/","/api/ban-hang/"))).trang_thai);
    if(duplicateStatus!=="CHO_THANH_TOAN")throw Error("Duplicate bank reference changed order state");
    if(errors.length)throw Error(errors.join("\n"));
    console.log("PASS: integrated auth, warehouse desktop/mobile, receipt create/confirm, receipt list, lot names/supplier, search, product filter, alerts, logout, sales order/payment/invoice using real IKho.");
  } finally {
    await browser?.close();
    worker.stdin.end();
    await new Promise(resolve=>worker.once("exit",resolve));
    for(const suffix of ["","-wal","-shm"])fs.rmSync(database+suffix,{force:true});
  }
}
run().catch(e=>{console.error(e);process.exitCode=1;});
