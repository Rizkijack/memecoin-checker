/**
 * Memecoin Checker — Frontend App v2.0
 * Aggregator analisis memecoin dari 6+ platform berbeda.
 */

const API_BASE = '';

// ─── DOM refs ─────────────────────────────────────
const form = document.getElementById('searchForm');
const input = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');

// ─── Search ───────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = input.value.trim();
  if (!query) return;
  await searchToken(query);
});

document.querySelectorAll('.hint-tag').forEach(tag => {
  tag.addEventListener('click', () => {
    input.value = tag.dataset.query;
    form.dispatchEvent(new Event('submit'));
  });
});

async function searchToken(query) {
  resetState();
  loading.classList.add('active');
  error.classList.remove('active');
  results.classList.remove('active');
  searchBtn.disabled = true;

  const stepSequence = ['dex','rug','gmgn','sniffer','sharpe','pump','agg'];

  try {
    for (const stepId of stepSequence) {
      activateStep(stepId);
      await sleep(350);
    }

    const resp = await fetch(`${API_BASE}/api/analyze?q=${encodeURIComponent(query)}`);
    const json = await resp.json();

    if (!json.success) {
      showError(json.error || 'Analysis failed');
      return;
    }

    // Complete all steps
    for (const stepId of stepSequence) {
      completeStep(stepId);
      await sleep(150);
    }

    renderResults(json.data);

  } catch (err) {
    showError(err.message || 'Network error. Is the server running?');
  } finally {
    loading.classList.remove('active');
    searchBtn.disabled = false;
  }
}

function resetState() {
  document.querySelectorAll('.step').forEach(s => {
    s.className = 'step';
    s.innerHTML = s.dataset.label || s.innerHTML;
  });
}

function activateStep(id) {
  const el = document.getElementById('step' + id.charAt(0).toUpperCase() + id.slice(1)) || document.getElementById(id);
  if (!el) return;
  el.className = 'step step-active';
  el.innerHTML = '⏳ ' + (el.dataset.active || el.innerHTML);
}

function completeStep(id) {
  const el = document.getElementById('step' + id.charAt(0).toUpperCase() + id.slice(1)) || document.getElementById(id);
  if (!el) return;
  el.className = 'step step-done';
  el.innerHTML = '✅ ' + (el.dataset.done || el.innerHTML.replace(/^[^ ]+ /, ''));
}

function showError(msg) {
  error.classList.add('active');
  error.querySelector('.error-text').textContent = msg;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ─── Render Results ───────────────────────────────
function renderResults(data) {
  const s = data.summary;
  if (!s) return;

  // Token info
  const icon = document.getElementById('tokenIcon');
  icon.src = s.imageUrl || 'https://icons.llamao.fi/icons/tokens/unknown.svg';
  icon.onerror = () => { icon.src = 'https://icons.llamao.fi/icons/tokens/unknown.svg'; };
  document.getElementById('tokenName').textContent = s.tokenName;
  document.getElementById('tokenSymbol').textContent = '$' + s.tokenSymbol;
  document.getElementById('tokenChain').textContent = s.chain;
  document.getElementById('tokenDex').textContent = s.dex;

  // Badges
  renderBadge('riskBadge', s.riskLevel);
  renderBadge('oppBadge', s.opportunity);

  // Metrics
  setMetric('metricMC', formatUSD(s.marketCap));
  setMetric('metricPrice', '$' + parseFloat(s.priceUsd).toFixed(8));
  setMetric('metricVol', formatUSD(s.volume24h));
  setMetric('metricLiq', formatUSD(s.liquidity));
  setMetric('metricChange', (s.priceChange24h > 0 ? '+' : '') + s.priceChange24h.toFixed(2) + '%',
    s.priceChange24h > 0 ? 'positive' : s.priceChange24h < 0 ? 'negative' : 'neutral');
  setMetric('metricBuySell', s.buySellRatio, s.buySellRatio > 1 ? 'positive' : 'negative');

  // RugCheck
  renderRugCheck(s, data.rugCheck);

  // Top Pairs
  renderPairs(data.dexScreener.topPairs || []);

  // GMGN
  renderGMGN(data.gmgn);

  // Token Sniffer
  renderTokenSniffer(data.tokensniffer);

  // SharpeAI
  renderSharpeAI(data.sharpeai);

  // pump.fun
  renderPumpFun(data.pumpfun);

  // Address & links
  renderAddress(s.tokenAddress, s.chain);

  // Show
  results.classList.add('active');
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderBadge(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text || '—';
  el.className = 'badge';
  if (text.includes('Low') || text.includes('Gem') || text.includes('Major')) el.classList.add('badge-green');
  else if (text.includes('Medium') || text.includes('Neutral')) el.classList.add('badge-yellow');
  else if (text.includes('Risk') || text.includes('Danger') || text.includes('Critical')) el.classList.add('badge-red');
  else if (text.includes('Established')) el.classList.add('badge-blue');
  else el.classList.add('badge-yellow');
}

function renderRugCheck(s, rug) {
  if (s.rugScore !== null) {
    document.getElementById('rugScore').textContent = s.rugScore;
    document.getElementById('rugScoreNormalised').textContent = (s.rugScore / 10).toFixed(0) + '%';
    const bar = document.getElementById('riskBar');
    bar.style.width = Math.min(100, s.rugScore / 10) + '%';
    bar.className = 'risk-bar-fill';
    if (s.rugScore >= 700) bar.classList.add('risk-low');
    else if (s.rugScore >= 500) bar.classList.add('risk-medium');
    else bar.classList.add('risk-high');
  }
  const list = document.getElementById('riskList');
  list.innerHTML = '';
  if (rug && rug.summary && rug.summary.risks && rug.summary.risks.length > 0) {
    rug.summary.risks.forEach(r => {
      const li = document.createElement('li');
      const level = (r.level || r.severity || 'info').toLowerCase();
      const cls = level === 'danger' || level === 'critical' ? 'risk-level-bad' : level === 'warning' ? 'risk-level-warn' : '';
      li.innerHTML = `<span class="risk-name">${r.name || r.description}</span> <span class="${cls}">${level.toUpperCase()}</span>`;
      list.appendChild(li);
    });
  } else {
    list.innerHTML = '<li>✅ No risks detected by RugCheck</li>';
  }
}

function renderPairs(pairs) {
  const body = document.getElementById('pairBody');
  body.innerHTML = '';
  pairs.slice(0, 8).forEach(p => {
    const ch = p.priceChange?.h24 ?? 0;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="chain-cell">${p.chainId}</span> / <span class="dex-cell">${p.dexId}</span></td>
      <td class="num-cell">$${parseFloat(p.priceUsd || 0).toFixed(8)}</td>
      <td class="num-cell ${ch > 0 ? 'positive' : ch < 0 ? 'negative' : ''}">${ch > 0 ? '+' : ''}${ch.toFixed(2)}%</td>
      <td class="num-cell">${formatUSD(p.liquidity?.usd ?? 0)}</td>
      <td class="num-cell">${formatUSD(p.volume?.h24 ?? 0)}</td>
      <td class="num-cell positive">${(p.txns?.h24?.buys ?? 0)}</td>
      <td class="num-cell negative">${(p.txns?.h24?.sells ?? 0)}</td>
      <td><a class="pair-link" href="${p.url}" target="_blank">DS ↗</a></td>`;
    body.appendChild(tr);
  });
}

function renderGMGN(gmgn) {
  if (!gmgn) return;
  const h = gmgn.holderAnalysis || {};
  const hd = h.holderDistribution || {};
  document.getElementById('gmgnHolders').textContent = h.totalHolders != null ? h.totalHolders.toLocaleString() : '—';
  document.getElementById('gmgnTop10').textContent = hd.top10_pct != null ? hd.top10_pct + '%' : '—';
  const sn = h.sniperAnalysis || {};
  document.getElementById('gmgnSnipers').textContent = sn.sniperCount != null ? sn.sniperCount + ' wallets' : '—';
  document.getElementById('gmgnInsider').textContent = h.insiderScore != null ? h.insiderScore + '/100' : '—';
  document.getElementById('gmgnVerdict').textContent = h.verdict || '—';
}

function renderTokenSniffer(ts) {
  if (!ts) return;
  const sec = ts.contractSecurity || {};
  const score = sec.contractScore;
  if (score != null) {
    document.getElementById('tsScore').textContent = score;
    const bar = document.getElementById('tsBar');
    bar.style.width = Math.min(100, score / 10) + '%';
    bar.className = 'risk-bar-fill';
    if (score >= 700) bar.classList.add('risk-low');
    else if (score >= 400) bar.classList.add('risk-medium');
    else bar.classList.add('risk-high');
  }
  document.getElementById('tsLabel').textContent = sec.scoreLabel || '—';
  const sum = sec.summary || {};
  document.getElementById('tsCritical').textContent = sum.criticalRisks || 0;
  document.getElementById('tsGood').textContent = sum.goodSignals || 0;

  const list = document.getElementById('tsRiskList');
  list.innerHTML = '';
  const risks = sec.risks || [];
  if (risks.length > 0) {
    risks.forEach(r => {
      if (r.severity === 'GOOD') return; // skip good in risk list
      const li = document.createElement('li');
      const sev = (r.severity || '').toLowerCase();
      const cls = sev === 'critical' ? 'risk-level-bad' : sev === 'high' ? 'risk-level-warn' : '';
      const tag = sev === 'critical' ? '🔴' : sev === 'high' ? '⚠️' : 'ℹ️';
      li.innerHTML = `<span class="risk-name">${r.description || r.name}</span> <span class="${cls}">${tag} ${sev.toUpperCase()}</span>`;
      list.appendChild(li);
    });
  } else {
    list.innerHTML = '<li>✅ Contract looks clean</li>';
  }
}

function renderSharpeAI(sharpe) {
  if (!sharpe) return;
  const sent = sharpe.sentiment || {};
  const mkt = sharpe.marketScore || {};
  const sv = sent.socialVolume || {};

  document.getElementById('sharpeSentiment').textContent = sent.sentiment?.overall || '—';
  document.getElementById('sharpeScore').textContent = mkt.compositeScore != null ? mkt.compositeScore + '/100' : '—';
  document.getElementById('sharpeGrade').textContent = mkt.grade || '—';
  document.getElementById('sharpeTwitter').textContent = sv.twitterTweets24h != null ? sv.twitterTweets24h + ' tweets' : '—';
  document.getElementById('sharpeTelegram').textContent = sv.telegramMembers != null ? sv.telegramMembers.toLocaleString() + ' members' : '—';
  document.getElementById('sharpeBot').textContent = sv.organicVsBot || '—';
}

function renderPumpFun(pump) {
  if (!pump || !pump.found) {
    document.getElementById('pumpFound').style.display = 'none';
    document.getElementById('pumpNotFound').style.display = 'block';
    return;
  }
  document.getElementById('pumpFound').style.display = 'block';
  document.getElementById('pumpNotFound').style.display = 'none';
  const bc = pump.bondingCurve || {};
  const age = pump.age || {};
  const bp = pump.buyPressure || {};

  document.getElementById('pumpStage').textContent = bc.stage || '—';
  document.getElementById('pumpProgress').textContent = bc.progressPct != null ? bc.progressPct + '%' : '—';
  document.getElementById('pumpAge').textContent = age.label || '—';
  document.getElementById('pumpBuyPressure').textContent = bp.h1 != null ? bp.h1 + 'x' : '—';
  document.getElementById('pumpStatus').textContent = bp.status || '—';
}

function renderAddress(addr, chain) {
  const el = document.getElementById('tokenAddressDisplay');
  if (addr) {
    el.innerHTML = `<span>${shortenAddress(addr)}</span><button class="copy-btn" onclick="copyAddress('${addr}')" title="Copy">📋</button>`;
  } else {
    el.innerHTML = '<span class="text-muted">No address available</span>';
  }

  const links = document.getElementById('extLinks');
  links.innerHTML = '';
  if (addr) {
    const items = [
      { label: '🔍 DexScreener', url: `https://dexscreener.com/search?q=${addr}` },
      { label: '🛡️ RugCheck', url: `https://rugcheck.xyz/tokens/${addr}` },
      { label: '📊 Birdeye', url: `https://birdeye.so/token/${addr}?chain=${chain}` },
      { label: '🐍 GMGN', url: `https://gmgn.ai/sol/token/${addr}` },
      { label: '🚀 pump.fun', url: chain === 'solana' ? `https://pump.fun/coin/${addr}` : null },
      { label: '🐞 Solscan', url: chain === 'solana' ? `https://solscan.io/token/${addr}` : null },
      { label: '🔷 BaseScan', url: chain === 'base' ? `https://basescan.org/token/${addr}` : null },
    ].filter(l => l.url);
    items.forEach(l => {
      const a = document.createElement('a');
      a.href = l.url;
      a.target = '_blank';
      a.className = 'ext-link';
      a.textContent = l.label;
      links.appendChild(a);
    });
  }
}

// ─── Helpers ──────────────────────────────────────
function setMetric(id, value, type) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = value;
  el.className = 'metric-value' + (type ? ' ' + type : '');
}

function formatUSD(n) {
  if (!n || isNaN(n)) return '$0';
  if (n >= 1e9) return '$' + (n / 1e9).toFixed(2) + 'B';
  if (n >= 1e6) return '$' + (n / 1e6).toFixed(2) + 'M';
  if (n >= 1e3) return '$' + (n / 1e3).toFixed(2) + 'K';
  return '$' + n.toFixed(2);
}

function shortenAddress(a) {
  if (!a) return '';
  if (a.length <= 16) return a;
  return a.slice(0, 6) + '...' + a.slice(-4);
}

function copyAddress(addr) {
  navigator.clipboard.writeText(addr).then(() => {
    const btn = document.querySelector('.copy-btn');
    if (btn) { btn.textContent = '✅'; setTimeout(() => { btn.textContent = '📋'; }, 1500); }
  });
}
