/**
 * ==============================================================================
 * SACHIN & REENU CREATOR STUDIO — GOOGLE APPS SCRIPT ENGINE (3-TAB MASTER)
 * ==============================================================================
 * Dedicated 3-Sheet Architecture:
 * 1. TAB 1: [Episode_Story]
 *    - Base of current and next episode's story, synopsis, and cliffhangers.
 * 2. TAB 2: [Current_JSON_Prompts]
 *    - The exact Google Flow JSON prompts for each shot of the ACTIVE episode.
 *    - Automatically clears previous episode prompts and overwrites with next episode prompts!
 * 3. TAB 3: [Video_Checklist]
 *    - Column A: Shot Number (Shot 1..N)
 *    - Column B: Video Status (Present / Pending)
 *    - Used by GitHub Actions to strictly verify 100% video presence before merge & publish.
 *    - After publish: Trashes raw clips from Drive and resets checklist for next episode.
 * ==============================================================================
 */

// CONFIGURATION
const SPREADSHEET_ID = "1-7AHyFLXXgF1CdOfQPgPFbNelgiufxlsccpahrMG_VI";
const GITHUB_REPO = "YoutubeVideoUploader/sachin-and-reenu-series";
const GITHUB_WORKFLOW = "produce_and_publish.yml";
const GITHUB_PAT = "YOUR_GITHUB_PAT_HERE"; // Insert your GitHub PAT (Repo/Workflow scope)
const DRIVE_ROOT_FOLDER = "Sachin_And_Reenu_Studio";

const TAB_STORY = "Episode_Story";
const TAB_PROMPTS = "Current_JSON_Prompts";
const TAB_CHECKLIST = "Video_Checklist";

/**
 * Automatically gets the active spreadsheet (when opened via Extensions -> Apps Script)
 * or falls back to openById.
 */
function getStudioSpreadsheet() {
  try {
    const active = SpreadsheetApp.getActiveSpreadsheet();
    if (active) return active;
  } catch (e) {}
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

/**
 * Initializes and formats all 3 tabs in Google Sheet.
 */
function setupStudioSpreadsheet() {
  const ss = getStudioSpreadsheet();
  
  // -------------------------------------------------------------
  // 1. SETUP TAB 1: Episode_Story
  // -------------------------------------------------------------
  let storySheet = ss.getSheetByName(TAB_STORY);
  if (!storySheet) {
    storySheet = ss.insertSheet(TAB_STORY, 0);
  }
  
  const storyHeaders = [
    "Episode", 
    "Title", 
    "Status", 
    "Total Shots", 
    "Story Arc / Synopsis", 
    "Cliffhanger", 
    "Instagram URL", 
    "Published At (IST)"
  ];
  
  if (storySheet.getLastRow() === 0) {
    storySheet.appendRow(storyHeaders);
    storySheet.getRange(1, 1, 1, storyHeaders.length)
      .setBackground("#0f172a")
      .setFontColor("#f8fafc")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    storySheet.setFrozenRows(1);
    
    // Episode 1 (Current Active Production)
    storySheet.appendRow([
      1,
      "തിരിച്ചുവരവ് (The Homecoming)",
      "Active",
      22,
      "After two long years apart, Sachin touches down at Kochi CIAL from the UK. Reenu and Amal wait anxiously by the arrival barriers, leading to an overwhelming, heartfelt reunion.",
      "As Sachin holds Reenu close, his mysterious glance toward his travel pouch hints at a hidden secret from London.",
      "",
      ""
    ]);

    // Episode 2 (Next Upcoming Story)
    storySheet.appendRow([
      2,
      "കൊച്ചിയിലെ മഴയും ഒരു രഹസ്യവും (Kochi Rain & A Secret)",
      "Upcoming",
      22,
      "Stepping outside Kochi airport into the sudden monsoon rain, Sachin and Reenu share an umbrella and an intimate car ride, rekindling their unspoken chemistry while Amal playfully navigates the rain-swept streets.",
      "Amal glances in the rear-view mirror as Sachin's fingers brush against Reenu's hand.",
      "",
      ""
    ]);
  }

  // -------------------------------------------------------------
  // 2. SETUP TAB 2: Current_JSON_Prompts
  // -------------------------------------------------------------
  let promptSheet = ss.getSheetByName(TAB_PROMPTS);
  if (!promptSheet) {
    promptSheet = ss.insertSheet(TAB_PROMPTS, 1);
  }
  
  const promptHeaders = [
    "Shot #",
    "Duration",
    "Character",
    "Malayalam Dialogue",
    "Action Summary",
    "Google Flow JSON Prompt (Direct Copy)"
  ];
  
  if (promptSheet.getLastRow() === 0) {
    promptSheet.appendRow(promptHeaders);
    promptSheet.getRange(1, 1, 1, promptHeaders.length)
      .setBackground("#1e1b4b")
      .setFontColor("#e0e7ff")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    promptSheet.setFrozenRows(1);
  }

  // Auto-populate Tab 2 with Episode 1 prompts from GitHub
  try {
    const rawUrl = `https://raw.githubusercontent.com/${GITHUB_REPO}/main/current_episode_shots.json`;
    const res = UrlFetchApp.fetch(rawUrl);
    if (res.getResponseCode() === 200) {
      const epData = JSON.parse(res.getContentText());
      updateJsonPromptsSheet(epData.episode_number || 1, epData.shots || []);
      Logger.log("Tab 2 auto-populated with Episode 1 JSON prompts from GitHub!");
    }
  } catch (err) {
    Logger.log("Notice: Could not auto-fetch prompts from GitHub: " + err);
  }

  // -------------------------------------------------------------
  // 3. SETUP TAB 3: Video_Checklist
  // -------------------------------------------------------------
  let checkSheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!checkSheet) {
    checkSheet = ss.insertSheet(TAB_CHECKLIST, 2);
  }
  
  initVideoChecklist(1, 22, "തിരിച്ചുവരവ് (The Homecoming)");
  Logger.log("All 3 Google Sheet tabs initialized successfully!");
}

/**
 * Initializes or resets Tab 3: Video_Checklist for an episode.
 */
function initVideoChecklist(episodeNum, totalShots, episodeTitle) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_CHECKLIST);
  }
  
  sheet.clear();
  
  // Header Meta
  sheet.getRange(1, 1).setValue(`EPISODE ${episodeNum}: ${episodeTitle || ''}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(`TARGET SHOTS: ${totalShots}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#2563eb").setFontColor("#ffffff");
  
  // Column Headers (Strict 2-Column specification for GitHub Actions)
  sheet.getRange(2, 1).setValue("Shot Number (Column 1)").setFontWeight("bold").setBackground("#0f172a").setFontColor("#ffffff");
  sheet.getRange(2, 2).setValue("Video Status (Column 2)").setFontWeight("bold").setBackground("#0f172a").setFontColor("#ffffff");
  sheet.getRange(2, 3).setValue("Drive File Name").setFontWeight("bold").setBackground("#0f172a").setFontColor("#ffffff");
  sheet.getRange(2, 4).setValue("Drive File ID").setFontWeight("bold").setBackground("#0f172a").setFontColor("#ffffff");
  sheet.getRange(2, 5).setValue("Last Updated (IST)").setFontWeight("bold").setBackground("#0f172a").setFontColor("#ffffff");
  
  const rows = [];
  for (let s = 1; s <= totalShots; s++) {
    rows.push([`Shot ${s}`, "Pending", "", "", ""]);
  }
  
  if (rows.length > 0) {
    sheet.getRange(3, 1, rows.length, 5).setValues(rows);
    sheet.getRange(3, 2, rows.length, 1)
      .setBackground("#fef3c7")
      .setFontColor("#92400e")
      .setHorizontalAlignment("center");
    sheet.getRange(3, 1, rows.length, 1).setHorizontalAlignment("center").setFontWeight("bold");
  }
  
  sheet.setFrozenRows(2);
  Logger.log(`Video_Checklist initialized for Episode ${episodeNum} with ${totalShots} shots.`);
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
 * Scans Google Drive and syncs with Tab 3 (Video_Checklist).
 * Sets Column B to "Present" for uploaded clips.
 */
function syncDriveToChecklist(episodeNum) {
  const ss = getStudioSpreadsheet();
  const sheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!sheet || sheet.getLastRow() < 3) {
    Logger.log("Video_Checklist sheet is blank or uninitialized.");
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
    const shotNum = i + 1;
    let match = null;
    
    for (const f of driveFiles) {
      const lower = f.name.toLowerCase();
      const patterns = [
        `shot_${shotNum}.`,
        `shot_${shotNum < 10 ? '0' + shotNum : shotNum}.`,
        `shot ${shotNum}.`,
        `shot${shotNum}.`,
        `shot-${shotNum}.`,
        `shot_${shotNum}_`
      ];
      if (patterns.some(p => lower.includes(p))) {
        match = f;
        break;
      }
    }
    
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
  
  sheet.getRange(3, 1, totalShots, 5).setValues(shotData);
  
  for (let i = 0; i < totalShots; i++) {
    const row = 3 + i;
    if (shotData[i][1] === "Present") {
      sheet.getRange(row, 2).setBackground("#dcfce7").setFontColor("#15803d");
    } else {
      sheet.getRange(row, 2).setBackground("#fef3c7").setFontColor("#92400e");
    }
  }
  
  const allPresent = (presentCount === totalShots && totalShots > 0);
  Logger.log(`Episode ${episodeNum} Checklist: ${presentCount}/${totalShots} shots Present. All Present: ${allPresent}`);
  
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
 * Overwrites Tab 2: Current_JSON_Prompts with the new episode's prompts.
 * Deletes all previous prompts completely!
 */
function updateJsonPromptsSheet(episodeNum, shots) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_PROMPTS);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_PROMPTS);
  }
  
  // Wipe all existing prompts
  sheet.clear();
  
  // Header Meta
  sheet.getRange(1, 1).setValue(`CURRENT EPISODE PROMPTS: EPISODE ${episodeNum}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(`TOTAL SHOTS: ${shots.length}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#4338ca").setFontColor("#ffffff");

  // Headers
  const headers = [
    "Shot #",
    "Duration",
    "Character",
    "Malayalam Dialogue",
    "Action Summary",
    "Google Flow JSON Prompt (Direct Copy)"
  ];
  sheet.getRange(2, 1, 1, headers.length).setValues([headers])
    .setBackground("#1e1b4b")
    .setFontColor("#e0e7ff")
    .setFontWeight("bold")
    .setHorizontalAlignment("center");
  sheet.setFrozenRows(2);

  const rows = [];
  for (const s of shots) {
    rows.push([
      `Shot #${s.shot_number}`,
      s.duration || "4s",
      s.character || "Reenu",
      s.dialogue_malayalam || "",
      s.action_summary || "",
      typeof s.json_prompt === 'string' ? s.json_prompt : JSON.stringify(s.json_prompt, null, 2)
    ]);
  }

  if (rows.length > 0) {
    sheet.getRange(3, 1, rows.length, headers.length).setValues(rows);
    sheet.getRange(3, 6, rows.length, 1).setFontFamily("Consolas").setFontSize(9);
  }
  
  Logger.log(`Tab 2 [Current_JSON_Prompts] updated for Episode ${episodeNum} with ${shots.length} shots.`);
}

/**
 * Full Next-Episode Transition:
 * 1. Cleans Drive clips of published episode.
 * 2. Marks published episode as "Published" in Tab 1 (Episode_Story).
 * 3. Appends/updates next episode in Tab 1 as "Active".
 * 4. Wipes and writes new prompts into Tab 2 (Current_JSON_Prompts).
 * 5. Resets Tab 3 (Video_Checklist) for Shot 1..N with "Pending".
 */
function handleNextEpisodeFullUpdate(body) {
  const epNum = body.episode_number; // e.g. Episode 2
  const prevEp = epNum - 1;          // e.g. Episode 1
  
  Logger.log(`Handling full transition: Episode ${prevEp} -> Episode ${epNum}`);
  
  // 1. Delete previous clips from Google Drive
  cleanEpisodeDrive(prevEp);
  
  const ss = getStudioSpreadsheet();
  
  // 2. Update Tab 1 (Episode_Story)
  const storySheet = ss.getSheetByName(TAB_STORY);
  if (storySheet) {
    const data = storySheet.getDataRange().getValues();
    const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
    
    // Mark previous as Published
    for (let i = 1; i < data.length; i++) {
      if (data[i][0] == prevEp) {
        storySheet.getRange(i + 1, 3).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
        if (body.instagram_url) storySheet.getRange(i + 1, 7).setValue(body.instagram_url);
        storySheet.getRange(i + 1, 8).setValue(nowIst);
      }
      if (data[i][0] == epNum) {
        storySheet.getRange(i + 1, 3).setValue("Active").setBackground("#dbeafe").setFontColor("#1d4ed8");
      }
    }
  }

  // 3. Overwrite Tab 2 (Current_JSON_Prompts) with new prompts
  if (body.shots && body.shots.length > 0) {
    updateJsonPromptsSheet(epNum, body.shots);
  }

  // 4. Reset Tab 3 (Video_Checklist)
  initVideoChecklist(epNum, body.total_shots || body.shots.length, body.title_malayalam || `Episode ${epNum}`);
  
  return {
    success: true,
    active_episode: epNum,
    message: `Episode ${prevEp} archived and Episode ${epNum} activated across all 3 sheets!`
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
 * Scheduled cron: 12:00 PM IST & 6:00 PM IST.
 * Inspects Tab 3 (Video_Checklist). If all shots present -> dispatches GitHub Actions!
 */
function scheduledEpisodeCheckAndTrigger() {
  Logger.log("--- Scheduled 12:00 PM / 6:00 PM Trigger Started ---");
  const ss = getStudioSpreadsheet();
  const storySheet = ss.getSheetByName(TAB_STORY);
  
  let activeEp = 1;
  if (storySheet) {
    const data = storySheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      const status = (data[i][2] || "").toString().trim().toLowerCase();
      if (status === "active" || status === "queued") {
        activeEp = data[i][0];
        break;
      }
    }
  }

  const status = syncDriveToChecklist(activeEp);
  if (!status || status.total_shots === 0) {
    Logger.log("Tab 3 (Video_Checklist) has 0 shots or is empty. Clean exit.");
    return;
  }
  
  if (status.ready) {
    Logger.log(`🎯 ALL ${status.total_shots}/${status.total_shots} shots are PRESENT in Drive! Dispatching GitHub Actions...`);
    dispatchGitHubWorkflow(activeEp);
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

  // Tab 3: Checklist status
  if (action === "check_status" || action === "get_checklist") {
    const status = syncDriveToChecklist(epNum);
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      data: status
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // Tab 2: Get Current JSON Prompts
  if (action === "get_prompts") {
    const ss = getStudioSpreadsheet();
    const sheet = ss.getSheetByName(TAB_PROMPTS);
    const prompts = [];
    if (sheet && sheet.getLastRow() > 2) {
      const data = sheet.getRange(3, 1, sheet.getLastRow() - 2, 6).getValues();
      for (const row of data) {
        prompts.push({
          shot: row[0],
          duration: row[1],
          character: row[2],
          dialogue: row[3],
          action: row[4],
          json_prompt: row[5]
        });
      }
    }
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      episode: epNum,
      prompts: prompts
    })).setMimeType(ContentService.MimeType.JSON);
  }

  return ContentService.createTextOutput(JSON.stringify({ status: "running", app: "Sachin & Reenu 3-Tab Studio Engine" }))
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
      
      // Update Tab 3
      syncDriveToChecklist(epNum);

      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        filename: fileName,
        file_id: file.getId(),
        download_url: file.getDownloadUrl()
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 2. Full Next-Episode Transition (Update Tab 1, Overwrite Tab 2, Reset Tab 3, Clean Drive)
    if (action === "update_next_episode_full" || action === "cleanup_after_publish") {
      const res = handleNextEpisodeFullUpdate(body);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 3. Sync Tab 3 checklist
    if (action === "sync_checklist") {
      const res = syncDriveToChecklist(epNum);
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
