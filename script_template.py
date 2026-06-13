#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║       MATRIX AUTO CLAIMER — SINGLE FILE ALL-IN-ONE EDITION      ║
║  Combines: Dashboard Server + API Bridge + Telegram Sniper Bot  ║
╠══════════════════════════════════════════════════════════════════╣
║  INSTALL:  pip install pyrogram tgcrypto                        ║
║  RUN:      python3 matrix_all_in_one.py                         ║
║  OPEN:     http://localhost:8080  in Lemur browser              ║
║  NOTE:     Tampermonkey userscript still needed in browser      ║
╚══════════════════════════════════════════════════════════════════╝
"""

import re
import threading
import json
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pyrogram import Client, filters, idle as pyrogram_idle

# ══════════════════════════════════════════════════════════════════
#  YOUR TELEGRAM CREDENTIALS — CHANGE THESE
# ══════════════════════════════════════════════════════════════════
API_ID   = 0000000
API_HASH = "PLACEHOLDER_HASH"

# ══════════════════════════════════════════════════════════════════
#  INTERNAL STATE
# ══════════════════════════════════════════════════════════════════
latest_payload       = {"code": "", "channel": ""}
code_queue           = []
seen_codes           = set()
internalLock         = False
MEMORY_FILE          = "claimed_codes.txt"

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as _f:
        seen_codes = {line.strip() for line in _f if line.strip()}
    print(f"🧠 Brain loaded {len(seen_codes)} past codes from memory.")

def save_code_to_memory(code):
    with open(MEMORY_FILE, "a") as f:
        f.write(code + "\n")

# ══════════════════════════════════════════════════════════════════
#  EMBEDDED HTML DASHBOARD
# ══════════════════════════════════════════════════════════════════
HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Matrix Auto Claimer Pro</title>
    <style>
        body { background: #121212; color: #fff; font-family: sans-serif; margin: 0; padding: 0; }
        
        .top-bar { display: flex; justify-content: space-between; align-items: center; background: #1e1e1e; padding: 10px 15px; border-bottom: 1px solid #333; font-weight: bold; }
        .hide-panel-btn { background: transparent; color: #aaa; border: none; font-size: 12px; cursor: pointer; }

        #controlPanel { position: sticky; top: 0; z-index: 1000; background: #121212; padding: 8px; border-bottom: 2px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.6); }

        .tabs-container { display: flex; overflow-x: auto; gap: 5px; margin-bottom: 10px; padding-bottom: 2px; align-items: center; }
        .tab-btn { background: #333; color: white; border: 1px solid #555; padding: 12px 10px; border-radius: 5px; font-weight: bold; flex: 1; min-width: 90px; text-align: center; cursor: pointer; text-transform: capitalize; display: flex; justify-content: center; align-items: center; gap: 5px; }
        .tab-btn.active { background: #ff4500; border-color: #ff4500; }
        .btn-green-outline { background: #1b5e20; color: #4caf50; border: 1px solid #4caf50; }
        
        .move-arrow { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; color: #ffcc00; font-size: 12px; user-select: none; }
        .move-arrow:active { background: rgba(0,0,0,0.8); transform: scale(1.1); }
        .delete-tab-btn { background: #d32f2f; color: white; margin-left: 4px; }

        .code-row { display: flex; gap: 5px; margin-bottom: 10px; align-items: stretch; background: #222; padding: 5px; border-radius: 5px;}
        #masterCode { flex-grow: 1; font-size: 16px; padding: 10px; font-weight: bold; background: transparent; color: #fff; border: none; border-left: 2px solid #ffcc00; outline: none; }
        .btn-clear { background: #d32f2f; color: white; border: none; width: 40px; font-weight: bold; border-radius: 5px; cursor: pointer; font-size: 18px;}

        .main-controls { display: flex; gap: 5px; margin-bottom: 10px; }
        .control-btn { background: #333; color: #aaa; border: 1px solid #444; padding: 12px 5px; border-radius: 5px; font-weight: bold; flex: 1; cursor: pointer; font-size: 14px; }
        #autoBtn { color: #00c853; border-color: #00c853; }
        .btn-paste { color: #ffeb3b; border-color: #ffeb3b; font-weight: bold; }
        .btn-fire { background: #d30000; color: white; border: 1px solid #ff0000; flex: 1.5; font-size: 16px; }

        .matrix-curtain-row { display: flex; gap: 5px; margin-bottom: 5px; }
        .curtain-master-btn { border: 1px dashed #555; padding: 10px 5px; font-weight: bold; border-radius: 4px; flex: 1; cursor: pointer; font-size: 13px; color: #fff; }
        .bg-dark-black { background: #000; color: #ff3333; border-color: #ff3333; }
        .bg-light-green { background: #1b5e20; color: #00ff66; border-color: #00ff66; }

        .global-ram-master-row { display: flex; gap: 5px; margin-bottom: 10px; }
        .ram-master-btn { background: #01579b; color: #00b0ff; border: 1px solid #00b0ff; padding: 10px 5px; font-weight: bold; border-radius: 4px; flex: 1; cursor: pointer; font-size: 13px; }
        .ram-master-btn.strip-all { background: #e65100; color: #ffb74d; border-color: #ffb74d; }

        .sub-actions { display: flex; gap: 5px; margin-bottom: 5px; }
        .sub-btn { border: none; padding: 8px 5px; font-weight: bold; border-radius: 4px; color: white; flex: 1; cursor: pointer; font-size: 12px; }
        .bg-blue { background: #2962ff; }
        .bg-cyan { background: #00b8d4; }
        .bg-purple { background: #6200ea; }
        .bg-orange { background: #ff6d00; }

        .manage-row { display: flex; gap: 5px; margin-bottom: 10px; }
        .bg-green-full { background: #00c853; flex: 3; font-weight:bold; }
        .bg-light-blue { background: #40c4ff; flex: 1; color: black; font-weight:bold;}

        #addIdSection { display: none; flex-direction: column; gap: 5px; margin-bottom: 10px; background: #222; padding: 8px; border-radius: 5px; }
        .input-box { padding: 8px; border-radius: 4px; border: none; font-weight: bold; width: 95%; background: #333; color: #fff; margin-bottom: 5px; }
        .add-btn { background: #00c853; color: white; font-weight: bold; border: none; padding: 10px; border-radius: 4px; cursor: pointer; margin-top: 5px; }

        .power-grid-title { font-size: 12px; color: #ffcc00; font-weight: bold; margin-top: 10px; border-top: 1px dashed #444; padding-top: 10px; }
        .power-matrix-box { display: flex; flex-direction: column; gap: 5px; background: #111; padding: 6px; border-radius: 4px; max-height: 120px; overflow-y: auto; }
        .power-matrix-item { display: flex; justify-content: space-between; align-items: center; background: #222; padding: 6px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
        .power-switch-btn { border: none; padding: 4px 10px; font-weight: bold; border-radius: 3px; cursor: pointer; font-size: 11px; color: white; }
        .power-switch-btn.active-on { background: #00c853; box-shadow: 0 0 5px rgba(0,200,83,0.4); }
        .power-switch-btn.active-off { background: #757575; color: #e0e0e0; }

        .router-title { font-size: 12px; color: #00ff66; font-weight: bold; margin-top: 10px; border-top: 1px dashed #444; padding-top: 10px; }
        .router-row { display: flex; gap: 5px; margin-bottom: 5px; align-items: center; }
        .router-select { background: #333; color: #fff; padding: 7px; border-radius: 4px; border: none; font-weight: bold; }
        .router-list { display: flex; flex-direction: column; gap: 4px; background: #111; padding: 5px; border-radius: 4px; max-height: 100px; overflow-y: auto; font-family: monospace; font-size: 11px; }
        .router-item { display: flex; justify-content: space-between; background: #222; padding: 4px 8px; border-radius: 3px; align-items: center; }
        .del-route-btn { color: #ff3333; cursor: pointer; font-weight: bold; font-size: 12px; padding: 0 4px; }

        .grid { display: flex; flex-direction: column; gap: 15px; padding: 10px; padding-bottom: 80px; visibility: hidden; position: absolute; top: -9999px; left: -9999px; width: 100%; box-sizing: border-box; }
        .grid.active-matrix { visibility: visible; position: relative; top: 0; left: 0; display: flex; }
        
        .iframe-container { border: 2px solid #333; border-radius: 5px; background: #111; display: flex; flex-direction: column; overflow: hidden; position: relative; }
        .id-header { display: flex; justify-content: space-between; align-items: center; background: #000; padding: 8px 10px; border-bottom: 1px solid #222;}
        .id-title { color: #ffeb3b; font-weight: bold; font-size: 15px; }
        
        .ui-toggle-btn { background: #4caf50; color: white; border: none; padding: 5px 8px; font-weight: bold; border-radius: 4px; cursor: pointer; margin-right: 3px; font-size: 11px; }
        .ui-toggle-btn.mode-dark { background: #222; color: #888; border: 1px solid #444; }
        
        .ram-toggle-btn { background: #0288d1; color: white; border: none; padding: 5px 8px; font-weight: bold; border-radius: 4px; cursor: pointer; margin-right: 5px; font-size: 11px; }
        .ram-toggle-btn.ram-stripped { background: #e65100; color: #ffcc80; }

        .kill-account-btn { background: #d32f2f; color: white; border: none; padding: 5px 8px; font-weight: bold; border-radius: 4px; cursor: pointer; margin-right: 5px; font-size: 11px; }
        .kill-account-btn.dead-state { background: #4caf50; color: white; }

        .refresh-single { background: #1976d2; color: white; border: none; padding: 5px 10px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 11px; }
        .reload-inplace-btn { background: #e6c300; color: #000; border: none; padding: 5px 10px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 11px; margin-right: 5px; }

        .id-creds { padding: 10px; background: #151515; font-size: 13px; color: #aaa; border-bottom: 1px solid #222;}
        .cred-input { background: transparent; border: none; color: white; font-weight: bold; font-size: 13px; outline: none; width: 60%; }

        .frame-wrapper { display: flex; flex-grow: 1; height: 420px; position: relative; background: #000; }
        .drag-handle { width: 30px; background: #1a1a1a; display: flex; align-items: center; justify-content: center; color: #666; font-size: 11px; font-weight: bold; writing-mode: vertical-rl; text-orientation: upright; border-right: 1px solid #222; touch-action: pan-y; z-index: 10; }
        iframe { flex-grow: 1; border: none; background: #fff; height: 100%; }

        .black-curtain { position: absolute; top: 0; left: 30px; right: 0; bottom: 0; background: #000000; z-index: 5; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #444; font-family: monospace; font-size: 12px; pointer-events: all; border-left: 1px solid #222; transition: all 0.15s ease-in-out; }
        .black-curtain span { color: #00ff66; font-weight: bold; margin-bottom: 5px; font-size: 14px; text-shadow: 0 0 4px rgba(0,255,102,0.3); }
        .black-curtain p { margin: 0; font-size: 11px; color: #666; }
        
        .iframe-container.ui-active .black-curtain { opacity: 0; pointer-events: none; visibility: hidden; }
        .tabs-container::-webkit-scrollbar { display: none; }

        #statusBar { position:fixed; bottom:0; left:0; right:0; background:#0d1a0d; border-top:2px solid #00c853; padding:8px 12px; padding-bottom:calc(8px + env(safe-area-inset-bottom)); font-size:12px; font-family:monospace; color:#555; display:flex; justify-content:space-between; align-items:center; z-index:99999; }
        #statusBar .tg-live { color:#00ff66; font-weight:bold; }
        #statusBar .tg-offline { color:#ff4444; font-weight:bold; }
        #statusBar .code-display { color:#ffcc00; font-weight:bold; max-width:50%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

        #captchaAlert { display:none; position:fixed; top:0; left:0; right:0; background:#ff3300; color:#fff; font-weight:bold; font-size:13px; text-align:center; padding:8px; z-index:99998; cursor:pointer; }
    </style>
</head>
<body>

    <div id="fullScreenBlackout" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:#000; z-index:9999999; flex-direction:column; justify-content:center; align-items:center;">
        <div style="position:absolute; top:20px; right:30px; font-size:30px; cursor:pointer; color:red; font-weight:bold;" onclick="toggleFullScreenBlack()">❌</div>
        <h1 style="color:#00ff66; font-family:monospace; text-shadow: 0 0 10px #00ff66; text-align:center;">⚡ MATRIX CORE ACTIVE ⚡</h1>
        <p style="color:#888; font-family:monospace; text-align:center;">All systems listening and running in background.</p>
        <div class="code-display" id="blackoutCodeDisplay" style="color:#ffcc00; font-size:24px; margin-top:20px; font-family:monospace; text-align:center;">Waiting for drops...</div>
    </div>

    <div class="top-bar">
        <span>☰ &nbsp;&nbsp;Matrix Core Performance Console</span>
        <button class="hide-panel-btn" onclick="togglePanel()">HIDE PANEL △</button>
    </div>

    <div id="controlPanel">
        <button onclick="toggleFullScreenBlack()" style="background:#000; color:#00ff66; border:2px solid #00ff66; width:100%; padding:12px; margin-bottom:10px; font-weight:bold; font-size:14px; border-radius:6px; cursor:pointer; letter-spacing:1px; box-shadow: 0 0 8px rgba(0,255,102,0.3);">⬛ FULL SCREEN BLACKOUT (MAX SPEED)</button>
        <div class="tabs-container" id="tabsBox"></div>

        <div class="code-row">
            <input type="text" id="masterCode" placeholder="Paste Gift Code">
            <button class="btn-clear" onclick="clearCode()">X</button>
        </div>

        <div class="main-controls">
            <button class="control-btn" id="autoBtn" onclick="toggleAuto()" style="color: #00c853; border-color: #00c853;">AUTO: ON</button>
            <button class="control-btn btn-paste" onclick="pasteCode()">PASTE</button>
            <button class="control-btn btn-fire" onclick="fireAll()">Fire 🔥</button>
        </div>

        <div class="matrix-curtain-row">
            <button class="curtain-master-btn bg-dark-black" onclick="setGlobalCurtainState(true)">⚫ BLACK ALL (LAG-FREE)</button>
            <button class="curtain-master-btn bg-light-green" onclick="setGlobalCurtainState(false)">🟢 SHOW ALL UI</button>
        </div>

        <div class="global-ram-master-row">
            <button class="ram-master-btn strip-all" onclick="setGlobalRamFreeState(true)">⚡ RAM-FREE ALL TABS</button>
            <button class="ram-master-btn load-all" onclick="setGlobalRamFreeState(false)">🔓 FULL UI ALL TABS</button>
        </div>

        <div class="sub-actions">
            <button class="sub-btn bg-blue" onclick="broadcastCmd('LOGIN_ALL')">Login All</button>
            <button class="sub-btn bg-cyan" onclick="refreshAllCurrent()">Refresh All</button>
            <button class="sub-btn bg-purple" onclick="goToGiftPage()">Gift Page</button>
            <button class="sub-btn bg-orange" onclick="goToAccountPage()">Account Page</button>
        </div>

        <div class="manage-row">
            <button class="sub-btn bg-green-full" onclick="toggleAddId()">Manage Game URLs & IDs</button>
            <button class="sub-btn bg-light-blue" onclick="window.open('https://web.telegram.org/a/', '_blank')">TG</button>
        </div>

        <div id="addIdSection">
            <label style="font-size: 11px; color: #ffeb3b; font-weight: bold;">1. Main Base URL:</label>
            <input type="text" id="gameBaseUrlInput" class="input-box" placeholder="https://gameclub.com/#/home">
            
            <label style="font-size: 11px; color: #ffeb3b; font-weight: bold;">2. Gift Page Path or Full URL:</label>
            <input type="text" id="gameGiftUrlInput" class="input-box" placeholder="/#/pages/person/gift_code">
            
            <label style="font-size: 11px; color: #ffeb3b; font-weight: bold;">3. Account Page Path or Full URL:</label>
            <input type="text" id="gameAccountUrlInput" class="input-box" placeholder="/#/pages/person/index">
            
            <label style="font-size: 11px; color: #00ff66; font-weight: bold; margin-top: 5px;">4. Add New Account Credentials (Optional):</label>
            <textarea id="bulkCreds" class="input-box" rows="4" placeholder="Format: Phone Password&#10;Leave empty if only updating links" style="background:#111; font-family:monospace; resize:vertical;"></textarea>

            <div class="power-grid-title">🔌 GAME ACTIVATION MATRIX (RAM POWER SAVER)</div>
            <div class="power-matrix-box" id="powerMatrixControlBox"></div>

            <div class="router-title">⭐ TELEGRAM ROUTING INTELLIGENT GRID</div>
            <div class="router-row">
                <input type="text" id="channelRouteInput" style="padding: 7px; background:#333; color:white; border:none; border-radius:4px; font-weight:bold; flex:1;" placeholder="Channel Username (e.g. hackiiiiiiiii)">
                <span style="font-size:11px; font-weight:bold; color:#aaa;">➔ TARGET:</span>
                <select id="targetGameSelector" class="router-select"></select>
                <button type="button" onclick="addChannelRoute()" style="background:#00b8d4; color:white; border:none; padding:7px 12px; font-weight:bold; border-radius:4px;">LINK</button>
            </div>
            <div class="router-list" id="activeRoutesBox"></div>

            <button class="add-btn" onclick="processManagementPanel()">Save Configurations</button>
        </div>
    </div>

    <div id="captchaAlert" onclick="dismissCaptchaAlert()">
        ⚠️ CAPTCHA NEEDED — <span id="captchaAlertText">Account needs captcha solved</span> &nbsp;[tap to dismiss]
    </div>

    <div id="all-grids"></div>

    <div id="statusBar">
        <span>🤖 TG: <span id="tgStatus" class="tg-offline">connecting...</span></span>
        <span class="code-display" id="lastCodeDisplay">No code yet</span>
        <span id="queueCount">Seen: 0</span>
    </div>

    <script>
        // ── KEEP AWAKE KICK (NO WAKELOCK NEEDED) ──
        // Plays a silent, invisible 0-second Base64 audio loop in the background.
        // Android (MIUI) sees "Media Playing" and refuses to sleep the tab or kill the script overnight.
        const audioKick = new Audio("data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA");
        audioKick.loop = true;
        
        function activateWakeKick() {
            audioKick.play().catch(()=>{});
            setInterval(() => { if(audioKick.paused) audioKick.play().catch(()=>{}); }, 10000);
            document.removeEventListener('click', activateWakeKick);
            console.log("⚡ Night-Owl Kick Active: Browser will not sleep.");
        }
        document.addEventListener('click', activateWakeKick); // Needs 1 tap to bypass autoplay policies

        let tabNames = JSON.parse(localStorage.getItem('autoClaimerTabs')) || ['11club', 'Jaiclub'];
        let currentTab = localStorage.getItem('activeAutoClaimerTab') || tabNames[0];
        if (!tabNames.includes(currentTab)) currentTab = tabNames[0];

        let gameData = {};
        let channelRoutes = JSON.parse(localStorage.getItem('matrixChannelRoutes')) || {};
        let tabPowerStates = JSON.parse(localStorage.getItem('matrixTabPowerStates')) || {};
        let lastFiredCode = "";
        let autoEnabled = true; 

        function initData() {
            tabNames.forEach(tab => {
                if (tabPowerStates[tab] === undefined) tabPowerStates[tab] = true;
                let saved = localStorage.getItem('rajaAccounts_' + tab);
                let parsed = JSON.parse(saved) || [];
                if (!localStorage.getItem('gameUrl_' + tab) && parsed.length > 0) {
                    let firstUrl = typeof parsed[0] === 'string' ? parsed[0] : (parsed[0].url || '');
                    if (firstUrl) localStorage.setItem('gameUrl_' + tab, firstUrl);
                }
                gameData[tab] = parsed.map(item => ({ phone: item.phone || '', pass: item.pass || '' }));
                localStorage.setItem('rajaAccounts_' + tab, JSON.stringify(gameData[tab]));
            });
            localStorage.setItem('matrixTabPowerStates', JSON.stringify(tabPowerStates));
        }
        initData();

        function renderTabs() {
            const tabsBox = document.getElementById('tabsBox');
            tabsBox.innerHTML = '';
            tabNames.forEach(tab => {
                const btn = document.createElement('button');
                btn.className = 'tab-btn' + (tab === currentTab ? ' active' : '');
                let prefixMarker = tabPowerStates[tab] ? "" : "🛑 ";

                if (tab === currentTab) {
                    const leftArrow = document.createElement('span'); leftArrow.className = 'move-arrow'; leftArrow.innerText = '◀'; leftArrow.onclick = (e) => { e.stopPropagation(); moveTab(tab, -1); };
                    const rightArrow = document.createElement('span'); rightArrow.className = 'move-arrow'; rightArrow.innerText = '▶'; rightArrow.onclick = (e) => { e.stopPropagation(); moveTab(tab, 1); };
                    const deleteBtn = document.createElement('span'); deleteBtn.className = 'move-arrow delete-tab-btn'; deleteBtn.innerText = '🗑️'; deleteBtn.onclick = (e) => { e.stopPropagation(); promptDelete(tab); };
                    btn.appendChild(leftArrow);
                    btn.appendChild(document.createTextNode(' ' + prefixMarker + tab + ' '));
                    btn.appendChild(rightArrow);
                    btn.appendChild(deleteBtn);
                } else {
                    btn.innerText = prefixMarker + tab;
                }
                btn.onclick = () => switchTab(tab);
                tabsBox.appendChild(btn);
            });

            const addBtn = document.createElement('button');
            addBtn.className = 'tab-btn btn-green-outline'; addBtn.innerText = '+ ADD GAME';
            addBtn.onclick = () => {
                const newTab = prompt("Enter new Game Name:");
                if(newTab && !tabNames.includes(newTab)) {
                    tabNames.push(newTab);
                    tabPowerStates[newTab] = true;
                    localStorage.setItem('autoClaimerTabs', JSON.stringify(tabNames));
                    localStorage.setItem('matrixTabPowerStates', JSON.stringify(tabPowerStates));
                    localStorage.setItem('gameUrl_' + newTab, '');
                    localStorage.setItem('giftUrl_' + newTab, '/#/pages/person/gift_code');
                    localStorage.setItem('accountUrl_' + newTab, '/#/pages/person/index');
                    initData(); renderTabs(); bootAllTabs();
                    toggleAddId();
                }
            };
            tabsBox.appendChild(addBtn);
        }

        function moveTab(tab, direction) {
            const index = tabNames.indexOf(tab);
            if (index === -1) return;
            const newIndex = index + direction;
            if (newIndex < 0 || newIndex >= tabNames.length) return; 
            const temp = tabNames[index];
            tabNames[index] = tabNames[newIndex];
            tabNames[newIndex] = temp;
            localStorage.setItem('autoClaimerTabs', JSON.stringify(tabNames));
            renderTabs();
        }

        function promptDelete(tab) {
            if(confirm(`WARNING: Permanent delete: ${tab}?`)) {
                tabNames = tabNames.filter(t => t !== tab);
                delete tabPowerStates[tab];
                localStorage.setItem('autoClaimerTabs', JSON.stringify(tabNames));
                localStorage.setItem('matrixTabPowerStates', JSON.stringify(tabPowerStates));
                localStorage.removeItem('rajaAccounts_' + tab); 
                localStorage.removeItem('gameUrl_' + tab);
                localStorage.removeItem('giftUrl_' + tab);
                localStorage.removeItem('accountUrl_' + tab);
                if(currentTab === tab) {
                    currentTab = tabNames[0] || null;
                    if (currentTab) localStorage.setItem('activeAutoClaimerTab', currentTab);
                    else localStorage.removeItem('activeAutoClaimerTab');
                }
                if(currentTab) { initData(); renderTabs(); bootAllTabs(); } else { location.reload(); }
            }
        }

        function togglePanel() {
            const panel = document.getElementById('controlPanel');
            const btn = document.querySelector('.hide-panel-btn');
            if(panel.style.display === 'none') { panel.style.display = 'block'; btn.innerText = 'HIDE PANEL △'; } 
            else { panel.style.display = 'none'; btn.innerText = 'SHOW PANEL ▽'; }
        }

        function toggleAddId() {
            const sec = document.getElementById('addIdSection');
            if (sec.style.display === 'flex') {
                sec.style.display = 'none';
            } else {
                sec.style.display = 'flex';
                document.getElementById('gameBaseUrlInput').value = localStorage.getItem('gameUrl_' + currentTab) || '';
                document.getElementById('gameGiftUrlInput').value = localStorage.getItem('giftUrl_' + currentTab) || '';
                document.getElementById('gameAccountUrlInput').value = localStorage.getItem('accountUrl_' + currentTab) || '';
                syncRouterDropdownAndBox();
                buildPowerMatrixConsolePanel();
            }
        }

        function buildPowerMatrixConsolePanel() {
            const container = document.getElementById('powerMatrixControlBox');
            container.innerHTML = '';
            tabNames.forEach(tab => {
                const row = document.createElement('div');
                row.className = 'power-matrix-item';
                let btnStateClass = tabPowerStates[tab] ? "active-on" : "active-off";
                let btnText = tabPowerStates[tab] ? "ACTIVE (LOADED)" : "MUTED (0MB RAM)";
                row.innerHTML = `<span>🎮 ${tab.toUpperCase()}</span>
                                 <button class="power-switch-btn ${btnStateClass}" onclick="toggleGamePowerLine(this, '${tab}')">${btnText}</button>`;
                container.appendChild(row);
            });
        }

        function toggleGamePowerLine(btn, tabName) {
            tabPowerStates[tabName] = !tabPowerStates[tabName];
            localStorage.setItem('matrixTabPowerStates', JSON.stringify(tabPowerStates));
            if (tabPowerStates[tabName]) {
                btn.className = "power-switch-btn active-on"; btn.innerText = "ACTIVE (LOADED)";
                renderSpecificTab(tabName);
            } else {
                btn.className = "power-switch-btn active-off"; btn.innerText = "MUTED (0MB RAM)";
                const grid = document.getElementById('grid-' + tabName);
                if (grid) grid.querySelectorAll('iframe').forEach(frame => { frame.src = 'about:blank'; });
            }
            renderTabs();
        }

        function toggleFullScreenBlack() {
            const blackout = document.getElementById('fullScreenBlackout');
            if (blackout.style.display === 'none') blackout.style.display = 'flex';
            else blackout.style.display = 'none';
        }

        function syncRouterDropdownAndBox() {
            const sel = document.getElementById('targetGameSelector');
            sel.innerHTML = '';
            tabNames.forEach(t => { const opt = document.createElement('option'); opt.value = t; opt.innerText = t.toUpperCase(); sel.appendChild(opt); });
            
            const box = document.getElementById('activeRoutesBox');
            box.innerHTML = '';
            let keys = Object.keys(channelRoutes);
            if(keys.length === 0) { box.innerHTML = '<span style="color:#555; text-align:center; padding:5px;">No active links mapped yet.</span>'; return; }
            
            keys.forEach(ch => {
                const item = document.createElement('div'); item.className = 'router-item';
                item.innerHTML = `<span>📢 @${ch} ➔ <b style="color:#ff4500;">${channelRoutes[ch].toUpperCase()}</b></span>
                                  <span class="del-route-btn" onclick="removeChannelRoute('${ch}')">✕</span>`;
                box.appendChild(item);
            });
        }

        function addChannelRoute() {
            let ch = document.getElementById('channelRouteInput').value.trim().toLowerCase().replace('@', '');
            let target = document.getElementById('targetGameSelector').value;
            if(!ch) return; channelRoutes[ch] = target;
            localStorage.setItem('matrixChannelRoutes', JSON.stringify(channelRoutes));
            document.getElementById('channelRouteInput').value = '';
            syncRouterDropdownAndBox();
        }

        function removeChannelRoute(ch) {
            delete channelRoutes[ch];
            localStorage.setItem('matrixChannelRoutes', JSON.stringify(channelRoutes));
            syncRouterDropdownAndBox();
        }

        document.addEventListener("DOMContentLoaded", function() { initData(); renderTabs(); bootAllTabs(); });

        function resolvePathUrl(base, path) {
            if (!path) return base;
            if (path.startsWith('http')) return path;
            try { let urlObj = new URL(base); return urlObj.origin + path; } catch(e) { return base + path; }
        }

        function switchTab(newTab) {
            const oldGrid = document.getElementById('grid-' + currentTab);
            if(oldGrid) oldGrid.classList.remove('active-matrix');
            currentTab = newTab;
            localStorage.setItem('activeAutoClaimerTab', currentTab);
            const newGrid = document.getElementById('grid-' + currentTab);
            if(newGrid) newGrid.classList.add('active-matrix');
            renderTabs();
            document.getElementById('gameBaseUrlInput').value = localStorage.getItem('gameUrl_' + currentTab) || '';
        }

        function toggleIframeUI(btn, containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
            if (container.classList.contains('ui-active')) {
                container.classList.remove('ui-active'); btn.innerText = "SHOW APP UI"; btn.classList.remove('mode-dark');
            } else {
                container.classList.add('ui-active'); btn.innerText = "BLACK MODE"; btn.classList.add('mode-dark');
            }
        }

        function toggleRamFreeState(btn, frameId) {
            const frame = document.getElementById(frameId);
            if (!frame) return;
            if (btn.classList.contains('ram-stripped')) {
                btn.classList.remove('ram-stripped'); btn.innerText = "RAM-FREE UI";
                frame.contentWindow.postMessage({ cmd: 'SET_RAM_MODE', state: 'full' }, '*');
            } else {
                btn.classList.add('ram-stripped'); btn.innerText = "FULL UI VIEW";
                frame.contentWindow.postMessage({ cmd: 'SET_RAM_MODE', state: 'stripped' }, '*');
            }
        }

        function setGlobalRamFreeState(shouldStripAll) {
            tabNames.forEach(tab => {
                const grid = document.getElementById('grid-' + tab);
                if (!grid) return;
                grid.querySelectorAll('iframe').forEach(frame => {
                    if (frame.src && frame.src !== 'about:blank') {
                        let targetState = shouldStripAll ? 'stripped' : 'full';
                        frame.contentWindow.postMessage({ cmd: 'SET_RAM_MODE', state: targetState }, '*');
                    }
                });
                grid.querySelectorAll('.ram-toggle-btn').forEach(btn => {
                    if(shouldStripAll) { btn.classList.add('ram-stripped'); btn.innerText = "FULL UI VIEW"; } 
                    else { btn.classList.remove('ram-stripped'); btn.innerText = "RAM-FREE UI"; }
                });
            });
        }

        function forceInPlaceReload(frameId) {
            const frame = document.getElementById(frameId);
            if (!frame) return;
            try { frame.contentWindow.location.reload(true); } catch (err) { frame.src = frame.src; }
        }

        function toggleSingleAccountPower(frameId, originalUrl, btnId) {
            const frame = document.getElementById(frameId);
            const btn = document.getElementById(btnId);
            if (!frame || !btn) return;
            
            if (frame.src === 'about:blank') {
                frame.src = originalUrl;
                btn.classList.remove('dead-state');
                btn.innerText = "KILL (0MB)";
            } else {
                frame.src = 'about:blank';
                btn.classList.add('dead-state');
                btn.innerText = "WAKE UP";
            }
        }

        function setGlobalCurtainState(shouldBeBlackAll) {
            const currentGrid = document.getElementById('grid-' + currentTab);
            if (!currentGrid) return;
            currentGrid.querySelectorAll('.iframe-container').forEach(container => {
                const btn = container.querySelector('.ui-toggle-btn');
                if(shouldBeBlackAll) {
                    container.classList.remove('ui-active'); if(btn) { btn.innerText = "SHOW APP UI"; btn.classList.remove('mode-dark'); }
                } else {
                    container.classList.add('ui-active'); if(btn) { btn.innerText = "BLACK MODE"; btn.classList.add('mode-dark'); }
                }
            });
        }

        function addAccounts() {
            const bulkCredsInput = document.getElementById('bulkCreds').value.trim();
            if (!bulkCredsInput) return;
            const lines = bulkCredsInput.split('\n');
            if (!gameData[currentTab]) gameData[currentTab] = [];
            lines.forEach(line => {
                let cleanLine = line.trim(); if (!cleanLine) return;
                let parts = cleanLine.split(/[\s,:]+/);
                if (parts.length >= 2) gameData[currentTab].push({ phone: parts[0].trim(), pass: parts[1].trim() });
            });
            localStorage.setItem('rajaAccounts_' + currentTab, JSON.stringify(gameData[currentTab]));
            document.getElementById('bulkCreds').value = '';
            initData(); bootAllTabs(); 
        }

        function processManagementPanel() {
            const baseUrl = document.getElementById('gameBaseUrlInput').value.trim();
            const giftUrl = document.getElementById('gameGiftUrlInput').value.trim();
            const accountUrl = document.getElementById('gameAccountUrlInput').value.trim();
            if (baseUrl) localStorage.setItem('gameUrl_' + currentTab, baseUrl);
            if (giftUrl) localStorage.setItem('giftUrl_' + currentTab, giftUrl);
            if (accountUrl) localStorage.setItem('accountUrl_' + currentTab, accountUrl);
            addAccounts(); initData(); bootAllTabs(); toggleAddId();
        }

        function bootAllTabs() {
            const wrapper = document.getElementById('all-grids'); wrapper.innerHTML = '';
            tabNames.forEach(tab => {
                const grid = document.createElement('div'); grid.className = 'grid' + (tab === currentTab ? ' active-matrix' : ''); grid.id = 'grid-' + tab;
                wrapper.appendChild(grid); renderSpecificTab(tab);
            });
        }

        function renderSpecificTab(tabName) {
            const grid = document.getElementById('grid-' + tabName);
            if (!grid) return; grid.innerHTML = ''; 
            const safeTabId = tabName.replace(/\s/g, '');
            const baseUrl = localStorage.getItem('gameUrl_' + tabName) || '';
            if (!gameData[tabName]) return;

            gameData[tabName].forEach((item, index) => {
                const container = document.createElement('div'); container.className = 'iframe-container'; 
                const containerId = 'container-' + safeTabId + '-' + index; container.id = containerId; 
                const frameId = 'iframe-' + safeTabId + '-' + index;
                const killBtnId = 'killbtn-' + safeTabId + '-' + index;
                
                const isolatedUrl = (baseUrl && tabPowerStates[tabName]) ? (baseUrl.includes('?') ? `${baseUrl}&matrixId=${safeTabId}&subId=${index}` : `${baseUrl}#matrixId=${safeTabId}&subId=${index}`) : 'about:blank';

                container.innerHTML = `
                    <div class="id-header">
                        <div class="id-title">${tabName.toUpperCase()} - ID ${index + 1}</div>
                        <div>
                            <button class="kill-account-btn" id="${killBtnId}" onclick="toggleSingleAccountPower('${frameId}', '${isolatedUrl}', '${killBtnId}')">KILL (0MB)</button>
                            <button class="ui-toggle-btn" onclick="toggleIframeUI(this, '${containerId}')">SHOW APP UI</button>
                            <button class="ram-toggle-btn" onclick="toggleRamFreeState(this, '${frameId}')">RAM-FREE UI</button>
                            <button class="refresh-single" onclick="removeAccount('${tabName}', ${index})" style="background:red; margin-right:5px;">Delete</button>
                            <button class="reload-inplace-btn" onclick="forceInPlaceReload('${frameId}')">Reload</button>
                            <button class="refresh-single" onclick="document.getElementById('${frameId}').src='${isolatedUrl}'">Refres</button>
                        </div>
                    </div>
                    <div class="id-creds">
                        Number : <input type="text" class="cred-input" value="${item.phone}" onchange="saveCred('${tabName}', ${index}, 'phone', this.value)"><br>
                        Password : <input type="text" class="cred-input" value="${item.pass}" onchange="saveCred('${tabName}', ${index}, 'pass', this.value)">
                    </div>
                    <div class="frame-wrapper">
                        <div class="drag-handle">SCROLL</div>
                        <div class="black-curtain">
                            <span>⚫ BLACK PERFORMANCE ACTIVE</span>
                            <p>Listening & Claiming at 20ms in background...</p>
                        </div>
                        <iframe id="${frameId}" src="${isolatedUrl}"></iframe>
                    </div>
                `;
                grid.appendChild(container);
            });
        }

        function saveCred(tab, index, field, value) { gameData[tab][index][field] = value; localStorage.setItem('rajaAccounts_' + tab, JSON.stringify(gameData[tab])); }
        function removeAccount(tabName, index) { if (confirm("Permanently delete this ID?")) { gameData[tabName].splice(index, 1); localStorage.setItem('rajaAccounts_' + tabName, JSON.stringify(gameData[tabName])); bootAllTabs(); } }

        function refreshAllCurrent() {
            const baseUrl = localStorage.getItem('gameUrl_' + currentTab) || '';
            document.getElementById('grid-' + currentTab).querySelectorAll('iframe').forEach((frame, index) => { 
                const safeTabId = currentTab.replace(/\s/g, '');
                frame.src = baseUrl.includes('?') ? `${baseUrl}&matrixId=${safeTabId}&subId=${index}` : `${baseUrl}#matrixId=${safeTabId}&subId=${index}`;
            });
        }

        function goToGiftPage() {
            const baseUrl = localStorage.getItem('gameUrl_' + currentTab) || '';
            const path = localStorage.getItem('giftUrl_' + currentTab) || '';
            const fullTarget = resolvePathUrl(baseUrl, path);
            document.getElementById('grid-' + currentTab).querySelectorAll('iframe').forEach((frame, index) => {
                const safeTabId = currentTab.replace(/\s/g, '');
                frame.src = fullTarget.includes('?') ? `${fullTarget}&matrixId=${safeTabId}&subId=${index}` : `${fullTarget}#matrixId=${safeTabId}&subId=${index}`;
            });
        }

        function goToAccountPage() {
            const baseUrl = localStorage.getItem('gameUrl_' + currentTab) || '';
            const path = localStorage.getItem('accountUrl_' + currentTab) || '';
            const fullTarget = resolvePathUrl(baseUrl, path);
            document.getElementById('grid-' + currentTab).querySelectorAll('iframe').forEach((frame, index) => {
                const safeTabId = currentTab.replace(/\s/g, '');
                frame.src = fullTarget.includes('?') ? `${fullTarget}&matrixId=${safeTabId}&subId=${index}` : `${fullTarget}#matrixId=${safeTabId}&subId=${index}`;
            });
        }

        function fireTargetTab(targetTabName, code) {
            if(!targetTabName || !code || !tabPowerStates[targetTabName]) return; 
            const baseUrl = localStorage.getItem('gameUrl_' + targetTabName) || '';
            const giftPath = localStorage.getItem('giftUrl_' + targetTabName) || '';
            const fullGiftUrl = resolvePathUrl(baseUrl, giftPath);
            const safeTabId = targetTabName.replace(/\s/g, '');
            const targetGrid = document.getElementById('grid-' + targetTabName);
            
            if (targetGrid) {
                targetGrid.querySelectorAll('iframe').forEach((frame, index) => { 
                    if(frame.src && frame.src !== 'about:blank') {
                        const dynamicFrameGiftUrl = fullGiftUrl.includes('?') ? `${fullGiftUrl}&matrixId=${safeTabId}&subId=${index}` : `${fullGiftUrl}#matrixId=${safeTabId}&subId=${index}`;
                        frame.contentWindow.postMessage({ cmd: 'FIRE', code: code, giftUrl: dynamicFrameGiftUrl }, '*'); 
                    }
                });
            }
        }

        function fireAll() {
            const code = document.getElementById('masterCode').value.trim();
            if(!code) return;
            fireTargetTab(currentTab, code);
        }

        function broadcastCmd(cmdType) {
            const grid = document.getElementById('grid-' + currentTab); if (!grid) return;
            grid.querySelectorAll('iframe').forEach((frame, index) => {
                if(frame.src && frame.src !== 'about:blank') {
                    const creds = gameData[currentTab][index];
                    if(creds) frame.contentWindow.postMessage({cmd: cmdType, phone: creds.phone, pass: creds.pass}, '*');
                }
            });
        }

        async function pasteCode() { 
            try { 
                const rawText = await navigator.clipboard.readText(); if (!rawText) return;
                const codeMatch = rawText.match(/[A-Za-z0-9]{15,45}/); 
                document.getElementById('masterCode').value = codeMatch ? codeMatch[0] : rawText.trim(); 
            } catch (err) { 
                let fallbackPrompt = prompt("Clipboard locked. Paste manually below:");
                if (fallbackPrompt) {
                    const fallbackMatch = fallbackPrompt.match(/[A-Za-z0-9]{15,45}/);
                    document.getElementById('masterCode').value = fallbackMatch ? fallbackMatch[0] : fallbackPrompt.trim();
                }
            } 
        }
        function clearCode() { document.getElementById('masterCode').value = ''; }

        // ── HYPER-FAST HTTP POLLING (NO WEBSOCKET NEEDED) ──
        async function scanPythonServer() {
            if (autoEnabled) {
                try {
                    const data = await (await fetch('/code')).json();
                    const el = document.getElementById('tgStatus');
                    if (el) { el.innerText = 'LIVE ✓ (HTTP Fast-Poll)'; el.className = 'tg-live'; }
                    
                    if (data.code && document.getElementById('lastCodeDisplay')) document.getElementById('lastCodeDisplay').innerText = '🎯 ' + data.code;
                    if (document.getElementById('queueCount')) document.getElementById('queueCount').innerText = 'Seen: ' + (data.seen_count || 0);
                    
                    if (data.code && data.code !== lastFiredCode) {
                        lastFiredCode = data.code;
                        if (document.getElementById('blackoutCodeDisplay')) document.getElementById('blackoutCodeDisplay').innerText = '🎯 ' + data.code;
                        let target = channelRoutes[data.channel];
                        if (!target && data.channel && data.channel.includes('fallback_engine')) {
                            const part = data.channel.split('_')[0];
                            target = tabNames.find(t => t.toLowerCase() === part);
                        }
                        target = target || currentTab;
                        fireTargetTab(target, data.code);
                    }
                } catch(e) {
                    const el = document.getElementById('tgStatus');
                    if (el) { el.innerText = 'offline ✗'; el.className = 'tg-offline'; }
                }
            }
            setTimeout(scanPythonServer, 150); // Calls itself every 150ms 
        }
        setTimeout(scanPythonServer, 150); // Start Loop
        
        function dismissCaptchaAlert(){ document.getElementById('captchaAlert').style.display='none'; }
        
        window.addEventListener('message', function(e) {
            if (!e.data) return;
            if (e.data.cmd === 'CAPTCHA_MANUAL') {
                const id = e.data.idIndex !== null ? 'ID '+(e.data.idIndex+1) : 'unknown';
                const alert = document.getElementById('captchaAlert');
                document.getElementById('captchaAlertText').innerText = currentTab.toUpperCase()+' '+id+' — Scroll down to that account and solve the puzzle captcha';
                alert.style.display = 'block';
                setTimeout(() => { alert.style.display='none'; }, 30000);
            }
            if (e.data.cmd === 'CAPTCHA_SOLVED') { document.getElementById('captchaAlert').style.display='none'; }
        });

        function toggleAuto() { 
            autoEnabled = !autoEnabled; const btn = document.getElementById('autoBtn'); 
            if(autoEnabled) { 
                btn.innerText = 'AUTO: ON'; btn.style.color = '#00c853'; btn.style.borderColor = '#00c853'; 
            } else { 
                btn.innerText = 'AUTO: OFF'; btn.style.color = '#aaa'; btn.style.borderColor = '#444'; 
            } 
        }
    </script>
</body>
</html>
"""

# ══════════════════════════════════════════════════════════════════
#  COMBINED HTTP HANDLER & NOTIFICATION ENGINE
# ══════════════════════════════════════════════════════════════════
class CombinedHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/index.html":
                body = HTML_DASHBOARD.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            elif self.path == "/code":
                payload = dict(latest_payload)
                payload["seen_count"] = len(seen_codes)
                body = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)

            elif self.path == "/status":
                body = json.dumps({
                    "server": "ok",
                    "seen_codes": len(seen_codes),
                    "queue_size": len(code_queue),
                    "latest_code": latest_payload.get("code", ""),
                    "latest_channel": latest_payload.get("channel", ""),
                }).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            pass

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()
        except Exception:
            pass

    def log_message(self, format, *args):
        pass

def process_queue():
    global latest_payload
    while True:
        if code_queue:
            next_payload = code_queue.pop(0)
            latest_payload = next_payload
            print(f"⚡ DEPLOYING: {latest_payload['code']}  ←  @{latest_payload['channel']}")
            time.sleep(1.0)
        else:
            time.sleep(0.1)

def run_web_server():
    server = HTTPServer(("0.0.0.0", 8080), CombinedHandler)
    print("🌐 Dashboard running  →  http://localhost:8080")
    print("🔌 Code API running   →  http://localhost:8080/code")
    server.serve_forever()

tg_app = Client("claimer_session", api_id=API_ID, api_hash=API_HASH)

@tg_app.on_message(filters.text | filters.caption)
def code_catcher(client, message):
    text = message.text or message.caption
    if not text:
        return

    channel_username = message.chat.username if message.chat else None

    if not channel_username:
        lower_text = text.lower()
        if "raja" in lower_text: channel_username = "raja_fallback_engine"
        elif "jai" in lower_text: channel_username = "jaiclub_fallback_engine"
        elif "jalwa" in lower_text: channel_username = "jalwa_fallback_engine"
        else: channel_username = "unknown_anonymous_source"

    raw_matches = re.findall(r'\b[A-Za-z0-9]{15,45}\b', text)
    valid_codes = [c for c in raw_matches if not c.isalpha() and not c.isdigit()]

    if valid_codes:
        new_count = 0
        for code in valid_codes:
            if code not in seen_codes:
                seen_codes.add(code)
                save_code_to_memory(code)
                code_queue.append({"code": code, "channel": channel_username.lower().strip()})
                new_count += 1

        if new_count > 0:
            print(f"🎯 {new_count} NEW CODE(S) from @{channel_username}")
            # Trigger Lock Screen Notification
            try:
                os.system(f'termux-notification -i 100 -t "🔥 MATRIX: CODE CLAIMED!" -c "Fired {new_count} code(s) from @{channel_username}" --priority max --vibrate 500,500')
            except Exception:
                pass

async def boot_sniper():
    await tg_app.start()
    print("👁️  Telegram Sniper Engine booted...")
    
    # Push Background Running Notification
    try:
        os.system('termux-notification -i 100 -t "⚡ Matrix Core Active" -c "Listening for drops. Screen can be locked." --ongoing --priority high')
    except Exception:
        pass
        
    print("🔄  Syncing dialog cache (prevents Peer ID errors)...")
    try:
        async for dialog in tg_app.get_dialogs(): pass
    except Exception: pass
    print("✅  Cache synced. Watching all channels live. Waiting for drops...")
    await pyrogram_idle()
    await tg_app.stop()

if __name__ == "__main__":
    print("=" * 60)
    print("  MATRIX AUTO CLAIMER — ALL-IN-ONE EDITION")
    print("=" * 60)
    threading.Thread(target=run_web_server, daemon=True).start()
    threading.Thread(target=process_queue,  daemon=True).start()
    tg_app.run(boot_sniper())
