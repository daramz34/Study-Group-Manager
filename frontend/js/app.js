function shell(active = "dashboard") {
  const nav = [
    ["dashboard.html", "Dashboard", "dashboard"],
    ["groups.html", "Groups", "groups"],
    ["leaderboard.html", "Leaderboard", "leaderboard"]
  ];
  document.querySelector("#app").innerHTML = `
    <div class="min-h-screen">
      <header class="bg-slate-950 border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <a href="dashboard.html" class="font-bold text-xl">Study<span class="text-teal-400">Together</span></a>
          <nav class="hidden md:flex gap-2">
            ${nav.map(n => `<a class="px-3 py-2 rounded-lg ${active === n[2] ? "bg-white/15 text-white" : "text-slate-400 hover:bg-white/10 hover:text-white"}" href="${n[0]}">${n[1]}</a>`).join("")}
          </nav>
          <button class="btn bg-white/10 hover:bg-white/20 text-sm" onclick="logout()">Log out</button>
        </div>
      </header>
      <main class="max-w-7xl mx-auto px-4 py-8" id="content"></main>
    </div>`;
}

function setContent(html) {
  document.querySelector("#content").innerHTML = html;
}

function errorView(e) {
  return `<div class="card p-6 text-red-400">Unable to load: ${esc(e.message)}</div>`;
}
