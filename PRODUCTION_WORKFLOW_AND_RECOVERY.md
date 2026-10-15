# Sachin & Reenu AI Animation Studio — Production Workflow & Recovery Guide

## 1. Executive Summary & Architecture Overview

The **Sachin & Reenu AI Animation Studio** is a fully automated, cloud-synchronized 3D animation production pipeline built for vertical 9:16 Disney Pixar-style episodic animated series.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CANONICAL PRODUCTION PIPELINE                   │
└────────────────────────────────────────────────────────────────────────┘
                                   │
      ┌────────────────────────────┴───────────────────────────┐
      ▼                                                        ▼
[Google Sheet Live Canon]                            [Local State Machine]
Tab 1: Episode_Story                                 season_3_shot_outline.json (100 shots)
Tab 2: Current_JSON_Prompts                          current_episode_shots.json (Active Ep)
Tab 3: Video_Checklist                               story_state.json (Persistent History)
Tab 4: Season_Story_Arc
Tab 5: Character_Registry
Tab 7: Season_Shot_Outline
      │                                                        │
      └────────────────────────────┬───────────────────────────┘
                                   │
                                   ▼
          [Universal Scene State & Continuity Engine (USCE)]
          • Mathematical 1:6.5 Disney Pixar proportions
          • Strict anti-fat / anti-chibi diffusion guards
          • Spatial & role invariance (Amal: Driver, Sachin: Passenger, Reenu: Rear)
          • 100% Immutable Malayalam dialogue protection
                                   │
                                   ▼
          [Dynamic Story Dependency & Propagation Engine (SDCE)]
          • Causal boundary handshake validation (Ep N Shot 10 -> Ep N+1 Shot 1)
          • Automated detection of teleportation, unresolved stalls & emotional disconnects
          • Surgical change-impact reporting before any disk mutation
          • Content-hashed snapshot backups & 1-click rollback
                                   │
                                   ▼
          [GitHub Actions CI/CD Production Runner (.github/workflows)]
          Step 5:  drive_sync_and_check.py (Auto-resolves Season/Ep -> $GITHUB_OUTPUT)
          Step 6:  watermark_remover.py (Gemini sparkle removal)
          Step 7:  video_merger.py (Dialogue audio preservation + BGM mix + validation)
          Step 7b: generate_thumbnail.py (Drive template sync + Season/Ep stamping)
          Step 8:  instagram_publisher.py (300s Meta polling + duplicate protection)
          Step 9:  Autonomous next-episode activation & portal update
```

---

## 2. Dynamic Episode Resolution Pipeline

In production runs, hardcoded defaults (such as Season 2 Episode 7) have been completely eliminated across all studio tools.

### Resolution Hierarchy:
1. **Explicit Workflow Input / CLI Argument**: `--season <N> --episode <N>`
2. **Environment Variables**: `SEASON_NUMBER`, `EPISODE_NUMBER` / `ACTIVE_EPISODE`
3. **Active Episode JSON**: `current_episode_shots.json` (`season_number`, `episode_number`)
4. **Local Persistent State**: `story_state.json` (`season_number`, `episode_number`)
5. **Live Google Sheet Query**: Tab `Season_Story_Arc` Cell A1 (via Google Apps Script `get_season_story`)
6. **Safe Fallback**: Season 3, Episode 1 if brand new project.

### Pipeline Parameter Passing:
In `.github/workflows/produce_and_publish.yml`:
- **Step 5 (`drive_sync_and_check.py`)** dynamically evaluates the active episode and emits outputs:
  ```bash
  echo "season=$RESOLVED_SEASON" >> $GITHUB_OUTPUT
  echo "episode=$RESOLVED_EPISODE" >> $GITHUB_OUTPUT
  ```
- **Downstream Steps (7, 7b, 8)** consume these outputs directly:
  ```yaml
  --season "${{ steps.drive_check.outputs.season }}"
  --episode "${{ steps.drive_check.outputs.episode }}"
  ```

---

## 3. Universal Continuity & Character DNA Contracts

All prompt compilation routes through [`scripts/universal_continuity_engine.py`](file:///c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/repo_studio/scripts/universal_continuity_engine.py).

### Architectural Invariants:
1. **Sacred Malayalam Dialogue**: Input dialogue and speaker identities are strictly read-only constants. The engine NEVER translates, summarizes, or hallucinates lines.
2. **Mathematical 1:6.5 Proportions**: Character DNA explicitly mandates 1:6.5 head-to-body ratios for 18-19yo teenagers.
3. **Anti-Fat Guards**: Every character prompt injects negative diffusion constraints:
   `PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/HEAVY/STOCKY BUILD, PROHIBIT DOUBLE CHIN, ZERO BEARD, ZERO STUBBLE`.
4. **Physical Role Invariance**:
   - **Vehicle Interior**: Amal is locked as the driver, Sachin as the front passenger, and Reenu in the rear.
   - **Eyeline Tracking**: Direct eye contact and spatial anchors (Screen-Left, Screen-Center, Screen-Right) remain fixed across consecutive shots until an explicit scene transition occurs.
5. **Direct Lip-Sync Coupling**: Spoken character dialogue triggers `Character Dialogue ({Speaker} Speaking)` and explicit animated mouth movement directives while enforcing `ABSOLUTELY NO BACKGROUND MUSIC` in raw clip audio generation.

---

## 4. Dynamic Story Propagation & Dependency-Update Workflow

When an episode or shot is edited, the changes must not cause downstream narrative fractures (e.g., characters jumping from a stalled car into a homestay with zero transit).

### CLI Commands:

#### 1. Validate Season Continuity
Audits all 100 shots in the season outline for physical boundary fractures:
```bash
python scripts/story_dependency_engine.py validate
```

#### 2. Propose an Edit & Generate Change-Impact Report
Evaluates causal downstream impact without modifying the master outline:
```bash
python scripts/story_dependency_engine.py propose \
  --season 3 \
  --episode 2 \
  --shot 10 \
  --action "Amal notices a distant lantern swinging in the dense fog approaching their car." \
  --dialogue "ഡാ... ആ മഞ്ഞിലൂടെ ആരോ ഒരു റാന്തൽ വിളക്കുമായി വരുന്നുണ്ട്!" \
  --notes "Introduce caretaker lantern arrival narrative bridge"
```
This generates a versioned proposal file in `story_revisions/pending_<rev_id>.json`.

#### 3. Review Pending Revision
Inspects the Markdown Change-Impact Report:
```bash
python scripts/story_dependency_engine.py review --revision_id <rev_id>
```

#### 4. Approve and Commit Revision
Atomic commit that creates a timestamped backup snapshot, commits the revision to `season_3_shot_outline.json` and `current_episode_shots.json`, and records the hash in `story_revisions/committed_<rev_id>.json`:
```bash
python scripts/story_dependency_engine.py approve --revision_id <rev_id>
```

#### 5. Rollback Revision
Restores the exact pre-revision snapshot in 1 click:
```bash
python scripts/story_dependency_engine.py rollback --revision_id <rev_id>
```

---

## 5. Media Pipeline & Instagram Reliability

### Video Merger Protections:
1. **Automatic Temporary Cleanup**: Intermediate files (`temp_merger/std_shot_*.mp4`, `concat_list.txt`, `concatenated_raw.mp4`) are automatically deleted in a `try...finally` block upon completion or failure, leaving original assets in `clean_shots/` completely intact.
2. **Output Validation**: Master output is verified with `ffprobe` for valid vertical dimensions (`1080x1920`), non-zero audio streams, minimum runtime, and file integrity before declaring success.

### Instagram Publishing Protections:
1. **300-Second Container Polling**: Extended Meta container polling up to 60 iterations (5-second intervals = 300s max) to accommodate 4K/60fps rendering without premature timeouts.
2. **Duplicate Publishing Guard**: Pre-checks publication history in `story_state.json`. If an episode is already recorded as published, the publisher warns cleanly and stops, preventing accidental duplicate Reels unless `--force` is explicitly provided.

---

## 6. Automated Test Suite

To verify all continuity, metadata, and causal dependency invariants across the studio:

```bash
# Run full automated test suite (12 tests)
python -m unittest discover tests

# Or run individual modules:
python -m unittest tests/test_continuity_engine.py
python -m unittest tests/test_story_dependency.py
python -m unittest tests/test_metadata_resolution.py
```

All 12 test assertions are verified passing (100% pass rate).
