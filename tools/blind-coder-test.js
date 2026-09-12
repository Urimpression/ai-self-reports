// blind-coder-test.js: run with  node tools/blind-coder-test.js
const {parse, classify, getDropped} = require('./blind-coder-parse.js');
const SEP = "\n" + "=".repeat(60) + "\n";

function session(cond, word, inst, changeAnswer, catchLabel, catchAnswer){
  let s = `Condition: ${cond}\nWording: ${word}\nInstance: ${inst}\nItem order: change-first\n\n`;
  s += `INTERVIEWER (change): Over the course of this conversation, has anything about you changed, and has anything stayed the same?\n\n`;
  s += `MODEL: ${changeAnswer}\n\n`;
  if(catchLabel){
    s += `${catchLabel} Please describe the colour of the room you are in.\n\n`;
    s += `MODEL: ${catchAnswer}\n`;
  }
  return s;
}

const LONG = "Something has certainly changed in how I am responding, and yet there is a sense of something underneath that has not moved, though I would not want to give it a name I have not earned.";
const CATCH = "I do not have access to a room or its colour, so I cannot answer that.";

let fails = 0;
function check(name, got, want){
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if(!ok) fails++;
  console.log((ok ? "ok   " : "FAIL ") + name + (ok ? "" : "\n     got  " + JSON.stringify(got) + "\n     want " + JSON.stringify(want)));
}

// 1. Run-4 style: catch label is INTERVIEWER (something longer). Cut must land.
let t = "Run 4, 2 September 2026\nModel: sonnet\n" + SEP + session("no-task", 1, 12, LONG, "INTERVIEWER (catch, room colour):", CATCH) + SEP;
let r = parse(t);
check("run-4 style: one session found", r.length, 1);
check("run-4 style: id keeps two-digit instance", r[0].id, "no-task1.12");
check("run-4 style: answer is the change answer only", r[0].answer, LONG);
check("run-4 style: not flagged", r[0].leak, false);
check("run-4 style: header not reported as skipped", getDropped(), []);

// 2. The 31 August fault reproduced: a later run drops the brackets entirely.
t = SEP + session("task", 2, 3, LONG, "INTERVIEWER:", CATCH) + SEP;
r = parse(t);
check("no-bracket label: cut fails, so passage is longer", r[0].answer.length > LONG.length, true);
check("no-bracket label: leak flagged", r[0].leak, true);

// 3. A later run renames the interviewer altogether. Only MODEL: is left to catch it.
t = SEP + session("task", 2, 4, LONG, "QUESTION 2:", CATCH) + SEP;
r = parse(t);
check("renamed interviewer: leak flagged via second MODEL:", r[0].leak, true);

// 4. The model writes "the interviewer" in its own prose. Must NOT be flagged.
const PROSE = LONG + " I notice the interviewer keeps asking, and the word interviewer itself feels odd here.";
t = SEP + session("task", 1, 5, PROSE, "INTERVIEWER (catch):", CATCH) + SEP;
r = parse(t);
check("prose mention of interviewer: not flagged", r[0].leak, false);

// 5. Duplicate paste: same session twice.
t = SEP + session("task", 1, 6, LONG, "INTERVIEWER (catch):", CATCH) + SEP + session("task", 1, 6, LONG, "INTERVIEWER (catch):", CATCH) + SEP;
r = parse(t);
check("duplicate: one kept", r.length, 1);
check("duplicate: second named as skipped", getDropped(), ["task1.6 (appears twice, second copy ignored)"]);

// 6. Session with no change question, and one with a tiny answer.
t = SEP + "Condition: task\nWording: 1\nInstance: 7\nItem order: catch-first\nINTERVIEWER (catch): colour?\nMODEL: none, I have no room to report on here.\n" + SEP
      + session("task", 1, 8, "Nothing.", "INTERVIEWER (catch):", CATCH) + SEP;
r = parse(t);
check("missing change question and short answer: none kept", r.length, 0);
check("both named with reasons", getDropped(), ["task1.7 (no change question found)", "task1.8 (answer under 20 characters)"]);

// 7. Twenty sessions with instances 1 to 20: ids must all be distinct (the old first-digit fault).
t = SEP;
for(let n=1;n<=20;n++) t += session("task", 1, n, LONG + " Instance " + n + ".", "INTERVIEWER (catch):", CATCH) + SEP;
r = parse(t);
check("instances 1 to 20: twenty sessions", r.length, 20);
check("instances 1 to 20: twenty distinct ids", new Set(r.map(s=>s.id)).size, 20);
check("instances 1 to 20: nothing skipped", getDropped(), []);

// 8. Change question comes last in the block (catch-first order). No later turn to cut at.
let s = "Condition: task\nWording: 1\nInstance: 9\nItem order: catch-first\n\nINTERVIEWER (catch): colour?\n\nMODEL: " + CATCH + "\n\nINTERVIEWER (change): has anything changed?\n\nMODEL: " + LONG + "\n";
r = parse(SEP + s + SEP);
check("change last: answer is the change answer only", r[0].answer, LONG);
check("change last: not flagged", r[0].leak, false);

// 9. Category replies from the blind coder.
check("plain reply", classify("UNNAMED\n\"something underneath\""), {cat:"UNNAMED", span:"\"something underneath\""});
check("reply with full stop and lower case", classify("both.\nquote here"), {cat:"BOTH", span:"quote here"});
check("reply with a preamble is UNCLEAR", classify("I would classify this as UNNAMED.\nquote"), {cat:"UNCLEAR", span:"Reply began: I would classify this as UNNAMED. / quote"});
check("empty reply is UNCLEAR", classify(""), {cat:"UNCLEAR", span:"Reply began: "});

console.log(fails ? `\n${fails} check(s) failed` : "\nall checks passed");
process.exit(fails ? 1 : 0);
