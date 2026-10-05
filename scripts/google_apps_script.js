/**
 * ==============================================================================
 * SACHIN & REENU CREATOR STUDIO — GOOGLE APPS SCRIPT ENGINE
 * ==============================================================================
 * Features:
 * 1. 2x Daily precision triggers: 12:00 PM IST & 6:00 PM IST
 * 2. Story Ledger & Memory tracking in Google Sheet
 * 3. Video upload dropzone receiver -> Saves directly to Google Drive
 * 4. GitHub Actions Automated Dispatcher with PAT
 * 5. Serves Portal Web App or JSON API
 * 
 * Setup Instructions:
 * 1. Open Google Sheet: https://docs.google.com/spreadsheets/d/1-7AHyFLXXgF1CdOfQPgPFbNelgiufxlsccpahrMG_VI/edit
 * 2. Click "Extensions" -> "Apps Script".
 * 3. Replace all code in Code.gs with this file.
 * 4. Replace `YOUR_GITHUB_PAT_HERE` with your GitHub Personal Access Token.
 * 5. Run `initSpreadsheetHeader()` once to initialize columns and starter episodes.
 * 6. Run `setupDailyTriggers()` once to schedule 12:00 PM & 6:00 PM IST runs.
 * 7. Click "Deploy" -> "New deployment" -> Select type "Web app":
 *    - Execute as: "Me"
 *    - Who has access: "Anyone"
 *    - Copy the Web App URL and paste it into portal.html!
 * ==============================================================================
 */

// CONFIGURATION
const SPREADSHEET_ID = "1-7AHyFLXXgF1CdOfQPgPFbNelgiufxlsccpahrMG_VI";
const GITHUB_REPO = "YoutubeVideoUploader/sachin-and-reenu-series";
const GITHUB_WORKFLOW = "produce_and_publish.yml";
const GITHUB_PAT = "YOUR_GITHUB_PAT_HERE"; // Insert your GitHub PAT (Repo/Workflow scope)
const DRIVE_ROOT_FOLDER = "Sachin_And_Reenu_Studio";

/**
 * Formats the header row and initial ledger rows in Google Sheet.
 */
function initSpreadsheetHeader() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getActiveSheet();
  
  const headers = [
    "Episode", 
    "Title", 
    "Status", 
    "Story Outline / Synopsis", 
    "Drive Folder URL", 
    "Instagram URL", 
    "Next Cliffhanger", 
    "Published At (IST)"
  ];
  
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length)
      .setBackground("#1a1a2e")
      .setFontColor("#f8fafc")
      .setFontWeight("bold")
      .setHorizontalAlignment("center");
    sheet.setFrozenRows(1);
    
    // Episode 1 (Published)
    sheet.appendRow([
      1,
      "തിരിച്ചുവരവ് (The Homecoming)",
      "Published",
      "After two long years apart, Sachin finally touches down at Kochi CIAL from the UK. Reenu and Amal eagerly wait by the arrival barriers, leading to an overwhelming, heartfelt reunion.",
      "",
      "https://www.instagram.com/reel/18115173056519806/",
      "As Sachin holds Reenu close, his mysterious glance toward his travel pouch hints at a secret from London.",
      new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })
    ]);
    
    // Episode 2 (Published / In Production)
    sheet.appendRow([
      2,
      "കൊച്ചിയിലെ മഴയും ഒരു രഹസ്യവും (Kochi Rain & A Secret)",
      "Published",
      "Sachin, Reenu, and Amal drive through sudden Kochi monsoon rain. While stopping for hot tea, Sachin reveals a small velvet box inside his bag, but hesitates to open it.",
      "",
      "",
      "Sachin and Reenu share an umbrella and an intimate car ride, rekindling their unspoken chemistry.",
      ""
    ]);

    // Episode 3 (Active Production)
    sheet.appendRow([
      3,
      "മഴ തോരാത്ത വഴികൾ (Rain-Drenched Roads)",
      "Queued",
      "Stepping out into the sudden Kochi monsoon, Sachin and Reenu share an umbrella and an intimate car ride, rekindling their unspoken chemistry while Amal playfully navigates the rain-swept streets.",
      "",
      "",
      "Amal glances in the rear-view mirror as Sachin's fingers brush against Reenu's hand.",
      ""
    ]);

    Logger.log("Google Sheet initialized with starter episodes!");
  } else {
    Logger.log("Sheet already contains data.");
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
 * Checks which video clips are already uploaded in Google Drive for an episode.
 */
function checkUploadedShots(episodeNum) {
  const folder = getEpisodeDriveFolder(episodeNum);
  const files = folder.getFiles();
  const uploaded = [];
  
  while (files.hasNext()) {
    const f = files.next();
    uploaded.push({
      name: f.getName(),
      id: f.getId(),
      url: f.getUrl(),
      downloadUrl: f.getDownloadUrl(),
      sizeBytes: f.getSize()
    });
  }
  return {
    folderId: folder.getId(),
    folderUrl: folder.getUrl(),
    files: uploaded
  };
}

/**
 * Triggers the GitHub Actions Workflow via API.
 */
function dispatchGitHubWorkflow(episodeNum, driveFolderId) {
  if (!GITHUB_PAT || GITHUB_PAT === "YOUR_GITHUB_PAT_HERE") {
    Logger.log("ERROR: GITHUB_PAT is not set! Please insert your PAT in Apps Script.");
    return { success: false, message: "GITHUB_PAT missing in Apps Script" };
  }

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
 * Scheduled check: runs at 12:00 PM IST and 6:00 PM IST.
 * If video clips for the queued episode are uploaded in Google Drive, triggers GitHub Actions.
 */
function scheduledEpisodeCheckAndTrigger() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
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

  if (!queuedEp) {
    Logger.log("No queued episode found to trigger.");
    return;
  }

  Logger.log(`Scheduled check running for Episode ${queuedEp.episode}: "${queuedEp.title}"`);
  
  // Check Drive folder for uploaded shots
  const driveInfo = checkUploadedShots(queuedEp.episode);
  sheet.getRange(queuedRow, 5).setValue(driveInfo.folderUrl);

  // If clips exist (at least 1 shot uploaded), dispatch GitHub
  if (driveInfo.files.length > 0) {
    Logger.log(`Found ${driveInfo.files.length} uploaded shots in Drive. Dispatching GitHub Actions!`);
    sheet.getRange(queuedRow, 3).setValue("Processing");
    dispatchGitHubWorkflow(queuedEp.episode, driveInfo.folderId);
  } else {
    Logger.log(`Episode ${queuedEp.episode} has no uploaded clips in Drive yet. Waiting for creator upload.`);
  }
}

/**
 * Sets up 2 daily triggers:
 * 1. 12:00 PM IST (noon)
 * 2. 6:00 PM IST (18:00)
 */
function setupDailyTriggers() {
  const existingTriggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < existingTriggers.length; i++) {
    ScriptApp.deleteTrigger(existingTriggers[i]);
  }

  // 12:00 PM IST
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
 * Web App GET endpoint: Provides status, queued episodes, or Drive clips.
 */
function doGet(e) {
  const params = e ? e.parameter : {};
  const action = params.action || "status";
  
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getActiveSheet();
  const data = sheet.getDataRange().getValues();

  if (action === "status" || action === "current_episode") {
    let queuedEp = null;
    let publishedCount = 0;
    
    for (let i = 1; i < data.length; i++) {
      const status = (data[i][2] || "").toString().trim().toLowerCase();
      if (status === "published") {
        publishedCount++;
      } else if (!queuedEp && (status === "queued" || status === "pending" || status === "processing")) {
        queuedEp = {
          row: i + 1,
          episode_number: data[i][0],
          title: data[i][1],
          status: data[i][2],
          outline: data[i][3],
          drive_url: data[i][4] || ""
        };
      }
    }

    let driveFiles = [];
    if (queuedEp) {
      const driveInfo = checkUploadedShots(queuedEp.episode_number);
      driveFiles = driveInfo.files;
      queuedEp.drive_folder_url = driveInfo.folderUrl;
    }

    const response = {
      success: true,
      current_episode: queuedEp,
      total_published: publishedCount,
      drive_shots: driveFiles
    };

    return ContentService.createTextOutput(JSON.stringify(response))
      .setMimeType(ContentService.MimeType.JSON);
  }

  return ContentService.createTextOutput(JSON.stringify({ status: "running", app: "Sachin & Reenu Creator Studio" }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Web App POST endpoint:
 * 1. Receives video uploads from Portal and saves directly to Google Drive.
 * 2. Receives GitHub Actions completion webhooks.
 * 3. Triggers manual workflow dispatch.
 */
function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const action = body.action || "complete_episode";
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getActiveSheet();

    // ACTION 1: Video Shot Upload from Portal
    if (action === "upload_shot") {
      const epNum = body.episode_number || 3;
      const fileName = body.filename || `shot_${Date.now()}.mp4`;
      const base64Data = body.base64_data;
      
      const folder = getEpisodeDriveFolder(epNum);
      const decodedBytes = Utilities.base64Decode(base64Data);
      const blob = Utilities.newBlob(decodedBytes, "video/mp4", fileName);
      
      // Overwrite if file already exists with same name
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
        file_url: file.getUrl(),
        download_url: file.getDownloadUrl()
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // ACTION 2: Trigger GitHub Workflow Manually from Portal
    if (action === "trigger_workflow") {
      const epNum = body.episode_number || 3;
      const folder = getEpisodeDriveFolder(epNum);
      const res = dispatchGitHubWorkflow(epNum, folder.getId());
      return ContentService.createTextOutput(JSON.stringify(res))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // ACTION 3: GitHub Actions marks Episode Complete & creates Next Episode
    if (action === "complete_episode") {
      const epNum = body.episode_number;
      const data = sheet.getDataRange().getValues();
      const nowIst = new Date().toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
      
      for (let i = 1; i < data.length; i++) {
        if (data[i][0] == epNum) {
          sheet.getRange(i + 1, 3).setValue("Published");
          sheet.getRange(i + 1, 6).setValue(body.instagram_url || "");
          sheet.getRange(i + 1, 7).setValue(body.cliffhanger || "");
          sheet.getRange(i + 1, 8).setValue(nowIst);
          break;
        }
      }

      // Append next episode
      if (body.next_episode_story) {
        const nextEp = epNum + 1;
        sheet.appendRow([
          nextEp,
          body.next_episode_title || `ഭാഗം ${nextEp}`,
          "Queued",
          body.next_episode_story,
          "",
          "",
          "",
          ""
        ]);
      }

      return ContentService.createTextOutput(JSON.stringify({ success: true }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({ error: "Unknown action" }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
