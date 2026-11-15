/**
 * MRAC 2025 & HVAC/R Integrated Study Helper
 * Offline-first & Google Sites safe controller for all 52 chapters, EPA 608,
 * interactive labs, split-companion staging, telemetry, and live manifest updates.
 */
(function () {
  'use strict';

  const HUB_PREFS_KEY = 'ish_hub_prefs_v1';
  const DEFAULT_EPA608_KEYS = ['cte_epa608_esco_v10', 'cte_epa608_esco_v9'];
  const CAREER_RANKS = [
    { min: 10000, name: 'Master HVAC/R', icon: '🏆' },
    { min: 5000,  name: 'Lead Tech',     icon: '🥇' },
    { min: 2000,  name: 'Journeyman',    icon: '⚡' },
    { min: 500,   name: 'Field Tech',    icon: '❄️' },
    { min: 0,     name: 'Apprentice',    icon: '🛠️' }
  ];

  // In-memory fallback map when third-party storage is blocked inside iframes.
  const memoryStorage = new Map();
  let storageBlocked = false;

  function safeGetItem(key) {
    if (!key) return null;
    try {
      const ls = window.localStorage;
      if (ls) {
        const val = ls.getItem(key);
        if (val !== null && val !== undefined) {
          memoryStorage.set(key, val);
          return val;
        }
      }
    } catch (_err) {
      storageBlocked = true;
    }
    return memoryStorage.has(key) ? memoryStorage.get(key) : null;
  }

  function safeSetItem(key, value) {
    if (!key) return false;
    const strVal = String(value);
    memoryStorage.set(key, strVal);
    try {
      const ls = window.localStorage;
      if (ls) {
        ls.setItem(key, strVal);
        return true;
      }
    } catch (_err) {
      storageBlocked = true;
    }
    return false;
  }

  function safeParseJson(raw, fallback) {
    if (!raw || typeof raw !== 'string') return fallback;
    try {
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? parsed : fallback;
    } catch (_err) {
      return fallback;
    }
  }

  function loadPrefs() {
    const base = {
      theme: 'dark',
      lastModuleId: null,
      lastModuleQuery: '',
      bannerDismissed: false
    };
    const parsed = safeParseJson(safeGetItem(HUB_PREFS_KEY), null);
    if (!parsed) return base;
    return {
      theme: parsed.theme === 'light' ? 'light' : 'dark',
      lastModuleId: typeof parsed.lastModuleId === 'string' && parsed.lastModuleId ? parsed.lastModuleId : null,
      lastModuleQuery: typeof parsed.lastModuleQuery === 'string' ? parsed.lastModuleQuery : '',
      bannerDismissed: Boolean(parsed.bannerDismissed)
    };
  }

  const state = {
    prefs: loadPrefs(),
    manifest: null,
    manifestSig: '',
    moduleById: new Map(),
    orderedModules: [],
    unitById: new Map(),
    filters: {
      search: '',
      unitId: 'all',
      epa608: false,
      handout: false,
      inprogress: false
    },
    curriculumView: 'chapters',
    vocab: {
      chapterId: 'all',
      sort: 'chapter',
      selfCheck: false,
      revealedKeys: new Set(),
      showAllLimit: 240
    },
    stage: {
      activeId: null,
      moduleQuery: '',
      handoutMode: false,
      primaryUrl: '',
      companionKey: null,
      companionUrl: '',
      readyFrames: new WeakSet()
    },
    isCheckingUpdates: false
  };

  // DOM Cache (populated after DOMContentLoaded)
  const dom = {};

  function cacheDom() {
    dom.hubView = document.getElementById('hub-view');
    dom.stageView = document.getElementById('stage-view');
    dom.hubTitle = document.getElementById('hub-title');
    dom.hubSubtitle = document.getElementById('hub-subtitle');
    dom.syncPill = document.getElementById('sync-timestamp-pill');
    dom.searchInput = document.getElementById('hub-search');
    dom.searchKbd = document.getElementById('search-kbd-hint');
    dom.clearSearchBtn = document.getElementById('btn-clear-search');
    dom.themeBtn = document.getElementById('btn-theme-toggle');
    dom.checkUpdatesBtn = document.getElementById('btn-check-updates');
    dom.fullTabBtn = document.getElementById('btn-full-tab');

    dom.telBolts = document.getElementById('tel-total-bolts');
    dom.telXpSub = document.getElementById('tel-total-xp-sub');
    dom.telRank = document.getElementById('tel-career-rank');
    dom.telRankSub = document.getElementById('tel-rank-sub');
    dom.telActive = document.getElementById('tel-chapters-active');
    dom.telActiveSub = document.getElementById('tel-chapters-sub');
    dom.telEpaPct = document.getElementById('tel-epa608-pct');
    dom.telEpaSub = document.getElementById('tel-epa608-sub');

    dom.continueBanner = document.getElementById('continue-banner');
    dom.continueTitle = document.getElementById('continue-title');
    dom.continueResumeBtn = document.getElementById('btn-continue-resume');
    dom.continueDismissBtn = document.getElementById('btn-continue-dismiss');
    dom.manifestMissing = document.getElementById('manifest-missing-banner');

    dom.featuredSection = document.getElementById('featured-section');
    dom.featuredCountBadge = document.getElementById('featured-count-badge');
    dom.featuredGrid = document.getElementById('featured-grid');

    dom.curriculumSection = document.getElementById('curriculum-section');
    dom.curriculumTotals = document.getElementById('curriculum-totals-line');
    dom.matchStatus = document.getElementById('search-match-status');
    dom.vocabViewSwitch = document.getElementById('vocab-view-switch');
    dom.btnViewChapters = document.getElementById('btn-view-chapters');
    dom.btnViewVocab = document.getElementById('btn-view-vocab');
    dom.unitTabs = document.getElementById('unit-tabs');
    dom.chipEpa = document.getElementById('chip-epa608');
    dom.chipHandout = document.getElementById('chip-handout');
    dom.chipInProgress = document.getElementById('chip-inprogress');
    dom.chaptersGrid = document.getElementById('chapters-grid');
    dom.chaptersEmpty = document.getElementById('chapters-empty');
    dom.resetFiltersBtn = document.getElementById('btn-reset-filters');
    dom.vocabExplorerPanel = document.getElementById('vocab-explorer-panel');
    dom.vocabChapterSelect = document.getElementById('vocab-chapter-select');
    dom.btnVocabSort = document.getElementById('btn-vocab-sort');
    dom.btnVocabSelfCheck = document.getElementById('btn-vocab-selfcheck');
    dom.vocabMatchStatus = document.getElementById('vocab-match-status');
    dom.vocabExplorerList = document.getElementById('vocab-explorer-list');
    dom.vocabEmpty = document.getElementById('vocab-empty');
    dom.btnResetVocabFilters = document.getElementById('btn-reset-vocab-filters');

    dom.backHubBtn = document.getElementById('btn-back-hub');
    dom.prevModuleBtn = document.getElementById('btn-prev-module');
    dom.stageSelect = document.getElementById('stage-module-select');
    dom.nextModuleBtn = document.getElementById('btn-next-module');
    dom.stageContext = document.getElementById('stage-context-controls');
    dom.stageVersionBadge = document.getElementById('stage-version-badge');
    dom.stageThemeBtn = document.getElementById('btn-stage-theme');
    dom.focusModeBtn = document.getElementById('btn-focus-mode');
    dom.openNewTabLink = document.getElementById('btn-open-new-tab');
    dom.primaryPane = document.getElementById('primary-pane');
    dom.primaryFrame = document.getElementById('primary-frame');
    dom.companionPane = document.getElementById('companion-pane');
    dom.companionTitle = document.getElementById('companion-title');
    dom.companionNewTabLink = document.getElementById('btn-companion-new-tab');
    dom.closeCompanionBtn = document.getElementById('btn-close-companion');
    dom.companionFrame = document.getElementById('companion-frame');
    dom.exitFocusBtn = document.getElementById('btn-exit-focus');
    dom.toastContainer = document.getElementById('toast-container');
  }

  function savePrefs(patch) {
    state.prefs = Object.assign({}, state.prefs, patch || {});
    safeSetItem(HUB_PREFS_KEY, JSON.stringify(state.prefs));
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function showToast(message, tone) {
    if (!dom.toastContainer) return;
    const el = document.createElement('div');
    el.className = 'toast toast-' + (tone || 'info');
    el.textContent = String(message);
    dom.toastContainer.appendChild(el);
    window.setTimeout(function () {
      el.remove();
    }, 3400);
  }

  function formatTimestamp(isoStr) {
    if (!isoStr) return 'Not synced';
    const d = new Date(isoStr);
    if (Number.isNaN(d.getTime())) return String(isoStr);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  }

  // =========================================================================
  // THEME MANAGEMENT
  // =========================================================================

  function applyTheme(theme) {
    const isLight = theme === 'light';
    document.documentElement.classList.toggle('theme-light', isLight);
    if (dom.themeBtn) {
      dom.themeBtn.textContent = isLight ? '🌙 Dark' : '☀️ Light';
      dom.themeBtn.setAttribute('aria-pressed', String(isLight));
    }
    if (dom.stageThemeBtn) {
      dom.stageThemeBtn.textContent = isLight ? '🌙' : '☀️';
      dom.stageThemeBtn.title = isLight
        ? 'Switch to Dark Lab mode'
        : 'Switch to Light Classroom Projector mode';
    }
    notifyFrameTheme(dom.primaryFrame, theme);
    notifyFrameTheme(dom.companionFrame, theme);
  }

  function toggleTheme() {
    const next = state.prefs.theme === 'light' ? 'dark' : 'light';
    savePrefs({ theme: next });
    applyTheme(next);
    if (state.stage.activeId) {
      const entry = state.moduleById.get(state.stage.activeId);
      if (entry) {
        const targetPath = state.stage.handoutMode && entry.handout
          ? entry.handout.path
          : entry.path;
        const targetVer = state.stage.handoutMode && entry.handout
          ? entry.handout.version
          : entry.version;
        const targetQuery = state.stage.handoutMode ? '' : state.stage.moduleQuery;
        const updatedHref = buildModuleUrl(targetPath, targetVer, targetQuery, next);
        if (dom.openNewTabLink) dom.openNewTabLink.href = updatedHref;
      }
    }
  }

  function notifyFrameTheme(iframe, theme) {
    if (!iframe || !iframe.contentWindow) return;
    try {
      iframe.contentWindow.postMessage(
        { type: 'ish-theme', source: 'integrated-study-helper', theme: theme },
        '*'
      );
    } catch (_err) {
      // Ignore cross-origin or uninitialized frame errors.
    }
  }

  // =========================================================================
  // PROGRESS & TELEMETRY
  // =========================================================================

  function readModuleProgress(storageKey) {
    if (!storageKey) {
      return { bolts: 0, totalXp: 0, masteredIds: [], masteredVocabIds: [] };
    }
    const parsed = safeParseJson(safeGetItem(storageKey), null);
    if (!parsed) {
      return { bolts: 0, totalXp: 0, masteredIds: [], masteredVocabIds: [] };
    }
    const bolts = Math.max(0, Number(parsed.bolts) || 0);
    const totalXp = Math.max(bolts, Number(parsed.totalXp) || 0);
    const masteredIds = Array.isArray(parsed.masteredIds) ? parsed.masteredIds : [];
    const masteredVocabIds = Array.isArray(parsed.masteredVocabIds) ? parsed.masteredVocabIds : [];
    return {
      bolts: bolts,
      totalXp: totalXp,
      masteredIds: masteredIds,
      masteredVocabIds: masteredVocabIds
    };
  }

  function resolveCareerRank(totalXp) {
    for (let i = 0; i < CAREER_RANKS.length; i++) {
      if (totalXp >= CAREER_RANKS[i].min) {
        const current = CAREER_RANKS[i];
        const next = i > 0 ? CAREER_RANKS[i - 1] : null;
        return { current: current, next: next };
      }
    }
    return { current: CAREER_RANKS[CAREER_RANKS.length - 1], next: CAREER_RANKS[CAREER_RANKS.length - 2] };
  }

  function getEpa608Entry() {
    if (!state.manifest) return null;
    return state.manifest.featured_labs.find(function (lab) {
      return lab.id === 'epa608';
    }) || null;
  }

  function computeEpa608Stats(epaEntry) {
    const keys = epaEntry && Array.isArray(epaEntry.storage_keys) && epaEntry.storage_keys.length
      ? epaEntry.storage_keys
      : DEFAULT_EPA608_KEYS;
    const cardTotals = (epaEntry && epaEntry.card_totals) || {};
    const editions = keys.map(function (key) {
      const prog = readModuleProgress(key);
      const total = Math.max(0, Number(cardTotals[key]) || 0);
      const mastered = prog.masteredIds.length;
      const pct = total > 0 ? Math.min(100, Math.round((mastered / total) * 100)) : 0;
      const shortLabel = key.indexOf('v10') !== -1 ? 'ESCO v10' : (key.indexOf('v9') !== -1 ? 'ESCO v9' : key);
      return {
        key: key,
        label: shortLabel,
        mastered: mastered,
        total: total,
        pct: pct,
        bolts: prog.bolts
      };
    });

    const maxPct = editions.length
      ? Math.max.apply(null, editions.map(function (e) { return e.pct; }))
      : 0;

    return { editions: editions, readinessPct: maxPct };
  }

  function computeTelemetry() {
    const manifest = state.manifest;
    const chapters = manifest ? manifest.chapters : [];
    const epaEntry = getEpa608Entry();
    const seenKeys = new Set();

    let totalBolts = 0;
    let totalXp = 0;
    let chaptersActive = 0;

    chapters.forEach(function (ch) {
      const key = ch.storage_key;
      const prog = readModuleProgress(key);
      if (prog.bolts > 0 || prog.masteredIds.length > 0 || prog.masteredVocabIds.length > 0 || prog.totalXp > 0) {
        chaptersActive += 1;
      }
      if (key && !seenKeys.has(key)) {
        seenKeys.add(key);
        totalBolts += prog.bolts;
        totalXp += prog.totalXp;
      }
    });

    const epaKeys = epaEntry && Array.isArray(epaEntry.storage_keys) && epaEntry.storage_keys.length
      ? epaEntry.storage_keys
      : DEFAULT_EPA608_KEYS;

    epaKeys.forEach(function (key) {
      if (key && !seenKeys.has(key)) {
        seenKeys.add(key);
        const prog = readModuleProgress(key);
        totalBolts += prog.bolts;
        totalXp += prog.totalXp;
      }
    });

    const rankInfo = resolveCareerRank(totalXp);
    const epaStats = computeEpa608Stats(epaEntry);

    return {
      totalBolts: totalBolts,
      totalXp: totalXp,
      rankInfo: rankInfo,
      chaptersActive: chaptersActive,
      chapterCount: chapters.length || 52,
      epaStats: epaStats
    };
  }

  function renderTelemetry() {
    if (!dom.telBolts) return;
    const tel = computeTelemetry();

    dom.telBolts.textContent = tel.totalBolts.toLocaleString();
    dom.telXpSub.textContent = tel.totalXp.toLocaleString() + ' Lifetime XP' + (storageBlocked ? ' (session)' : '');

    dom.telRank.textContent = tel.rankInfo.current.icon + ' ' + tel.rankInfo.current.name;
    if (tel.rankInfo.next) {
      const remaining = Math.max(0, tel.rankInfo.next.min - tel.totalXp);
      dom.telRankSub.textContent = 'Next: ' + tel.rankInfo.next.name + ' (' + remaining.toLocaleString() + ' XP)';
    } else {
      dom.telRankSub.textContent = 'Top HVAC/R career rank achieved!';
    }

    dom.telActive.textContent = tel.chaptersActive + ' / ' + tel.chapterCount;
    dom.telActiveSub.textContent = tel.chaptersActive > 0
      ? Math.round((tel.chaptersActive / Math.max(1, tel.chapterCount)) * 100) + '% of curriculum engaged'
      : 'Open any chapter to start tracking';

    dom.telEpaPct.textContent = tel.epaStats.readinessPct + '%';
    const edSummary = tel.epaStats.editions
      .map(function (ed) { return ed.label + ': ' + ed.pct + '%'; })
      .join(' • ');
    dom.telEpaSub.textContent = edSummary || 'ESCO v10 & v9 certification prep';
  }

  // =========================================================================
  // MANIFEST NORMALIZATION & SYNC
  // =========================================================================

  function normalizeManifest(raw) {
    if (!raw || typeof raw !== 'object') return null;
    const featuredLabs = Array.isArray(raw.featured_labs) ? raw.featured_labs.slice() : [];
    const chapters = Array.isArray(raw.chapters)
      ? raw.chapters.slice().sort(function (a, b) {
          return (Number(a.chapter_num) || 0) - (Number(b.chapter_num) || 0);
        })
      : [];
    const units = Array.isArray(raw.units) ? raw.units.slice() : [];
    return {
      hub_title: raw.hub_title || 'MRAC 2025 & HVAC/R Integrated Study Helper',
      hub_subtitle: raw.hub_subtitle || '52 Chapter Study Guides, EPA Section 608 Prep, & Interactive HVAC Simulators',
      generated_at_utc: raw.generated_at_utc || '',
      totals: raw.totals || {},
      units: units,
      featured_labs: featuredLabs,
      chapters: chapters
    };
  }

  function computeManifestSignature(m) {
    if (!m) return '';
    const parts = [m.generated_at_utc || ''];
    m.featured_labs.forEach(function (lab) {
      parts.push(String(lab.id) + ':' + String(lab.version || ''));
    });
    m.chapters.forEach(function (ch) {
      const hv = ch.handout && ch.handout.version ? ch.handout.version : '';
      parts.push(String(ch.id) + ':' + String(ch.version || '') + ':' + String(hv));
    });
    return parts.join('|');
  }

  function applyManifest(rawManifest) {
    const normalized = normalizeManifest(rawManifest);
    if (!normalized) return false;
    const nextSig = computeManifestSignature(normalized);
    if (nextSig && nextSig === state.manifestSig && state.manifest) {
      return false;
    }

    state.manifest = normalized;
    state.manifestSig = nextSig;
    state.moduleById = new Map();
    state.unitById = new Map();
    state.orderedModules = [];

    normalized.units.forEach(function (u) {
      state.unitById.set(u.id, u);
    });

    normalized.featured_labs.forEach(function (lab) {
      const entry = Object.assign({ isLab: true }, lab);
      state.moduleById.set(String(lab.id).toLowerCase(), entry);
      state.orderedModules.push(entry);
    });

    normalized.chapters.forEach(function (ch) {
      const entry = Object.assign({ isLab: false }, ch);
      state.moduleById.set(String(ch.id).toLowerCase(), entry);
      state.orderedModules.push(entry);
    });

    return true;
  }

  async function fetchLiveManifest() {
    const url = './manifest.json?t=' + Date.now();
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    return response.json();
  }

  function reloadCatalogScriptFallback() {
    return new Promise(function (resolve, reject) {
      const script = document.createElement('script');
      script.src = './js/catalog_manifest.js?t=' + Date.now();
      script.async = true;
      script.onload = function () {
        script.remove();
        resolve(window.INTEGRATED_STUDY_MANIFEST || null);
      };
      script.onerror = function () {
        script.remove();
        reject(new Error('Failed to load catalog_manifest.js'));
      };
      document.head.appendChild(script);
    });
  }

  async function checkUpdates(manualTrigger) {
    if (state.isCheckingUpdates) return;
    state.isCheckingUpdates = true;
    if (manualTrigger && dom.checkUpdatesBtn) {
      dom.checkUpdatesBtn.disabled = true;
      dom.checkUpdatesBtn.textContent = '↻ Checking…';
    }

    try {
      let candidate = null;
      try {
        candidate = await fetchLiveManifest();
      } catch (fetchErr) {
        // Ignore fetch errors on file:// unless user explicitly requested update check.
        if (window.location.protocol === 'file:') {
          if (manualTrigger) {
            try {
              candidate = await reloadCatalogScriptFallback();
            } catch (_scriptErr) {
              candidate = null;
            }
          }
        } else if (manualTrigger) {
          throw fetchErr;
        }
      }

      if (candidate) {
        const changed = applyManifest(candidate);
        if (changed) {
          onManifestUpdated();
          if (manualTrigger) {
            showToast('Catalog updated to latest build!', 'success');
          }
        } else if (manualTrigger) {
          showToast('Catalog is already up to date.', 'info');
        }
      } else if (manualTrigger) {
        showToast('Offline file:// mode — reload page after running sync_and_publish.py.', 'info');
      }
    } catch (_err) {
      if (manualTrigger) {
        showToast('Could not fetch manifest.json right now.', 'warn');
      }
    } finally {
      state.isCheckingUpdates = false;
      if (dom.checkUpdatesBtn) {
        dom.checkUpdatesBtn.disabled = false;
        dom.checkUpdatesBtn.textContent = '↻ Check Updates';
      }
    }
  }

  function onManifestUpdated() {
    renderHubHeaderMeta();
    renderVocabChapterSelect();
    renderStageModuleSelect();
    if (state.stage.activeId) {
      const activeEntry = state.moduleById.get(state.stage.activeId);
      if (activeEntry) {
        const nextTargetPath = state.stage.handoutMode && activeEntry.handout
          ? activeEntry.handout.path
          : activeEntry.path;
        const nextTargetVer = state.stage.handoutMode && activeEntry.handout
          ? activeEntry.handout.version
          : activeEntry.version;
        const nextTargetQuery = state.stage.handoutMode ? '' : state.stage.moduleQuery;
        const nextUrl = buildModuleUrl(nextTargetPath, nextTargetVer, nextTargetQuery, state.prefs.theme);
        if (nextUrl !== state.stage.primaryUrl) {
          openStage(activeEntry, state.stage.handoutMode ? 'handout=1' : state.stage.moduleQuery, true);
        } else {
          updateStageVersionBadge(activeEntry, state.stage.handoutMode);
        }
      } else {
        handleRoute();
      }
    } else {
      handleRoute();
    }
    renderHubContent();
  }

  // =========================================================================
  // URL & CACHE-BUSTING HELPERS
  // =========================================================================

  function buildModuleUrl(pathStr, version, rawQuery, theme) {
    const rawPath = String(pathStr || '');
    const qIdx = rawPath.indexOf('?');
    const basePath = qIdx === -1 ? rawPath : rawPath.slice(0, qIdx);
    const baseQuery = qIdx === -1 ? '' : rawPath.slice(qIdx + 1);

    const params = new URLSearchParams(baseQuery);
    if (rawQuery) {
      const extra = new URLSearchParams(rawQuery);
      extra.forEach(function (val, key) {
        if (key !== 'handout' && key !== 'companion' && key !== 'cq') {
          params.set(key, val);
        }
      });
    }

    if (theme === 'light' && !params.has('theme')) {
      params.set('theme', 'light');
    }
    if (version) {
      params.set('v', String(version));
    }

    const qs = params.toString();
    return qs ? (basePath + '?' + qs) : basePath;
  }

  function parseHash(hashStr) {
    const cleaned = String(hashStr || '').replace(/^#\/?/, '').trim();
    if (!cleaned) return { id: 'hub', rawQuery: '' };
    const qIdx = cleaned.indexOf('?');
    const rawId = qIdx === -1 ? cleaned : cleaned.slice(0, qIdx);
    const rawQuery = qIdx === -1 ? '' : cleaned.slice(qIdx + 1);
    let id = 'hub';
    try {
      id = decodeURIComponent(rawId).trim().toLowerCase() || 'hub';
    } catch (_err) {
      id = rawId.trim().toLowerCase() || 'hub';
    }
    return { id: id, rawQuery: rawQuery };
  }

  function navigateToModule(id, rawQuery) {
    const q = rawQuery ? ('?' + rawQuery.replace(/^\?/, '')) : '';
    const nextHash = '#' + encodeURIComponent(id) + q;
    if (window.location.hash === nextHash) {
      handleRoute();
    } else {
      window.location.hash = nextHash;
    }
  }

  function navigateToHub() {
    if (window.location.hash === '#hub' || !window.location.hash) {
      handleRoute();
    } else {
      window.location.hash = '#hub';
    }
  }

  // =========================================================================
  // SEARCH & FILTER MATCHING
  // =========================================================================

  function getSearchableText(entry) {
    const parts = [
      entry.id || '',
      entry.chapter_code || '',
      entry.title || '',
      entry.subtitle || '',
      entry.badge || '',
      entry.engine_label || ''
    ];
    if (Array.isArray(entry.highlights)) {
      parts.push(entry.highlights.join(' '));
    }
    if (Array.isArray(entry.keywords)) {
      parts.push(entry.keywords.join(' '));
    }
    if (Array.isArray(entry.sections)) {
      entry.sections.forEach(function (sec) {
        parts.push((sec.id || '') + ' ' + (sec.title || ''));
      });
    }
    if (Array.isArray(entry.companions)) {
      entry.companions.forEach(function (comp) {
        parts.push(comp.label || '');
      });
    }
    if (Number(entry.epa_608_count) > 0) {
      parts.push('epa 608 epa608');
    }
    return parts.join(' ').toLowerCase();
  }

  function matchesEntrySearch(entry, rawQuery) {
    const q = String(rawQuery || '').trim().toLowerCase();
    if (!q) return { match: true, exactCh: false };

    // Handle explicit chapter patterns like "11", "ch11", "ch 11", "chapter 11"
    const chPrefixMatch = q.match(/^(ch(?:apter)?\s*)?0*(\d{1,2})$/i);
    if (chPrefixMatch && !entry.isLab) {
      const hasPrefix = Boolean(chPrefixMatch[1]);
      const targetNum = Number(chPrefixMatch[2]);
      if (entry.chapter_num === targetNum) {
        return { match: true, exactCh: true };
      }
      if (!hasPrefix && String(entry.chapter_num).indexOf(String(targetNum)) !== -1) {
        return { match: true, exactCh: false };
      }
      if (hasPrefix) {
        // Explicit "ch11" only matches Ch 11 unless keywords explicitly contain it.
        const corpus = getSearchableText(entry);
        return { match: corpus.indexOf(q) !== -1, exactCh: false };
      }
    }

    const terms = q.split(/\s+/).filter(Boolean);
    const corpus = getSearchableText(entry);
    const allHit = terms.every(function (term) {
      return corpus.indexOf(term) !== -1;
    });
    return { match: allHit, exactCh: false };
  }

  // =========================================================================
  // HUB RENDERING
  // =========================================================================

  function renderHubHeaderMeta() {
    const m = state.manifest;
    if (!m) {
      if (dom.manifestMissing) dom.manifestMissing.classList.remove('hidden');
      if (dom.featuredSection) dom.featuredSection.classList.add('hidden');
      if (dom.curriculumSection) dom.curriculumSection.classList.add('hidden');
      return;
    }

    if (dom.manifestMissing) dom.manifestMissing.classList.add('hidden');
    if (dom.featuredSection) dom.featuredSection.classList.remove('hidden');
    if (dom.curriculumSection) dom.curriculumSection.classList.remove('hidden');

    if (dom.hubTitle) dom.hubTitle.textContent = m.hub_title;
    if (dom.hubSubtitle) dom.hubSubtitle.textContent = m.hub_subtitle;
    document.title = m.hub_title;

    if (dom.syncPill) {
      dom.syncPill.textContent = m.generated_at_utc
        ? ('Synced ' + formatTimestamp(m.generated_at_utc))
        : 'Local Catalog';
      dom.syncPill.title = m.generated_at_utc
        ? ('Manifest generated UTC: ' + m.generated_at_utc)
        : 'Manifest loaded';
    }

    if (dom.curriculumTotals) {
      const t = m.totals || {};
      const totalVocabTerms = Number(t.total_vocab_terms) || m.chapters.reduce(function (acc, c) {
        return acc + (Number(c.vocab_count) || (Array.isArray(c.vocabulary) ? c.vocabulary.length : 0));
      }, 0);
      const parts = [];
      if (t.chapter_count || m.chapters.length) {
        parts.push((t.chapter_count || m.chapters.length) + ' Chapters');
      }
      if (t.total_exam_questions) {
        parts.push(Number(t.total_exam_questions).toLocaleString() + ' Exam Questions');
      }
      if (t.total_study_items) {
        parts.push(Number(t.total_study_items).toLocaleString() + ' Study Cards');
      }
      if (totalVocabTerms > 0) {
        parts.push(totalVocabTerms.toLocaleString() + ' Key Vocabulary Terms');
      }
      if (t.handout_count) {
        parts.push(Number(t.handout_count) + ' Printable Handouts');
      }
      if (t.total_epa608_tagged) {
        parts.push(Number(t.total_epa608_tagged) + ' EPA 608 Tagged');
      }
      dom.curriculumTotals.textContent = parts.length
        ? parts.join(' • ')
        : 'Organized by curriculum unit with live study mastery tracking';

      if (dom.btnViewChapters) {
        dom.btnViewChapters.textContent = '📚 Chapter Guides (' + (t.chapter_count || m.chapters.length || 52) + ')';
      }
      if (dom.btnViewVocab) {
        dom.btnViewVocab.textContent = totalVocabTerms > 0
          ? ('📖 Vocabulary (' + totalVocabTerms.toLocaleString() + ' Terms)')
          : '📖 Vocabulary (Ch 1–52)';
      }
    }
  }

  function renderContinueBanner() {
    if (!dom.continueBanner || !state.manifest) return;
    const lastId = state.prefs.lastModuleId;
    const entry = lastId ? state.moduleById.get(String(lastId).toLowerCase()) : null;
    if (!entry || state.prefs.bannerDismissed) {
      dom.continueBanner.classList.add('hidden');
      return;
    }
    const label = entry.isLab
      ? entry.title
      : (entry.chapter_code + ' — ' + entry.title);
    dom.continueTitle.textContent = label;
    dom.continueBanner.classList.remove('hidden');
  }

  function getLabCtaLabel(lab) {
    if (lab.id === 'epa608') return 'Launch EPA 608 Hub →';
    if (lab.id === 'electrical-board') return 'Launch Electrical Board →';
    if (lab.id === 'electrical-simulator') return 'Launch Electrical Trainer →';
    if (lab.id === 'refrigerant-cycle') return 'Launch Cycle Lab →';
    return 'Launch Lab →';
  }

  function getAccentBtnClass(accent) {
    if (accent === 'amber') return 'tone-amber';
    if (accent === 'emerald') return 'tone-emerald';
    return '';
  }

  function renderFeaturedLabs() {
    if (!dom.featuredGrid || !state.manifest) return;
    const query = state.filters.search;
    const labs = state.manifest.featured_labs.filter(function (lab) {
      return matchesEntrySearch(Object.assign({ isLab: true }, lab), query).match;
    });

    if (dom.featuredCountBadge) {
      dom.featuredCountBadge.textContent = labs.length + (labs.length === 1 ? ' Lab' : ' Labs');
    }

    if (labs.length === 0) {
      dom.featuredGrid.innerHTML = '';
      if (dom.featuredSection) dom.featuredSection.classList.add('hidden');
      return;
    }
    if (dom.featuredSection) dom.featuredSection.classList.remove('hidden');

    const epaStats = computeEpa608Stats(getEpa608Entry());

    dom.featuredGrid.innerHTML = labs.map(function (lab) {
      const accent = lab.accent === 'amber' || lab.accent === 'emerald' ? lab.accent : 'cyan';
      const highlights = Array.isArray(lab.highlights) ? lab.highlights : [];
      const presets = Array.isArray(lab.quick_presets) ? lab.quick_presets : [];

      let epaBlock = '';
      if (lab.id === 'epa608' && epaStats.editions.length) {
        epaBlock = '<div class="epa-progress-list">' + epaStats.editions.map(function (ed) {
          return (
            '<div class="epa-ed-row">' +
              '<div class="epa-ed-meta">' +
                '<span class="epa-ed-label">' + escapeHtml(ed.label) + '</span>' +
                '<span class="epa-ed-stats">' + ed.mastered + ' / ' + ed.total + ' (' + ed.pct + '%) • ⚡ ' + ed.bolts.toLocaleString() + '</span>' +
              '</div>' +
              '<div class="progress-track"><div class="progress-fill amber" style="width:' + ed.pct + '%"></div></div>' +
            '</div>'
          );
        }).join('') + '</div>';
      }

      const presetsBlock = presets.length
        ? '<div class="preset-row">' + presets.map(function (p) {
            return '<button type="button" class="preset-btn" data-nav-id="' + escapeHtml(lab.id) + '" data-nav-query="' + escapeHtml(p.query || '') + '">' + escapeHtml(p.label) + '</button>';
          }).join('') + '</div>'
        : '';

      const standaloneLink = lab.standalone_live_url
        ? '<a class="icon-action-btn" href="' + escapeHtml(lab.standalone_live_url) + '" target="_blank" rel="noopener" title="Open standalone live link in new tab" aria-label="Open standalone live link in new tab">↗</a>'
        : '';

      return (
        '<article class="lab-card accent-' + escapeHtml(accent) + '">' +
          '<div class="lab-top">' +
            '<div class="lab-icon-wrap">' +
              '<div class="lab-icon" aria-hidden="true">' + escapeHtml(lab.icon || '⚡') + '</div>' +
              '<div>' +
                '<span class="lab-badge">' + escapeHtml(lab.badge || 'Interactive Lab') + '</span>' +
                '<h3 class="lab-title">' + escapeHtml(lab.title) + '</h3>' +
              '</div>' +
            '</div>' +
          '</div>' +
          '<p class="lab-subtitle">' + escapeHtml(lab.subtitle || '') + '</p>' +
          (highlights.length
            ? '<div class="pill-list">' + highlights.map(function (h) {
                return '<span class="info-pill">' + escapeHtml(h) + '</span>';
              }).join('') + '</div>'
            : '') +
          epaBlock +
          presetsBlock +
          '<div class="lab-footer">' +
            '<button type="button" class="btn-primary ' + getAccentBtnClass(accent) + '" data-nav-id="' + escapeHtml(lab.id) + '">' +
              escapeHtml(getLabCtaLabel(lab)) +
            '</button>' +
            standaloneLink +
          '</div>' +
        '</article>'
      );
    }).join('');
  }

  function renderUnitTabs() {
    if (!dom.unitTabs || !state.manifest) return;
    const totalCount = state.manifest.chapters.length;
    const activeUnit = state.filters.unitId;

    const tabsHtml = [
      '<button type="button" role="tab" class="unit-tab' + (activeUnit === 'all' ? ' active' : '') + '" data-unit="all" aria-selected="' + (activeUnit === 'all') + '">All (' + totalCount + ')</button>'
    ];

    state.manifest.units.forEach(function (unit) {
      const count = Array.isArray(unit.chapters) ? unit.chapters.length : 0;
      const isActive = activeUnit === unit.id;
      const shortLabel = unit.short_label || unit.label || unit.id;
      tabsHtml.push(
        '<button type="button" role="tab" class="unit-tab' + (isActive ? ' active' : '') + '" data-unit="' + escapeHtml(unit.id) + '" title="' + escapeHtml(unit.label || shortLabel) + '" aria-selected="' + isActive + '">' +
          escapeHtml(shortLabel) + ' (' + count + ')' +
        '</button>'
      );
    });

    dom.unitTabs.innerHTML = tabsHtml.join('');
  }

  function formatSectionTag(sec) {
    if (!sec) return '';
    const id = String(sec.id || '').trim();
    const title = String(sec.title || '').trim();
    if (!id) return title;
    if (!title) return id;
    if (title.toLowerCase().indexOf(id.toLowerCase()) === 0) return title;
    return id + ' ' + title;
  }

  function getCompanionIcon(targetId) {
    if (targetId === 'electrical-board') return '⚡';
    if (targetId === 'electrical-simulator') return '🔌';
    if (targetId === 'refrigerant-cycle') return '❄️';
    if (targetId === 'epa608') return '🛡️';
    return '🔬';
  }

  function renderChaptersGrid() {
    if (!dom.chaptersGrid || !state.manifest) return;
    const chapters = state.manifest.chapters;
    const q = state.filters.search;

    const matched = [];
    chapters.forEach(function (ch) {
      if (state.filters.unitId !== 'all' && ch.unit_id !== state.filters.unitId) return;
      if (state.filters.epa608 && !(Number(ch.epa_608_count) > 0)) return;
      if (state.filters.handout && !ch.handout) return;

      const prog = readModuleProgress(ch.storage_key);
      const isInProgress = prog.bolts > 0 || prog.masteredIds.length > 0 || prog.masteredVocabIds.length > 0 || prog.totalXp > 0;
      if (state.filters.inprogress && !isInProgress) return;

      const res = matchesEntrySearch(Object.assign({ isLab: false }, ch), q);
      if (!res.match) return;

      matched.push({ ch: ch, prog: prog, exactCh: res.exactCh });
    });

    if (q.trim()) {
      matched.sort(function (a, b) {
        if (a.exactCh !== b.exactCh) return a.exactCh ? -1 : 1;
        return (Number(a.ch.chapter_num) || 0) - (Number(b.ch.chapter_num) || 0);
      });
    }

    const isVocabView = state.curriculumView === 'vocab';
    if (!isVocabView && dom.matchStatus) {
      dom.matchStatus.textContent = matched.length + ' of ' + chapters.length + ' chapters';
    }

    if (dom.chaptersGrid) dom.chaptersGrid.classList.toggle('hidden', isVocabView);

    if (matched.length === 0) {
      dom.chaptersGrid.innerHTML = '';
      if (dom.chaptersEmpty) dom.chaptersEmpty.classList.toggle('hidden', isVocabView);
      return;
    }

    if (dom.chaptersEmpty) dom.chaptersEmpty.classList.add('hidden');

    dom.chaptersGrid.innerHTML = matched.map(function (item) {
      const ch = item.ch;
      const prog = item.prog;
      const studyTotal = Math.max(0, Number(ch.study_item_count) || 0);
      const masteredCount = prog.masteredIds.length;
      const pct = studyTotal > 0 ? Math.min(100, Math.max(0, Math.round((masteredCount / studyTotal) * 100))) : 0;

      const sections = Array.isArray(ch.sections) ? ch.sections : [];
      const firstTwo = sections.slice(0, 2);
      const extraSections = sections.slice(2);
      const extraTitle = extraSections.map(formatSectionTag).join(' • ');

      const sectionsHtml = firstTwo.map(function (sec) {
        const text = formatSectionTag(sec);
        return '<span class="section-tag" title="' + escapeHtml(text) + '">' + escapeHtml(text) + '</span>';
      }).join('') + (extraSections.length
        ? '<span class="section-tag section-tag-more" title="' + escapeHtml(extraTitle) + '">+' + extraSections.length + ' more</span>'
        : '');

      const companions = Array.isArray(ch.companions) ? ch.companions : [];
      const companionBtns = companions.map(function (comp) {
        const icon = getCompanionIcon(comp.target_id);
        const label = comp.label || comp.target_id;
        return (
          '<button type="button" class="icon-action-btn" data-nav-id="' + escapeHtml(comp.target_id) + '" data-nav-query="' + escapeHtml(comp.query || '') + '" title="Launch Companion: ' + escapeHtml(label) + '" aria-label="Launch Companion: ' + escapeHtml(label) + '">' +
            icon +
          '</button>'
        );
      }).join('');

      const handoutBtn = ch.handout
        ? '<button type="button" class="icon-action-btn" data-nav-id="' + escapeHtml(ch.id) + '" data-nav-query="handout=1" title="Open Printable Handout: ' + escapeHtml(ch.handout.title || 'Student Handout') + '" aria-label="Open Printable Handout">📄</button>'
        : '';

      const chCode = ch.chapter_code || ('Ch ' + ch.chapter_num);
      const vocabQuickBtn = '<button type="button" class="btn-secondary btn-vocab-quick" data-nav-id="' + escapeHtml(ch.id) + '" data-nav-query="subtab=vocab" title="Open ' + escapeHtml(chCode) + ' Key Vocabulary" aria-label="Open ' + escapeHtml(chCode) + ' Key Vocabulary">📖 Vocab</button>';

      return (
        '<article class="chapter-card">' +
          '<div class="chapter-top">' +
            '<div class="chapter-badges-left">' +
              '<span class="ch-code-pill">' + escapeHtml(chCode) + '</span>' +
              '<span class="engine-pill">' + escapeHtml(ch.engine_label || 'Interactive Lab') + '</span>' +
            '</div>' +
            '<div class="chapter-badges-right">' +
              (Number(ch.epa_608_count) > 0
                ? '<span class="tag-608" title="' + Number(ch.epa_608_count) + ' EPA 608-tagged items">🛡️ 608</span>'
                : '') +
              (ch.handout
                ? '<span class="tag-handout" title="' + escapeHtml(ch.handout.title || 'Printable Student Handout') + '">📄 Handout</span>'
                : '') +
            '</div>' +
          '</div>' +
          '<h3 class="chapter-title">' + escapeHtml(ch.title) + '</h3>' +
          (sectionsHtml ? '<div class="chapter-sections">' + sectionsHtml + '</div>' : '') +
          '<div class="chapter-stats">' +
            '<span>' + (Number(ch.exam_question_count) || 0) + ' Exam Qs</span>' +
            '<span>•</span>' +
            '<span>' + studyTotal + ' Study Cards</span>' +
            '<span>•</span>' +
            '<span>' + (Number(ch.vocab_count) || 0) + ' Vocab Terms</span>' +
            '<span>•</span>' +
            '<span>' + (Number(ch.sim_mission_count) || 0) + ' Sim Missions</span>' +
          '</div>' +
          '<div class="chapter-progress">' +
            '<div class="progress-meta">' +
              '<span class="progress-pct">' + masteredCount + ' / ' + studyTotal + ' mastered (' + pct + '%)</span>' +
              '<span class="progress-bolts">⚡ ' + prog.bolts.toLocaleString() + '</span>' +
            '</div>' +
            '<div class="progress-track"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
          '</div>' +
          '<div class="chapter-footer">' +
            '<button type="button" class="btn-primary" data-nav-id="' + escapeHtml(ch.id) + '">Open Study &amp; Game →</button>' +
            vocabQuickBtn +
            companionBtns +
            handoutBtn +
          '</div>' +
        '</article>'
      );
    }).join('');
  }

  function renderVocabChapterSelect() {
    if (!dom.vocabChapterSelect || !state.manifest) return;
    const prevVal = state.vocab.chapterId || 'all';
    const options = ['<option value="all">All Chapters (Ch 01–52)</option>'];
    state.manifest.chapters.forEach(function (ch) {
      const count = Number(ch.vocab_count) || (Array.isArray(ch.vocabulary) ? ch.vocabulary.length : 0);
      const countSuffix = count > 0 ? (' (' + count + ')') : '';
      options.push(
        '<option value="' + escapeHtml(ch.id) + '">' +
          escapeHtml((ch.chapter_code || ('Ch ' + ch.chapter_num)) + ' — ' + ch.title + countSuffix) +
        '</option>'
      );
    });
    dom.vocabChapterSelect.innerHTML = options.join('');
    dom.vocabChapterSelect.value = state.moduleById.has(prevVal) ? prevVal : 'all';
    state.vocab.chapterId = dom.vocabChapterSelect.value || 'all';
  }

  function syncVocabControlButtons() {
    const isAz = state.vocab.sort === 'az';
    if (dom.btnVocabSort) {
      dom.btnVocabSort.textContent = isAz ? '🔤 A–Z Glossary' : '📑 Group by Chapter';
      dom.btnVocabSort.classList.toggle('active', isAz);
      dom.btnVocabSort.setAttribute('aria-pressed', String(isAz));
    }
    const selfCheck = Boolean(state.vocab.selfCheck);
    if (dom.btnVocabSelfCheck) {
      dom.btnVocabSelfCheck.textContent = selfCheck
        ? '👁️ Self-Check: Definitions Hidden'
        : '👁️ Self-Check: Hide Definitions';
      dom.btnVocabSelfCheck.classList.toggle('active', selfCheck);
      dom.btnVocabSelfCheck.setAttribute('aria-pressed', String(selfCheck));
    }
  }

  function setCurriculumView(view) {
    const isVocab = view === 'vocab';
    state.curriculumView = isVocab ? 'vocab' : 'chapters';
    if (dom.btnViewChapters) {
      dom.btnViewChapters.classList.toggle('active', !isVocab);
      dom.btnViewChapters.setAttribute('aria-pressed', String(!isVocab));
    }
    if (dom.btnViewVocab) {
      dom.btnViewVocab.classList.toggle('active', isVocab);
      dom.btnViewVocab.setAttribute('aria-pressed', String(isVocab));
    }
    if (dom.vocabExplorerPanel) {
      dom.vocabExplorerPanel.classList.toggle('hidden', !isVocab);
    }
    if (isVocab) {
      if (dom.chaptersGrid) dom.chaptersGrid.classList.add('hidden');
      if (dom.chaptersEmpty) dom.chaptersEmpty.classList.add('hidden');
      syncVocabControlButtons();
      renderVocabExplorer();
    } else {
      renderChaptersGrid();
    }
  }

  function renderVocabDefSlot(definition, chId, idx, key) {
    if (!state.vocab.selfCheck) {
      return '<p class="vocab-def">' + escapeHtml(definition || 'No definition available.') + '</p>';
    }
    const isRevealed = state.vocab.revealedKeys.has(key);
    if (isRevealed) {
      return (
        '<p class="vocab-def">' + escapeHtml(definition || 'No definition available.') + '</p>' +
        '<button type="button" class="vocab-reveal-btn is-revealed" data-vocab-reveal="' + escapeHtml(key) + '" data-vocab-ch="' + escapeHtml(chId) + '" data-vocab-idx="' + idx + '" aria-expanded="true">Hide Definition</button>'
      );
    }
    return '<button type="button" class="vocab-reveal-btn" data-vocab-reveal="' + escapeHtml(key) + '" data-vocab-ch="' + escapeHtml(chId) + '" data-vocab-idx="' + idx + '" aria-expanded="false">👁️ Click to Reveal Definition</button>';
  }

  function renderVocabTermCard(item, showChapterJump) {
    const ch = item.ch;
    const v = item.v;
    const chCode = ch.chapter_code || ('Ch ' + ch.chapter_num);
    const secId = String(v.section_id || '').trim();
    const secTitle = String(v.section_title || '').trim();
    let secLabel = '';
    if (showChapterJump) {
      secLabel = secId ? (chCode + ' • Sec ' + secId) : chCode;
    } else if (secId && secTitle) {
      secLabel = 'Sec ' + secId + ' — ' + secTitle;
    } else if (secId) {
      secLabel = 'Sec ' + secId;
    } else if (secTitle) {
      secLabel = secTitle;
    }

    const metaPills = [];
    if (secLabel) {
      metaPills.push(
        '<span class="vocab-sec-pill" title="' + escapeHtml(secTitle || secLabel) + '">' + escapeHtml(secLabel) + '</span>'
      );
    }
    if (Number(v.page) > 0) {
      metaPills.push('<span class="vocab-page-pill">p. ' + Number(v.page) + '</span>');
    }
    if (v.is_epa_608) {
      metaPills.push('<span class="tag-608" title="EPA Section 608 tagged vocabulary">🛡️ 608</span>');
    }
    if (item.isMastered) {
      metaPills.push('<span class="vocab-mastered-badge">✅ Mastered</span>');
    }

    const footerHtml = showChapterJump
      ? '<div class="vocab-card-footer">' +
          '<button type="button" class="btn-secondary vocab-jump-btn" data-nav-id="' + escapeHtml(ch.id) + '" data-nav-query="subtab=vocab">Open in ' + escapeHtml(chCode) + ' →</button>' +
        '</div>'
      : '';

    return (
      '<article class="vocab-term-card' + (item.isMastered ? ' is-mastered' : '') + '">' +
        '<div class="vocab-card-head">' +
          '<h4 class="vocab-term-title">' + escapeHtml(v.term) + '</h4>' +
        '</div>' +
        (metaPills.length ? '<div class="vocab-card-meta">' + metaPills.join('') + '</div>' : '') +
        '<div class="vocab-def-slot" data-vocab-slot="' + escapeHtml(item.key) + '">' +
          renderVocabDefSlot(v.definition, ch.id, item.idx, item.key) +
        '</div>' +
        footerHtml +
      '</article>'
    );
  }

  function renderVocabExplorer() {
    if (!dom.vocabExplorerList || !state.manifest) return;
    const chapters = state.manifest.chapters;
    const rawSearch = String(state.filters.search || '').trim().toLowerCase();
    const searchTerms = rawSearch ? rawSearch.split(/\s+/).filter(Boolean) : [];

    let totalVocabAll = 0;
    const matched = [];

    chapters.forEach(function (ch) {
      const vocabList = Array.isArray(ch.vocabulary) ? ch.vocabulary : [];
      totalVocabAll += vocabList.length;

      if (state.vocab.chapterId !== 'all' && ch.id !== state.vocab.chapterId) return;
      if (state.filters.unitId !== 'all' && ch.unit_id !== state.filters.unitId) return;

      const prog = readModuleProgress(ch.storage_key);
      const isInProgress = prog.bolts > 0 || prog.masteredIds.length > 0 || prog.masteredVocabIds.length > 0 || prog.totalXp > 0;
      if (state.filters.inprogress && !isInProgress) return;

      const masteredSet = new Set(prog.masteredVocabIds);
      const chCode = ch.chapter_code || ('Ch ' + ch.chapter_num);
      const chHaystackPrefix = [chCode, ch.title || '', 'ch' + ch.chapter_num].join(' ').toLowerCase();

      vocabList.forEach(function (v, idx) {
        if (!v || !v.term) return;
        if (state.filters.epa608 && !v.is_epa_608) return;

        if (searchTerms.length) {
          const haystack = (
            chHaystackPrefix + ' ' +
            String(v.term || '') + ' ' +
            String(v.definition || '') + ' ' +
            String(v.section_title || '') + ' ' +
            String(v.section_id || '') +
            (v.is_epa_608 ? ' epa 608 epa608' : '')
          ).toLowerCase();
          const allHit = searchTerms.every(function (t) {
            return haystack.indexOf(t) !== -1;
          });
          if (!allHit) return;
        }

        const key = ch.id + ':' + (v.id || ('idx' + idx));
        matched.push({
          ch: ch,
          v: v,
          idx: idx,
          key: key,
          isMastered: Boolean(v.id && masteredSet.has(v.id))
        });
      });
    });

    if (state.vocab.sort === 'az') {
      matched.sort(function (a, b) {
        const cmp = String(a.v.term || '').localeCompare(String(b.v.term || ''), undefined, { sensitivity: 'base' });
        if (cmp !== 0) return cmp;
        const chDiff = (Number(a.ch.chapter_num) || 0) - (Number(b.ch.chapter_num) || 0);
        return chDiff !== 0 ? chDiff : (a.idx - b.idx);
      });
    }

    const visible = matched.slice(0, state.vocab.showAllLimit);
    const statusText = totalVocabAll === 0
      ? '0 vocabulary terms loaded yet'
      : (visible.length < matched.length
        ? (matched.length.toLocaleString() + ' of ' + totalVocabAll.toLocaleString() + ' terms (showing ' + visible.length.toLocaleString() + ')')
        : (matched.length.toLocaleString() + ' of ' + totalVocabAll.toLocaleString() + ' terms'));

    if (dom.vocabMatchStatus) {
      dom.vocabMatchStatus.textContent = statusText;
    }
    if (state.curriculumView === 'vocab' && dom.matchStatus) {
      dom.matchStatus.textContent = matched.length.toLocaleString() + ' of ' + totalVocabAll.toLocaleString() + ' terms';
    }

    if (matched.length === 0) {
      dom.vocabExplorerList.innerHTML = '';
      if (dom.vocabEmpty) dom.vocabEmpty.classList.remove('hidden');
      return;
    }

    if (dom.vocabEmpty) dom.vocabEmpty.classList.add('hidden');

    const htmlChunks = [];
    if (state.vocab.sort === 'az') {
      htmlChunks.push(
        '<div class="vocab-term-grid vocab-az-grid">' +
          visible.map(function (item) {
            return renderVocabTermCard(item, true);
          }).join('') +
        '</div>'
      );
    } else {
      const grouped = [];
      const groupMap = new Map();
      visible.forEach(function (item) {
        let group = groupMap.get(item.ch.id);
        if (!group) {
          group = { ch: item.ch, items: [] };
          groupMap.set(item.ch.id, group);
          grouped.push(group);
        }
        group.items.push(item);
      });

      grouped.forEach(function (group) {
        const ch = group.ch;
        const chCode = ch.chapter_code || ('Ch ' + ch.chapter_num);
        const termCountLabel = group.items.length + (group.items.length === 1 ? ' term' : ' terms');
        htmlChunks.push(
          '<section class="vocab-chapter-group">' +
            '<div class="vocab-chapter-head">' +
              '<div class="vocab-chapter-head-left">' +
                '<span class="ch-code-pill">' + escapeHtml(chCode) + '</span>' +
                '<h3 class="vocab-chapter-title">' + escapeHtml(chCode + ' — ' + ch.title) + '</h3>' +
                '<span class="vocab-chapter-count">' + escapeHtml(termCountLabel) + '</span>' +
              '</div>' +
              '<button type="button" class="btn-secondary" data-nav-id="' + escapeHtml(ch.id) + '" data-nav-query="subtab=vocab">Open ' + escapeHtml(chCode) + ' Vocabulary Tab →</button>' +
            '</div>' +
            '<div class="vocab-term-grid">' +
              group.items.map(function (item) {
                return renderVocabTermCard(item, false);
              }).join('') +
            '</div>' +
          '</section>'
        );
      });
    }

    if (matched.length > visible.length) {
      const remaining = matched.length - visible.length;
      htmlChunks.push(
        '<div class="vocab-load-more">' +
          '<button type="button" id="btn-vocab-show-all" class="btn-primary">Show All Matching Terms (' + remaining.toLocaleString() + ' more)</button>' +
        '</div>'
      );
    }

    dom.vocabExplorerList.innerHTML = htmlChunks.join('');
  }

  function resetAllCurriculumFilters() {
    state.filters.search = '';
    state.filters.unitId = 'all';
    state.filters.epa608 = false;
    state.filters.handout = false;
    state.filters.inprogress = false;
    state.vocab.chapterId = 'all';
    state.vocab.showAllLimit = 240;
    if (dom.searchInput) dom.searchInput.value = '';
    if (dom.vocabChapterSelect) dom.vocabChapterSelect.value = 'all';
    updateSearchClearState();
    [dom.chipEpa, dom.chipHandout, dom.chipInProgress].forEach(function (chip) {
      if (!chip) return;
      chip.classList.remove('active');
      chip.setAttribute('aria-pressed', 'false');
    });
    renderFeaturedLabs();
    renderUnitTabs();
    renderChaptersGrid();
    renderVocabExplorer();
  }

  function renderHubContent() {
    renderTelemetry();
    renderContinueBanner();
    renderFeaturedLabs();
    renderUnitTabs();
    syncVocabControlButtons();
    renderChaptersGrid();
    renderVocabExplorer();
    if (dom.vocabExplorerPanel) {
      dom.vocabExplorerPanel.classList.toggle('hidden', state.curriculumView !== 'vocab');
    }
  }

  // =========================================================================
  // STAGE VIEW & SPLIT COMPANION
  // =========================================================================

  function renderStageModuleSelect() {
    if (!dom.stageSelect || !state.manifest) return;
    const m = state.manifest;
    const groups = [];

    if (m.featured_labs.length) {
      groups.push(
        '<optgroup label="Certification &amp; Interactive Labs">' +
          m.featured_labs.map(function (lab) {
            return '<option value="' + escapeHtml(lab.id) + '">' + escapeHtml((lab.icon ? lab.icon + ' ' : '') + lab.title) + '</option>';
          }).join('') +
        '</optgroup>'
      );
    }

    const chapterMap = new Map();
    m.chapters.forEach(function (ch) {
      chapterMap.set(Number(ch.chapter_num), ch);
    });

    const assignedNums = new Set();
    m.units.forEach(function (unit) {
      const unitChapters = (unit.chapters || [])
        .map(function (num) { return chapterMap.get(Number(num)); })
        .filter(Boolean);
      unitChapters.forEach(function (ch) { assignedNums.add(Number(ch.chapter_num)); });
      if (unitChapters.length) {
        groups.push(
          '<optgroup label="' + escapeHtml(unit.label || unit.short_label || unit.id) + '">' +
            unitChapters.map(function (ch) {
              return '<option value="' + escapeHtml(ch.id) + '">' + escapeHtml(ch.chapter_code + ' — ' + ch.title) + '</option>';
            }).join('') +
          '</optgroup>'
        );
      }
    });

    const unassigned = m.chapters.filter(function (ch) {
      return !assignedNums.has(Number(ch.chapter_num));
    });
    if (unassigned.length) {
      groups.push(
        '<optgroup label="Additional Chapters">' +
          unassigned.map(function (ch) {
            return '<option value="' + escapeHtml(ch.id) + '">' + escapeHtml(ch.chapter_code + ' — ' + ch.title) + '</option>';
          }).join('') +
        '</optgroup>'
      );
    }

    dom.stageSelect.innerHTML = groups.join('');
    if (state.stage.activeId) {
      dom.stageSelect.value = state.stage.activeId;
    }
  }

  function updateStageVersionBadge(entry, handoutMode) {
    if (!dom.stageVersionBadge || !entry) return;
    const rawVer = (handoutMode && entry.handout && entry.handout.version)
      ? entry.handout.version
      : (entry.version || 'dev');
    const shortVer = String(rawVer).slice(0, 6);
    dom.stageVersionBadge.textContent = 'v' + shortVer;
    dom.stageVersionBadge.title = 'Updated ' + formatTimestamp(entry.updated_at_utc);
  }

  function setFocusMode(enabled) {
    document.body.classList.toggle('focus-mode', Boolean(enabled));
  }

  function closeCompanionPane() {
    state.stage.companionKey = null;
    state.stage.companionUrl = '';
    document.body.classList.remove('companion-open');
    if (dom.companionPane) dom.companionPane.classList.add('hidden');
    if (dom.companionFrame) dom.companionFrame.src = 'about:blank';
    if (dom.companionTitle) dom.companionTitle.textContent = '';
    syncContextButtonStates();
  }

  function openCompanionPane(comp) {
    if (!comp || !comp.target_id) return;
    const targetEntry = state.moduleById.get(String(comp.target_id).toLowerCase());
    if (!targetEntry) {
      showToast('Companion module "' + comp.target_id + '" is not in the catalog yet.', 'warn');
      return;
    }

    const key = comp.target_id + '?' + (comp.query || '');
    if (state.stage.companionKey === key && !dom.companionPane.classList.contains('hidden')) {
      closeCompanionPane();
      return;
    }

    const compUrl = buildModuleUrl(targetEntry.path, targetEntry.version, comp.query || '', state.prefs.theme);
    state.stage.companionKey = key;
    state.stage.companionUrl = compUrl;

    document.body.classList.add('companion-open');
    if (dom.companionPane) dom.companionPane.classList.remove('hidden');
    if (dom.companionTitle) {
      dom.companionTitle.textContent = comp.label || targetEntry.title;
    }
    if (dom.companionNewTabLink) {
      dom.companionNewTabLink.href = compUrl;
    }
    if (dom.companionFrame) {
      dom.companionFrame.src = compUrl;
    }
    syncContextButtonStates();
  }

  function syncContextButtonStates() {
    if (!dom.stageContext) return;
    dom.stageContext.querySelectorAll('[data-companion-key]').forEach(function (btn) {
      const isActive = btn.dataset.companionKey === state.stage.companionKey;
      btn.classList.toggle('is-active', isActive);
      btn.setAttribute('aria-pressed', String(isActive));
    });
    const handoutBtn = document.getElementById('btn-toggle-handout');
    if (handoutBtn) {
      handoutBtn.classList.toggle('is-handout-active', state.stage.handoutMode);
      handoutBtn.setAttribute('aria-pressed', String(state.stage.handoutMode));
    }

    const activeEntry = state.stage.activeId ? state.moduleById.get(state.stage.activeId) : null;
    const isChapter = Boolean(activeEntry && !activeEntry.isLab);
    const activeParams = new URLSearchParams(state.stage.moduleQuery || '');
    const activeSubtab = activeParams.get('subtab') || '';

    dom.stageContext.querySelectorAll('[data-preset-query]').forEach(function (btn) {
      const pq = btn.dataset.presetQuery || '';
      let isMatch = false;
      if (isChapter && (pq === 'subtab=notes' || pq === 'subtab=vocab')) {
        if (!state.stage.handoutMode) {
          if (pq === 'subtab=vocab') {
            isMatch = activeSubtab === 'vocab';
          } else {
            isMatch = activeSubtab === 'notes' || !activeSubtab;
          }
        }
      } else {
        isMatch = pq === state.stage.moduleQuery;
      }
      btn.classList.toggle('is-active', isMatch);
      btn.setAttribute('aria-pressed', String(isMatch));
    });
  }

  function renderStageContextControls(entry) {
    if (!dom.stageContext) return;
    const chunks = [];

    if (!entry.isLab && !state.stage.handoutMode && Number(entry.vocab_count) > 0) {
      chunks.push(
        '<button type="button" class="stage-btn" data-preset-query="subtab=notes" aria-pressed="false" title="Study Guide &amp; Notes">📝 Study Guide</button>'
      );
      chunks.push(
        '<button type="button" class="stage-btn" data-preset-query="subtab=vocab" aria-pressed="false" title="Chapter Key Vocabulary">📖 Vocabulary (' + Number(entry.vocab_count) + ')</button>'
      );
    }

    if (!entry.isLab && Array.isArray(entry.companions) && entry.companions.length) {
      entry.companions.forEach(function (comp, idx) {
        const key = comp.target_id + '?' + (comp.query || '');
        const icon = getCompanionIcon(comp.target_id);
        const label = comp.label || comp.target_id;
        const text = label.indexOf(icon) === 0 ? label : (icon + ' ' + label);
        chunks.push(
          '<button type="button" class="stage-btn" data-companion-idx="' + idx + '" data-companion-key="' + escapeHtml(key) + '" aria-pressed="false" title="Toggle split companion: ' + escapeHtml(label) + '">' +
            escapeHtml(text) +
          '</button>'
        );
      });
    }

    if (!entry.isLab && entry.handout) {
      chunks.push(
        '<button type="button" id="btn-toggle-handout" class="stage-btn" aria-pressed="false" title="Toggle Printable Student Handout">📄 Handout</button>'
      );
      if (state.stage.handoutMode) {
        chunks.push(
          '<button type="button" id="btn-print-handout" class="stage-btn" title="Print Student Handout">🖨️ Print</button>'
        );
      }
    }

    if (entry.isLab && Array.isArray(entry.quick_presets) && entry.quick_presets.length) {
      entry.quick_presets.forEach(function (preset) {
        chunks.push(
          '<button type="button" class="stage-btn" data-preset-query="' + escapeHtml(preset.query || '') + '" aria-pressed="false">' +
            escapeHtml(preset.label) +
          '</button>'
        );
      });
    }

    dom.stageContext.innerHTML = chunks.join('');
    syncContextButtonStates();
  }

  function applyStagePreset(entry, presetQuery) {
    const cleanQuery = String(presetQuery || '').replace(/^\?/, '');
    state.stage.moduleQuery = cleanQuery;

    const paramsObj = {};
    new URLSearchParams(cleanQuery).forEach(function (val, key) {
      paramsObj[key] = val;
    });

    const nextUrl = buildModuleUrl(entry.path, entry.version, cleanQuery, state.prefs.theme);
    if (dom.openNewTabLink) dom.openNewTabLink.href = nextUrl;

    // Preserve browser hash without re-triggering full route reload.
    const nextHash = '#' + encodeURIComponent(entry.id) + (cleanQuery ? '?' + cleanQuery : '');
    try {
      window.history.replaceState(null, '', nextHash);
    } catch (_err) {
      // Ignore history restrictions in constrained frames.
    }
    savePrefs({ lastModuleId: entry.id, lastModuleQuery: cleanQuery, bannerDismissed: false });

    let handledViaPostMessage = false;
    if (dom.primaryFrame && dom.primaryFrame.contentWindow) {
      try {
        dom.primaryFrame.contentWindow.postMessage(
          {
            type: 'ish-preset',
            source: 'integrated-study-helper',
            moduleId: entry.id,
            query: cleanQuery,
            params: paramsObj
          },
          '*'
        );
        if (state.stage.readyFrames.has(dom.primaryFrame.contentWindow)) {
          handledViaPostMessage = true;
        }
      } catch (_err) {
        handledViaPostMessage = false;
      }
    }

    state.stage.primaryUrl = nextUrl;
    if (!handledViaPostMessage && dom.primaryFrame) {
      try {
        if (dom.primaryFrame.contentWindow) {
          state.stage.readyFrames.delete(dom.primaryFrame.contentWindow);
        }
      } catch (_err) {
        // Ignore cross-origin window access error.
      }
      dom.primaryFrame.src = nextUrl;
    }

    syncContextButtonStates();
  }

  function openStage(entry, rawQuery, forceReload) {
    const params = new URLSearchParams(rawQuery || '');
    const handoutMode = params.get('handout') === '1' && Boolean(entry.handout);

    const moduleParams = new URLSearchParams();
    params.forEach(function (val, key) {
      if (key !== 'handout' && key !== 'companion' && key !== 'cq') {
        moduleParams.set(key, val);
      }
    });
    const moduleQuery = moduleParams.toString();

    const switchingModule = state.stage.activeId !== entry.id;
    state.stage.activeId = entry.id;
    state.stage.moduleQuery = moduleQuery;
    state.stage.handoutMode = handoutMode;

    document.documentElement.classList.add('module-active');
    document.body.classList.add('module-active');
    if (dom.hubView) dom.hubView.classList.add('hidden');
    if (dom.stageView) dom.stageView.classList.remove('hidden');

    if (dom.stageSelect) {
      dom.stageSelect.value = entry.id;
    }
    updateStageVersionBadge(entry, handoutMode);

    if (switchingModule) {
      closeCompanionPane();
    }

    const targetPath = handoutMode && entry.handout ? entry.handout.path : entry.path;
    const targetVer = handoutMode && entry.handout ? entry.handout.version : entry.version;
    const nextUrl = buildModuleUrl(targetPath, targetVer, handoutMode ? '' : moduleQuery, state.prefs.theme);

    if (forceReload || state.stage.primaryUrl !== nextUrl) {
      try {
        if (dom.primaryFrame && dom.primaryFrame.contentWindow) {
          state.stage.readyFrames.delete(dom.primaryFrame.contentWindow);
        }
      } catch (_err) {
        // Ignore cross-origin window access error.
      }
      state.stage.primaryUrl = nextUrl;
      if (dom.primaryFrame) dom.primaryFrame.src = nextUrl;
    }

    if (dom.openNewTabLink) dom.openNewTabLink.href = nextUrl;

    savePrefs({
      lastModuleId: entry.id,
      lastModuleQuery: rawQuery || '',
      bannerDismissed: false
    });

    renderStageContextControls(entry);
  }

  function exitStageToHub() {
    setFocusMode(false);
    closeCompanionPane();
    state.stage.activeId = null;
    state.stage.moduleQuery = '';
    state.stage.handoutMode = false;
    state.stage.primaryUrl = '';

    try {
      if (dom.primaryFrame && dom.primaryFrame.contentWindow) {
        state.stage.readyFrames.delete(dom.primaryFrame.contentWindow);
      }
    } catch (_err) {
      // Ignore cross-origin window access error.
    }
    if (dom.primaryFrame) dom.primaryFrame.src = 'about:blank';
    document.documentElement.classList.remove('module-active');
    document.body.classList.remove('module-active');

    if (dom.stageView) dom.stageView.classList.add('hidden');
    if (dom.hubView) dom.hubView.classList.remove('hidden');

    renderHubContent();
  }

  function stepModule(delta) {
    if (!state.orderedModules.length) return;
    const idx = state.orderedModules.findIndex(function (m) {
      return String(m.id).toLowerCase() === state.stage.activeId;
    });
    const nextIdx = idx === -1
      ? 0
      : (idx + delta + state.orderedModules.length) % state.orderedModules.length;
    navigateToModule(state.orderedModules[nextIdx].id, '');
  }

  function handleRoute() {
    const parsed = parseHash(window.location.hash);
    if (!state.manifest || parsed.id === 'hub') {
      exitStageToHub();
      return;
    }
    const entry = state.moduleById.get(parsed.id);
    if (!entry) {
      exitStageToHub();
      return;
    }
    openStage(entry, parsed.rawQuery, false);
  }

  // =========================================================================
  // EVENT BINDING
  // =========================================================================

  function bindEvents() {
    if (dom.searchInput) {
      dom.searchInput.addEventListener('input', function () {
        state.filters.search = dom.searchInput.value || '';
        state.vocab.showAllLimit = 240;
        updateSearchClearState();
        renderFeaturedLabs();
        renderChaptersGrid();
        renderVocabExplorer();
      });

      dom.searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          if (dom.searchInput.value) {
            e.preventDefault();
            clearSearch();
          } else {
            dom.searchInput.blur();
          }
        }
      });
    }

    if (dom.clearSearchBtn) {
      dom.clearSearchBtn.addEventListener('click', function () {
        clearSearch();
        if (dom.searchInput) dom.searchInput.focus();
      });
    }

    if (dom.themeBtn) dom.themeBtn.addEventListener('click', toggleTheme);
    if (dom.stageThemeBtn) dom.stageThemeBtn.addEventListener('click', toggleTheme);

    if (dom.checkUpdatesBtn) {
      dom.checkUpdatesBtn.addEventListener('click', function () {
        checkUpdates(true);
      });
    }

    if (dom.fullTabBtn) {
      dom.fullTabBtn.addEventListener('click', function () {
        window.open(window.location.href, '_blank', 'noopener');
      });
    }

    if (dom.continueResumeBtn) {
      dom.continueResumeBtn.addEventListener('click', function () {
        if (state.prefs.lastModuleId) {
          navigateToModule(state.prefs.lastModuleId, state.prefs.lastModuleQuery || '');
        }
      });
    }

    if (dom.continueDismissBtn) {
      dom.continueDismissBtn.addEventListener('click', function () {
        savePrefs({ bannerDismissed: true });
        renderContinueBanner();
      });
    }

    if (dom.unitTabs) {
      dom.unitTabs.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-unit]');
        if (!btn) return;
        state.filters.unitId = btn.dataset.unit || 'all';
        state.vocab.showAllLimit = 240;
        renderUnitTabs();
        renderChaptersGrid();
        renderVocabExplorer();
      });
    }

    [dom.chipEpa, dom.chipHandout, dom.chipInProgress].forEach(function (chip) {
      if (!chip) return;
      chip.addEventListener('click', function () {
        const key = chip.dataset.filter;
        state.filters[key] = !state.filters[key];
        state.vocab.showAllLimit = 240;
        chip.classList.toggle('active', state.filters[key]);
        chip.setAttribute('aria-pressed', String(state.filters[key]));
        renderChaptersGrid();
        renderVocabExplorer();
      });
    });

    if (dom.resetFiltersBtn) {
      dom.resetFiltersBtn.addEventListener('click', resetAllCurriculumFilters);
    }

    if (dom.btnResetVocabFilters) {
      dom.btnResetVocabFilters.addEventListener('click', resetAllCurriculumFilters);
    }

    if (dom.vocabViewSwitch) {
      dom.vocabViewSwitch.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-curriculum-view]');
        if (!btn) return;
        setCurriculumView(btn.dataset.curriculumView || 'chapters');
      });
    }

    if (dom.vocabChapterSelect) {
      dom.vocabChapterSelect.addEventListener('change', function () {
        state.vocab.chapterId = dom.vocabChapterSelect.value || 'all';
        state.vocab.showAllLimit = 240;
        renderVocabExplorer();
      });
    }

    if (dom.btnVocabSort) {
      dom.btnVocabSort.addEventListener('click', function () {
        state.vocab.sort = state.vocab.sort === 'chapter' ? 'az' : 'chapter';
        state.vocab.showAllLimit = 240;
        syncVocabControlButtons();
        renderVocabExplorer();
      });
    }

    if (dom.btnVocabSelfCheck) {
      dom.btnVocabSelfCheck.addEventListener('click', function () {
        state.vocab.selfCheck = !state.vocab.selfCheck;
        state.vocab.revealedKeys.clear();
        syncVocabControlButtons();
        renderVocabExplorer();
      });
    }

    if (dom.vocabExplorerPanel) {
      dom.vocabExplorerPanel.addEventListener('click', function (e) {
        if (e.target.closest('#btn-vocab-show-all')) {
          state.vocab.showAllLimit = Number.MAX_SAFE_INTEGER;
          renderVocabExplorer();
          return;
        }

        const revealBtn = e.target.closest('[data-vocab-reveal]');
        if (revealBtn) {
          const key = revealBtn.dataset.vocabReveal || '';
          const chId = revealBtn.dataset.vocabCh || '';
          const idx = Number(revealBtn.dataset.vocabIdx);
          if (!key) return;
          if (state.vocab.revealedKeys.has(key)) {
            state.vocab.revealedKeys.delete(key);
          } else {
            state.vocab.revealedKeys.add(key);
          }
          const ch = state.moduleById.get(String(chId).toLowerCase());
          const vocabItem = ch && Array.isArray(ch.vocabulary) ? ch.vocabulary[idx] : null;
          const slot = revealBtn.closest('[data-vocab-slot]');
          if (slot && vocabItem) {
            slot.innerHTML = renderVocabDefSlot(vocabItem.definition, chId, idx, key);
          } else {
            renderVocabExplorer();
          }
        }
      });
    }

    // Delegated card click launcher for both Featured Labs and Chapter Cards
    if (dom.hubView) {
      dom.hubView.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-nav-id]');
        if (!btn) return;
        navigateToModule(btn.dataset.navId, btn.dataset.navQuery || '');
      });
    }

    // Stage Navigation Controls
    if (dom.backHubBtn) {
      dom.backHubBtn.addEventListener('click', navigateToHub);
    }

    if (dom.prevModuleBtn) {
      dom.prevModuleBtn.addEventListener('click', function () {
        stepModule(-1);
      });
    }

    if (dom.nextModuleBtn) {
      dom.nextModuleBtn.addEventListener('click', function () {
        stepModule(1);
      });
    }

    if (dom.stageSelect) {
      dom.stageSelect.addEventListener('change', function () {
        if (dom.stageSelect.value) {
          navigateToModule(dom.stageSelect.value, '');
        }
      });
    }

    if (dom.focusModeBtn) {
      dom.focusModeBtn.addEventListener('click', function () {
        setFocusMode(!document.body.classList.contains('focus-mode'));
      });
    }

    if (dom.exitFocusBtn) {
      dom.exitFocusBtn.addEventListener('click', function () {
        setFocusMode(false);
      });
    }

    if (dom.closeCompanionBtn) {
      dom.closeCompanionBtn.addEventListener('click', closeCompanionPane);
    }

    if (dom.stageContext) {
      dom.stageContext.addEventListener('click', function (e) {
        const entry = state.stage.activeId ? state.moduleById.get(state.stage.activeId) : null;
        if (!entry) return;

        const compBtn = e.target.closest('[data-companion-idx]');
        if (compBtn) {
          const idx = Number(compBtn.dataset.companionIdx);
          const comp = Array.isArray(entry.companions) ? entry.companions[idx] : null;
          if (comp) openCompanionPane(comp);
          return;
        }

        if (e.target.closest('#btn-toggle-handout')) {
          const nextHandout = !state.stage.handoutMode;
          const nextQuery = nextHandout ? 'handout=1' : '';
          navigateToModule(entry.id, nextQuery);
          return;
        }

        if (e.target.closest('#btn-print-handout')) {
          try {
            if (dom.primaryFrame && dom.primaryFrame.contentWindow) {
              dom.primaryFrame.contentWindow.focus();
              dom.primaryFrame.contentWindow.print();
              return;
            }
          } catch (_err) {
            // Fall through to opening handout in new tab if browser blocks print().
          }
          if (dom.openNewTabLink && dom.openNewTabLink.href) {
            window.open(dom.openNewTabLink.href, '_blank', 'noopener');
          }
          return;
        }

        const presetBtn = e.target.closest('[data-preset-query]');
        if (presetBtn) {
          applyStagePreset(entry, presetBtn.dataset.presetQuery || '');
        }
      });
    }

    // Global Keyboard Shortcuts (/ and Ctrl+K for search, Esc to exit focus)
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && document.body.classList.contains('focus-mode')) {
        setFocusMode(false);
        return;
      }

      const isModK = (e.ctrlKey || e.metaKey) && String(e.key).toLowerCase() === 'k';
      const activeTag = document.activeElement ? document.activeElement.tagName : '';
      const typing = activeTag === 'INPUT' || activeTag === 'TEXTAREA' || activeTag === 'SELECT' ||
        (document.activeElement && document.activeElement.isContentEditable);

      if (!state.stage.activeId && (isModK || (e.key === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey))) {
        if (dom.searchInput) {
          e.preventDefault();
          dom.searchInput.focus();
          dom.searchInput.select();
        }
      }
    });

    // Hash routing
    window.addEventListener('hashchange', handleRoute);

    // Live storage & message sync across tabs / embedded iframes
    window.addEventListener('storage', function () {
      if (!state.stage.activeId) {
        renderHubContent();
      }
    });

    window.addEventListener('focus', function () {
      if (!state.stage.activeId) {
        renderTelemetry();
        renderFeaturedLabs();
        renderChaptersGrid();
        renderVocabExplorer();
      }
    });

    document.addEventListener('visibilitychange', function () {
      if (!document.hidden && !state.stage.activeId) {
        renderTelemetry();
        renderFeaturedLabs();
        renderChaptersGrid();
        renderVocabExplorer();
      }
    });

    window.addEventListener('message', function (e) {
      const data = e && e.data;
      if (!data || typeof data !== 'object') return;
      if (data.type === 'ish-ready' || data.type === 'ish-preset-ack') {
        if (e.source) state.stage.readyFrames.add(e.source);
        if (data.type === 'ish-ready' && e.source && state.prefs.theme === 'light') {
          try {
            e.source.postMessage({ type: 'ish-theme', source: 'integrated-study-helper', theme: 'light' }, '*');
          } catch (_err) {
            // Ignore postMessage restriction.
          }
        }
      } else if (data.type === 'hvacProgressUpdated' || data.type === 'ish-progress') {
        if (!state.stage.activeId) {
          renderTelemetry();
          renderFeaturedLabs();
          renderChaptersGrid();
          renderVocabExplorer();
        }
      }
    });
  }

  function updateSearchClearState() {
    const hasVal = Boolean(dom.searchInput && dom.searchInput.value.length > 0);
    if (dom.clearSearchBtn) dom.clearSearchBtn.classList.toggle('hidden', !hasVal);
    if (dom.searchKbd) dom.searchKbd.classList.toggle('hidden', hasVal);
  }

  function clearSearch() {
    state.filters.search = '';
    state.vocab.showAllLimit = 240;
    if (dom.searchInput) dom.searchInput.value = '';
    updateSearchClearState();
    renderFeaturedLabs();
    renderChaptersGrid();
    renderVocabExplorer();
  }

  // =========================================================================
  // BOOTSTRAP
  // =========================================================================

  function init() {
    cacheDom();
    applyTheme(state.prefs.theme);
    bindEvents();
    updateSearchClearState();

    if (window.INTEGRATED_STUDY_MANIFEST && typeof window.INTEGRATED_STUDY_MANIFEST === 'object') {
      applyManifest(window.INTEGRATED_STUDY_MANIFEST);
    }

    renderHubHeaderMeta();
    renderVocabChapterSelect();
    renderStageModuleSelect();
    renderHubContent();
    handleRoute();

    // Asynchronously fetch latest manifest.json without blocking startup.
    checkUpdates(false);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
