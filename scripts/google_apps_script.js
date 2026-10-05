/**
 * ==============================================================================
 * SACHIN & REENU SERIES - AUTONOMOUS 2X DAILY STUDIO TRIGGER & STORY LEDGER
 * ==============================================================================
 * Instructions:
 * 1. Open your Google Sheet: "Sachin and Reenu"
 * 2. Click "Extensions" -> "Apps Script".
 * 3. Delete any code in Code.gs and paste this entire script.
 * 4. Run `initSpreadsheetHeader()` once to format your columns.
 * 5. Run `setupDailyTriggers()` once to activate the 12:00 PM and 6:00 PM IST schedules!
 * 6. (Optional) Deploy as Web App if you want two-way automated sync from GitHub Actions.
 * ==============================================================================
 */

// GitHub Repository Configuration
const GITHUB_REPO = "YoutubeVideoUploader/sachin-and-reenu-series";
const GITHUB_WORKFLOW = "produce_and_publish.yml";
// Paste your GitHub Personal Access Token (PAT) below
const GITHUB_PAT = "YOUR_GITHUB_PAT_HERE"; // Replace with your GitHub PAT

/**
 * Formats the header row of your Google Sheet.
 */
function initSpreadsheetHeader() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const headers = [
    "Episode", 
    "Title", 
    "Status", 
    "Story Outline / Synopsis", 
    "Instagram URL", 
    "Next Episode Cliffhanger", 
    "Published At (IST)"
  ];
  
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length)
      .setBackground("#1a1a2e")
      .setFontColor("#ffffff")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    sheet.setFrozenRows(1);
    
    // Add default row for Episode 1 if empty
    sheet.appendRow([
      1,
      "തിരിച്ചുവരവ് (The Homecoming)",
      "Published",
      "After two long years apart, Sachin finally touches down at Kochi CIAL from the UK. Reenu and Amal eagerly wait by the arrival barriers, leading to an overwhelming, heartfelt reunion.",
      "https://www.instagram.com/reel/18115173056519806/",
      "As Sachin holds Reenu close, his mysterious glance toward his travel pouch hints at a secret from London.",
      new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })
    ]);
    
    // Add queued row for Episode 2
    sheet.appendRow([
      2,
      "കൊച്ചിയിലെ മഴയും ഒരു രഹസ്യവും (Kochi Rain & A Secret)",
      "Queued",
      "Sachin, Reenu, and Amal drive from CIAL into Kochi amid sudden monsoon rain. While stopping for hot tea, Sachin reveals a small velvet box inside his bag, but hesitates to open it.",
      "",
      "",
      ""
    ]);
  }
}

/**
 * Triggers the GitHub Actions Episode Studio workflow.
 * Can be called manually or automatically by the time-driven triggers.
 */
function triggerEpisodeStudio() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // Find the first queued episode
  let queuedEp = null;
  let queuedRow = -1;
  
  for (let i = 1; i < data.length; i++) {
    const status = (data[i][2] || "").toString().trim().toLowerCase();
    if (status === "queued" || status === "pending") {
      queuedEp = {
        episode: data[i][0],
        title: data[i][1],
        outline: data[i][3]
      };
      queuedRow = i + 1;
      break;
    }
  }

  Logger.log("Triggering Episode Studio for: " + (queuedEp ? "Episode " + queuedEp.episode : "Next automatic episode"));

  const url = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${GITHUB_WORKFLOW}/dispatches`;
  const payload = {
    ref: "main",
    inputs: {
      dry_run: false
    }
  };

  const options = {
    method: "post",
    headers: {
      "Authorization": `Bearer ${GITHUB_PAT}`,
      "Accept": "application/vnd.github+json",
      "User-Agent": "Google-Apps-Script-SachinAndReenu"
    },
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  
  if (code === 204) {
    Logger.log("Successfully triggered GitHub Actions workflow!");
    if (queuedRow > 0) {
      sheet.getRange(queuedRow, 3).setValue("Processing");
    }
  } else {
    Logger.log(`Failed to trigger workflow: HTTP ${code} - ${response.getContentText()}`);
  }
}

/**
 * Sets up the 2 daily triggers:
 * 1. Morning 12:00 PM (Noon) IST
 * 2. Evening 6:00 PM IST
 */
function setupDailyTriggers() {
  // Clear any existing triggers
  const existingTriggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < existingTriggers.length; i++) {
    ScriptApp.deleteTrigger(existingTriggers[i]);
  }

  // Trigger 1: Daily at 12:00 PM IST (noon)
  ScriptApp.newTrigger("triggerEpisodeStudio")
    .timeBased()
    .atHour(12)
    .nearMinute(0)
    .everyDays(1)
    .inTimezone("Asia/Kolkata")
    .create();

  // Trigger 2: Daily at 6:00 PM (18:00) IST
  ScriptApp.newTrigger("triggerEpisodeStudio")
    .timeBased()
    .atHour(18)
    .nearMinute(0)
    .everyDays(1)
    .inTimezone("Asia/Kolkata")
    .create();

  Logger.log("Configured 2 daily triggers: 12:00 PM IST & 6:00 PM IST!");
}

/**
 * Web App GET endpoint: Returns the next queued story outline.
 */
function doGet(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  for (let i = 1; i < data.length; i++) {
    const status = (data[i][2] || "").toString().trim().toLowerCase();
    if (status === "queued" || status === "pending" || status === "processing") {
      return ContentService.createTextOutput(JSON.stringify({
        found: true,
        row: i + 1,
        episode: data[i][0],
        title: data[i][1],
        outline: data[i][3]
      })).setMimeType(ContentService.MimeType.JSON);
    }
  }

  return ContentService.createTextOutput(JSON.stringify({
    found: false,
    message: "No queued story found"
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Web App POST endpoint: Receives completed episode details and appends next episode.
 */
function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });

    // 1. Update published episode status
    const data = sheet.getDataRange().getValues();
    const epNum = body.episode_number;
    let updated = false;

    for (let i = 1; i < data.length; i++) {
      if (data[i][0] == epNum) {
        sheet.getRange(i + 1, 3).setValue("Published");
        sheet.getRange(i + 1, 5).setValue(body.instagram_url || "");
        sheet.getRange(i + 1, 6).setValue(body.cliffhanger || "");
        sheet.getRange(i + 1, 7).setValue(nowIst);
        updated = true;
        break;
      }
    }

    // 2. Append next episode queued row
    if (body.next_episode_story) {
      const nextEpNum = epNum + 1;
      sheet.appendRow([
        nextEpNum,
        body.next_episode_title || `ഭാഗം ${nextEpNum}`,
        "Queued",
        body.next_episode_story,
        "",
        "",
        ""
      ]);
    }

    return ContentService.createTextOutput(JSON.stringify({ success: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
