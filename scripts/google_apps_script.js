/**
 * ==============================================================================
 * SACHIN & REENU CREATOR STUDIO — GOOGLE APPS SCRIPT ENGINE (V3 ROBUST)
 * ==============================================================================
 * Features:
 * 1. 2-Column Episode Checklist in Google Sheet:
 *    - Column A: Shot Name (Shot 1, Shot 2, ..., Shot 22)
 *    - Column B: Video Status (Present / Pending)
 * 2. Automatic Google Drive detection:
 *    - Automatically scans Episode Drive folder and updates Column B to "Present".
 * 3. Strict Pre-Check API:
 *    - Only triggers/allows production if ALL shots (e.g. 22/22) are "Present".
 * 4. Post-Publish Auto-Cleanup:
 *    - Automatically deletes all uploaded clips from Google Drive.
 *    - Automatically blanks/resets the Google Sheet checklist for the next episode.
 * 5. 2x Daily Automated Triggers at 12:00 PM IST & 6:00 PM IST.
 * 
 * Setup Instructions:
 * 1. Open Google Sheet: https://docs.google.com/spreadsheets/d/1-7AHyFLXXgF1CdOfQPgPFbNelgiufxlsccpahrMG_VI/edit
 * 2. Click "Extensions" -> "Apps Script".
 * 3. Replace all code in Code.gs with this file.
 * 4. Replace `YOUR_GITHUB_PAT_HERE` with your GitHub Personal Access Token.
 * 5. Run `setupStudioSpreadsheet()` once to create/format the Ledger & Checklist sheets.
 * 6. Run `setupDailyTriggers()` once to schedule 12:00 PM & 6:00 PM IST runs.
 * 7. Deploy as Web App ("Execute as: Me", "Who has access: Anyone").
 * ==============================================================================
 */

// CONFIGURATION
const SPREADSHEET_ID = "1-7AHyFLXXgF1CdOfQPgPFbNelgiufxlsccpahrMG_VI";
const GITHUB_REPO = "YoutubeVideoUploader/sachin-and-reenu-series";
const GITHUB_WORKFLOW = "produce_and_publish.yml";
const GITHUB_PAT = "YOUR_GITHUB_PAT_HERE"; // Insert your GitHub PAT (Repo/Workflow scope)
const DRIVE_ROOT_FOLDER = "Sachin_And_Reenu_Studio";

const TAB_LEDGER = "Episode_Ledger";
const TAB_CHECKLIST = "Production_Checklist";

/**
 * Initializes and formats both sheets: Episode_Ledger and Production_Checklist.
 */
function setupStudioSpreadsheet() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  
  // 1. Setup Episode_Ledger
  let ledgerSheet = ss.getSheetByName(TAB_LEDGER);
  if (!ledgerSheet) {
    ledgerSheet = ss.insertSheet(TAB_LEDGER, 0);
  }
  
  const ledgerHeaders = [
    "Episode", 
    "Title", 
    "Status", 
    "Total Shots", 
    "Drive Folder URL", 
    "Instagram URL", 
    "Story Outline / Synopsis", 
    "Published At (IST)"
  ];
  
  if (ledgerSheet.getLastRow() === 0) {
    ledgerSheet.appendRow(ledgerHeaders);
    ledgerSheet.getRange(1, 1, 1, ledgerHeaders.length)
      .setBackground("#0f172a")
      .setFontColor("#f8fafc")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    ledgerSheet.setFrozenRows(1);
    
    // Episode 1 (Current Active Production: 22 Shots)
    ledgerSheet.appendRow([
      1,
      "തിരിച്ചുവരവ് (The Homecoming)",
      "Queued",
      22,
      "",
      "",
      "After two long years of separation, Sachin returns from the UK to a nervous Reenu waiting with Amal at Kochi CIAL airport. Amidst the tearful reunion, a secret from London awaits.",
      ""
    ]);
  }
  
  // 2. Setup Production_Checklist
  let checkSheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!checkSheet) {
    checkSheet = ss.insertSheet(TAB_CHECKLIST, 1);
  }
  
  initChecklist(1, 22, "തിരിച്ചുവരവ് (The Homecoming)");
  Logger.log("Studio Spreadsheet setup successfully initialized!");
}

/**
 * Populates or resets the 2-Column Checklist for a specific episode.
 * Column 1: Shot Number (Shot 1..N)
 * Column 2: Video Status (Pending / Present)
 */
function initChecklist(episodeNum, totalShots, episodeTitle) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_CHECKLIST);
  }
  
  sheet.clear();
  
  // Header Meta
  sheet.getRange(1, 1).setValue(`EPISODE ${episodeNum}: ${episodeTitle || ''}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(`TARGET SHOTS: ${totalShots}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#3b82f6").setFontColor("#ffffff");
  
  // Column Headers (Strict 2-Column specification)
  sheet.getRange(2, 1).setValue("Shot Number (Column 1)").setFontWeight("bold").setBackground("#1e293b").setFontColor("#ffffff");
  sheet.getRange(2, 2).setValue("Video Status (Column 2)").setFontWeight("bold").setBackground("#1e293b").setFontColor("#ffffff");
  sheet.getRange(2, 3).setValue("Drive File Name").setFontWeight("bold").setBackground("#1e293b").setFontColor("#ffffff");
  sheet.getRange(2, 4).setValue("Drive File ID").setFontWeight("bold").setBackground("#1e293b").setFontColor("#ffffff");
  sheet.getRange(2, 5).setValue("Last Updated (IST)").setFontWeight("bold").setBackground("#1e293b").setFontColor("#ffffff");
  
  const rows = [];
  for (let s = 1; s <= totalShots; s++) {
    rows.push([`Shot ${s}`, "Pending", "", "", ""]);
  }
  
  if (rows.length > 0) {
    sheet.getRange(3, 1, rows.length, 5).setValues(rows);
    // Format Pending in light amber
    sheet.getRange(3, 2, rows.length, 1)
      .setBackground("#fef3c7")
      .setFontColor("#92400e")
      .setHorizontalAlignment("center");
    sheet.getRange(3, 1, rows.length, 1).setHorizontalAlignment("center").setFontWeight("bold");
  }
  
  sheet.setFrozenRows(2);
  Logger.log(`Checklist initialized for Episode ${episodeNum} with ${totalShots} shots.`);
}

/**
 * Completely blanks the Production_Checklist sheet after publishing.
 */
function makeChecklistBlank() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(TAB_CHECKLIST);
  if (sheet) {
    sheet.clear();
    sheet.getRange(1, 1).setValue("CHECKLIST BLANK — Awaiting Next Episode Configuration")
      .setFontWeight("bold")
      .setFontColor("#64748b");
    Logger.log("Production_Checklist successfully cleared and made blank.");
  }
}

/**
 * Gets or creates the Google Drive folder for an episode.
 */
function getEpisodeDriveFolder(episodeNum) {
  let rootIter = DriveApp.getFoldersByName(DRIVE_ROOT_FOLDER);
  let rootFolder = rootIter.hasNext() ? rootIter.next() : DriveApp.createFolder(DRIVE_ROOT_FOLDER);
  
  const subFolderName = `Episode_${episodeNum}`;
  let subIter = rootFolder.getFoldersByName(subFolderName);
  let subFolder = subIter.hasNext() ? subIter.next() : rootFolder.createFolder(subFolderName);
  
  return subFolder;
}

/**
 * Scans Google Drive and syncs with the Production_Checklist in Google Sheets.
 * Matches files like "shot_1.mp4", "shot 1", "shot_01", or files uploaded into Drive.
 */
function syncDriveToChecklist(episodeNum) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!sheet || sheet.getLastRow() < 3) {
    Logger.log("Checklist sheet is blank or uninitialized.");
    return { ready: false, total_shots: 0, present_shots: 0, files: [] };
  }
  
  const folder = getEpisodeDriveFolder(episodeNum);
  const filesIter = folder.getFiles();
  const driveFiles = [];
  
  while (filesIter.hasNext()) {
    const f = filesIter.next();
    driveFiles.push({
      name: f.getName(),
      id: f.getId(),
      url: f.getUrl(),
      downloadUrl: f.getDownloadUrl(),
      size: f.getSize()
    });
  }
  
  const lastRow = sheet.getLastRow();
  const totalShots = lastRow - 2;
  const shotData = sheet.getRange(3, 1, totalShots, 5).getValues();
  const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
  
  let presentCount = 0;
  const matchedFiles = [];
  
  for (let i = 0; i < shotData.length; i++) {
    const shotNum = i + 1; // 1-indexed
    
    // Find matching file in driveFiles
    let match = null;
    for (const f of driveFiles) {
      const lower = f.name.toLowerCase();
      // Match patterns: shot_1, shot 1, shot01, shot_01, or shot-1
      const patterns = [
        `shot_${shotNum}.`,
        `shot_${shotNum < 10 ? '0' + shotNum : shotNum}.`,
        `shot ${shotNum}.`,
        `shot${shotNum}.`,
        `shot-${shotNum}.`,
        `shot_${shotNum}_`,
        `shot${shotNum < 10 ? '0' + shotNum : shotNum}.`
      ];
      if (patterns.some(p => lower.includes(p))) {
        match = f;
        break;
      }
    }
    
    // If exact name didn't match and there is a 1-to-1 match by sorted position when total files match
    if (!match && driveFiles.length === totalShots) {
      match = driveFiles[i];
    }
    
    if (match) {
      shotData[i][1] = "Present";
      shotData[i][2] = match.name;
      shotData[i][3] = match.id;
      shotData[i][4] = nowIst;
      presentCount++;
      matchedFiles.push({
        shot_number: shotNum,
        filename: match.name,
        file_id: match.id,
        download_url: match.downloadUrl
      });
    } else {
      shotData[i][1] = "Pending";
      shotData[i][2] = "";
      shotData[i][3] = "";
    }
  }
  
  // Write back updated checklist
  sheet.getRange(3, 1, totalShots, 5).setValues(shotData);
  
  // Apply formatting: Green for Present, Amber for Pending
  for (let i = 0; i < totalShots; i++) {
    const row = 3 + i;
    if (shotData[i][1] === "Present") {
      sheet.getRange(row, 2).setBackground("#dcfce7").setFontColor("#15803d");
    } else {
      sheet.getRange(row, 2).setBackground("#fef3c7").setFontColor("#92400e");
    }
  }
  
  const allPresent = (presentCount === totalShots && totalShots > 0);
  Logger.log(`Episode ${episodeNum} Checklist Sync: ${presentCount}/${totalShots} shots Present. All Present: ${allPresent}`);
  
  return {
    episode_number: episodeNum,
    ready: allPresent,
    total_shots: totalShots,
    present_shots: presentCount,
    files: matchedFiles,
    folder_url: folder.getUrl()
  };
}

/**
 * Trashes/deletes all video files from the Episode Google Drive folder.
 */
function cleanEpisodeDrive(episodeNum) {
  const folder = getEpisodeDriveFolder(episodeNum);
  const filesIter = folder.getFiles();
  let deletedCount = 0;
  
  while (filesIter.hasNext()) {
    const f = filesIter.next();
    f.setTrashed(true);
    deletedCount++;
  }
  Logger.log(`Cleaned Google Drive: Trashed ${deletedCount} files from Episode ${episodeNum} folder.`);
  return deletedCount;
}

/**
 * Post-publish cleanup:
 * 1. Deletes videos from Google Drive.
 * 2. Blanks the Google Sheet checklist so future runs won't duplicate.
 * 3. Marks Episode as "Published" in Episode_Ledger.
 */
function cleanupAfterPublish(episodeNum, instagramUrl) {
  Logger.log(`Starting post-publish cleanup for Episode ${episodeNum}...`);
  
  // 1. Delete videos from Google Drive
  const deletedFiles = cleanEpisodeDrive(episodeNum);
  
  // 2. Blank the Google Sheet checklist
  makeChecklistBlank();
  
  // 3. Update Episode_Ledger status to Published
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const ledger = ss.getSheetByName(TAB_LEDGER);
  if (ledger) {
    const data = ledger.getDataRange().getValues();
    const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
    for (let i = 1; i < data.length; i++) {
      if (data[i][0] == episodeNum) {
        ledger.getRange(i + 1, 3).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
        if (instagramUrl) {
          ledger.getRange(i + 1, 6).setValue(instagramUrl);
        }
        ledger.getRange(i + 1, 8).setValue(nowIst);
        break;
      }
    }
  }
  
  return {
    success: true,
    deleted_files: deletedFiles,
    checklist_blanked: true
  };
}

/**
 * Dispatches GitHub Actions workflow when ALL videos are ready.
 */
function dispatchGitHubWorkflow(episodeNum) {
  if (!GITHUB_PAT || GITHUB_PAT === "YOUR_GITHUB_PAT_HERE") {
    Logger.log("ERROR: GITHUB_PAT is not set! Please insert your PAT in Apps Script.");
    return { success: false, message: "GITHUB_PAT missing in Apps Script" };
  }

  const url = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${GITHUB_WORKFLOW}/dispatches`;
  const payload = {
    ref: "main",
    inputs: {
      mode: "hybrid_flow",
      dry_run: false
    }
  };

  const options = {
    method: "post",
    headers: {
      "Authorization": `Bearer ${GITHUB_PAT}`,
      "Accept": "application/vnd.github+json",
      "User-Agent": "SachinAndReenu-Studio"
    },
    contentType: "application/json",
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  const code = response.getResponseCode();
  
  if (code === 204) {
    Logger.log(`Successfully dispatched GitHub workflow for Episode ${episodeNum}!`);
    return { success: true };
  } else {
    Logger.log(`GitHub API error ${code}: ${response.getContentText()}`);
    return { success: false, code: code, details: response.getContentText() };
  }
}

/**
 * Scheduled cron handler: Runs at 12:00 PM IST & 6:00 PM IST.
 * Reads Google Sheet checklist:
 * - If checklist is blank or missing shots -> stops cleanly.
 * - If ALL shots are present -> dispatches GitHub Actions!
 */
function scheduledEpisodeCheckAndTrigger() {
  Logger.log("--- Scheduled 12:00 PM / 6:00 PM Trigger Started ---");
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const ledger = ss.getSheetByName(TAB_LEDGER);
  
  if (!ledger) {
    Logger.log("Episode_Ledger sheet not found. Exiting.");
    return;
  }
  
  const data = ledger.getDataRange().getValues();
  let queuedEp = null;
  let queuedRow = -1;
  
  for (let i = 1; i < data.length; i++) {
    const status = (data[i][2] || "").toString().trim().toLowerCase();
    if (status === "queued" || status === "pending") {
      queuedEp = {
        episode: data[i][0],
        title: data[i][1],
        total_shots: data[i][3] || 22
      };
      queuedRow = i + 1;
      break;
    }
  }

  if (!queuedEp) {
    Logger.log("No queued episode in Episode_Ledger. Checking checklist...");
  }
  
  const currentEp = queuedEp ? queuedEp.episode : 1;
  const status = syncDriveToChecklist(currentEp);
  
  if (!status || status.total_shots === 0) {
    Logger.log("Checklist is blank. No video processing needed. Clean exit.");
    return;
  }
  
  if (status.ready) {
    Logger.log(`🎯 ALL ${status.total_shots}/${status.total_shots} shots are PRESENT! Dispatching GitHub Actions...`);
    if (queuedRow > 0) {
      ledger.getRange(queuedRow, 3).setValue("Processing").setBackground("#dbeafe").setFontColor("#1d4ed8");
    }
    dispatchGitHubWorkflow(currentEp);
  } else {
    Logger.log(`⏳ Incomplete: Only ${status.present_shots} of ${status.total_shots} shots present in Google Drive. Stopping cleanly without running.`);
  }
}

/**
 * Sets up 2 daily triggers: 12:00 PM IST and 6:00 PM IST.
 */
function setupDailyTriggers() {
  const existingTriggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < existingTriggers.length; i++) {
    ScriptApp.deleteTrigger(existingTriggers[i]);
  }

  // 12:00 PM IST (noon)
  ScriptApp.newTrigger("scheduledEpisodeCheckAndTrigger")
    .timeBased()
    .atHour(12)
    .nearMinute(0)
    .everyDays(1)
    .inTimezone("Asia/Kolkata")
    .create();

  // 6:00 PM (18:00) IST
  ScriptApp.newTrigger("scheduledEpisodeCheckAndTrigger")
    .timeBased()
    .atHour(18)
    .nearMinute(0)
    .everyDays(1)
    .inTimezone("Asia/Kolkata")
    .create();

  Logger.log("Configured 2 daily triggers: 12:00 PM IST and 6:00 PM IST!");
}

/**
 * Web App GET endpoint.
 */
function doGet(e) {
  const params = e ? e.parameter : {};
  const action = params.action || "check_status";
  const epNum = parseInt(params.episode || "1", 10);

  if (action === "check_status" || action === "get_checklist") {
    const status = syncDriveToChecklist(epNum);
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      data: status
    })).setMimeType(ContentService.MimeType.JSON);
  }

  if (action === "init_episode") {
    const totalShots = parseInt(params.total_shots || "22", 10);
    const title = params.title || "Episode " + epNum;
    initChecklist(epNum, totalShots, title);
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: `Initialized Episode ${epNum} with ${totalShots} shots`
    })).setMimeType(ContentService.MimeType.JSON);
  }

  return ContentService.createTextOutput(JSON.stringify({ status: "running", app: "Sachin & Reenu Studio Engine" }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Web App POST endpoint.
 */
function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const action = body.action;
    const epNum = parseInt(body.episode_number || "1", 10);

    // 1. Direct upload from Portal
    if (action === "upload_shot") {
      const fileName = body.filename || `shot_${Date.now()}.mp4`;
      const base64Data = body.base64_data;
      
      const folder = getEpisodeDriveFolder(epNum);
      const decodedBytes = Utilities.base64Decode(base64Data);
      const blob = Utilities.newBlob(decodedBytes, "video/mp4", fileName);
      
      const existing = folder.getFilesByName(fileName);
      while (existing.hasNext()) {
        existing.next().setTrashed(true);
      }
      
      const file = folder.createFile(blob);
      file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
      
      // Update checklist
      syncDriveToChecklist(epNum);

      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        filename: fileName,
        file_id: file.getId(),
        download_url: file.getDownloadUrl()
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 2. Post-Publish Cleanup (Delete from Drive & Blank the Sheet)
    if (action === "cleanup_after_publish") {
      const res = cleanupAfterPublish(epNum, body.instagram_url);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 3. Sync checklist
    if (action === "sync_checklist") {
      const res = syncDriveToChecklist(epNum);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 4. Manual workflow trigger
    if (action === "trigger_workflow") {
      const res = dispatchGitHubWorkflow(epNum);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({ error: "Unknown action" }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
