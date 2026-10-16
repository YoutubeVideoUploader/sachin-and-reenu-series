/**
 * ==============================================================================
 * SACHIN & REENU CREATOR STUDIO — GOOGLE APPS SCRIPT ENGINE (5-TAB MASTER)
 * ==============================================================================
 * Complete 5-Sheet Architecture:
 * 1. TAB 1: [Episode_Story]       -> Active & Upcoming episode story outline & publication history
 * 2. TAB 2: [Current_JSON_Prompts]-> Exact Google Flow JSON prompts for the active episode
 * 3. TAB 3: [Video_Checklist]     -> Drive upload sync & strict pre-check for GitHub Actions
 * 4. TAB 4: [Season_Story_Arc]    -> Overall Season 1..N story arc & 10-episode narrative summaries
 * 5. TAB 5: [Character_Registry]  -> Permanent cast database (Stylized 3D DNA, locked attire, voice)
 * ==============================================================================
 */

// CONFIGURATION
const SPREADSHEET_ID = "1-7AHyFLXXgF1CdOfQPgPFbNelgiufxlsccpahrMG_VI";
const GITHUB_REPO = "YoutubeVideoUploader/sachin-and-reenu-series";
const GITHUB_WORKFLOW = "produce_and_publish.yml";
const GITHUB_PAT = PropertiesService.getScriptProperties().getProperty("GH_PAT") || "";
const DRIVE_ROOT_FOLDER = "Sachin_And_Reenu_Studio";

// ==============================================================================
// 5-TAB MASTER ARCHITECTURE
// ==============================================================================
// 1. TAB 1: [Episode_Story]       -> Master Episode list & statuses (derived from Tab 5)
// 2. TAB 2: [Current_JSON_Prompts]-> Active episode Google Flow JSON prompts (compiled from Tab 4 & 5)
// 3. TAB 3: [Video_Checklist]     -> Drive upload verification & GitHub Actions gate
// 4. TAB 4: [Character_Registry]  -> Permanent cast database & locked season costumes (was Tab 5)
// 5. TAB 5: [Season_Shot_Outline] -> The Core 100-Shot Master Screenplay Engine (was Tab 7)
// ==============================================================================

const TAB_STORY = "Episode_Story";             // Tab 1
const TAB_PROMPTS = "Current_JSON_Prompts";    // Tab 2
const TAB_CHECKLIST = "Video_Checklist";       // Tab 3
const TAB_CHARACTERS = "Character_Registry";   // Tab 4 (formerly Tab 5)
const TAB_SHOT_OUTLINE = "Season_Shot_Outline";// Tab 5 (formerly Tab 7) - CORE ENGINE
const TAB_SEASON_ARC = "Season_Story_Arc";     // Deprecated (Removed in 5-tab system)
const TAB_PAST_PROMPTS = "Past_Episodes_Prompts"; // Deprecated (Removed in 5-tab system)

/**
 * Creates custom studio menu when Google Spreadsheet is opened.
 */
function onOpen() {
  try {
    SpreadsheetApp.getUi()
      .createMenu("🎬 Studio Controls")
      .addItem("🔄 Sync Drive Uploads Now", "menuSyncDrive")
      .addItem("📋 Re-scan Single 'Episode' Folder", "menuSyncDrive")
      .addSeparator()
      .addItem("🧹 Reorganize to Clean 5-Tab Architecture", "reorganizeTo5TabArchitecture")
      .addItem("🎬 Setup 100-Shot Season Outline (Tab 5)", "menuSetupSeasonShotOutline")
      .addItem("⏪ Reset Sheet: Episodes 1-9 Published (Ep 10 Active)", "resetToSeason2Episode9Published")
      .addSeparator()
      .addItem("⚡ Trigger Instagram Assembly via GitHub Actions", "menuTriggerGitHubWorkflow")
      .addToUi();
  } catch (e) {}
}

/**
 * Reorganizes the Google Spreadsheet into the clean 5-Tab Master Architecture:
 * Deletes old Tab 4 (Season_Story_Arc) and old Tab 6 (Past_Episodes_Prompts),
 * arranges remaining 5 tabs in canonical order:
 * 1. Episode_Story
 * 2. Current_JSON_Prompts
 * 3. Video_Checklist
 * 4. Character_Registry
 * 5. Season_Shot_Outline
 */
function reorganizeTo5TabArchitecture() {
  const ss = getStudioSpreadsheet();
  let deletedSheets = [];

  // 1. Delete deprecated old Tab 4 (Season_Story_Arc)
  const arcSheet = ss.getSheetByName(TAB_SEASON_ARC);
  if (arcSheet) {
    try {
      ss.deleteSheet(arcSheet);
      deletedSheets.push(TAB_SEASON_ARC);
    } catch (e) {
      Logger.log("Could not delete TAB_SEASON_ARC: " + e);
    }
  }

  // 2. Delete deprecated old Tab 6 (Past_Episodes_Prompts)
  const pastSheet = ss.getSheetByName(TAB_PAST_PROMPTS);
  if (pastSheet) {
    try {
      ss.deleteSheet(pastSheet);
      deletedSheets.push(TAB_PAST_PROMPTS);
    } catch (e) {
      Logger.log("Could not delete TAB_PAST_PROMPTS: " + e);
    }
  }

  // 3. Ensure the 5 canonical sheets exist
  let storySheet = ss.getSheetByName(TAB_STORY);
  if (!storySheet) storySheet = ss.insertSheet(TAB_STORY);

  let promptSheet = ss.getSheetByName(TAB_PROMPTS);
  if (!promptSheet) promptSheet = ss.insertSheet(TAB_PROMPTS);

  let checkSheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!checkSheet) checkSheet = ss.insertSheet(TAB_CHECKLIST);

  let charSheet = ss.getSheetByName(TAB_CHARACTERS);
  if (!charSheet) charSheet = ss.insertSheet(TAB_CHARACTERS);

  let shotSheet = ss.getSheetByName(TAB_SHOT_OUTLINE);
  if (!shotSheet) shotSheet = ss.insertSheet(TAB_SHOT_OUTLINE);

  // 4. Arrange in tab order 1 to 5
  try {
    ss.setActiveSheet(storySheet);
    ss.moveActiveSheet(1);
    ss.setActiveSheet(promptSheet);
    ss.moveActiveSheet(2);
    ss.setActiveSheet(checkSheet);
    ss.moveActiveSheet(3);
    ss.setActiveSheet(charSheet);
    ss.moveActiveSheet(4);
    ss.setActiveSheet(shotSheet);
    ss.moveActiveSheet(5);
  } catch (e) {
    Logger.log("Tab order reordering note: " + e);
  }

  const msg = `Successfully reorganized to 5-Tab Architecture! Deleted [${deletedSheets.join(", ") || "none"}]. Canonical order: 1: Episode_Story, 2: Current_JSON_Prompts, 3: Video_Checklist, 4: Character_Registry, 5: Season_Shot_Outline.`;
  try {
    SpreadsheetApp.getActiveSpreadsheet().toast(msg, "5-Tab Architecture", 6);
  } catch (e) {}

  return {
    success: true,
    deleted_tabs: deletedSheets,
    tabs: [TAB_STORY, TAB_PROMPTS, TAB_CHECKLIST, TAB_CHARACTERS, TAB_SHOT_OUTLINE],
    message: msg
  };
}

/**
 * One-click menu action to create and format Tab 5 [Season_Shot_Outline].
 */
function menuSetupSeasonShotOutline() {
  setupSeasonShotOutlineSheet(3);
  try {
    SpreadsheetApp.getActiveSpreadsheet().toast(
      "Tab 5 [Season_Shot_Outline] successfully created & formatted!",
      "Success",
      5
    );
  } catch (e) {}
}

/**
 * Resets Tab 1 [Episode_Story] so Episodes 1-9 are Published, Episode 10 is Active,
 * and any rows beyond Row 11 (such as Episodes 11 and 12) are completely deleted.
 */
function resetToSeason2Episode9Published() {
  const ss = getStudioSpreadsheet();
  const storySheet = ss.getSheetByName(TAB_STORY);
  if (!storySheet) return;

  const lastRow = storySheet.getLastRow();
  // 1. Delete rows 12 and beyond (Episode 11, Episode 12, etc.)
  if (lastRow > 11) {
    storySheet.deleteRows(12, lastRow - 11);
  }

  // 2. Mark Episodes 1 to 9 as Published
  for (let r = 2; r <= 10; r++) {
  storySheet.getRange(r, 6).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
  }

  // 3. Mark Episode 10 as Active
  storySheet.getRange(11, 6).setValue("In Progress").setBackground("#dbeafe").setFontColor("#1d4ed8");

  try {
    ss.toast("Sheet reset: Episodes 1-9 Published, Episode 10 Active! Rows 12+ deleted.", "Reset Complete", 5);
  } catch (e) {}
}

/**
 * One-click menu action to remove Episode 7 from Tab [Past_Episodes_Prompts].
 */
function menuDeleteEp7FromPastPrompts() {
  removeEpisodeFromPastPrompts(null, 7);
  try {
    SpreadsheetApp.getActiveSpreadsheet().toast(
      "Episode 7 prompts removed from Past_Episodes_Prompts!",
      "Deleted",
      5
    );
  } catch (e) {}
}

/**
 * One-click menu action to append Tab 2 (Current_JSON_Prompts) into Tab [Past_Episodes_Prompts].
 */
function menuAppendCurrentPrompts() {
  const res = appendCurrentPromptsToPastEpisodes();
  try {
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `Episode ${res.episode_number || ''} prompts successfully appended to ${TAB_PAST_PROMPTS}!`,
      "Archive Saved",
      5
    );
  } catch (e) {}
}

/**
 * One-click menu action to consolidate all Prompts_Ep<N> tabs into Past_Episodes_Prompts and delete old tabs.
 */
function menuMigrateOldPromptsTabs() {
  const res = migrateAllPromptEpSheetsToPastPrompts();
  try {
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `Consolidated ${res.migrated_count || 0} episode tabs into ${TAB_PAST_PROMPTS} and cleaned up old sheets!`,
      "Migration Complete",
      6
    );
  } catch (e) {}
}

/**
 * Legacy wrapper: calls appendCurrentPromptsToPastEpisodes.
 */
function menuArchiveCurrentPrompts() {
  menuAppendCurrentPrompts();
}

/**
 * One-click menu sync for current active episode.
 */
function menuSyncDrive() {
  const ss = getStudioSpreadsheet();
  let epNum = 1;
  const storySheet = ss.getSheetByName(TAB_STORY);
  if (storySheet) {
    const data = storySheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      if (data[i][5] === "In Progress") {
        epNum = parseInt(data[i][0], 10);
        break;
      }
    }
  }
  const result = syncDriveToChecklist(epNum);
  try {
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `Drive Synced: ${result.present_shots} / ${result.total_shots} shots found in 'Episode' folder!`,
      "Sync Complete",
      5
    );
  } catch (e) {}
}

/**
 * One-click menu trigger from inside Google Sheet to run GitHub Actions.
 */
function menuTriggerGitHubWorkflow() {
  const ss = getStudioSpreadsheet();
  let epNum = 1;
  const storySheet = ss.getSheetByName(TAB_STORY);
  if (storySheet) {
    const data = storySheet.getDataRange().getValues();
    for (let i = 1; i < data.length; i++) {
      if (data[i][5] === "In Progress") {
        epNum = parseInt(data[i][0], 10);
        break;
      }
    }
  }

  const result = triggerGitHubWorkflowFromAppsScript({ episode_number: epNum });
  if (result.success) {
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `🚀 GitHub Actions Assembly triggered successfully for Episode ${epNum}!`,
      "Production Started",
      8
    );
  } else {
    SpreadsheetApp.getUi().alert(
      "GitHub Dispatch Notice:\n\n" + (result.message || result.error) + 
      "\n\nMake sure your GH_PAT is set in Script Properties (Key: GH_PAT) or configured in script."
    );
  }
}

/**
 * Gets the active spreadsheet or falls back to openById.
 */
function getStudioSpreadsheet() {
  try {
    const active = SpreadsheetApp.getActiveSpreadsheet();
    if (active) return active;
  } catch (e) {}
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

/**
 * Initializes and formats all 5 tabs in the Google Spreadsheet.
 */
function setupStudioSpreadsheet() {
  const ss = getStudioSpreadsheet();
  
  // -------------------------------------------------------------
  // 1. TAB 1: Episode_Story
  // -------------------------------------------------------------
  let storySheet = ss.getSheetByName(TAB_STORY);
  if (!storySheet) {
    storySheet = ss.insertSheet(TAB_STORY, 0);
  }
  
  const storyHeaders = ["Episode_Number", "Title_English", "Title_Malayalam", "Synopsis", "Cliffhanger", "Status"];
  
  if (storySheet.getLastRow() === 0) {
    storySheet.appendRow(storyHeaders);
    storySheet.getRange(1, 1, 1, storyHeaders.length)
      .setBackground("#0f172a")
      .setFontColor("#f8fafc")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    storySheet.setFrozenRows(1);
    
  }

  // -------------------------------------------------------------
  // 2. TAB 2: Current_JSON_Prompts
  // -------------------------------------------------------------
  let promptSheet = ss.getSheetByName(TAB_PROMPTS);
  if (!promptSheet) {
    promptSheet = ss.insertSheet(TAB_PROMPTS, 1);
  }
  
  const promptHeaders = ["Shot_Number", "Duration", "Character", "Dialogue_Malayalam", "Action_Summary", "JSON_Prompt"];
  
  if (promptSheet.getLastRow() === 0) {
    promptSheet.appendRow(promptHeaders);
    promptSheet.getRange(1, 1, 1, promptHeaders.length)
      .setBackground("#1e1b4b")
      .setFontColor("#e0e7ff")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    promptSheet.setFrozenRows(1);
  }

  // -------------------------------------------------------------
  // 3. TAB 3: Video_Checklist
  // -------------------------------------------------------------
  let checkSheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!checkSheet) {
    checkSheet = ss.insertSheet(TAB_CHECKLIST, 2);
  }

  // -------------------------------------------------------------
  // 4. TAB 4: Character_Registry
  setupCharacterRegistrySheet();
  // 5. TAB 5: Season_Shot_Outline (master source of truth)
  setupSeasonShotOutlineSheet(1);

  Logger.log("All 5 Google Sheet tabs initialized with clean headers!");
}

/**
 * Initializes Tab 4: Season_Story_Arc headers cleanly without hardcoding any episode story.
 */
function setupSeasonStoryArcSheet(seasonNum) {
  // Legacy tab removed by reorganizeTo5TabArchitecture. Never recreate it.
  return { success: true, deprecated: true, canonical_tab: TAB_STORY };
}

/**
 * Initializes Tab 5: Character_Registry with permanent cast database.
 */
function setupCharacterRegistrySheet() {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_CHARACTERS);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_CHARACTERS, 4);
  }

  if (sheet.getLastRow() > 0) return; // Already initialized

  // Meta Banner
  sheet.getRange(1, 1).setValue("SACHIN & REENU: CHARACTER CAST REGISTRY (CHARACTER BIBLE)").setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue("PERSISTENT 3D CARTOON DNA").setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#059669").setFontColor("#ffffff");

  const headers = ["Character_Name", "Role", "3D_Pixar_Visual_DNA", "Locked_Signature_Attire", "Voice_Persona", "First_Appearance"];

  sheet.getRange(2, 1, 1, headers.length).setValues([headers])
    .setBackground("#064e3b")
    .setFontColor("#ecfdf5")
    .setFontWeight("bold")
    .setHorizontalAlignment("center");
  sheet.setFrozenRows(2);

  const initialCharacters = [
    [
      "Reenu",
      "Lead Female",
      "Season 1 • Ep 1",
      "Active",
      "Stylized 3D Pixar-style cartoon animation character, 22yo South Indian Malayali girl, big expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, soft rounded cute cartoon cheeks, sweet warm animated smile, voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, stylized 3D character proportions with smooth vibrant cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES).",
      "Pastel baby-blue and soft yellow cloud-pattern camouflage t-shirt, sky-blue denim skirt, white sneakers, silver wrist watch. Absolutely zero costume variations.",
      "Sweet, expressive 22yo South Indian Malayali female voice, warm, gentle, emotionally vulnerable, clear acoustic studio warmth."
    ],
    [
      "Sachin",
      "Lead Male",
      "Season 1 • Ep 1",
      "Active",
      "Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, endearing boyish cartoon features, large expressive warm animated brown eyes, playful genuine contagious cartoon smile, stylized soft textured wavy dark cartoon hair, cute slightly exaggerated 3D character proportions with smooth cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES).",
      "Forest-green and dark navy-blue check flannel button-down shirt worn open over a plain crisp white crewneck inner t-shirt, dark charcoal denim jeans, brown leather travel cross-bag worn diagonally across chest. Absolutely zero costume variations.",
      "Endearing, slightly nervous young Malayali male voice, warm, playful, sincere, clear studio cadence."
    ],
    [
      "Amal",
      "Best Friend / Comic Anchor",
      "Season 1 • Ep 1",
      "Active",
      "Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, cheerful animated face, lively expressive cartoon eyes, broad energetic friendly cartoon smile, neat stylized short cartoon hairstyle, warm medium brown cartoon skin tone (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES).",
      "Solid mustard-yellow polo t-shirt with brown buttons, slim-fit beige chinos, casual loafers. Absolutely zero costume variations.",
      "Youthful energetic Malayali male voice, friendly, casual, slightly teasing tone, natural cheerful energy."
    ]
  ];

  const registryRows = initialCharacters.map(row => [row[0], row[1], row[4], row[5], row[6], row[2]]);
  sheet.getRange(3, 1, registryRows.length, headers.length).setValues(registryRows);
  sheet.setColumnWidth(3, 450);
  sheet.setColumnWidth(4, 350);
  sheet.setColumnWidth(5, 300);
  Logger.log("Character_Registry sheet initialized with Reenu, Sachin, and Amal.");
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
  
  sheet.getRange(1, 1).setValue(`EPISODE ${episodeNum}: ${episodeTitle || ''}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(`TARGET SHOTS: ${totalShots}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#2563eb").setFontColor("#ffffff");
  
  const checklistHeaders = ["Shot_Number", "Drive_File_ID", "File_Name", "Upload_Status", "Verification_Timestamp"];
  sheet.getRange(2, 1, 1, checklistHeaders.length).setValues([checklistHeaders])
    .setFontWeight("bold").setBackground("#0f172a").setFontColor("#ffffff");
  
  const rows = [];
  for (let s = 1; s <= totalShots; s++) {
    rows.push([`Shot ${s}`, "", "", "Pending", ""]);
  }
  
  if (rows.length > 0) {
    sheet.getRange(3, 1, rows.length, 5).setValues(rows);
    sheet.getRange(3, 4, rows.length, 1)
      .setBackground("#fef3c7")
      .setFontColor("#92400e")
      .setHorizontalAlignment("center");
    sheet.getRange(3, 1, rows.length, 1).setHorizontalAlignment("center").setFontWeight("bold");
  }
  
  sheet.setFrozenRows(2);
  Logger.log(`Video_Checklist initialized for Episode ${episodeNum} with ${totalShots} shots.`);
}

/**
 * Gets the single Google Drive folder 'Episode' for all video uploads.
 * All episode clips are stored in this ONE folder ('Episode').
 * No separate folders are created for each episode.
 */
function getEpisodeDriveFolder(episodeNum) {
  // 1. Search for existing folder named "Episode" anywhere in Drive
  let iter = DriveApp.getFoldersByName("Episode");
  if (iter.hasNext()) {
    return iter.next();
  }
  
  // 2. Check inside DRIVE_ROOT_FOLDER if present
  let rootIter = DriveApp.getFoldersByName(DRIVE_ROOT_FOLDER);
  if (rootIter.hasNext()) {
    let rootFolder = rootIter.next();
    let subIter = rootFolder.getFoldersByName("Episode");
    if (subIter.hasNext()) return subIter.next();
    
    // Fallback: check if legacy Episode_N folder contains files
    if (episodeNum) {
      let legIter = rootFolder.getFoldersByName(`Episode_${episodeNum}`);
      if (legIter.hasNext()) return legIter.next();
    }
    return rootFolder.createFolder("Episode");
  }
  
  // 3. Otherwise create the single "Episode" folder directly in Drive root
  return DriveApp.createFolder("Episode");
}

/**
 * Gets or creates the dedicated Google Drive folder 'Episode_Music' for custom background music.
 */
function getEpisodeMusicDriveFolder() {
  let iter = DriveApp.getFoldersByName("Episode_Music");
  if (iter.hasNext()) {
    return iter.next();
  }
  let rootIter = DriveApp.getFoldersByName(DRIVE_ROOT_FOLDER);
  if (rootIter.hasNext()) {
    let rootFolder = rootIter.next();
    let subIter = rootFolder.getFoldersByName("Episode_Music");
    if (subIter.hasNext()) return subIter.next();
    return rootFolder.createFolder("Episode_Music");
  }
  return DriveApp.createFolder("Episode_Music");
}

/**
 * Lists all audio tracks inside the 'Episode_Music' folder.
 */
function listEpisodeMusicFiles() {
  const folder = getEpisodeMusicDriveFolder();
  const filesIter = folder.getFiles();
  const musicList = [];
  while (filesIter.hasNext()) {
    const file = filesIter.next();
    if (!file.isTrashed()) {
      musicList.push({
        id: file.getId(),
        name: file.getName(),
        size: file.getSize(),
        size_mb: (file.getSize() / (1024 * 1024)).toFixed(2),
        mime_type: file.getMimeType(),
        created_at: file.getDateCreated().toISOString(),
        download_url: file.getDownloadUrl()
      });
    }
  }
  return {
    success: true,
    folder_name: "Episode_Music",
    count: musicList.length,
    files: musicList
  };
}

/**
 * Deletes one or all files from the 'Episode_Music' folder.
 */
function deleteEpisodeMusicFiles(fileId, deleteAll) {
  const folder = getEpisodeMusicDriveFolder();
  let deletedCount = 0;
  if (deleteAll === true || deleteAll === "true") {
    const filesIter = folder.getFiles();
    while (filesIter.hasNext()) {
      const file = filesIter.next();
      file.setTrashed(true);
      deletedCount++;
    }
    return {
      success: true,
      message: `Deleted all (${deletedCount}) music tracks from Episode_Music.`,
      deleted_count: deletedCount
    };
  } else if (fileId) {
    try {
      const file = DriveApp.getFileById(fileId);
      file.setTrashed(true);
      return {
        success: true,
        message: `File ${fileId} moved to trash.`,
        deleted_count: 1
      };
    } catch (e) {
      return {
        success: false,
        error: e.toString()
      };
    }
  }
  return {
    success: false,
    error: "No fileId or deleteAll specified."
  };
}

/**
 * Scans Google Drive 'Episode' folder and syncs with Tab 3 (Video_Checklist).
 * Dynamically detects column headers to support both 5-col and 6-col layouts.
 */
function syncDriveToChecklist(episodeNum) {
  const ss = getStudioSpreadsheet();
  const sheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!sheet || sheet.getLastRow() < 3) {
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
      size: (f.getSize() / (1024 * 1024)).toFixed(2)
    });
  }
  
  const lastRow = sheet.getLastRow();
  const totalShots = lastRow - 2;
  const headerCols = sheet.getLastColumn();
  const headerRow = sheet.getRange(2, 1, 1, headerCols).getValues()[0];
  
  // Dynamic column detection based on header names
  let colStatus = 4;
  let colFileId = 2;
  let colFileName = 3;
  let colTime = 5;
  
  for (let c = 0; c < headerRow.length; c++) {
    const h = String(headerRow[c]).toLowerCase();
    if (h.includes("status")) colStatus = c + 1;
    else if (h.includes("id")) colFileId = c + 1;
    else if (h.includes("file_name") || h.includes("filename") || h.includes("file name")) colFileName = c + 1;
    else if (h.includes("time") || h.includes("updated") || h.includes("date")) colTime = c + 1;
  }
  
  const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
  let presentCount = 0;
  const matchedFiles = [];
  
  for (let i = 0; i < totalShots; i++) {
    const shotNum = i + 1;
    const rowIdx = i + 3;
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
      sheet.getRange(rowIdx, colStatus).setValue("Present").setBackground("#dcfce7").setFontColor("#15803d").setHorizontalAlignment("center").setFontWeight("bold");
      if (colFileId <= headerCols) sheet.getRange(rowIdx, colFileId).setValue(match.id);
      if (colFileName <= headerCols) sheet.getRange(rowIdx, colFileName).setValue(match.name);
      if (colTime <= headerCols) sheet.getRange(rowIdx, colTime).setValue(nowIst);
      presentCount++;
      matchedFiles.push({
        shot_number: shotNum,
        filename: match.name,
        file_id: match.id,
        size: match.size,
        download_url: match.downloadUrl
      });
    } else {
      sheet.getRange(rowIdx, colStatus).setValue("Missing").setBackground("#fee2e2").setFontColor("#991b1b").setHorizontalAlignment("center");
      if (colFileId <= headerCols) sheet.getRange(rowIdx, colFileId).setValue("");
      if (colFileName <= headerCols) sheet.getRange(rowIdx, colFileName).setValue("");
      if (colTime <= headerCols) sheet.getRange(rowIdx, colTime).setValue("");
    }
  }
  
  const allPresent = (presentCount === totalShots && totalShots > 0);
  return {
    episode_number: episodeNum,
    ready: allPresent,
    total_shots: totalShots,
    present_shots: presentCount,
    files: matchedFiles,
    folder_name: "Episode",
    folder_url: folder.getUrl()
  };
}

/**
 * Trashes all video files from an episode Drive folder.
 */
function cleanEpisodeDrive(episodeNum) {
  const folder = getEpisodeDriveFolder(episodeNum);
  const filesIter = folder.getFiles();
  let deletedCount = 0;
  while (filesIter.hasNext()) {
    filesIter.next().setTrashed(true);
    deletedCount++;
  }
  return deletedCount;
}

/**
 * Marks an episode as Published in Tab 1 (Episode_Story) and Tab 4 (Season_Story_Arc),
 * sets its Instagram URL and published timestamp, and activates the next episode.
 */
function markEpisodePublishedInStorySheet(epNum, instagramUrl) {
  const ss = getStudioSpreadsheet();
  const storySheet = ss.getSheetByName(TAB_STORY);
  const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });

  if (storySheet && storySheet.getLastRow() > 1) {
    const data = storySheet.getDataRange().getValues();
    let publishedFound = false;
    let nextEpFound = false;

    for (let i = 1; i < data.length; i++) {
      const rowEp = parseInt(data[i][0], 10);
      if (rowEp === epNum) {
        storySheet.getRange(i + 1, 6).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
        publishedFound = true;
      } else if (rowEp === epNum + 1 && epNum < 10) {
        storySheet.getRange(i + 1, 6).setValue("In Progress").setBackground("#dbeafe").setFontColor("#1d4ed8");
        nextEpFound = true;
      }
    }

    if (!nextEpFound && epNum < 10) {
      storySheet.appendRow([
        epNum + 1,
        `Episode ${epNum + 1}`,
        "",
        "",
        "",
        "In Progress"
      ]);
      const newRow = storySheet.getLastRow();
      storySheet.getRange(newRow, 6).setBackground("#dbeafe").setFontColor("#1d4ed8");
    }
  }

  // Also update Tab 4 (Season_Story_Arc)
  try {
    const seasonSheet = ss.getSheetByName(TAB_SEASON_ARC);
    if (seasonSheet && seasonSheet.getLastRow() >= 3) {
      const sData = seasonSheet.getRange(3, 1, seasonSheet.getLastRow() - 2, 8).getValues();
      for (let r = 0; r < sData.length; r++) {
        const rowEp = parseInt(sData[r][1], 10);
        if (rowEp === epNum) {
          seasonSheet.getRange(r + 3, 5).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
        } else if (rowEp === epNum + 1 && epNum < 10) {
          seasonSheet.getRange(r + 3, 5).setValue("Active").setBackground("#dbeafe").setFontColor("#1d4ed8");
        }
      }
    }
  } catch (err) {
    Logger.log("Notice updating Tab 4 on publish: " + err.toString());
  }

  // Also archive published episode prompts into single master tab [Past_Episodes_Prompts]
  try {
    appendCurrentPromptsToPastEpisodes(epNum);
  } catch (err) {
    Logger.log("Notice archiving prompts on publish: " + err.toString());
  }
}

/**
 * Initializes and styles the single master Tab 6: [Past_Episodes_Prompts] if not already present.
 */
function setupPastEpisodesPromptsSheet(ss) {
  if (!ss) ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_PAST_PROMPTS);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_PAST_PROMPTS);
  }
  if (sheet.getLastRow() === 0) {
    const headers = [
      "Episode #",
      "Shot #",
      "Duration",
      "Character",
      "Malayalam Dialogue",
      "Action Summary",
      "Google Flow JSON Prompt",
      "Archived At (IST)"
    ];
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length)
      .setBackground("#312e81")
      .setFontColor("#e0e7ff")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 85);   // Episode #
    sheet.setColumnWidth(2, 75);   // Shot #
    sheet.setColumnWidth(3, 80);   // Duration
    sheet.setColumnWidth(4, 110);  // Character
    sheet.setColumnWidth(5, 260);  // Malayalam Dialogue
    sheet.setColumnWidth(6, 320);  // Action Summary
    sheet.setColumnWidth(7, 450);  // Google Flow JSON Prompt
    sheet.setColumnWidth(8, 160);  // Archived At (IST)
  }
  return sheet;
}

/**
 * Safely removes existing rows for a specific episode from Tab [Past_Episodes_Prompts] to prevent duplicates.
 */
function removeEpisodeFromPastPrompts(ss, epNum) {
  if (!ss) ss = getStudioSpreadsheet();
  const sheet = ss.getSheetByName(TAB_PAST_PROMPTS);
  if (!sheet || sheet.getLastRow() <= 1) return;
  const lastRow = sheet.getLastRow();
  const data = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (let r = data.length - 1; r >= 0; r--) {
    if (parseInt(data[r][0], 10) === epNum) {
      sheet.deleteRow(r + 2);
    }
  }
}

/**
 * Appends current active prompts from Tab 2: [Current_JSON_Prompts] underneath the existing
 * rows in Tab [Past_Episodes_Prompts]. Ensures strict chronological stacking and no duplicate rows.
 */
function appendCurrentPromptsToPastEpisodes(fallbackEpNum) {
  const ss = getStudioSpreadsheet();
  const promptSheet = ss.getSheetByName(TAB_PROMPTS);
  if (!promptSheet || promptSheet.getLastRow() < 3) {
    return { success: false, message: "No active prompts in Tab 2 to archive." };
  }

  let epNumToArchive = fallbackEpNum;
  if (!epNumToArchive) {
    try {
      const banner = (promptSheet.getRange(1, 1).getValue() || "").toString();
      const m = banner.match(/EPISODE\s+(\d+)/i);
      if (m) epNumToArchive = parseInt(m[1], 10);
    } catch (e) {}
  }

  if (!epNumToArchive) epNumToArchive = 1;

  const pastSheet = setupPastEpisodesPromptsSheet(ss);
  const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });

  // Remove existing rows for this episode if re-archiving, to avoid duplicate shots
  removeEpisodeFromPastPrompts(ss, epNumToArchive);

  const lastRow = promptSheet.getLastRow();
  const lastCol = Math.max(6, promptSheet.getLastColumn());
  const values = promptSheet.getRange(3, 1, lastRow - 2, lastCol).getValues();

  const rowsToAppend = [];
  for (let i = 0; i < values.length; i++) {
    const row = values[i];
    let shotNum = row[0];
    if (typeof shotNum === 'string') {
      const sm = shotNum.match(/\d+/);
      shotNum = sm ? parseInt(sm[0], 10) : (i + 1);
    } else {
      shotNum = parseInt(shotNum, 10) || (i + 1);
    }

    let jsonStr = row[5] || "";
    if (typeof jsonStr === 'object') {
      try { jsonStr = JSON.stringify(jsonStr); } catch (e) {}
    }

    rowsToAppend.push([
      epNumToArchive,
      shotNum,
      row[1] || "6s",
      row[2] || "",
      row[3] || "",
      row[4] || "",
      jsonStr,
      nowIst
    ]);
  }

  if (rowsToAppend.length > 0) {
    const startRow = pastSheet.getLastRow() + 1;
    pastSheet.getRange(startRow, 1, rowsToAppend.length, rowsToAppend[0].length).setValues(rowsToAppend);
  }

  Logger.log(`Successfully appended Episode ${epNumToArchive} (${rowsToAppend.length} shots) to Tab [${TAB_PAST_PROMPTS}]`);
  return {
    success: true,
    episode_number: epNumToArchive,
    shots_appended: rowsToAppend.length,
    tab_name: TAB_PAST_PROMPTS
  };
}

/**
 * Consolidates all legacy Prompts_Ep<N> tabs (e.g. Prompts_Ep3, Prompts_Ep4, Prompts_Ep5, Prompts_Ep6)
 * in chronological order (Ep 3 then 4 then 5 then 6 down to down) into the single master tab
 * [Past_Episodes_Prompts], and DELETES the individual Prompts_Ep tabs.
 */
function migrateAllPromptEpSheetsToPastPrompts() {
  const ss = getStudioSpreadsheet();
  const allSheets = ss.getSheets();
  const epSheets = [];

  for (const s of allSheets) {
    const m = s.getName().match(/^Prompts_Ep(\d+)$/i);
    if (m) {
      epSheets.push({
        sheet: s,
        name: s.getName(),
        epNum: parseInt(m[1], 10)
      });
    }
  }

  if (epSheets.length === 0) {
    Logger.log("No legacy Prompts_Ep<N> tabs found to migrate.");
    return {
      success: true,
      message: "No legacy Prompts_Ep tabs found.",
      migrated_count: 0,
      episodes: []
    };
  }

  // Sort numerically ascending (e.g. Ep 3, Ep 4, Ep 5, Ep 6...)
  epSheets.sort((a, b) => a.epNum - b.epNum);

  const pastSheet = setupPastEpisodesPromptsSheet(ss);
  const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
  let totalRowsMigrated = 0;
  const migratedEps = [];

  for (const item of epSheets) {
    const s = item.sheet;
    const epNum = item.epNum;
    const lastRow = s.getLastRow();

    if (lastRow >= 3) {
      const lastCol = Math.max(6, s.getLastColumn());
      const values = s.getRange(3, 1, lastRow - 2, lastCol).getValues();

      // Clean prior rows for this episode in Past_Episodes_Prompts to avoid duplication
      removeEpisodeFromPastPrompts(ss, epNum);

      const rowsToAppend = [];
      for (let i = 0; i < values.length; i++) {
        const row = values[i];
        let shotNum = row[0];
        if (typeof shotNum === 'string') {
          const sm = shotNum.match(/\d+/);
          shotNum = sm ? parseInt(sm[0], 10) : (i + 1);
        } else {
          shotNum = parseInt(shotNum, 10) || (i + 1);
        }

        let jsonStr = row[5] || "";
        if (typeof jsonStr === 'object') {
          try { jsonStr = JSON.stringify(jsonStr); } catch (e) {}
        }

        rowsToAppend.push([
          epNum,
          shotNum,
          row[1] || "6s",
          row[2] || "",
          row[3] || "",
          row[4] || "",
          jsonStr,
          nowIst
        ]);
      }

      if (rowsToAppend.length > 0) {
        const startRow = pastSheet.getLastRow() + 1;
        pastSheet.getRange(startRow, 1, rowsToAppend.length, rowsToAppend[0].length).setValues(rowsToAppend);
        totalRowsMigrated += rowsToAppend.length;
      }
    }

    migratedEps.push(epNum);
    Logger.log(`Migrated Episode ${epNum} from sheet [${item.name}]. Deleting sheet now.`);
    try {
      ss.deleteSheet(s);
    } catch (err) {
      Logger.log(`Notice deleting sheet [${item.name}]: ${err.toString()}`);
    }
  }

  return {
    success: true,
    message: `Migrated ${migratedEps.length} episode tabs (${totalRowsMigrated} shots) into [${TAB_PAST_PROMPTS}] and deleted old tabs.`,
    migrated_count: migratedEps.length,
    episodes: migratedEps,
    total_shots: totalRowsMigrated
  };
}

/**
 * Backward compatibility alias: appends current prompts to Past_Episodes_Prompts.
 */
function archiveCurrentPromptsSheet(fallbackEpNum) {
  return appendCurrentPromptsToPastEpisodes(fallbackEpNum);
}

/**
 * Overwrites Tab 2: Current_JSON_Prompts with the new episode prompts.
 * Automatically appends previous episode prompts to Tab [Past_Episodes_Prompts] before overwriting.
 */
function updateJsonPromptsSheet(episodeNum, shots) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_PROMPTS);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_PROMPTS);
  }
  
  sheet.clear();
  sheet.getRange(1, 1).setValue(`CURRENT EPISODE PROMPTS: EPISODE ${episodeNum}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(`TOTAL SHOTS: ${shots.length}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#4338ca").setFontColor("#ffffff");

  if (!Array.isArray(shots) || shots.length !== 10) throw new Error("Current_JSON_Prompts must contain exactly 10 shots.");
  const headers = ["Shot_Number", "Duration", "Character", "Dialogue_Malayalam", "Action_Summary", "JSON_Prompt"];
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
      s.duration || "6s",
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
}

/**
 * Reads Tab 4: Season_Story_Arc and returns structured JSON.
 */
/**
 * Updates or overwrites Tab 4: Season_Story_Arc with a complete 10-episode roadmap.
 */
function updateSeasonStoryArcInSheet(seasonNum, seasonTitle, episodes) {
  // Backward-compatible action name; the canonical roadmap lives in Tab 1.
  return updateEpisodeStoryFromOutline(seasonNum, episodes);
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_SEASON_ARC);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_SEASON_ARC);
  }

  sheet.clear();
  sheet.getRange(1, 1).setValue(`MASTER STORY ROADMAP: SEASON ${seasonNum}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(seasonTitle || `Season ${seasonNum}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#312e81").setFontColor("#ffffff");

  const headers = [
    "Season #",
    "Episode #",
    "Title (English)",
    "Title (Malayalam)",
    "Status",
    "Episode Story Summary / Synopsis",
    "Episode Climax / Cliffhanger",
    "Creator Story Suggestion / Notes"
  ];

  sheet.getRange(2, 1, 1, headers.length).setValues([headers])
    .setBackground("#1e1b4b")
    .setFontColor("#e0e7ff")
    .setFontWeight("bold")
    .setHorizontalAlignment("center");
  sheet.setFrozenRows(2);

  const rows = [];
  for (let i = 0; i < episodes.length; i++) {
    const ep = episodes[i];
    rows.push([
      seasonNum || ep.season_number || 1,
      ep.episode_number || (i + 1),
      ep.title_english || `Episode ${i + 1}`,
      ep.title_malayalam || "",
      ep.status || (i === 0 ? "Active" : "Upcoming"),
      ep.synopsis || ep.story_summary || "",
      ep.cliffhanger || "",
      ep.creator_notes || ""
    ]);
  }

  if (rows.length > 0) {
    sheet.getRange(3, 1, rows.length, headers.length).setValues(rows);
    sheet.getRange(3, 5, rows.length, 1).setHorizontalAlignment("center");
  }

  return {
    success: true,
    season_number: seasonNum,
    count: rows.length,
    message: `Updated Season ${seasonNum} arc (${rows.length} episodes) in Tab 4 [Season_Story_Arc]!`
  };
}

/** Tab 1 is a direct projection of the ten episode summaries from Tab 5. */
function updateEpisodeStoryFromOutline(seasonNum, episodes, preserveStatuses) {
  const ss = getStudioSpreadsheet();
  const sheet = ss.getSheetByName(TAB_STORY) || ss.insertSheet(TAB_STORY, 0);
  const headers = ["Episode_Number", "Title_English", "Title_Malayalam", "Synopsis", "Cliffhanger", "Status"];
  const items = Array.isArray(episodes) ? episodes : [];
  if (items.length !== 10) throw new Error(`Episode_Story requires 10 episodes; received ${items.length}.`);
  const priorStatuses = {};
  if (preserveStatuses && sheet.getLastRow() >= 2) {
    sheet.getRange(2, 1, sheet.getLastRow() - 1, Math.min(headers.length, sheet.getLastColumn())).getValues().forEach(row => {
      priorStatuses[Number(row[0])] = row[5] || row[4] || "Draft";
    });
  }
  const rows = items.map((ep, index) => [
    Number(ep.episode_number || index + 1), ep.title_english || `Episode ${index + 1}`,
    ep.title_malayalam || "", ep.synopsis || ep.story_summary || "", ep.cliffhanger || "",
    preserveStatuses ? (priorStatuses[Number(ep.episode_number || index + 1)] || (index === 0 ? "In Progress" : "Draft")) : (index === 0 ? "In Progress" : "Draft")
  ]);
  sheet.clear();
  sheet.getRange(1, 1, 1, headers.length).setValues([headers])
    .setBackground("#1e1b4b").setFontColor("#e0e7ff").setFontWeight("bold");
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(4, 420);
  sheet.setColumnWidth(5, 320);
  return { success: true, season_number: seasonNum, count: rows.length };
}

/**
 * Tab 7: Season_Shot_Outline
 * Manages the 100-shot columnar screenplay outline (10 episodes x 10 shots).
 */
function setupSeasonShotOutlineSheet(seasonNum) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_SHOT_OUTLINE);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_SHOT_OUTLINE);
  }
  if (sheet.getLastRow() > 0) return;

  sheet.getRange(1, 1).setValue(`MASTER 100-SHOT SCREENPLAY OUTLINE: SEASON ${seasonNum || 1}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(`Season ${seasonNum || 1}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#0f766e").setFontColor("#ffffff");

  const headers = ["Global_Shot_ID", "Season_Number", "Episode_Number", "Shot_Number", "Speaker", "Action_Description", "Dialogue_Malayalam", "Location", "Persistent_Props", "Camera_Framing"];

  sheet.getRange(2, 1, 1, headers.length).setValues([headers])
    .setBackground("#134e4a")
    .setFontColor("#ccfbf1")
    .setFontWeight("bold")
    .setHorizontalAlignment("center");
  sheet.setFrozenRows(2);
  sheet.setColumnWidth(4, 250);
  sheet.setColumnWidth(6, 400);
  sheet.setColumnWidth(7, 300);
}

function updateSeasonShotOutlineInSheet(seasonNum, seasonTitle, shots) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_SHOT_OUTLINE);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_SHOT_OUTLINE);
  }

  sheet.clear();
  sheet.getRange(1, 1).setValue(`MASTER 100-SHOT SCREENPLAY OUTLINE: SEASON ${seasonNum || 1}`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue(seasonTitle || `Season ${seasonNum || 1}`).setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#0f766e").setFontColor("#ffffff");

  const headers = ["Global_Shot_ID", "Season_Number", "Episode_Number", "Shot_Number", "Speaker", "Action_Description", "Dialogue_Malayalam", "Location", "Persistent_Props", "Camera_Framing"];

  sheet.getRange(2, 1, 1, headers.length).setValues([headers])
    .setBackground("#134e4a")
    .setFontColor("#ccfbf1")
    .setFontWeight("bold")
    .setHorizontalAlignment("center");
  sheet.setFrozenRows(2);

  const rows = [];
  const shotsList = Array.isArray(shots) ? shots : [];
  if (shotsList.length !== 100) throw new Error(`Season_Shot_Outline requires exactly 100 shots; received ${shotsList.length}.`);
  for (let i = 0; i < shotsList.length; i++) {
    const s = shotsList[i];
    const epNum = s.episode_number || Math.floor(i / 10) + 1;
    const shotNum = s.shot_number || (i % 10) + 1;
    const speaker = s.speaker || "Third-Person Narrator";
    const action = s.action || s.action_summary || "";
    const dialogue = s.dialogue_malayalam || s.dialogue || "";
    const loc = s.location || "";
    const props = Array.isArray(s.persistent_props) ? s.persistent_props.join(", ") : (s.persistent_props || "");
    const camera = s.camera_framing || s.camera_hint || s.camera || "";

    rows.push([
      i + 1,
      seasonNum || 1,
      epNum,
      shotNum,
      speaker,
      action,
      dialogue,
      loc,
      props,
      camera
    ]);
  }

  if (rows.length > 0) {
    sheet.getRange(3, 1, rows.length, headers.length).setValues(rows);
    sheet.setColumnWidth(4, 250);
    sheet.setColumnWidth(6, 400);
    sheet.setColumnWidth(7, 300);
  }

  return {
    success: true,
    season_number: seasonNum,
    count: rows.length,
    message: `Updated ${rows.length} shots in Tab 7 [${TAB_SHOT_OUTLINE}]!`
  };
}

function getSeasonShotOutlineData(seasonNum) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_SHOT_OUTLINE);
  if (!sheet || sheet.getLastRow() < 3) {
    return {
      success: true,
      season_number: seasonNum || 1,
      total_shots: 0,
      shots: []
    };
  }

  const lastRow = sheet.getLastRow();
  const data = sheet.getRange(3, 1, lastRow - 2, 10).getValues();
  const shots = [];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    shots.push({
      global_shot_id: row[0], season_number: row[1], episode_number: row[2], shot_number: row[3],
      speaker: row[4], action: row[5], dialogue_malayalam: row[6], location: row[7],
      persistent_props: typeof row[8] === "string" ? row[8].split(",").map(p => p.trim()).filter(Boolean) : [],
      camera_hint: row[9]
    });
  }

  return {
    success: true,
    season_number: seasonNum || 1,
    total_shots: shots.length,
    shots: shots
  };
}

/**
 * Clean-slate Season Transition:
 * 1. Sheet 1 (Episode_Story): Wiped & populated with all 10 episodes (Ep 1 Active, Ep 2-10 Upcoming, blank URLs).
 * 2. Sheet 4 (Season_Story_Arc): Wiped & populated with the full 10 continuous episodes roadmap.
 * 3. Sheet 2 (Current_JSON_Prompts): Wiped & populated with all 10 long JSON prompts for Episode 1.
 * 4. Sheet 3 (Video_Checklist): UNTOUCHED!
 * 5. Sheet 5 (Character_Registry): Updates existing character attire & registers new recurring characters.
 */
function cleanSlateSeasonTransition(body) {
  const ss = getStudioSpreadsheet();
  const seasonNum = parseInt(body.season_number || "1", 10);
  const seasonTitle = body.season_title || `Season ${seasonNum}`;
  const episodes = body.episodes || body.season_arc || [];
  const outlineShots = body.outline_shots || [];
  const promptShots = body.shots || [];

  if (episodes.length !== 10) throw new Error("Season transition requires exactly ten episode summaries.");
  if (outlineShots.length !== 100) throw new Error(`Season transition requires exactly 100 Tab 5 shots; received ${outlineShots.length}.`);
  if (promptShots.length !== 10) throw new Error(`Season transition requires exactly 10 Episode 1 prompts; received ${promptShots.length}.`);
  for (let i = 0; i < 100; i++) {
    const shot = outlineShots[i];
    if (Number(shot.episode_number) !== Math.floor(i / 10) + 1 || Number(shot.shot_number) !== (i % 10) + 1 || !String(shot.action || "").trim()) {
      throw new Error(`Invalid Tab 5 outline at global shot ${i + 1}.`);
    }
  }
  const registryChanges = [...(body.character_updates || []), ...(body.new_characters || [])];
  for (const character of registryChanges) {
    const attire = character.locked_attire || character.attire || "";
    if (/\b(saree|sari|kurti|dhoti|traditional|ethnic wear)\b/i.test(String(attire))) {
      throw new Error(`Character Registry attire for ${character.name || character.character_name || "a character"} must use modern casual streetwear.`);
    }
  }

  // Validate first, then clear prior season state before any new season data is written.
  reorganizeTo5TabArchitecture();
  [TAB_STORY, TAB_PROMPTS, TAB_SHOT_OUTLINE].forEach(name => {
    const sheet = ss.getSheetByName(name);
    if (sheet) sheet.clear();
  });

  // Required write order: Tab 5, Tab 4, Tab 1, then Tab 2.
  updateSeasonShotOutlineInSheet(seasonNum, seasonTitle, outlineShots);
  const castResult = syncCharacterRegistry({
    season_number: seasonNum,
    character_updates: body.character_updates || [],
    new_characters: body.new_characters || []
  });
  if (!castResult.success) throw new Error("Character Registry update failed.");
  updateEpisodeStoryFromOutline(seasonNum, episodes);
  updateJsonPromptsSheet(1, promptShots);
  resetVideoChecklistForEpisode(1);

  return {
    success: true,
    season_number: seasonNum,
    active_episode: 1,
    message: `Season ${seasonNum} transition completed: cleared Tabs 1, 2, and 5; wrote Tab 5 outline, Tab 4 cast, Tab 1 episodes, and Tab 2 Episode 1 prompts.`
  };
}

function applyDirectorOutlineChange(body) {
  const seasonNum = parseInt(body.season_number || "1", 10);
  const pivot = Number(body.pivot_global_shot_id || 1);
  const shots = body.shots || [];
  const episodes = body.episodes || [];
  const prompts = body.prompts || [];
  const activeEpisode = Number(body.active_episode || 1);
  if (shots.length !== 100 || episodes.length !== 10 || prompts.length !== 10) {
    throw new Error("Director update requires the full 100-shot outline, ten episode records, and ten active-episode prompts.");
  }
  if (pivot < 1 || pivot > 100 || activeEpisode < 1 || activeEpisode > 10) throw new Error("Director pivot or active episode is outside the season.");
  for (let i = 0; i < 100; i++) {
    if (Number(shots[i].episode_number) !== Math.floor(i / 10) + 1 || Number(shots[i].shot_number) !== (i % 10) + 1) {
      throw new Error(`Director update has an invalid Tab 5 position at shot ${i + 1}.`);
    }
  }
  for (let i = 0; i < 10; i++) {
    if (Number(episodes[i].episode_number) !== i + 1 || Number(prompts[i].shot_number) !== i + 1 || !prompts[i].json_prompt) {
      throw new Error(`Director update is missing valid Episode ${activeEpisode} prompt or episode data at item ${i + 1}.`);
    }
  }
  const prior = getSeasonShotOutlineData(seasonNum).shots;
  if (prior.length !== 100) throw new Error("Tab 5 must contain 100 shots before a director edit can be applied.");
  for (let i = 0; i < pivot - 1; i++) {
    if (String(shots[i].action || "") !== String(prior[i].action || "") ||
        String(shots[i].dialogue_malayalam || "") !== String(prior[i].dialogue_malayalam || "") ||
        String(shots[i].location || "") !== String(prior[i].location || "") ||
        String(shots[i].speaker || "") !== String(prior[i].speaker || "") ||
        JSON.stringify(shots[i].persistent_props || []) !== JSON.stringify(prior[i].persistent_props || []) ||
        String(shots[i].camera_hint || "") !== String(prior[i].camera_hint || "")) {
      throw new Error(`Director update attempted to alter frozen shot ${i + 1}.`);
    }
  }
  updateSeasonShotOutlineInSheet(seasonNum, body.season_title || `Season ${seasonNum}`, shots);
  updateEpisodeStoryFromOutline(seasonNum, episodes, true);
  updateJsonPromptsSheet(activeEpisode, prompts);
  return { success: true, season_number: seasonNum, active_episode: activeEpisode, pivot_global_shot_id: pivot, message: `Director changes from shot ${pivot} saved to Tab 5, Tab 1, and Tab 2.` };
}

function applyDirectorSeasonRewrite(body) {
  const seasonNum = parseInt(body.season_number || "1", 10);
  const pivot = Number(body.pivot_global_shot_id || 1);
  const activeEpisode = Number(body.active_episode || 1);
  const shots = body.shots || [];
  const generatedPrompts = body.prompts || [];
  if (shots.length !== 100 || pivot < 1 || pivot > 100 || activeEpisode < 1 || activeEpisode > 10) {
    throw new Error("Season rewrite requires 100 ordered shots, a valid pivot, and an active episode.");
  }
  const prior = getSeasonShotOutlineData(seasonNum).shots;
  if (prior.length !== 100) throw new Error("Tab 5 must contain all 100 shots before a season rewrite.");
  for (let i = 0; i < 100; i++) {
    if (Number(shots[i].episode_number) !== Math.floor(i / 10) + 1 || Number(shots[i].shot_number) !== (i % 10) + 1) {
      throw new Error(`Season rewrite returned an invalid position at Global Shot ${i + 1}.`);
    }
    if (i < pivot - 1) {
      const a = shots[i], b = prior[i];
      if (String(a.action || "") !== String(b.action || "") ||
          String(a.dialogue_malayalam || "") !== String(b.dialogue_malayalam || "") ||
          String(a.location || "") !== String(b.location || "") ||
          String(a.speaker || "") !== String(b.speaker || "") ||
          JSON.stringify(a.persistent_props || []) !== JSON.stringify(b.persistent_props || []) ||
          String(a.camera_hint || "") !== String(b.camera_hint || "")) {
        throw new Error(`Season rewrite changed frozen Global Shot ${i + 1}.`);
      }
    }
  }

  const pivotEpisode = Math.floor((pivot - 1) / 10) + 1;
  const pivotShot = ((pivot - 1) % 10) + 1;
  let finalPrompts = [];
  if (activeEpisode >= pivotEpisode) {
    const firstChangedPrompt = activeEpisode === pivotEpisode ? pivotShot : 1;
    const promptSheet = getStudioSpreadsheet().getSheetByName(TAB_PROMPTS);
    const existingRows = promptSheet && promptSheet.getLastRow() >= 3
      ? promptSheet.getRange(3, 1, Math.min(10, promptSheet.getLastRow() - 2), 6).getValues() : [];
    const priorByNumber = {};
    existingRows.forEach(row => {
      const match = String(row[0] || "").match(/(\d+)/);
      if (!match) return;
      let jsonPrompt = row[5] || "{}";
      try { if (typeof jsonPrompt === "string") jsonPrompt = JSON.parse(jsonPrompt); } catch (e) { throw new Error(`Existing Tab 2 prompt ${match[1]} is invalid JSON.`); }
      priorByNumber[Number(match[1])] = { shot_number: Number(match[1]), duration: row[1] || "6s", character: row[2] || "Reenu", dialogue_malayalam: row[3] || "", action_summary: row[4] || "", json_prompt: jsonPrompt };
    });
    for (let n = 1; n < firstChangedPrompt; n++) {
      if (!priorByNumber[n]) throw new Error(`Cannot preserve Tab 2 Shot ${n}; it is missing from the current prompt sheet.`);
      finalPrompts.push(priorByNumber[n]);
    }
    const expectedGenerated = 11 - firstChangedPrompt;
    if (generatedPrompts.length !== expectedGenerated) throw new Error(`Tab 2 rewrite must contain ${expectedGenerated} prompts from Shot ${firstChangedPrompt} through Shot 10.`);
    generatedPrompts.forEach((prompt, index) => {
      if (Number(prompt.shot_number) !== firstChangedPrompt + index || !prompt.json_prompt) {
        throw new Error(`Tab 2 generated prompt sequence is invalid at Shot ${firstChangedPrompt + index}.`);
      }
      finalPrompts.push(prompt);
    });
  } else if (generatedPrompts.length !== 0) {
    throw new Error("Tab 2 prompts must remain unchanged when the active episode is before the rewrite pivot.");
  }

  updateSeasonShotOutlineInSheet(seasonNum, body.season_title || `Season ${seasonNum}`, shots);
  if (finalPrompts.length) updateJsonPromptsSheet(activeEpisode, finalPrompts);
  return { success: true, season_number: seasonNum, pivot_global_shot_id: pivot, active_episode: activeEpisode,
    message: finalPrompts.length ? `GitHub rewrite saved to Tab 5 from Global Shot ${pivot}; Tab 2 refreshed from Shot ${finalPrompts[0].shot_number}. Tab 1 and Tab 4 were left unchanged.` : `GitHub rewrite saved to Tab 5 from Global Shot ${pivot}. Tab 2 was before the pivot, so it stayed unchanged; Tab 1 and Tab 4 were left unchanged.` };
}

function getSeasonStoryArcData() {
  const ss = getStudioSpreadsheet();
  const sheet = ss.getSheetByName(TAB_STORY);
  if (!sheet || sheet.getLastRow() < 2) return { success: true, season_number: 1, total_episodes: 0, episodes: [] };
  const data = sheet.getRange(2, 1, sheet.getLastRow() - 1, 6).getValues();
  const episodes = [];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    episodes.push({
      episode_number: row[0] || (i + 1),
      title_english: row[1] || `Episode ${i + 1}`,
      title_malayalam: row[2] || "",
      status: row[5] || "Draft",
      synopsis: row[3] || "",
      cliffhanger: row[4] || ""
    });
  }

  let currentSeasonNum = 1;
  let currentSeasonTitle = "Season 1";
  let cellA1Raw = "";
  try {
    const outline = getStudioSpreadsheet().getSheetByName(TAB_SHOT_OUTLINE);
    cellA1Raw = outline ? String(outline.getRange(1, 1).getValue() || "") : "";
    const match = cellA1Raw.match(/SEASON\s*(\d+)/i) || cellA1Raw.match(/(\d+)/);
    if (match) currentSeasonNum = parseInt(match[1], 10);
    currentSeasonTitle = outline ? (outline.getRange(1, 2).getValue() || `Season ${currentSeasonNum}`) : `Season ${currentSeasonNum}`;
  } catch (e) {}

  return {
    success: true,
    season_number: currentSeasonNum,
    season_title: currentSeasonTitle,
    cell_a1: cellA1Raw,
    total_episodes: episodes.length,
    climax_target_episode: 10,
    episodes: episodes
  };
}

/**
 * Reads Tab [Past_Episodes_Prompts] to provide complete multi-episode story and prompt continuity.
 * Returns:
 * - episodes: list of archived episode numbers
 * - episodes_map: object mapping episode number -> shots array
 * - last_shot: full details of the last shot (Shot 10 of targetEp-1, or the latest shot in the sheet)
 * - last_episode_number: the latest completed episode number
 * - timeline_summary: text narrative summary of past shots and story progression
 */
function getPastEpisodesPromptsData(targetEp) {
  const ss = getStudioSpreadsheet();
  const sheet = ss.getSheetByName(TAB_PAST_PROMPTS);
  if (!sheet || sheet.getLastRow() <= 1) {
    return {
      success: true,
      total_shots: 0,
      episodes: [],
      episodes_map: {},
      last_shot: null,
      last_episode_number: 0,
      timeline_summary: "No past episodes archived yet."
    };
  }

  const lastRow = sheet.getLastRow();
  const lastCol = Math.max(8, sheet.getLastColumn());
  const data = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();

  const episodesMap = {};
  const episodesList = [];
  const allShots = [];
  let absoluteLastShot = null;

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    const epNum = parseInt(row[0], 10);
    if (isNaN(epNum)) continue;

    let shotNum = row[1];
    if (typeof shotNum === 'string') {
      const m = shotNum.match(/\d+/);
      shotNum = m ? parseInt(m[0], 10) : (i + 1);
    } else {
      shotNum = parseInt(shotNum, 10) || (i + 1);
    }

    let jsonPrompt = row[6];
    if (typeof jsonPrompt === 'string' && jsonPrompt.trim().startsWith('{')) {
      try {
        jsonPrompt = JSON.parse(jsonPrompt);
      } catch (e) {}
    }

    const shotObj = {
      episode_number: epNum,
      shot_number: shotNum,
      duration: row[2] || "6s",
      character: row[3] || "",
      dialogue_malayalam: row[4] || "",
      action_summary: row[5] || "",
      json_prompt: jsonPrompt,
      archived_at: row[7] || ""
    };

    if (!episodesMap[epNum]) {
      episodesMap[epNum] = [];
      episodesList.push(epNum);
    }
    episodesMap[epNum].push(shotObj);
    allShots.push(shotObj);
    absoluteLastShot = shotObj;
  }

  episodesList.sort((a, b) => a - b);

  // Determine last_shot specifically for targetEp if provided
  let relevantLastShot = absoluteLastShot;
  if (targetEp && targetEp > 1) {
    const prevEp = targetEp - 1;
    if (episodesMap[prevEp] && episodesMap[prevEp].length > 0) {
      const prevShots = episodesMap[prevEp];
      relevantLastShot = prevShots[prevShots.length - 1];
    }
  }

  // Build timeline narrative summary
  const summaryParts = [];
  for (const ep of episodesList) {
    const shots = episodesMap[ep] || [];
    if (shots.length === 0) continue;
    const firstShot = shots[0];
    const lastShotInEp = shots[shots.length - 1];
    let epSummary = `[Episode ${ep} (${shots.length} Shots)]: Begins with: "${firstShot.action_summary}" (${firstShot.character}). Ends with: "${lastShotInEp.action_summary}" (${lastShotInEp.character}) -> Final line: "${lastShotInEp.dialogue_malayalam}"`;
    summaryParts.push(epSummary);
  }

  return {
    success: true,
    total_shots: allShots.length,
    episodes: episodesList,
    episodes_map: episodesMap,
    all_shots: allShots,
    last_shot: relevantLastShot,
    last_episode_number: episodesList.length > 0 ? episodesList[episodesList.length - 1] : 0,
    timeline_summary: summaryParts.join("\n")
  };
}

/**
 * Reads archived prompts from Tab [Past_Episodes_Prompts], or legacy Prompts_Ep<N> / TAB_PROMPTS.
 */
function getArchivedEpisodePrompts(epNum) {
  const ss = getStudioSpreadsheet();

  // 1. Check Tab [Past_Episodes_Prompts] first
  const pastSheet = ss.getSheetByName(TAB_PAST_PROMPTS);
  if (pastSheet && pastSheet.getLastRow() > 1) {
    const lastRow = pastSheet.getLastRow();
    const data = pastSheet.getRange(2, 1, lastRow - 1, 8).getValues();
    const matchingShots = [];
    for (let i = 0; i < data.length; i++) {
      const row = data[i];
      if (parseInt(row[0], 10) === epNum) {
        let promptJson = row[6];
        if (typeof promptJson === 'string' && promptJson.trim().startsWith('{')) {
          try {
            promptJson = JSON.parse(promptJson);
          } catch (e) {}
        }
        let shotNum = row[1];
        if (typeof shotNum === 'string') {
          const m = shotNum.match(/\d+/);
          shotNum = m ? parseInt(m[0], 10) : (matchingShots.length + 1);
        }
        matchingShots.push({
          shot_number: shotNum,
          duration: row[2] || "6s",
          character: row[3] || "",
          dialogue_malayalam: row[4] || "",
          action_summary: row[5] || "",
          json_prompt: promptJson
        });
      }
    }
    if (matchingShots.length > 0) {
      return {
        success: true,
        episode_number: epNum,
        tab_name: TAB_PAST_PROMPTS,
        total_shots: matchingShots.length,
        shots: matchingShots
      };
    }
  }

  // 2. Fallback to legacy Prompts_Ep<N> or Tab 2
  const archiveTabName = `Prompts_Ep${epNum}`;
  let sheet = ss.getSheetByName(archiveTabName);
  if (!sheet) {
    sheet = ss.getSheetByName(TAB_PROMPTS);
  }
  if (!sheet || sheet.getLastRow() < 3) {
    return {
      success: false,
      episode_number: epNum,
      message: `No archived prompts found for Episode ${epNum}`
    };
  }

  const lastRow = sheet.getLastRow();
  const data = sheet.getRange(3, 1, lastRow - 2, 6).getValues();
  const shots = [];
  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    let promptJson = row[5];
    if (typeof promptJson === 'string') {
      try {
        promptJson = JSON.parse(promptJson);
      } catch (e) {}
    }
    shots.push({
      shot_number: i + 1,
      duration: row[1] || "6s",
      character: row[2] || "",
      dialogue_malayalam: row[3] || "",
      action_summary: row[4] || "",
      json_prompt: promptJson
    });
  }

  return {
    success: true,
    episode_number: epNum,
    tab_name: sheet.getName(),
    total_shots: shots.length,
    shots: shots
  };
}

/**
 * Reads Tab 5: Character_Registry and returns structured JSON.
 */
function getCharacterRegistryData() {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_CHARACTERS);
  if (!sheet || sheet.getLastRow() < 3) {
    setupCharacterRegistrySheet();
    sheet = ss.getSheetByName(TAB_CHARACTERS);
  }

  // Migrate legacy seven-column rows lazily without creating a second sheet.
  if (sheet.getLastColumn() >= 7 && sheet.getLastRow() >= 3) {
    const legacyRows = sheet.getRange(3, 1, sheet.getLastRow() - 2, 7).getValues();
    const migratedRows = legacyRows.map(row => String(row[3]).toLowerCase() === "active"
      ? [row[0], row[1], row[4], row[5], row[6], row[2]]
      : row.slice(0, 6));
    sheet.getRange(2, 1, 1, 6).setValues([["Character_Name", "Role", "3D_Pixar_Visual_DNA", "Locked_Signature_Attire", "Voice_Persona", "First_Appearance"]]);
    sheet.getRange(3, 1, migratedRows.length, 6).setValues(migratedRows);
    sheet.getRange(1, 7, sheet.getMaxRows(), 1).clearContent();
  }

  const data = sheet.getRange(3, 1, sheet.getLastRow() - 2, 6).getValues();
  const characters = [];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    characters.push({
      name: row[0],
      role: row[1],
      visual_dna: row[2],
      locked_attire: row[3],
      voice_persona: row[4],
      first_appearance: row[5]
    });
  }

  return {
    success: true,
    total_characters: characters.length,
    characters: characters
  };
}

function syncCharacterRegistry(body) {
  const validateAttire = attire => {
    if (/\b(saree|sari|kurti|dhoti|traditional|ethnic wear)\b/i.test(String(attire || ""))) {
      throw new Error("Character Registry attire must use modern casual streetwear.");
    }
    return attire;
  };
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_CHARACTERS);
  if (!sheet) {
    setupCharacterRegistrySheet();
    sheet = ss.getSheetByName(TAB_CHARACTERS);
  }
  getCharacterRegistryData();
  const rows = sheet.getLastRow() >= 3 ? sheet.getRange(3, 1, sheet.getLastRow() - 2, 6).getValues() : [];
  const byName = new Map(rows.map((row, idx) => [String(row[0]).toLowerCase(), idx + 3]));
  for (const update of (body.character_updates || [])) {
    const row = byName.get(String(update.name || update.character_name || "").toLowerCase());
    if (!row) continue;
    if (update.role) sheet.getRange(row, 2).setValue(update.role);
    if (update.visual_dna) sheet.getRange(row, 3).setValue(update.visual_dna);
    if (update.attire || update.locked_attire) sheet.getRange(row, 4).setValue(validateAttire(update.attire || update.locked_attire));
    if (update.voice_persona) sheet.getRange(row, 5).setValue(update.voice_persona);
  }
  for (const character of (body.new_characters || [])) {
    const name = String(character.name || character.character_name || "").trim();
    if (!name || byName.has(name.toLowerCase())) continue;
    const attire = validateAttire(character.locked_attire || character.attire || "Modern casual streetwear, locked for season continuity.");
    sheet.appendRow([
      name, character.role || "Supporting Character",
      character.visual_dna || "Stylized 3D Pixar animated character; no realistic human skin texture.",
      attire,
      character.voice_persona || "Malayalam voice persona",
      `Season ${body.season_number || 1}, Episode 1`
    ]);
    byName.set(name.toLowerCase(), sheet.getLastRow());
  }
  return { success: true, total_characters: sheet.getLastRow() - 2 };
}

/**
 * Records a creator story pitch / suggestion into Tab 4.
 */
function recordCreatorStoryIdea(epNum, idea) {
  const key = `CREATOR_STORY_IDEAS_${epNum || "GENERAL"}`;
  const props = PropertiesService.getScriptProperties();
  const prior = JSON.parse(props.getProperty(key) || "[]");
  prior.push({ idea: String(idea || ""), recorded_at: new Date().toISOString() });
  props.setProperty(key, JSON.stringify(prior.slice(-50)));
  return { success: true, message: `Story idea recorded for Episode ${epNum || "General"}.` };
}

/**
 * Full Next-Episode Transition.
 */
function handleNextEpisodeFullUpdate(body) {
  const epNum = body.episode_number || 1;
  const prevEp = epNum - 1;
  const isNewSeason = (body.is_new_season === true || body.is_new_season === "true" || (body.season_number && body.season_number > 1 && epNum === 1));
  const seasonNum = body.season_number || (isNewSeason ? 2 : 1);
  
  const ss = getStudioSpreadsheet();
  const storySheet = ss.getSheetByName(TAB_STORY);
  if (storySheet) {
    if (isNewSeason) {
      updateEpisodeStoryFromOutline(seasonNum, body.season_arc || body.episodes || []);
    } else {
      // Regular mid-season episode update
      const data = storySheet.getDataRange().getValues();
      const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
      let epRowFound = false;
      
      for (let i = 1; i < data.length; i++) {
        const rowEp = parseInt(data[i][0], 10);
        if (prevEp > 0 && rowEp <= prevEp) {
          storySheet.getRange(i + 1, 6).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
        }
        if (rowEp === epNum) {
          storySheet.getRange(i + 1, 6).setValue("In Progress").setBackground("#dbeafe").setFontColor("#1d4ed8");
          if (body.title_english) storySheet.getRange(i + 1, 2).setValue(body.title_english);
          if (body.title_malayalam) storySheet.getRange(i + 1, 3).setValue(body.title_malayalam);
          if (body.synopsis) storySheet.getRange(i + 1, 4).setValue(body.synopsis);
          if (body.cliffhanger) storySheet.getRange(i + 1, 5).setValue(body.cliffhanger);
          epRowFound = true;
        }
        if (rowEp > epNum) {
          storySheet.getRange(i + 1, 6).setValue("Draft").setBackground("#fef3c7").setFontColor("#92400e");
        }
      }

      if (!epRowFound) {
        storySheet.appendRow([
          epNum,
          body.title_english || `Episode ${epNum}`,
          body.title_malayalam || "",
          body.synopsis || "",
          body.cliffhanger || "",
          "In Progress"
        ]);
        const newRow = storySheet.getLastRow();
        storySheet.getRange(newRow, 6).setBackground("#dbeafe").setFontColor("#1d4ed8");
      }
    }
  }

  // 2. Overwrite Tab 2: Current_JSON_Prompts
  if (body.shots && Array.isArray(body.shots) && body.shots.length > 0) {
    updateJsonPromptsSheet(epNum, body.shots);
  }

  // 3. Reset Tab 3: Video_Checklist (ONLY if not a new season transition; Sheet 3 must remain untouched on season reset)
  if (!isNewSeason) {
    const totalShots = body.total_shots || (body.shots && body.shots.length ? body.shots.length : 10);
    initVideoChecklist(epNum, totalShots, body.title_malayalam || `Episode ${epNum}`);
  }
  
  // 4. Update Tab 4: Season_Story_Arc
  try {
    let seasonSheet = ss.getSheetByName(TAB_SEASON_ARC);
    if (!seasonSheet) {
      setupSeasonStoryArcSheet(seasonNum);
      seasonSheet = ss.getSheetByName(TAB_SEASON_ARC);
    }
    
    // If full season roadmap is provided, update all 10 episodes in Tab 4
    const roadmapEpisodes = body.season_arc || body.episodes;
    if (roadmapEpisodes && Array.isArray(roadmapEpisodes) && roadmapEpisodes.length > 0) {
      updateSeasonStoryArcInSheet(seasonNum, body.season_title, roadmapEpisodes);
    } else if (seasonSheet && seasonSheet.getLastRow() >= 3) {
      // Remove any Episode 11+ rows from Tab 4
      const lastArcRow = seasonSheet.getLastRow();
      if (lastArcRow > 12) {
        seasonSheet.deleteRows(13, lastArcRow - 12);
      }
      const sData = seasonSheet.getRange(3, 1, Math.min(10, seasonSheet.getLastRow() - 2), 8).getValues();
      let arcFound = false;
      for (let r = 0; r < sData.length; r++) {
        if (sData[r][1] == epNum) {
          if (body.title_english) seasonSheet.getRange(r + 3, 3).setValue(body.title_english);
          if (body.title_malayalam) seasonSheet.getRange(r + 3, 4).setValue(body.title_malayalam);
          seasonSheet.getRange(r + 3, 5).setValue("Active").setBackground("#dcfce7").setFontColor("#15803d");
          if (body.synopsis) seasonSheet.getRange(r + 3, 6).setValue(body.synopsis);
          if (body.cliffhanger) seasonSheet.getRange(r + 3, 7).setValue(body.cliffhanger);
          arcFound = true;
          break;
        }
      }
    }
  } catch (arcErr) {
    Logger.log("Error updating Season_Story_Arc: " + arcErr.toString());
  }

  // 5. Update Tab 5: Character_Registry if new characters are introduced
  try {
    if (body.new_characters_introduced && Array.isArray(body.new_characters_introduced) && body.new_characters_introduced.length > 0) {
      let charSheet = ss.getSheetByName(TAB_CHARACTERS);
      if (!charSheet) {
        setupCharacterRegistrySheet();
        charSheet = ss.getSheetByName(TAB_CHARACTERS);
      }
      const existingNames = [];
      if (charSheet.getLastRow() >= 3) {
        const namesData = charSheet.getRange(3, 1, charSheet.getLastRow() - 2, 1).getValues();
        namesData.forEach(row => existingNames.push((row[0] || "").toString().toLowerCase().trim()));
      }
      for (const nc of body.new_characters_introduced) {
        const cName = (nc.name || "").trim();
        if (cName && !existingNames.includes(cName.toLowerCase())) {
          charSheet.appendRow([
            cName,
            nc.role || "Supporting Character",
            `Season ${seasonNum} • Ep ${epNum}`,
            "Active",
            nc.visual_dna || "Stylized 3D Pixar cartoon character (Strictly non-human realism)",
            nc.locked_attire || "Locked signature costume (100% consistent across shots)",
            nc.voice_persona || "Malayalam voice"
          ]);
          const newRowIdx = charSheet.getLastRow();
          charSheet.getRange(newRowIdx, 4).setBackground("#dcfce7").setFontColor("#15803d").setFontWeight("bold");
          existingNames.push(cName.toLowerCase());
          Logger.log(`Added new character: ${cName} to Character_Registry`);
        }
      }
    }
  } catch (charErr) {
    Logger.log("Error updating Character_Registry: " + charErr.toString());
  }

  // 6. Synchronize Tab 7: Season_Shot_Outline for active episode shots
  try {
    const outlineSheet = ss.getSheetByName(TAB_SHOT_OUTLINE);
    if (outlineSheet && outlineSheet.getLastRow() >= 3 && body.shots && Array.isArray(body.shots)) {
      for (let sIdx = 0; sIdx < body.shots.length; sIdx++) {
        const s = body.shots[sIdx];
        const sNum = s.shot_number || (sIdx + 1);
        const targetRow = 3 + (epNum - 1) * 10 + (sNum - 1);
        if (targetRow <= outlineSheet.getLastRow()) {
          if (s.character) outlineSheet.getRange(targetRow, 5).setValue(s.character);
          if (s.action_summary) outlineSheet.getRange(targetRow, 6).setValue(s.action_summary);
          if (s.dialogue_malayalam) outlineSheet.getRange(targetRow, 7).setValue(s.dialogue_malayalam);
          if (s.camera_hint) outlineSheet.getRange(targetRow, 10).setValue(s.camera_hint);
        }
      }
      Logger.log(`Synchronized Episode ${epNum} (${body.shots.length} shots) to Tab 7 [${TAB_SHOT_OUTLINE}]`);
    }
  } catch (outErr) {
    Logger.log("Error synchronizing Tab 7: " + outErr.toString());
  }


  // Auto-scan single 'Episode' Drive folder immediately
  try {
    syncDriveToChecklist(epNum);
  } catch (syncErr) {
    Logger.log("Notice auto-syncing Drive: " + syncErr.toString());
  }

  return {
    success: true,
    season_number: seasonNum,
    episode_number: epNum,
    active_episode: epNum,
    message: isNewSeason ? `Season ${seasonNum} cleanly initialized! Tab 1 URLs cleared, Tab 4 updated.` : `Episode ${epNum} activated across all 5 sheets!`
  };
}

/**
 * Web App GET endpoint.
 */
function doGet(e) {
  const params = (e && e.parameter) || {};
  const action = (params.action || "get_prompts").toLowerCase();
  const epNum = parseInt(params.episode || "1", 10);

  // Tab 3 Checklist (used by GitHub Actions)
  if (action === "check_status" || action === "get_checklist") {
    const status = syncDriveToChecklist(epNum);
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      data: status
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // Episode Music Management
  if (action === "list_episode_music" || action === "get_episode_music") {
    const res = listEpisodeMusicFiles();
    return ContentService.createTextOutput(JSON.stringify(res))
      .setMimeType(ContentService.MimeType.JSON);
  }

  if (action === "delete_episode_music") {
    const res = deleteEpisodeMusicFiles(params.file_id, params.delete_all);
    return ContentService.createTextOutput(JSON.stringify(res))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Tab 4: Season Story Arc
  if (action === "get_season_story" || action === "season_story") {
    const data = getSeasonStoryArcData();
    return ContentService.createTextOutput(JSON.stringify(data))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Tab 5: Character Registry
  if (action === "get_characters" || action === "characters") {
    const data = getCharacterRegistryData();
    return ContentService.createTextOutput(JSON.stringify(data))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Tab 6: Master Past Episodes Prompts & Multi-Episode Continuity
  if (action === "get_past_prompts" || action === "get_past_episodes_prompts" || action === "past_prompts") {
    const targetEp = params.episode ? parseInt(params.episode, 10) : (epNum > 1 ? (epNum - 1) : 1);
    const data = getPastEpisodesPromptsData(targetEp);
    return ContentService.createTextOutput(JSON.stringify(data))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Remove specific episode from Past_Episodes_Prompts via GET
  if (action === "delete_from_past_prompts" || action === "remove_past_episode") {
    const targetEp = parseInt(params.episode || params.ep || "7", 10);
    removeEpisodeFromPastPrompts(null, targetEp);
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: `Episode ${targetEp} removed from Past_Episodes_Prompts.`
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // Migrate legacy Prompts_Ep tabs into Past_Episodes_Prompts via GET
  if (action === "migrate_to_past_episodes" || action === "migrate_old_tabs") {
    const res = migrateAllPromptEpSheetsToPastPrompts();
    return ContentService.createTextOutput(JSON.stringify(res))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Archived & Previous Episode Prompts for Sequence Continuity
  if (action === "get_previous_prompts" || action === "get_archived_prompts" || action === "get_episode_prompts") {
    const targetEp = parseInt(params.episode || params.ep || (epNum > 1 ? (epNum - 1) : 1), 10);
    const data = getArchivedEpisodePrompts(targetEp);
    return ContentService.createTextOutput(JSON.stringify(data))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Creator Story Idea Submission via GET
  if (action === "suggest_story_idea") {
    const idea = params.idea || "";
    const targetEp = parseInt(params.target_episode || "0", 10);
    const result = recordCreatorStoryIdea(targetEp, idea);
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Tab 7: Master Season Shot Outline (100 shots)
  if (action === "get_season_shot_outline" || action === "get_100_shots" || action === "shot_outline") {
    const targetSeason = parseInt(params.season || "1", 10);
    const data = getSeasonShotOutlineData(targetSeason);
    return ContentService.createTextOutput(JSON.stringify(data))
      .setMimeType(ContentService.MimeType.JSON);
  }

  if (action === "get_current_episode_prompts") {
    const sheet = getStudioSpreadsheet().getSheetByName(TAB_PROMPTS);
    const rows = sheet && sheet.getLastRow() >= 3
      ? sheet.getRange(3, 1, Math.min(10, sheet.getLastRow() - 2), 6).getValues() : [];
    const shots = rows.map(row => {
      const match = String(row[0] || "").match(/(\d+)/);
      let jsonPrompt = row[5] || "{}";
      try { if (typeof jsonPrompt === "string") jsonPrompt = JSON.parse(jsonPrompt); } catch (e) {}
      return match ? { shot_number: Number(match[1]), duration: row[1] || "6s", character: row[2] || "Reenu",
        dialogue_malayalam: row[3] || "", action_summary: row[4] || "", json_prompt: jsonPrompt } : null;
    }).filter(Boolean);
    return ContentService.createTextOutput(JSON.stringify({ success: true, shots }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Get Series Thumbnail details
  if (action === "get_series_thumbnail" || action === "thumbnail") {
    const thumbData = getSeriesThumbnailData();
    return ContentService.createTextOutput(JSON.stringify(thumbData))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // Pull episode from GitHub
  if (action === "sync_from_github") {
    try {
      const rawUrl = `https://raw.githubusercontent.com/${GITHUB_REPO}/main/current_episode_shots.json?_t=${Date.now()}`;
      const res = UrlFetchApp.fetch(rawUrl);
      if (res.getResponseCode() === 200) {
        const epData = JSON.parse(res.getContentText());
        const updateRes = handleNextEpisodeFullUpdate(epData);
        return ContentService.createTextOutput(JSON.stringify({
          success: true,
          message: `Episode ${epData.episode_number} synced from GitHub!`,
          details: updateRes
        })).setMimeType(ContentService.MimeType.JSON);
      }
    } catch (err) {
      return ContentService.createTextOutput(JSON.stringify({ success: false, error: err.toString() }))
        .setMimeType(ContentService.MimeType.JSON);
    }
  }

  // Cleanup after Instagram publish via GET
  if (action === "cleanup_after_publish") {
    cleanEpisodeDrive(epNum);
    markEpisodePublishedInStorySheet(epNum, params.instagram_url || "");
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: `Episode ${epNum} Drive files trashed and marked Published in Sheet.`
    })).setMimeType(ContentService.MimeType.JSON);
  }

  // DEFAULT MASTER CALL: Returns Active Episode Prompts + Season Arc + Character Registry
  const ss = getStudioSpreadsheet();
  let storySheet = ss.getSheetByName(TAB_STORY);
  let promptSheet = ss.getSheetByName(TAB_PROMPTS);

  if (!storySheet || !promptSheet || promptSheet.getLastRow() <= 2) {
    try {
      setupStudioSpreadsheet();
      storySheet = ss.getSheetByName(TAB_STORY);
      promptSheet = ss.getSheetByName(TAB_PROMPTS);
    } catch (err) {}
  }

  let activeEp = 1;
  let epTitleEn = "Episode 1";
  let epTitleMl = "";
  let epSynopsis = "";

  if (storySheet && storySheet.getLastRow() > 1) {
    const storyData = storySheet.getDataRange().getValues();
    for (let i = 1; i < storyData.length; i++) {
      const st = (storyData[i][5] || "").toString().trim().toLowerCase();
      if (st === "in progress") {
        activeEp = storyData[i][0];
        epTitleEn = storyData[i][1] || epTitleEn;
        epTitleMl = storyData[i][2] || "";
        epSynopsis = storyData[i][3] || epSynopsis;
        break;
      }
    }
  }

  const shots = [];
  if (promptSheet && promptSheet.getLastRow() > 2) {
    const pData = promptSheet.getRange(3, 1, promptSheet.getLastRow() - 2, 6).getValues();
    for (let i = 0; i < pData.length; i++) {
      const row = pData[i];
      let parsedJson = null;
      try {
        parsedJson = typeof row[5] === 'string' ? JSON.parse(row[5]) : row[5];
      } catch(e) {
        parsedJson = row[5];
      }
      shots.push({
        shot_number: i + 1,
        shot: `Shot #${i + 1}`,
        duration: row[1] || "6s",
        character: row[2] || "Reenu",
        dialogue_malayalam: row[3] || "",
        dialogue: row[3] || "",
        action_summary: row[4] || "",
        action: row[4] || "",
        json_prompt: parsedJson
      });
    }
  }

  const seasonData = getSeasonStoryArcData();
  const characterData = getCharacterRegistryData();

  const response = {
    success: true,
    episode: activeEp,
    episode_number: activeEp,
    title_english: epTitleEn,
    title_malayalam: epTitleMl,
    synopsis: epSynopsis,
    total_shots: shots.length,
    shots: shots,
    prompts: shots,
    season_story: seasonData,
    characters: characterData.characters
  };

  return ContentService.createTextOutput(JSON.stringify(response, null, 2))
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
      syncDriveToChecklist(epNum);

      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        filename: fileName,
        file_id: file.getId(),
        download_url: file.getDownloadUrl()
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 1b. Episode Music Upload
    if (action === "upload_episode_music") {
      const fileName = body.filename || `music_${Date.now()}.mp3`;
      const base64Data = body.base64_data;
      const mimeType = body.mime_type || "audio/mpeg";
      const folder = getEpisodeMusicDriveFolder();
      const decodedBytes = Utilities.base64Decode(base64Data);
      const blob = Utilities.newBlob(decodedBytes, mimeType, fileName);

      // Overwrite if same file name already exists in Episode_Music
      const existing = folder.getFilesByName(fileName);
      while (existing.hasNext()) {
        existing.next().setTrashed(true);
      }

      const file = folder.createFile(blob);
      file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        filename: fileName,
        file_id: file.getId(),
        download_url: file.getDownloadUrl()
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 1c. Episode Music Delete
    if (action === "delete_episode_music") {
      const res = deleteEpisodeMusicFiles(body.file_id, body.delete_all);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 1d. Episode Music List via POST
    if (action === "list_episode_music") {
      const res = listEpisodeMusicFiles();
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 2. Creator Story Idea Submission
    if (action === "suggest_story_idea") {
      const res = recordCreatorStoryIdea(body.target_episode, body.idea);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // Clean-slate Season Transition (Sheets 1, 4, 2 updated, Sheet 3 untouched, Sheet 5 updated)
    if (action === "clean_slate_season_transition") {
      const res = cleanSlateSeasonTransition(body);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 3. Full Next-Episode Transition
    if (action === "update_next_episode_full") {
      if (body.is_new_season === true || body.is_new_season === "true") {
        const res = cleanSlateSeasonTransition(body);
        return ContentService.createTextOutput(JSON.stringify(res))
          .setMimeType(ContentService.MimeType.JSON);
      }
      const res = handleNextEpisodeFullUpdate(body);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 4. Cleanup after publish
    if (action === "cleanup_after_publish") {
      cleanEpisodeDrive(epNum);
      markEpisodePublishedInStorySheet(epNum, body.instagram_url || "");
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: `Episode ${epNum} raw clips cleaned from Drive and marked Published in Sheet.`
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 4b. Consolidate & Migrate all old Prompts_Ep tabs into Past_Episodes_Prompts
    if (action === "migrate_to_past_episodes" || action === "migrate_old_tabs") {
      const res = migrateAllPromptEpSheetsToPastPrompts();
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 4c. Append current prompts to Past_Episodes_Prompts
    if (action === "archive_to_past_episodes" || action === "append_past_prompts") {
      const res = appendCurrentPromptsToPastEpisodes(body.episode_number || epNum);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 4d. Remove specific episode from Past_Episodes_Prompts
    if (action === "delete_from_past_prompts" || action === "remove_past_episode") {
      const targetEp = parseInt(body.episode_number || epNum || "7", 10);
      removeEpisodeFromPastPrompts(null, targetEp);
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: `Episode ${targetEp} removed from Past_Episodes_Prompts.`
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 5. Trigger GitHub Actions Workflow from Google Apps Script / Sheet
    if (action === "trigger_workflow") {
      const res = triggerGitHubWorkflowFromAppsScript(body);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 6. Save GitHub PAT into Script Properties
    if (action === "save_gh_token" && body.token) {
      PropertiesService.getScriptProperties().setProperty("GH_PAT", body.token);
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: "GH_PAT successfully saved to Script Properties."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 7. Update Single Shot Prompt in Tab 2
    if (action === "update_shot_prompt") {
      const res = updateSingleShotPrompt(epNum, body.shot_number, body.shot_data);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 8. Gemini Director AI Proxy (Bypasses browser adblockers and CORS)
        // 9. Update Master Season Story Arc in Tab 4
    if (action === "update_season_story_arc") {
      const res = updateSeasonStoryArcInSheet(body.season_number || 1, body.season_title, body.episodes || []);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    if (action === "gemini_proxy") {
      const model = body.model || "gemini-3.5-flash";
      const token = body.key || PropertiesService.getScriptProperties().getProperty("GEMINI_API_KEY") || "";
      const gUrl = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + token;
      const gRes = UrlFetchApp.fetch(gUrl, {
        method: "post",
        contentType: "application/json",
        payload: JSON.stringify({ contents: body.contents }),
        muteHttpExceptions: true
      });
      return ContentService.createTextOutput(gRes.getContentText()).setMimeType(ContentService.MimeType.JSON);
    }

    // 10. Upload Series Thumbnail to Google Drive (Deletes any old series thumbnail and saves the new one)
    if (action === "upload_series_thumbnail") {
      const res = handleUploadSeriesThumbnail(body);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 11. Tab 7: Save 100-Shot Master Screenplay Outline
    if (action === "save_season_shot_outline") {
      const res = updateSeasonShotOutlineInSheet(body.season_number || 1, body.season_title, body.shots || []);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    if (action === "apply_director_outline_change") {
      const res = applyDirectorOutlineChange(body);
      return ContentService.createTextOutput(JSON.stringify(res)).setMimeType(ContentService.MimeType.JSON);
    }

    if (action === "apply_director_season_rewrite") {
      const res = applyDirectorSeasonRewrite(body);
      return ContentService.createTextOutput(JSON.stringify(res)).setMimeType(ContentService.MimeType.JSON);
    }

    if (action === "update_episode_story_from_outline") {
      const res = updateEpisodeStoryFromOutline(body.season_number || 1, body.episodes || []);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    if (action === "sync_character_registry") {
      return ContentService.createTextOutput(JSON.stringify(syncCharacterRegistry(body)))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 12. Reset Sheet: Episodes 1-9 Published, Episode 10 Active, delete rows 12+
    if (action === "reset_to_season_2_ep9_published" || action === "reset_sheet_ep10_active") {
      resetToSeason2Episode9Published();
      return ContentService.createTextOutput(JSON.stringify({
        success: true,
        message: "Sheet reset: Episodes 1-9 Published, Episode 10 Active, Rows 12+ deleted."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // 13. Reorganize Google Sheet to 5-Tab Architecture (Delete Tab 4 & Tab 6, re-order 1-5)
    if (action === "reorganize_to_5_tabs") {
      const res = reorganizeTo5TabArchitecture();
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

/**
 * Triggers GitHub Actions workflow produce_and_publish.yml using UrlFetchApp.
 * Supports workflow_dispatch and repository_dispatch.
 */
function triggerGitHubWorkflowFromAppsScript(params) {
  params = params || {};
  const token = params.gh_token || PropertiesService.getScriptProperties().getProperty("GH_PAT") || GITHUB_PAT;
  const epNum = parseInt(params.episode_number || "1", 10);
  const workflow = String(params.workflow || "produce_and_publish.yml");
  const allowedWorkflows = ["generate_next_episode.yml", "produce_and_publish.yml", "harmonize_season_flow.yml", "rewrite_season_from_shot.yml"];
  if (!allowedWorkflows.includes(workflow)) {
    return { success: false, error: "INVALID_WORKFLOW", message: `Workflow ${workflow} is not allowed.` };
  }

  if (!token || token === "YOUR_GITHUB_PAT_HERE") {
    return {
      success: false,
      error: "MISSING_TOKEN",
      message: "GitHub Personal Access Token (GH_PAT) is not configured in Google Apps Script properties or provided in request payload."
    };
  }

  // 1. Try workflow_dispatch
  const dispatchUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${workflow}/dispatches`;
  try {
    const res = UrlFetchApp.fetch(dispatchUrl, {
      method: "post",
      contentType: "application/json",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Sachin-Reenu-Studio-AppsScript"
      },
      payload: JSON.stringify({
        ref: "main",
        inputs: workflow === "generate_next_episode.yml" ? {
          target_episode: String(params.target_episode || "1"),
          season_number: String(params.season_number || "1"),
          is_new_season: String(params.is_new_season === true || params.is_new_season === "true"),
          story_premise: String(params.story_premise || "")
        } : workflow === "rewrite_season_from_shot.yml" ? {
          season_number: String(params.season_number || "1"),
          pivot_global_shot_id: String(params.pivot_global_shot_id || "1"),
          active_episode: String(params.active_episode || "1"),
          story_idea: String(params.story_idea || ""),
          roadmap_json: String(params.roadmap_json || "")
        } : workflow === "harmonize_season_flow.yml" ? {
          season_number: String(params.season_number || "1"),
          use_ai_review: String(params.use_ai_review !== false && params.use_ai_review !== "false")
        } : {
          force_run: true,
          advance_to_next: false
        }
      }),
      muteHttpExceptions: true
    });

    const code = res.getResponseCode();
    if (code === 204 || code === 200 || code === 201) {
      return {
        success: true,
        method: "workflow_dispatch",
        status_code: code,
        message: `GitHub Actions workflow [${workflow}] triggered successfully by Google Apps Script for Episode ${epNum}!`
      };
    }

    if (workflow === "rewrite_season_from_shot.yml") {
      return { success: false, method: "workflow_dispatch", status_code: code,
        message: `GitHub rejected the season rewrite dispatch (HTTP ${code}); no fallback production workflow was started.` };
    }

    // 2. Try repository_dispatch as fallback
    const repoDispatchUrl = `https://api.github.com/repos/${GITHUB_REPO}/dispatches`;
    const repoRes = UrlFetchApp.fetch(repoDispatchUrl, {
      method: "post",
      contentType: "application/json",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Sachin-Reenu-Studio-AppsScript"
      },
      payload: JSON.stringify({
        event_type: "trigger-assembly",
        client_payload: {
          episode_number: epNum,
          force_run: true
        }
      }),
      muteHttpExceptions: true
    });

    const repoCode = repoRes.getResponseCode();
    if (repoCode === 204 || repoCode === 200 || repoCode === 201) {
      return {
        success: true,
        method: "repository_dispatch",
        status_code: repoCode,
        message: `GitHub Actions assembly triggered successfully via repository_dispatch for Episode ${epNum}!`
      };
    }

    return {
      success: false,
      error: "GITHUB_API_ERROR",
      status_code: code,
      response_text: res.getContentText() || repoRes.getContentText(),
      message: `GitHub API error (HTTP ${code}): ${res.getContentText()}`
    };

  } catch (err) {
    return {
      success: false,
      error: "FETCH_EXCEPTION",
      message: err.toString()
    };
  }
}

/**
 * Updates a single shot row in Tab 2 [Current_JSON_Prompts] without overwriting other shots.
 */
function updateSingleShotPrompt(episodeNum, shotNum, shotData) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_PROMPTS);
  if (!sheet || sheet.getLastRow() < 3) {
    return { success: false, error: "Tab 2 [Current_JSON_Prompts] not initialized" };
  }
  
  const lastRow = sheet.getLastRow();
  const numRows = lastRow - 2;
  const pData = sheet.getRange(3, 1, numRows, 6).getValues();
  let updatedInTab2 = false;
  
  for (let i = 0; i < pData.length; i++) {
    const currentShotNum = i + 1;
    if (currentShotNum === shotNum) {
      if (shotData.duration) sheet.getRange(i + 3, 2).setValue(shotData.duration);
      if (shotData.character) sheet.getRange(i + 3, 3).setValue(shotData.character);
      if (shotData.dialogue_malayalam) sheet.getRange(i + 3, 4).setValue(shotData.dialogue_malayalam);
      if (shotData.action_summary) sheet.getRange(i + 3, 5).setValue(shotData.action_summary);
      if (shotData.json_prompt) {
        const jsonStr = typeof shotData.json_prompt === 'string' ? shotData.json_prompt : JSON.stringify(shotData.json_prompt, null, 2);
        sheet.getRange(i + 3, 6).setValue(jsonStr);
      }
      updatedInTab2 = true;
      break;
    }
  }

  // BIDIRECTIONAL SYNC: Simultaneously update Tab 7 [Season_Shot_Outline]
  try {
    const outlineSheet = ss.getSheetByName(TAB_SHOT_OUTLINE);
    if (outlineSheet && outlineSheet.getLastRow() >= 3) {
      const epN = Number(episodeNum) || 1;
      const shN = Number(shotNum) || 1;
      const targetRow = 3 + (epN - 1) * 10 + (shN - 1);
      if (targetRow <= outlineSheet.getLastRow()) {
        if (shotData.character) outlineSheet.getRange(targetRow, 5).setValue(shotData.character);
        if (shotData.action_summary) outlineSheet.getRange(targetRow, 6).setValue(shotData.action_summary);
        if (shotData.dialogue_malayalam) outlineSheet.getRange(targetRow, 7).setValue(shotData.dialogue_malayalam);
        if (shotData.location) outlineSheet.getRange(targetRow, 8).setValue(shotData.location);
        outlineSheet.getRange(targetRow, 10).setValue("Prompt Ready");
      }
    }
  } catch (syncErr) {
    Logger.log("Notice syncing to Tab 7: " + syncErr.toString());
  }

  if (updatedInTab2) {
    return {
      success: true,
      message: `Shot #${shotNum} updated in Tab 2 [Current_JSON_Prompts] & synchronized with Tab 7 [Season_Shot_Outline]!`
    };
  }
  return { success: false, error: `Shot #${shotNum} not found in Tab 2` };
}

/**
 * Uploads a series thumbnail image to Google Drive:
 * 1. Finds or creates the folder 'Series_Thumbnails' in Google Drive.
 * 2. Deletes/trashes any existing previous series thumbnail image in that folder.
 * 3. Saves the new thumbnail image and sets view permissions.
 * 4. Records the thumbnail URL into Tab 4 (Season_Story_Arc) metadata or returns file details.
 */
function handleUploadSeriesThumbnail(body) {
  try {
    const seasonNum = body.season_number || 1;
    const base64Data = body.base64_data;
    const fileName = body.filename || `series_thumbnail_season_${seasonNum}.jpg`;
    const mimeType = body.mime_type || "image/jpeg";

    if (!base64Data) {
      return { success: false, error: "Missing base64_data payload for thumbnail upload." };
    }

    // 1. Locate or create folder for Series Thumbnails
    let thumbFolder = null;
    const folderName = "Series_Thumbnails";
    
    // Check inside DRIVE_ROOT_FOLDER if it exists
    const rootIter = DriveApp.getFoldersByName(DRIVE_ROOT_FOLDER);
    if (rootIter.hasNext()) {
      const rootFolder = rootIter.next();
      const subIter = rootFolder.getFoldersByName(folderName);
      if (subIter.hasNext()) {
        thumbFolder = subIter.next();
      } else {
        thumbFolder = rootFolder.createFolder(folderName);
      }
    } else {
      const directIter = DriveApp.getFoldersByName(folderName);
      if (directIter.hasNext()) {
        thumbFolder = directIter.next();
      } else {
        thumbFolder = DriveApp.createFolder(folderName);
      }
    }

    // 2. Trash ANY old thumbnail in this folder (guarantees previous image is deleted)
    const existingFiles = thumbFolder.getFiles();
    let deletedCount = 0;
    while (existingFiles.hasNext()) {
      const oldFile = existingFiles.next();
      oldFile.setTrashed(true);
      deletedCount++;
    }

    // 3. Create the new thumbnail file
    const decodedBytes = Utilities.base64Decode(base64Data);
    const blob = Utilities.newBlob(decodedBytes, mimeType, fileName);
    const newFile = thumbFolder.createFile(blob);
    newFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

    const fileUrl = newFile.getUrl();
    const fileId = newFile.getId();
    const downloadUrl = `https://drive.google.com/uc?export=view&id=${fileId}`;

    // 4. Optionally record in Tab 4 (Season_Story_Arc) header / cell
    try {
      const ss = getStudioSpreadsheet();
      const seasonSheet = ss.getSheetByName(TAB_SEASON_ARC);
      if (seasonSheet) {
        seasonSheet.getRange(1, 3).setValue(`THUMBNAIL_URL: ${downloadUrl}`);
      }
    } catch (e) {
      Logger.log("Notice recording thumbnail in Tab 4: " + e.toString());
    }

    return {
      success: true,
      message: `New series thumbnail uploaded! ${deletedCount} previous thumbnail(s) removed from Drive.`,
      file_id: fileId,
      filename: fileName,
      folder_url: thumbFolder.getUrl(),
      download_url: downloadUrl,
      deleted_previous_count: deletedCount
    };
  } catch (err) {
    return { success: false, error: err.toString() };
  }
}

/**
 * Retrieves the currently active series thumbnail file from Google Drive.
 */
function getSeriesThumbnailData() {
  try {
    const folderName = "Series_Thumbnails";
    let thumbFolder = null;
    const directIter = DriveApp.getFoldersByName(folderName);
    if (directIter.hasNext()) {
      thumbFolder = directIter.next();
    } else {
      const rootIter = DriveApp.getFoldersByName(DRIVE_ROOT_FOLDER);
      if (rootIter.hasNext()) {
        const subIter = rootIter.next().getFoldersByName(folderName);
        if (subIter.hasNext()) thumbFolder = subIter.next();
      }
    }

    if (!thumbFolder) {
      return { success: true, has_thumbnail: false };
    }

    const files = thumbFolder.getFiles();
    if (files.hasNext()) {
      const f = files.next();
      return {
        success: true,
        has_thumbnail: true,
        file_id: f.getId(),
        filename: f.getName(),
        download_url: `https://drive.google.com/uc?export=view&id=${f.getId()}`,
        folder_url: thumbFolder.getUrl()
      };
    }
    return { success: true, has_thumbnail: false };
  } catch (err) {
    return { success: false, error: err.toString() };
  }
}

