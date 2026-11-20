const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const source=fs.readFileSync(path.join(__dirname,"../kho_ban_hang/static/chung/phien.js"),"utf8");
const parse=vm.runInNewContext(source+"; Api.docTien");
for(const [input,expected] of [
  ["500000",500000],["500.000",500000],["500,000",500000],["500 000",500000],
  ["1.250.000",1250000],["0",0],["",null],["  ",null],
])assert.equal(parse(input),expected,input);
for(const input of ["500.50","500,50","1.000,000","-100","1e3","abc","9007199254740992"])
  assert.ok(Number.isNaN(parse(input)),input);
console.log("PASS: grouped VND amounts, blank input and invalid amounts.");
