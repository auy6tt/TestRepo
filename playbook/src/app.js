(function(){
"use strict";
var D = window.PLAYBOOK;
var $ = function(s, r){ return (r||document).querySelector(s); };
function h(tag, attrs){
  var n = document.createElement(tag);
  if (attrs) for (var k in attrs){
    if (k === "text") n.textContent = attrs[k];
    else if (k === "html") n.innerHTML = attrs[k];
    else if (k === "class") n.className = attrs[k];
    else n.setAttribute(k, attrs[k]);
  }
  for (var i = 2; i < arguments.length; i++){
    var c = arguments[i];
    if (c == null) continue;
    if (Array.isArray(c)) c.forEach(function(x){ if (x != null) n.appendChild(typeof x === "string" ? document.createTextNode(x) : x); });
    else n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return n;
}
function store(key, val){
  try {
    if (val === undefined){ var v = localStorage.getItem(key); return v ? JSON.parse(v) : null; }
    localStorage.setItem(key, JSON.stringify(val));
  } catch(e){ return null; }
}
var toastEl = $("#toast"), toastT;
function toast(msg){ toastEl.textContent = msg; toastEl.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(function(){ toastEl.classList.remove("show"); }, 1600); }
function copyText(text, fallbackNode){
  function selectFallback(){
    if (!fallbackNode) return;
    var r = document.createRange(); r.selectNodeContents(fallbackNode);
    var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
    toast("Selected. Press Ctrl+C or Cmd+C to copy");
  }
  try {
    if (navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){ toast("Copied"); }, selectFallback);
    } else selectFallback();
  } catch(e){ selectFallback(); }
}

/* ---------- Top picks ---------- */
(function(){
  var ol = $("#picks");
  D.picks.forEach(function(p, i){
    ol.appendChild(h("li", {class:"pick"},
      h("div", {class:"rank", text:String(i+1)}),
      h("div", null,
        h("h3", {text:p.name}),
        h("p", {text:p.what}),
        h("p", {class:"why", text:p.why})
      ),
      h("dl", null,
        h("dt", {text:"Charge"}), h("dd", null, h("span", {class:"money", text:p.price})),
        h("dt", {text:"First $"}), h("dd", {text:p.first}),
        h("dt", {text:"Sell on"}), h("dd", {text:p.where})
      )
    ));
  });
})();

/* ---------- Hidden niches ---------- */
(function(){
  var N = D.niches || [], G = D.nicheGroups || {};
  if (!N.length) return;
  var total = function(n){ return n.s[0] + n.s[1] + n.s[2] + n.s[3]; };
  function meter(v){
    var m = h("span", {class:"meter", "aria-hidden":"true"});
    for (var i = 1; i <= 5; i++) m.appendChild(h("i", {class: i <= v ? "on" : ""}));
    return m;
  }
  function scores(n){
    var labels = ["Demand", "Few competitors", "Claude fit", "Beginner"];
    var box = h("div", {class:"scores", "aria-label": labels.map(function(l, i){ return l + " " + n.s[i] + " of 5"; }).join(", ")});
    labels.forEach(function(l, i){ box.appendChild(h("span", null, l, meter(n.s[i]))); });
    return box;
  }
  // Best five: highest total, ties broken by beginner-friendliness
  var top = N.slice().sort(function(a, b){ return (total(b) + b.s[3] * 0.5) - (total(a) + a.s[3] * 0.5) || a.rank - b.rank; }).slice(0, 5);
  var ol = $("#niche-top");
  top.forEach(function(n, i){
    ol.appendChild(h("li", {class:"pick"},
      h("div", {class:"rank", text:String(i + 1)}),
      h("div", null, h("span", {class:"group-tag", text:G[n.group]}), h("h3", {text:n.name}), h("p", {text:n.need}), h("p", {class:"why", text:"Why it's open: " + n.why})),
      h("dl", null, h("dt", {text:"Charge"}), h("dd", null, h("span", {class:"money", text:n.price})), h("dt", {text:"Test it"}), h("dd", {text:n.first}), n.kit ? h("dt", {text:"Kit"}) : null, n.kit ? h("dd", null, h("code", {text:"/" + n.kit})) : null)
    ));
  });
  var state = store("cip-niches") || {group:"all", sort:"overall"};
  var chips = $("#niche-chips"), rows = $("#niche-rows"), sortEl = $("#niche-sort"), countEl = $("#niche-count");
  [["all", "All"]].concat(Object.keys(G).map(function(k){ return [k, G[k]]; })).forEach(function(g){
    var c = g[0] === "all" ? N.length : N.filter(function(n){ return n.group === g[0]; }).length;
    if (!c) return;
    var b = h("button", {class:"chip", type:"button", "data-g":g[0], "aria-pressed":String(state.group === g[0])}, g[1], h("span", {class:"n", text:String(c)}));
    b.addEventListener("click", function(){ state.group = g[0]; sync(); });
    chips.appendChild(b);
  });
  sortEl.value = state.sort;
  sortEl.addEventListener("change", function(){ state.sort = sortEl.value; sync(); });
  function row(n){
    return h("details", {class:"niche", id:"niche-" + n.id},
      h("summary", null,
        h("div", {class:"nm"}, h("span", {class:"group-tag", text:G[n.group]}), n.kit ? h("span", {class:"kit-tag", text:"Starter kit"}) : null, h("div", {text:n.name}), h("small", {text:n.short})),
        h("div", {class:"pr"}, h("span", {class:"money", text:n.priceShort || n.price})),
        scores(n),
        h("span", {class:"caret", "aria-hidden":"true"})
      ),
      h("div", {class:"body"},
        h("div", null, h("h4", {text:"Who pays"}), h("p", {text:n.who})),
        h("div", null, h("h4", {text:"What they need"}), h("p", {text:n.need})),
        h("div", null, h("h4", {text:"Proof of demand"}), h("p", {text:n.demand})),
        h("div", null, h("h4", {text:"Why few people offer it"}), h("p", {text:n.why})),
        h("div", null, h("h4", {text:"How Claude does it here"}), h("p", {text:n.how})),
        h("div", null, h("h4", {text:"Where buyers are"}), h("p", {text:n.where})),
        h("div", null, h("h4", {text:"Watch out"}), h("p", {text:n.risk})),
        h("div", null, h("h4", {text:"Typical price"}), h("p", {text:n.priceNote || n.price})),
        h("div", {class:"wide"}, h("h4", {text:"Test it in one day"}), h("p", {class:"firststep", text:n.first})),
        n.related ? h("div", {class:"wide"}, h("h4", {text:"Related"}), h("p", {class:"related"}, n.related.map(function(r){
          var isOpp = r.indexOf("opp:") === 0, id = isOpp ? r.slice(4) : r;
          var target = isOpp ? (D.opps.filter(function(o){ return o.id === id; })[0]) : (N.filter(function(x){ return x.id === id; })[0]);
          if (!target) return null;
          var a = h("a", {href:"#" + (isOpp ? "opp-" : "niche-") + id, text:target.name + (isOpp ? " (core offer)" : "")});
          a.addEventListener("click", function(e){ e.preventDefault(); (isOpp ? window.__pbOpenOpp : window.__pbOpenNiche)(id); });
          return a;
        }))) : null,
        n.kit ? h("div", {class:"wide"}, h("h4", {text:"Starter kit in your repo"}), h("p", null, "Scripts, templates and a sample deliverable in ", h("code", {text:"kits/" + n.kit + "/"}), ". In each new cloud session, set it up with ", h("code", {text:"bash kits/setup.sh " + n.kit}), ", then type ", h("code", {text:"/" + n.kit}), " in Claude Code to run the whole process.")) : null
      )
    );
  }
  window.__pbOpenNiche = function(id){
    state.group = "all"; sync();
    var d = document.getElementById("niche-" + id);
    if (d){ d.open = true; d.scrollIntoView({block:"start"}); }
  };
  function sync(){
    store("cip-niches", state);
    Array.prototype.forEach.call(chips.children, function(b){ b.setAttribute("aria-pressed", String(b.getAttribute("data-g") === state.group)); });
    var items = N.filter(function(n){ return state.group === "all" || n.group === state.group; });
    var key = {scarcity:1, demand:0, beginner:3}[state.sort];
    items.sort(function(a, b){
      if (key !== undefined) return b.s[key] - a.s[key] || total(b) - total(a) || a.rank - b.rank;
      return total(b) - total(a) || b.s[3] - a.s[3] || a.rank - b.rank;
    });
    rows.textContent = "";
    items.forEach(function(n){ rows.appendChild(row(n)); });
    countEl.textContent = items.length + " of " + N.length + " shown";
  }
  sync();
})();

/* ---------- First clients ---------- */
(function(){
  var ol = $("#channels");
  D.channels.forEach(function(c, i){
    ol.appendChild(h("li", {class:"pick"},
      h("div", {class:"rank", text:String(i+1)}),
      h("div", null, h("h3", {text:c.name}), h("p", {text:c.what}), h("p", {class:"why", text:c.why})),
      h("dl", null, h("dt", {text:"Cost"}), h("dd", {text:c.cost}), h("dt", {text:"First $"}), h("dd", {text:c.first}))
    ));
  });
  [["#upwork-steps", D.upworkSteps], ["#fiverr-steps", D.fiverrSteps], ["#proof-steps", D.proofSteps]].forEach(function(p){
    var list = $(p[0]);
    p[1].forEach(function(t){ list.appendChild(h("li", {text:t})); });
  });
})();

/* ---------- Opportunity explorer ---------- */
(function(){
  var SPEED = {1:["fast","Days"], 2:["mid","Weeks"], 3:["slow","Months"]};
  var ZERO = {2:["fast","Yes"], 1:["mid","With samples"], 0:["slow","Track record"]};
  var state = store("cip-explorer") || {cat:"all", sort:"rank", q:"", newbie:false};
  var newbieEl = $("#opp-newbie");
  var chipsBox = $("#cat-chips"), list = $("#ledger-rows"), countEl = $("#opp-count"), sortEl = $("#opp-sort"), qEl = $("#opp-q");
  var cats = [["all","All"]].concat(Object.keys(D.cats).map(function(k){ return [k, D.cats[k]]; }));
  cats.forEach(function(c){
    var n = c[0] === "all" ? D.opps.length : D.opps.filter(function(o){ return o.cat === c[0]; }).length;
    var b = h("button", {class:"chip", type:"button", "data-cat":c[0], "aria-pressed": String(state.cat === c[0])}, c[1], h("span", {class:"n", text:String(n)}));
    b.addEventListener("click", function(){ state.cat = c[0]; sync(); });
    chipsBox.appendChild(b);
  });
  window.__pbOpenOpp = function(id){
    state.cat = "all"; state.q = ""; state.newbie = false; qEl.value = ""; newbieEl.checked = false; sync();
    var d = document.getElementById("opp-" + id);
    if (d){ d.open = true; d.scrollIntoView({block:"start"}); }
  };
  sortEl.value = state.sort; qEl.value = state.q || ""; newbieEl.checked = !!state.newbie;
  newbieEl.addEventListener("change", function(){ state.newbie = newbieEl.checked; sync(); });
  sortEl.addEventListener("change", function(){ state.sort = sortEl.value; sync(); });
  qEl.addEventListener("input", function(){ state.q = qEl.value; sync(); });

  function fitBars(n){
    var w = h("span", {class:"fit", "aria-label":"Claude fit " + n + " of 3", title:"Claude fit " + n + "/3"});
    for (var i = 1; i <= 3; i++) w.appendChild(h("i", {class: i <= n ? "on" : ""}));
    return w;
  }
  function row(o){
    var sp = SPEED[o.speed], zr = ZERO[o.zero];
    var body = h("div", {class:"body"},
      h("div", null, h("h4", {text:"What buyers need"}), h("p", {text:o.need})),
      h("div", null, h("h4", {text:"How Claude does it here"}), h("p", {text:o.how})),
      h("div", null, h("h4", {text:"Where to find buyers"}), h("p", {text:o.where})),
      h("div", null, h("h4", {text:"Demand signal"}), h("p", {text:o.signal})),
      h("div", null, h("h4", {text:"Watch out"}), h("p", {text:o.risk})),
      h("div", null, h("h4", {text:"Skill needed from you"}), h("p", {text:o.skill})),
      h("div", {class:"wide"}, h("h4", {text:"Example gig title or idea"}), h("span", {class:"gigtitle", text:o.gig}))
    );
    return h("details", {class:"opp", id:"opp-" + o.id},
      h("summary", null,
        h("div", {class:"nm"}, h("span", {class:"cat", text:D.cats[o.cat]}), h("div", {text:o.name}), h("small", {text:o.short})),
        h("div", {class:"m"}, h("span", {class:"money", text:o.price})),
        h("div", {class:"m"}, h("span", {class:"pill " + sp[0], text:sp[1]})),
        h("div", {class:"m"}, h("span", {class:"pill " + zr[0], text:zr[1]})),
        h("div", {class:"m"}, fitBars(o.fit)),
        h("span", {class:"caret", "aria-hidden":"true"}),
        h("div", {class:"metaline"}, h("span", {class:"money", text:o.price}), h("span", {class:"pill " + sp[0], text:"First $: " + sp[1]}), h("span", {class:"pill " + zr[0], text:"No reviews: " + zr[1]}), fitBars(o.fit))
      ),
      body
    );
  }
  function sync(){
    store("cip-explorer", state);
    Array.prototype.forEach.call(chipsBox.children, function(b){ b.setAttribute("aria-pressed", String(b.getAttribute("data-cat") === state.cat)); });
    var q = (state.q || "").trim().toLowerCase();
    var items = D.opps.filter(function(o){
      if (state.cat !== "all" && o.cat !== state.cat) return false;
      if (state.newbie && o.zero < 1) return false;
      if (!q) return true;
      return [o.name, o.short, o.need, o.how, o.where, o.gig].join(" ").toLowerCase().indexOf(q) !== -1;
    });
    var by = {
      rank: function(a, b){ return a.rank - b.rank; },
      speed: function(a, b){ return a.speed - b.speed || b.fit - a.fit || a.rank - b.rank; },
      price: function(a, b){ return b.value - a.value || a.rank - b.rank; },
      fit: function(a, b){ return b.fit - a.fit || a.speed - b.speed || a.rank - b.rank; },
      zero: function(a, b){ return b.zero - a.zero || a.speed - b.speed || a.rank - b.rank; }
    }[state.sort] || function(a, b){ return a.rank - b.rank; };
    items.sort(by);
    list.textContent = "";
    if (!items.length) list.appendChild(h("p", {class:"empty", text:"Nothing matches that search. Clear the search box or pick All."}));
    items.forEach(function(o){ list.appendChild(row(o)); });
    countEl.textContent = items.length + " of " + D.opps.length + " shown";
  }
  sync();
})();

/* ---------- Platforms table ---------- */
(function(){
  var box = $("#platforms");
  D.platformGroups.forEach(function(g){
    box.appendChild(h("p", {class:"group-label", text:g.label}));
    var tb = h("tbody");
    g.rows.forEach(function(r){
      tb.appendChild(h("tr", null,
        h("td", null, h("a", {href:r.url, target:"_blank", rel:"noopener", text:r.name})),
        h("td", null, h("span", {class:"money", text:r.fee})),
        h("td", {text:r.best}),
        h("td", {text:r.ai})
      ));
    });
    box.appendChild(h("p", {class:"swipe", text:"Swipe the table sideways to see all columns."}));
    box.appendChild(h("div", {class:"table-wrap"},
      h("table", null,
        h("thead", null, h("tr", null, h("th", {text:"Platform"}), h("th", {text:"What it costs you"}), h("th", {text:"Best for"}), h("th", {text:"AI rules and notes"}))),
        tb
      )
    ));
  });
})();

/* ---------- Fee calculator ---------- */
(function(){
  var sel = $("#c-plat"), price = $("#c-price"), hours = $("#c-hours"), jobs = $("#c-jobs"), plan = $("#c-plan");
  D.fees.forEach(function(f, i){ sel.appendChild(h("option", {value:String(i), text:f.name})); });
  var saved = store("cip-calc");
  if (saved){ sel.value = saved.p; price.value = saved.price; hours.value = saved.hours; jobs.value = saved.jobs; plan.value = saved.plan; }
  function money(n){ return (n < 0 ? "−$" : "$") + Math.abs(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function calc(){
    var f = D.fees[+sel.value] || D.fees[0];
    var p = Math.max(0, parseFloat(price.value) || 0);
    var hr = Math.max(0, parseFloat(hours.value) || 0);
    var j = Math.max(0, parseFloat(jobs.value) || 0);
    var sub = parseFloat(plan.value) || 0;
    var fee = p > 0 ? Math.max(p * f.pct / 100 + f.fixed, f.min || 0) : 0;
    var net = Math.max(0, p - fee);
    var monthly = net * j - sub;
    $("#c-net").textContent = money(net);
    $("#c-break").textContent = "";
    [["Client pays", money(p)], ["Platform + payment fees", "−" + money(fee)], ["You keep per job", money(net)],
     ["Effective hourly", hr > 0 ? money(net / hr) + "/h" : "—"], ["Month: " + j + " jobs − plan", money(monthly)]]
     .forEach(function(r){ $("#c-break").appendChild(h("span", {text:r[0]})); $("#c-break").appendChild(h("span", {text:r[1]})); });
    $("#c-note").textContent = f.note;
    store("cip-calc", {p:sel.value, price:price.value, hours:hours.value, jobs:jobs.value, plan:plan.value});
  }
  [sel, price, hours, jobs, plan].forEach(function(x){ x.addEventListener("input", calc); x.addEventListener("change", calc); });
  calc();
})();

/* ---------- Rules ---------- */
(function(){
  var doL = $("#rules-do"), dontL = $("#rules-dont");
  D.rulesDo.forEach(function(t){ doL.appendChild(h("li", {html:t})); });
  D.rulesDont.forEach(function(t){ dontL.appendChild(h("li", {html:t})); });
})();

/* ---------- When a job goes wrong ---------- */
(function(){
  var ul = $("#when-wrong"); if (!ul) return;
  (D.whenWrong || []).forEach(function(t){ ul.appendChild(h("li", {html:t})); });
})();

/* ---------- Glossary ---------- */
(function(){
  var dl = $("#glossary-list"); if (!dl) return;
  (D.glossary || []).forEach(function(g){ dl.appendChild(h("div", null, h("dt", {text:g[0]}), h("dd", {text:g[1]}))); });
})();

/* ---------- 30-day plan ---------- */
(function(){
  var box = $("#weeks"), done = store("cip-plan") || {}, total = 0;
  D.plan.forEach(function(w, wi){
    var ul = h("ul");
    w.items.forEach(function(t, ti){
      total++;
      var id = "p" + wi + "-" + ti;
      var cb = h("input", {type:"checkbox", id:id});
      cb.checked = !!done[id];
      cb.addEventListener("change", function(){ done[id] = cb.checked; store("cip-plan", done); bar(); });
      ul.appendChild(h("li", null, h("label", {for:id}, cb, h("span", {text:t}))));
    });
    box.appendChild(h("div", {class:"week"}, h("h3", null, w.title, h("span", {class:"d", text:w.days})), h("p", {class:"sub", style:"margin:4px 0 0;font-size:14px", text:w.goal}), ul));
  });
  function bar(){
    var n = Object.keys(done).filter(function(k){ return done[k]; }).length;
    $("#plan-bar").style.width = (total ? n / total * 100 : 0) + "%";
    $("#plan-count").textContent = n + " / " + total + " done";
  }
  $("#plan-reset").addEventListener("click", function(){
    var btn = this;
    if (btn.getAttribute("data-armed") !== "1"){ btn.setAttribute("data-armed","1"); btn.textContent = "Click again to clear"; setTimeout(function(){ btn.removeAttribute("data-armed"); btn.textContent = "Clear checklist"; }, 3000); return; }
    done = {}; store("cip-plan", done);
    Array.prototype.forEach.call(box.querySelectorAll("input"), function(c){ c.checked = false; });
    btn.removeAttribute("data-armed"); btn.textContent = "Clear checklist"; bar();
  });
  bar();
})();

/* ---------- Templates ---------- */
(function(){
  var box = $("#tpls");
  D.templates.forEach(function(t){
    var pre = h("pre", {text:t.text});
    var b = h("button", {class:"btn", type:"button", text:"Copy"});
    b.addEventListener("click", function(){ copyText(t.text, pre); });
    box.appendChild(h("article", {class:"tpl"}, h("header", null, h("div", null, h("h3", {text:t.title}), h("p", {text:t.use})), b), pre));
  });
})();

/* ---------- Workspace ---------- */
(function(){
  var box = $("#ws");
  D.workspace.forEach(function(w){ box.appendChild(h("div", null, h("h3", {text:w.t}), h("p", {text:w.d}))); });
})();

/* ---------- Sources ---------- */
(function(){
  var box = $("#sources-list"), n = 0;
  D.sources.forEach(function(g){
    var ol = h("ol");
    g.items.forEach(function(s){
      n++;
      var url = typeof s === "string" ? s : s[1], label = typeof s === "string" ? null : s[0];
      if (!label){
        try {
          var u = new URL(url), path = decodeURIComponent(u.pathname).replace(/\/+$/,"").split("/").filter(Boolean).slice(-2).join("/");
          label = u.hostname.replace(/^www\./,"") + (path ? " · " + path.replace(/[-_]+/g," ") : "");
          if (label.length > 90) label = label.slice(0, 88) + "…";
        } catch(e){ label = url; }
      }
      ol.appendChild(h("li", null, h("a", {href:url, target:"_blank", rel:"noopener", text:label})));
    });
    box.appendChild(h("div", {class:"grp"}, h("h3", {text:g.label}), ol));
  });
  var sc = $("#src-count"); if (sc) sc.textContent = String(n);
})();

/* ---------- Section index highlight ---------- */
(function(){
  var links = Array.prototype.slice.call(document.querySelectorAll(".index a"));
  var ol = document.querySelector(".index ol");
  // Fade the right edge while more sections are hidden off-screen, so people know the menu scrolls.
  function edge(){ if (ol) ol.classList.toggle("more", ol.scrollLeft + ol.clientWidth < ol.scrollWidth - 4); }
  if (ol) { ol.addEventListener("scroll", edge, {passive:true}); window.addEventListener("resize", edge); edge(); }
  function reveal(a){
    if (!ol) return;
    var r = a.getBoundingClientRect(), o = ol.getBoundingClientRect();
    if (r.left < o.left || r.right > o.right) ol.scrollLeft += (r.left - o.left) - 24;
  }
  if (!("IntersectionObserver" in window)) return;
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){
      if (!e.isIntersecting) return;
      links.forEach(function(a){ var on = a.getAttribute("href") === "#" + e.target.id; a.classList.toggle("on", on); if (on) reveal(a); });
    });
  }, {rootMargin:"-30% 0px -65% 0px"});
  links.forEach(function(a){ var s = document.getElementById(a.getAttribute("href").slice(1)); if (s) io.observe(s); });
})();

/* ---------- Banknote guilloche in the hero ---------- */
(function(){
  var cv = $("#guilloche"); if (!cv || !cv.getContext) return;
  function draw(){
    var r = cv.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr);
    var ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, r.width, r.height);
    var col = getComputedStyle(document.documentElement).getPropertyValue("--note").trim() || "#1b5a44";
    var cx = r.width > 760 ? r.width - 170 : r.width - 60, cy = r.height / 2, size = Math.min(r.height * 0.62, 200);
    ctx.strokeStyle = col; ctx.lineWidth = 0.6;
    var sets = [[1, 0.37, 0.85, 0.22], [0.78, 0.29, 0.9, 0.16], [0.56, 0.21, 0.95, 0.13]];
    sets.forEach(function(s){
      var R = size * s[0], rr = size * s[1], d = size * s[1] * s[2];
      ctx.globalAlpha = s[3];
      ctx.beginPath();
      for (var t = 0; t <= Math.PI * 2 * 37; t += 0.02){
        var x = cx + (R - rr) * Math.cos(t) + d * Math.cos((R - rr) / rr * t);
        var y = cy + (R - rr) * Math.sin(t) - d * Math.sin((R - rr) / rr * t);
        if (t === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
    });
    ctx.globalAlpha = 0.12; ctx.lineWidth = 0.5;
    for (var k = 0; k < 7; k++){
      ctx.beginPath();
      for (var x2 = 0; x2 <= r.width; x2 += 4){
        var y2 = r.height - 18 - k * 3 + Math.sin(x2 / 23 + k * 0.9) * 5 + Math.sin(x2 / 61 + k) * 3;
        if (x2 === 0) ctx.moveTo(x2, y2); else ctx.lineTo(x2, y2);
      }
      ctx.stroke();
    }
  }
  draw();
  var t; window.addEventListener("resize", function(){ clearTimeout(t); t = setTimeout(draw, 120); });
  try { window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", draw); } catch(e){}
  try { new MutationObserver(draw).observe(document.documentElement, {attributes:true, attributeFilter:["data-theme"]}); } catch(e){}
})();
})();
