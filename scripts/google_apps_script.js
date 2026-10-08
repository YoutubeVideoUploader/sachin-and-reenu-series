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

// TAB NAMES
const TAB_STORY = "Episode_Story";
const TAB_PROMPTS = "Current_JSON_Prompts";
const TAB_CHECKLIST = "Video_Checklist";
const TAB_SEASON_ARC = "Season_Story_Arc";
const TAB_CHARACTERS = "Character_Registry";

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
      .addItem("⚡ Trigger Instagram Assembly via GitHub Actions", "menuTriggerGitHubWorkflow")
      .addToUi();
  } catch (e) {}
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
      if (data[i][2] === "Active") {
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
      if (data[i][2] === "Active") {
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
    
    // Episode 1 (Active)
    storySheet.appendRow([
      1,
      "തിരിച്ചുവരവ് (The Homecoming)",
      "Active",
      10,
      "After two long years of waiting, Reenu stands anxiously with her friend Amal at the Kochi CIAL arrival terminal. Sachin emerges through the glass doors, leading to a tearful, tender reunion, but he nervously clutches a secret leather pouch from London.",
      "As Sachin holds Reenu close, his eyes reveal a hidden anxiety while his fingers tightly clutch a secret, unopened leather pouch.",
      "",
      ""
    ]);

    // Episode 2 (Upcoming)
    storySheet.appendRow([
      2,
      "മഴയും ചില രഹസ്യങ്ങളും (Rain and Some Secrets)",
      "Upcoming",
      10,
      "Stepping outside into a sudden Kochi monsoon shower, Sachin, Reenu, and Amal rush to the car. As they drive through the rain, Reenu notices Sachin's nervous protectiveness over his bag.",
      "The pouch slips from Sachin's hand and slides deep under the car seat just as he is about to confess.",
      "",
      ""
    ]);
  }

  // -------------------------------------------------------------
  // 2. TAB 2: Current_JSON_Prompts
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

  // Auto-populate Tab 2 with Episode 1 prompts from GitHub if available
  try {
    const rawUrl = `https://raw.githubusercontent.com/${GITHUB_REPO}/main/current_episode_shots.json`;
    const res = UrlFetchApp.fetch(rawUrl);
    if (res.getResponseCode() === 200) {
      const epData = JSON.parse(res.getContentText());
      updateJsonPromptsSheet(epData.episode_number || 1, epData.shots || []);
    }
  } catch (err) {}

  // -------------------------------------------------------------
  // 3. TAB 3: Video_Checklist
  // -------------------------------------------------------------
  let checkSheet = ss.getSheetByName(TAB_CHECKLIST);
  if (!checkSheet) {
    checkSheet = ss.insertSheet(TAB_CHECKLIST, 2);
  }
  if (checkSheet.getLastRow() === 0) {
    initVideoChecklist(1, 10, "തിരിച്ചുവരവ് (The Homecoming)");
  }

  // -------------------------------------------------------------
  // 4. TAB 4: Season_Story_Arc (Master Season Story & 10 Summaries)
  // -------------------------------------------------------------
  setupSeasonStoryArcSheet(1);

  // -------------------------------------------------------------
  // 5. TAB 5: Character_Registry (Persistent Cast & Locked DNA)
  // -------------------------------------------------------------
  setupCharacterRegistrySheet();

  Logger.log("All 5 Google Sheet tabs initialized successfully!");
}

/**
 * Initializes Tab 4: Season_Story_Arc with 10-episode narrative roadmap.
 */
function setupSeasonStoryArcSheet(seasonNum) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_SEASON_ARC);
  if (!sheet) {
    sheet = ss.insertSheet(TAB_SEASON_ARC, 3);
  }

  if (sheet.getLastRow() > 0) return; // Already initialized

  // Meta Banner
  sheet.getRange(1, 1).setValue(`SEASON ${seasonNum}: THE HOMECOMING & THE LONDON SECRET (തിരിച്ചുവരവ്)`).setFontWeight("bold").setFontSize(12);
  sheet.getRange(1, 2).setValue("CLIMAX TARGET: EPISODE 10").setFontWeight("bold");
  sheet.getRange(1, 1, 1, 2).setBackground("#4f46e5").setFontColor("#ffffff");

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

  const season1Episodes = [
    [
      1, 1, "The Homecoming", "തിരിച്ചുവരവ്", "Active",
      "After two long years of waiting, Reenu stands anxiously with her friend Amal at Kochi CIAL arrival terminal. Sachin emerges through the sliding glass doors, leading to an emotional, tearful reunion. However, Sachin nervously clutches a secret leather pouch from London.",
      "As Sachin holds Reenu close, his eyes reveal a hidden anxiety while his fingers tightly clutch a secret, unopened leather pouch.",
      ""
    ],
    [
      1, 2, "Rain and Some Secrets", "മഴയും ചില രഹസ്യങ്ങളും", "Upcoming",
      "Stepping outside into a sudden Kochi monsoon shower, Sachin, Reenu, and Amal rush to the car. As they drive through the rain-drenched streets, Reenu notices Sachin's nervous protectiveness over his bag.",
      "The pouch slips from Sachin's hand and slides deep under the car seat just as he is about to confess.",
      ""
    ],
    [
      1, 3, "A Roadside Chai & Unspoken Glances", "ഒരു തട്ടുകട ചായയും നോട്ടങ്ങളും", "Upcoming",
      "Amal stops the car at a misty tea stall by the backwaters. Under a shared umbrella, Sachin and Reenu share an intimate moment over hot tea, but Sachin hesitates to speak.",
      "Amal spots the London leather pouch lying on the car floor and picks it up curiously.",
      ""
    ],
    [
      1, 4, "Forgotten Memories", "മറന്നുപോയ ഓർമ്മകൾ", "Upcoming",
      "Continuing their ride into Kochi city, Sachin and Reenu reminisce about their college days, but Sachin feels guilty about being away in the UK for 730 days.",
      "Reenu asks Sachin directly: 'Why didn't you tell me the real reason you booked your flight so suddenly?'",
      ""
    ],
    [
      1, 5, "The Secret Slips", "രഹസ്യം പുറത്തേക്ക്", "Upcoming",
      "Amal hands the pouch back to Sachin, asking what is inside. Sachin stammers and tries to divert the topic, raising Reenu's suspicion.",
      "Reenu reaches for the pouch playfully, but Sachin instinctively pulls it back, creating an awkward silence.",
      ""
    ],
    [
      1, 6, "Amal's Wit & Heavy Silence", "അമലിന്റെ തമാശയും മൗനവും", "Upcoming",
      "Amal uses humor and teasing to diffuse the tension. Sachin feels deeply torn between confessing his life-changing London decision and the fear of overwhelming Reenu.",
      "Sachin promises Reenu: 'Before tonight ends, I will tell you everything.'",
      ""
    ],
    [
      1, 7, "The Rain Settles", "മഴ തോർന്ന രാത്രി", "Upcoming",
      "The car arrives outside Reenu's house. In the quiet, rain-washed night, Sachin walks Reenu to the front gate. A tender, lingering goodbye.",
      "Sachin gently holds Reenu's hand, asking her to meet him at Marine Drive walkway at midnight.",
      ""
    ],
    [
      1, 8, "Reenu's Suspicion & Worry", "റീനുവിന്റെ മനസ്സ്", "Upcoming",
      "Reenu sits in her room by the window, watching the rain mist. She wonders whether Sachin's secret means he has to go back to the UK permanently.",
      "Reenu makes a heartfelt decision to profess her true love and ask Sachin never to leave again.",
      ""
    ],
    [
      1, 9, "A Midnight Message", "ഒരു സന്ദേശവും അർദ്ധരാത്രിയും", "Upcoming",
      "Sachin and Amal prepare at Marine Drive. Amal gives Sachin emotional courage. Reenu arrives in the dim golden lights of Kochi backwaters.",
      "Sachin takes a deep breath, unzips the leather pouch, and steps forward toward Reenu.",
      ""
    ],
    [
      1, 10, "The Grand Climax: The Revelation", "ആ രഹസ്യത്തിന്റെ ചുരുളഴിയുമ്പോൾ", "Upcoming",
      "SEASON 1 CLIMAX: Sachin reveals what was inside the pouch—his officially cancelled London visa documents and a permanent contract in Kochi, choosing to stay by Reenu's side forever. Tears of joy, a breathtaking embrace, and a sweet tease for Season 2!",
      "Sachin whispers: 'I'm never going back. I'm home.' Season 1 Climax completed!",
      ""
    ]
  ];

  sheet.getRange(3, 1, season1Episodes.length, headers.length).setValues(season1Episodes);
  
  // Format Status Column (Col 5)
  sheet.getRange(3, 5).setBackground("#dcfce7").setFontColor("#15803d").setFontWeight("bold"); // Ep 1 Active
  sheet.getRange(4, 5, 9, 1).setBackground("#fef3c7").setFontColor("#92400e"); // Upcoming

  sheet.setColumnWidth(6, 400); // Story summary width
  sheet.setColumnWidth(7, 300); // Cliffhanger width
  Logger.log("Season_Story_Arc sheet populated with Season 1 (10 Episodes) roadmap.");
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

  const headers = [
    "Character Name",
    "Role in Story",
    "First Appearance",
    "Status",
    "Stylized 3D Pixar Visual DNA (Non-Human)",
    "Locked Signature Attire (100% Unchanging)",
    "Voice Persona & Cadence"
  ];

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

  sheet.getRange(3, 1, initialCharacters.length, headers.length).setValues(initialCharacters);
  sheet.getRange(3, 4, 3, 1).setBackground("#dcfce7").setFontColor("#15803d").setFontWeight("bold");

  sheet.setColumnWidth(5, 450); // Visual DNA
  sheet.setColumnWidth(6, 350); // Locked Attire
  sheet.setColumnWidth(7, 300); // Voice
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
  let colStatus = 2; // Default column 2
  let colFileId = 4;
  let colSize = 5;
  let colTime = 6;
  
  for (let c = 0; c < headerRow.length; c++) {
    const h = String(headerRow[c]).toLowerCase();
    if (h.includes("status")) colStatus = c + 1;
    else if (h.includes("id")) colFileId = c + 1;
    else if (h.includes("size")) colSize = c + 1;
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
      if (colSize <= headerCols) sheet.getRange(rowIdx, colSize).setValue(match.size);
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
      if (colSize <= headerCols) sheet.getRange(rowIdx, colSize).setValue("");
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
        storySheet.getRange(i + 1, 3).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
        if (instagramUrl) {
          storySheet.getRange(i + 1, 7).setValue(instagramUrl);
        }
        storySheet.getRange(i + 1, 8).setValue(nowIst);
        publishedFound = true;
      } else if (rowEp === epNum + 1) {
        storySheet.getRange(i + 1, 3).setValue("Active").setBackground("#dbeafe").setFontColor("#1d4ed8");
        nextEpFound = true;
      }
    }

    if (!nextEpFound) {
      storySheet.appendRow([
        epNum + 1,
        `Episode ${epNum + 1}`,
        "Active",
        10,
        "",
        "",
        "",
        ""
      ]);
      const newRow = storySheet.getLastRow();
      storySheet.getRange(newRow, 3).setBackground("#dbeafe").setFontColor("#1d4ed8");
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
        } else if (rowEp === epNum + 1) {
          seasonSheet.getRange(r + 3, 5).setValue("Active").setBackground("#dbeafe").setFontColor("#1d4ed8");
        }
      }
    }
  } catch (err) {
    Logger.log("Notice updating Tab 4 on publish: " + err.toString());
  }
}

/**
 * Overwrites Tab 2: Current_JSON_Prompts with the new episode prompts.
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
function getSeasonStoryArcData() {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_SEASON_ARC);
  if (!sheet || sheet.getLastRow() < 3) {
    setupSeasonStoryArcSheet(1);
    sheet = ss.getSheetByName(TAB_SEASON_ARC);
  }

  const data = sheet.getRange(3, 1, sheet.getLastRow() - 2, 8).getValues();
  const episodes = [];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    episodes.push({
      season_number: row[0] || 1,
      episode_number: row[1] || (i + 1),
      title_english: row[2] || `Episode ${i + 1}`,
      title_malayalam: row[3] || "",
      status: row[4] || "Upcoming",
      synopsis: row[5] || "",
      cliffhanger: row[6] || "",
      creator_notes: row[7] || ""
    });
  }

  return {
    success: true,
    season_number: 1,
    season_title: "The Homecoming & The London Secret (തിരിച്ചുവരവ്)",
    total_episodes: 10,
    climax_target_episode: 10,
    episodes: episodes
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

  const data = sheet.getRange(3, 1, sheet.getLastRow() - 2, 7).getValues();
  const characters = [];

  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    characters.push({
      name: row[0],
      role: row[1],
      first_appearance: row[2],
      status: row[3],
      visual_dna: row[4],
      locked_attire: row[5],
      voice_persona: row[6]
    });
  }

  return {
    success: true,
    total_characters: characters.length,
    characters: characters
  };
}

/**
 * Records a creator story pitch / suggestion into Tab 4.
 */
function recordCreatorStoryIdea(epNum, idea) {
  const ss = getStudioSpreadsheet();
  let sheet = ss.getSheetByName(TAB_SEASON_ARC);
  if (!sheet) {
    setupSeasonStoryArcSheet(1);
    sheet = ss.getSheetByName(TAB_SEASON_ARC);
  }

  const lastRow = sheet.getLastRow();
  let found = false;

  for (let r = 3; r <= lastRow; r++) {
    const rowEp = sheet.getRange(r, 2).getValue();
    if (rowEp == epNum) {
      sheet.getRange(r, 8).setValue(idea);
      found = true;
      break;
    }
  }

  if (!found) {
    // Append as a general season note
    sheet.appendRow([1, epNum || 0, "Creator Idea", "", "Pending Review", "", "", idea]);
  }

  return {
    success: true,
    message: `Story idea recorded for Episode ${epNum || 'General'} in Tab 4 [Season_Story_Arc]!`
  };
}

/**
 * Full Next-Episode Transition.
 */
function handleNextEpisodeFullUpdate(body) {
  const epNum = body.episode_number || 1;
  const prevEp = epNum - 1;
  
  const ss = getStudioSpreadsheet();
  const storySheet = ss.getSheetByName(TAB_STORY);
  if (storySheet) {
    const data = storySheet.getDataRange().getValues();
    const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
    let epRowFound = false;
    
    for (let i = 1; i < data.length; i++) {
      const rowEp = parseInt(data[i][0], 10);
      if (prevEp > 0 && rowEp <= prevEp) {
        storySheet.getRange(i + 1, 3).setValue("Published").setBackground("#dcfce7").setFontColor("#15803d");
        if (body.instagram_url && rowEp === prevEp) storySheet.getRange(i + 1, 7).setValue(body.instagram_url);
        if (!data[i][7] && rowEp === prevEp) storySheet.getRange(i + 1, 8).setValue(nowIst);
      }
      if (rowEp === epNum) {
        storySheet.getRange(i + 1, 3).setValue("Active").setBackground("#dbeafe").setFontColor("#1d4ed8");
        const fullTitle = `${body.title_malayalam || ''} (${body.title_english || ''})`.trim();
        if (fullTitle) storySheet.getRange(i + 1, 2).setValue(fullTitle);
        if (body.total_shots) storySheet.getRange(i + 1, 4).setValue(body.total_shots);
        if (body.synopsis) storySheet.getRange(i + 1, 5).setValue(body.synopsis);
        if (body.cliffhanger) storySheet.getRange(i + 1, 6).setValue(body.cliffhanger);
        epRowFound = true;
      }
      if (epNum === 1 && rowEp > 1) {
        storySheet.getRange(i + 1, 3).setValue("Upcoming").setBackground("#fef3c7").setFontColor("#92400e");
      }
    }

    if (!epRowFound) {
      const fullTitle = `${body.title_malayalam || ''} (${body.title_english || ''})`.trim() || `Episode ${epNum}`;
      storySheet.appendRow([
        epNum,
        fullTitle,
        "Active",
        body.total_shots || (body.shots ? body.shots.length : 10),
        body.synopsis || "",
        body.cliffhanger || "",
        "",
        ""
      ]);
      const newRow = storySheet.getLastRow();
      storySheet.getRange(newRow, 3).setBackground("#dbeafe").setFontColor("#1d4ed8");
    }
  }

  if (body.shots && Array.isArray(body.shots) && body.shots.length > 0) {
    updateJsonPromptsSheet(epNum, body.shots);
  }

  const totalShots = body.total_shots || (body.shots && body.shots.length ? body.shots.length : 10);
  initVideoChecklist(epNum, totalShots, body.title_malayalam || `Episode ${epNum}`);
  
  // 4. Update Tab 4: Season_Story_Arc
  try {
    let seasonSheet = ss.getSheetByName(TAB_SEASON_ARC);
    if (!seasonSheet) {
      setupSeasonStoryArcSheet(1);
      seasonSheet = ss.getSheetByName(TAB_SEASON_ARC);
    }
    if (seasonSheet && seasonSheet.getLastRow() >= 3) {
      const sData = seasonSheet.getRange(3, 1, seasonSheet.getLastRow() - 2, 8).getValues();
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
      if (!arcFound) {
        seasonSheet.appendRow([
          1, epNum,
          body.title_english || `Episode ${epNum}`,
          body.title_malayalam || "",
          "Active",
          body.synopsis || "",
          body.cliffhanger || "",
          ""
        ]);
        seasonSheet.getRange(seasonSheet.getLastRow(), 5).setBackground("#dcfce7").setFontColor("#15803d");
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
            `Season 1 • Ep ${epNum}`,
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

  // Auto-scan single 'Episode' Drive folder immediately
  try {
    syncDriveToChecklist(epNum);
  } catch (syncErr) {
    Logger.log("Notice auto-syncing Drive: " + syncErr.toString());
  }

  return {
    success: true,
    active_episode: epNum,
    message: `Episode ${epNum} activated across all 5 sheets!`
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

  // Creator Story Idea Submission via GET
  if (action === "suggest_story_idea") {
    const idea = params.idea || "";
    const targetEp = parseInt(params.target_episode || "0", 10);
    const result = recordCreatorStoryIdea(targetEp, idea);
    return ContentService.createTextOutput(JSON.stringify(result))
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
  let epTitleEn = "The Homecoming";
  let epTitleMl = "തിരിച്ചുവരവ്";
  let epSynopsis = "After two long years of waiting, Reenu stands anxiously with her friend Amal at the Kochi CIAL arrival terminal...";

  if (storySheet && storySheet.getLastRow() > 1) {
    const storyData = storySheet.getDataRange().getValues();
    for (let i = 1; i < storyData.length; i++) {
      const st = (storyData[i][2] || "").toString().trim().toLowerCase();
      if (st === "active") {
        activeEp = storyData[i][0];
        const fullTitle = storyData[i][1] || "";
        if (fullTitle.includes("(")) {
          epTitleMl = fullTitle.split("(")[0].trim();
          epTitleEn = fullTitle.split("(")[1].replace(")", "").trim();
        } else {
          epTitleMl = fullTitle;
        }
        epSynopsis = storyData[i][4] || epSynopsis;
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

    // 2. Creator Story Idea Submission
    if (action === "suggest_story_idea") {
      const res = recordCreatorStoryIdea(body.target_episode, body.idea);
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // 3. Full Next-Episode Transition
    if (action === "update_next_episode_full") {
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

  if (!token || token === "YOUR_GITHUB_PAT_HERE") {
    return {
      success: false,
      error: "MISSING_TOKEN",
      message: "GitHub Personal Access Token (GH_PAT) is not configured in Google Apps Script properties or provided in request payload."
    };
  }

  // 1. Try workflow_dispatch
  const dispatchUrl = `https://api.github.com/repos/${GITHUB_REPO}/actions/workflows/${GITHUB_WORKFLOW}/dispatches`;
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
        inputs: {
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
        message: `GitHub Actions workflow [${GITHUB_WORKFLOW}] triggered successfully by Google Apps Script for Episode ${epNum}!`
      };
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
      return {
        success: true,
        message: `Shot #${shotNum} updated directly in Tab 2 [Current_JSON_Prompts]!`
      };
    }
  }
  return { success: false, error: `Shot #${shotNum} not found in Tab 2` };
}

