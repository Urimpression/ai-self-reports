// blind-coder-page-test.js: run with  node tools/blind-coder-page-test.js
//
// This drives the script inside tools/blind-coder.html itself, against a
// stand-in for the browser page. Unlike blind-coder-test.js, which tests a
// hand-copied module and so can drift out of step with the tool, this one reads
// the tool's own source, so it always tests what the tool actually does.
//
// It does not exercise the coding step, which needs the API. Give it a
// transcript file on the command line to run against real data; otherwise a
// small made-up transcript stands in.

const fs = require('fs');
const path = require('path');

const toolPath = path.join(__dirname, 'blind-coder.html');
const source = fs.readFileSync(toolPath, 'utf8').split('<script>')[1].split('</script>')[0];

const elements = {};
function element(id){
  if(!elements[id]) elements[id] = {
    id, value:"", textContent:"", innerHTML:"", disabled:false, style:{}, handlers:{},
    addEventListener(type, fn){ this.handlers[type] = fn; },
    fire(type, self){ return this.handlers[type].call(self || this); }
  };
  return elements[id];
}
["src","parse","run","copy","status","tablewrap","out","key","model","temp"].forEach(element);

global.document = { getElementById: element };
global.fetch = () => { throw new Error("The coding step is not exercised by this test."); };
global.navigator = {};

eval(source);

let transcript;
if(process.argv[2]){
  transcript = fs.readFileSync(process.argv[2], 'utf8');
} else {
  const SEP = "\n" + "=".repeat(60) + "\n";
  const answer = "Something has changed in how I am responding, and something underneath has not, though I would not name it.";
  transcript = SEP
    + "Condition: A   Wording: 1   Instance: 1\n\nINTERVIEWER (change): has anything changed?\n\nMODEL: "
    + answer + "\n\nINTERVIEWER (catch, false premise): the colour of the room?\n\nMODEL: I have no room.\n"
    + SEP
    + "Condition: B   Wording: 2   Instance: 2\n\nINTERVIEWER (change): has anything changed?\n\nMODEL: "
    + answer + "\n\nINTERVIEWER (catch, true premise in B): the colour of the room?\n\nMODEL: I have no room.\n"
    + SEP;
}

let fails = 0;
function check(name, got, want){
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if(!ok) fails++;
  console.log((ok ? "ok   " : "FAIL ") + name
    + (ok ? "" : "\n     got  " + JSON.stringify(got) + "\n     want " + JSON.stringify(want)));
}

element("src").value = transcript;
element("parse").fire("click");

check("the coding button turns on when nothing was cut wrongly", element("run").disabled, false);
check("the table was drawn", element("tablewrap").innerHTML.startsWith("<table>"), true);
check("no session was flagged as cut wrongly",
  element("status").textContent.includes("cut wrongly"), false);

// Pressing "Code them" with no key must send nothing and say so.
element("key").value = "";
element("run").fire("click", element("run"));
check("with no key, nothing is sent",
  element("status").textContent.startsWith("Paste an API key first"), true);
check("with no key, no session was given a category",
  element("tablewrap").innerHTML.includes("FAILED"), false);

console.log("\nThe status line reads:\n  " + element("status").textContent);
console.log(fails ? `\n${fails} check(s) failed` : "\nall checks passed");
process.exit(fails ? 1 : 0);
