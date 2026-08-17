
const PROFILE_INDEX = 2; 
const LOCAL_API_URL = "http://127.0.0.1:9090/update_cookie";

async function fetchCookies() {
    let psid = null;
    let psidts = null;
    try {
        const cookies = await chrome.cookies.getAll({ domain: ".google.com" });
        for (let c of cookies) {
            if (c.name === "__Secure-1PSID") psid = c.value;
            if (c.name === "__Secure-1PSIDTS") psidts = c.value;
        }
        if (psid || psidts) {
            await syncToServer(psid, psidts);
        }
    } catch (e) { }
}

async function syncToServer(psid, psidts) {
    try {
        await fetch(LOCAL_API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ account_index: PROFILE_INDEX, psid: psid || "", psidts: psidts || "" })
        });
    } catch (e) { }
}
chrome.alarms.create("syncCookies", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => { if (alarm.name === "syncCookies") fetchCookies(); });
fetchCookies();
