/**
 * Tozalash Servis — Google Sheets Apps Script
 * Google Sheets da avtomatik formulalar va triggerlar
 * 
 * O'rnatish:
 * 1. Google Sheets ni oching
 * 2. Extensions → Apps Script
 * 3. Bu kodni joylashtiring
 * 4. Run → setupTriggers ni ishga tushiring
 */

// ================================================
// ASOSIY KONFIGURATSIYA
// ================================================
const CONFIG = {
  BUSINESS_NAME: "Tozalash Servis",
  TELEGRAM_BOT_TOKEN: "", // .env dan oling
  ADMIN_TELEGRAM_ID: "",  // .env dan oling
  SHEETS: {
    ORDERS: "Buyurtmalar",
    CLIENTS: "Mijozlar", 
    WORKERS: "Ishchilar",
    FINANCE: "Moliya",
    DASHBOARD: "Dashboard",
    AI_LOG: "AI_Log"
  }
};


// ================================================
// AVTOMATIK TRIGGERLAR SOZLASH
// ================================================
function setupTriggers() {
  // Eski triggerlarni o'chirish
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => ScriptApp.deleteTrigger(trigger));
  
  // Kunlik statistika (har kuni 22:00)
  ScriptApp.newTrigger('updateDashboard')
    .timeBased()
    .everyDays(1)
    .atHour(22)
    .create();
  
  // Haftalik hisobot (Dushanba 09:00)
  ScriptApp.newTrigger('sendWeeklyReport')
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY)
    .atHour(9)
    .create();
  
  Logger.log("✅ Triggerlar sozlandi!");
}


// ================================================
// DASHBOARD YANGILASH
// ================================================
function updateDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashSheet = ss.getSheetByName(CONFIG.SHEETS.DASHBOARD);
  const ordersSheet = ss.getSheetByName(CONFIG.SHEETS.ORDERS);
  const financeSheet = ss.getSheetByName(CONFIG.SHEETS.FINANCE);
  
  if (!dashSheet || !ordersSheet) {
    Logger.log("Varaqlar topilmadi!");
    return;
  }
  
  // Barcha buyurtmalarni olish
  const ordersData = ordersSheet.getDataRange().getValues();
  const today = new Date();
  const todayStr = Utilities.formatDate(today, "Asia/Tashkent", "yyyy-MM-dd");
  const monthStr = Utilities.formatDate(today, "Asia/Tashkent", "yyyy-MM");
  
  let todayOrders = 0;
  let todayRevenue = 0;
  let monthOrders = 0;
  let monthRevenue = 0;
  let totalOrders = 0;
  let totalRevenue = 0;
  let completedOrders = 0;
  
  // Sarlavha qatorini o'tkazib yuborish (i=1 dan boshlanadi)
  for (let i = 1; i < ordersData.length; i++) {
    const row = ordersData[i];
    if (!row[0]) continue; // Bo'sh qator
    
    const orderDate = row[14] ? String(row[14]).substring(0, 10) : "";
    const orderMonth = orderDate.substring(0, 7);
    const amount = parseFloat(String(row[10]).replace(/,/g, '')) || 0;
    const status = row[12] || "";
    
    totalOrders++;
    totalRevenue += amount;
    
    if (orderDate === todayStr) {
      todayOrders++;
      todayRevenue += amount;
    }
    
    if (orderMonth === monthStr) {
      monthOrders++;
      monthRevenue += amount;
    }
    
    if (status === "bajarildi") completedOrders++;
  }
  
  // Dashboard ni yangilash
  dashSheet.clearContents();
  dashSheet.getRange(1, 1, 1, 4).setValues([
    ["📊 KO'RSATKICH", "BUGUN", "BU OY", "JAMI"]
  ]);
  
  const stats = [
    ["💰 Daromad (so'm)", todayRevenue.toLocaleString(), monthRevenue.toLocaleString(), totalRevenue.toLocaleString()],
    ["📦 Buyurtmalar", todayOrders, monthOrders, totalOrders],
    ["✅ Bajarilgan", "-", "-", completedOrders],
    ["📈 Konversiya %", "-", "-", totalOrders > 0 ? (completedOrders/totalOrders*100).toFixed(1)+"%" : "0%"],
    ["📅 Yangilandi", Utilities.formatDate(today, "Asia/Tashkent", "HH:mm"), "-", Utilities.formatDate(today, "Asia/Tashkent", "dd.MM.yyyy")]
  ];
  
  dashSheet.getRange(2, 1, stats.length, 4).setValues(stats);
  
  // Formatlash
  const headerRange = dashSheet.getRange(1, 1, 1, 4);
  headerRange.setBackground("#2E75B6");
  headerRange.setFontColor("#FFFFFF");
  headerRange.setFontWeight("bold");
  
  Logger.log(`✅ Dashboard yangilandi: Bugun ${todayOrders} buyurtma, ${todayRevenue.toLocaleString()} so'm`);
}


// ================================================
// BUYURTMA QO'SHILGANDA AVTOMATIK FORMAT
// ================================================
function onEdit(e) {
  const sheet = e.range.getSheet();
  const sheetName = sheet.getName();
  
  // Faqat Buyurtmalar varaqida ishlash
  if (sheetName !== CONFIG.SHEETS.ORDERS) return;
  
  const row = e.range.getRow();
  const col = e.range.getColumn();
  
  if (row <= 1) return; // Sarlavhani o'tkazib yuborish
  
  // Status o'zgarganda rangni yangilash (13-ustun)
  if (col === 13) {
    const status = e.value;
    const statusColors = {
      'yangi': '#FFF9C4',       // Sariq
      'tayinlandi': '#E3F2FD',  // Ko'k
      'jarayonda': '#FFF3E0',   // To'q sariq
      'bajarildi': '#E8F5E9',   // Yashil
      'bekor': '#FFEBEE'        // Qizil
    };
    
    const color = statusColors[status] || '#FFFFFF';
    sheet.getRange(row, 1, 1, 15).setBackground(color);
  }
}


// ================================================
// HAFTALIK HISOBOT (TELEGRAM)
// ================================================
function sendWeeklyReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ordersSheet = ss.getSheetByName(CONFIG.SHEETS.ORDERS);
  
  if (!ordersSheet || !CONFIG.TELEGRAM_BOT_TOKEN || !CONFIG.ADMIN_TELEGRAM_ID) {
    Logger.log("Konfiguratsiya to'liq emas");
    return;
  }
  
  const ordersData = ordersSheet.getDataRange().getValues();
  
  // Bu haftaning buyurtmalari
  const today = new Date();
  const weekAgo = new Date(today - 7 * 24 * 60 * 60 * 1000);
  
  let weekOrders = 0;
  let weekRevenue = 0;
  
  for (let i = 1; i < ordersData.length; i++) {
    const row = ordersData[i];
    if (!row[0]) continue;
    
    const dateStr = String(row[14] || '').substring(0, 10);
    if (!dateStr) continue;
    
    const orderDate = new Date(dateStr);
    if (orderDate >= weekAgo) {
      weekOrders++;
      weekRevenue += parseFloat(String(row[10]).replace(/,/g, '')) || 0;
    }
  }
  
  const message = `📊 *HAFTALIK HISOBOT — ${CONFIG.BUSINESS_NAME}*\n\n` +
    `📅 Sana: ${Utilities.formatDate(today, "Asia/Tashkent", "dd.MM.yyyy")}\n\n` +
    `📦 Haftalik buyurtmalar: *${weekOrders} ta*\n` +
    `💰 Haftalik daromad: *${weekRevenue.toLocaleString()} so'm*\n\n` +
    `📈 _Google Sheets da to'liq ma'lumot bor_`;
  
  sendTelegramMessage(CONFIG.ADMIN_TELEGRAM_ID, message);
}


// ================================================
// TELEGRAM XABAR YUBORISH
// ================================================
function sendTelegramMessage(chatId, text) {
  if (!CONFIG.TELEGRAM_BOT_TOKEN) return;
  
  const url = `https://api.telegram.org/bot${CONFIG.TELEGRAM_BOT_TOKEN}/sendMessage`;
  const payload = {
    chat_id: chatId,
    text: text,
    parse_mode: "Markdown"
  };
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload)
  };
  
  try {
    UrlFetchApp.fetch(url, options);
    Logger.log(`✅ Telegram xabar yuborildi: ${chatId}`);
  } catch(e) {
    Logger.log(`❌ Telegram xabar xatosi: ${e}`);
  }
}


// ================================================
// VARAQLARNI AVTOMATIK FORMATLASH
// ================================================
function formatAllSheets() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  Object.values(CONFIG.SHEETS).forEach(sheetName => {
    const sheet = ss.getSheetByName(sheetName);
    if (!sheet) return;
    
    // Sarlavha formatlash
    if (sheet.getLastRow() > 0) {
      const headerRange = sheet.getRange(1, 1, 1, sheet.getLastColumn());
      headerRange.setBackground("#2E75B6");
      headerRange.setFontColor("#FFFFFF");
      headerRange.setFontWeight("bold");
      headerRange.setHorizontalAlignment("center");
    }
    
    // Ustun kengligini avtomatik moslashtirish
    sheet.autoResizeColumns(1, sheet.getLastColumn());
    
    Logger.log(`✅ ${sheetName} formatlandi`);
  });
}


// ================================================
// YANGI BUYURTMA XABARDORLIGI
// ================================================
function notifyNewOrder(orderData) {
  if (!CONFIG.TELEGRAM_BOT_TOKEN || !CONFIG.ADMIN_TELEGRAM_ID) return;
  
  const message = 
    `🔔 *YANGI BUYURTMA!*\n\n` +
    `📋 #${orderData.number}\n` +
    `🧹 ${orderData.service}\n` +
    `📍 ${orderData.address}\n` +
    `📅 ${orderData.date}\n` +
    `💰 ${parseInt(orderData.amount).toLocaleString()} so'm`;
  
  sendTelegramMessage(CONFIG.ADMIN_TELEGRAM_ID, message);
}
