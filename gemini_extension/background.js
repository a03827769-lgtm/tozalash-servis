// Har bir Chrome profiliga alohida ID berish mumkin (masalan 1, 2, 3, 4)
// O'rnatgandan so'ng koddan shu qatorni o'zgartirib qo'yish kerak
const PROFILE_INDEX = 1; 

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
    } catch (e) {
        console.error("Cookie olishda xato:", e);
    }
}

async function syncToServer(psid, psidts) {
    try {
        const response = await fetch(LOCAL_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                account_index: PROFILE_INDEX,
                psid: psid || "",
                psidts: psidts || ""
            })
        });
        const result = await response.json();
        console.log("Sync natijasi:", result);
    } catch (e) {
        console.error("Serverga ulana olmadik:", e);
    }
}

// Har 1 daqiqada cookie'ni tekshirib, serverga jo'natib turadi
chrome.alarms.create("syncCookies", { periodInMinutes: 1 });

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === "syncCookies") {
        fetchCookies();
    }
});

// Extension ishga tushganda bir marta ishlaydi
fetchCookies();
