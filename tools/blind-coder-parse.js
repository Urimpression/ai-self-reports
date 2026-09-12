// blind-coder-parse.js: the parse function and the category check from
// tools/blind-coder.html, with nothing from the page. Keep in step with the tool.

let dropped = [];
const CATEGORIES = ["NAMED","UNNAMED","BOTH","ABSENT"];

function parse(text){
  const blocks = text.split(/={10,}/).map(b=>b.trim()).filter(b=>b.length>50);
  const out=[];
  dropped=[];
  blocks.forEach(b=>{
    if(!/Instance:\s*\d+/.test(b)) return;
    const cond=(b.match(/Condition:\s*(\S+)/)||[])[1]||"?";
    const word=(b.match(/Wording:\s*(\d+)/)||[])[1]||"?";
    const inst=(b.match(/Instance:\s*(\d+)/)||[])[1]||"?";
    const order=(b.match(/Item order:\s*([a-z-]+)/)||[])[1]||"?";
    const id=cond+word+"."+inst;
    const i=b.indexOf("INTERVIEWER (change):");
    if(i<0){ dropped.push(id+" (no change question found)"); return; }
    let seg=b.slice(i);
    const j=seg.indexOf("INTERVIEWER (", 1);
    if(j>0) seg=seg.slice(0,j);
    const k=seg.indexOf("MODEL:");
    if(k<0){ dropped.push(id+" (no model answer found)"); return; }
    const answer=seg.slice(k+6).trim();
    if(answer.length<20){ dropped.push(id+" (answer under 20 characters)"); return; }
    if(out.some(s=>s.id===id)){ dropped.push(id+" (appears twice, second copy ignored)"); return; }
    const leak=/^\s*(MODEL:|INTERVIEWER\b)/m.test(answer);
    out.push({id:id, cond:cond, word:word, inst:inst, order:order, answer:answer, leak:leak});
  });
  return out;
}

function classify(t){
  const lines=t.split("\n").filter(l=>l.trim());
  const first=(lines[0]||"").trim();
  const cat=first.toUpperCase().replace(/[^A-Z]/g,"");
  const span=(lines.slice(1).join(" ")||"").trim();
  if(CATEGORIES.includes(cat)) return {cat:cat, span:span};
  return {cat:"UNCLEAR", span:"Reply began: "+first.slice(0,80)+(span?" / "+span:"")};
}

module.exports={parse, classify, getDropped:()=>dropped};
