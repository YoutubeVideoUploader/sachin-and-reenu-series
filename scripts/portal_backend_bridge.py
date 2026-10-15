#!/usr/bin/env python3
"""
=============================================================================
STUDIO PORTAL BACKEND BRIDGE (SPBB)
Sachin & Reenu AI Animation Studio
=============================================================================
Lightweight local HTTP bridge connecting browser portal.html to the canonical
Season-Wide Butterfly-Effect Story Propagation Engine.

Handles:
- POST /api/propagate_edit: Evaluates butterfly reach and generates 11-point report
- POST /api/approve_revision: Atomically commits revision to outline, state, prompts, portal
- POST /api/rollback_revision: 1-click byte-exact baseline restoration
- POST /exec: Intercepts portal Google Apps Script saves (action: update_shot_prompt)
              and routes them through season propagation instead of direct sheet write
- GET /portal.html: Serves the studio web portal
=============================================================================
"""

import os
import sys
import json
import argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from season_story_propagation_engine import SeasonStoryPropagationEngine


class StudioPortalHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler for Studio Portal Bridge."""

    def __init__(self, *args, workspace_root=None, **kwargs):
        self.workspace_root = workspace_root or REPO_ROOT
        super().__init__(*args, directory=str(self.workspace_root), **kwargs)

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "RUNNING", "engine": "SeasonStoryPropagationEngine"}).encode("utf-8"))
            return
        if parsed.path in ["/api/season_shot_outline", "/exec"] or "action=get_season_shot_outline" in parsed.query:
            outline_file = Path(self.directory) / "season_3_shot_outline.json"
            if outline_file.exists():
                self._set_headers(200, content_type="application/json; charset=utf-8")
                self.wfile.write(outline_file.read_bytes())
                return
        if parsed.path == "/":
            self.path = "/portal.html"
        # Serve static files from workspace root
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception as e:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {e}"}).encode("utf-8"))
            return

        engine = SeasonStoryPropagationEngine(workspace_root=self.workspace_root)

        # 1. Direct API: Propagate Edit
        if parsed.path == "/api/propagate_edit" or body.get("action") == "propagate_shot_edit":
            try:
                proposal = engine.propose_season_edit(
                    season_number=int(body.get("season_number", 3)),
                    episode_number=int(body.get("episode_number", 1)),
                    shot_number=int(body.get("shot_number", 1)),
                    new_action=body.get("new_action", ""),
                    new_dialogue=body.get("new_dialogue", ""),
                    user_notes=body.get("user_notes", "Browser portal edit"),
                    removed_fact_ids=body.get("removed_fact_ids"),
                    added_fact_ids=body.get("added_fact_ids")
                )
                report_markdown = engine.format_11_point_report(proposal)
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "proposal": proposal,
                    "report_markdown": report_markdown
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 2. Direct API: Approve & Commit Revision
        if parsed.path == "/api/approve_revision" or body.get("action") == "approve_season_revision":
            rev_id = body.get("revision_id")
            if not rev_id:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing revision_id"}).encode("utf-8"))
                return
            try:
                commit_res = engine.approve_and_commit(rev_id)
                self._set_headers(200)
                self.wfile.write(json.dumps(commit_res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 3. Direct API: Rollback Revision
        if parsed.path == "/api/rollback_revision" or body.get("action") == "rollback_season_revision":
            rev_id = body.get("revision_id")
            if not rev_id:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Missing revision_id"}).encode("utf-8"))
                return
            try:
                roll_res = engine.rollback(rev_id)
                self._set_headers(200)
                self.wfile.write(json.dumps(roll_res, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 3b. Direct API: Harmonize Season Flow
        if parsed.path == "/api/harmonize_season_flow" or body.get("action") == "harmonize_season_flow":
            try:
                from harmonize_season_flow import SeasonFlowHarmonizer
                harm = SeasonFlowHarmonizer(workspace_root=self.workspace_root)
                s_num = int(body.get("season_number", 3))
                no_ai = bool(body.get("no_ai", False))
                rep = harm.harmonize_all_100_shots(season_number=s_num, use_ai_review=not no_ai)
                self._set_headers(200)
                self.wfile.write(json.dumps({"status": "SUCCESS", "report": rep}, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # 4. Intercept Portal's update_shot_prompt: Connect save route to propagation engine
        if parsed.path in ("/exec", "/api/save_shot") or body.get("action") == "update_shot_prompt":
            ep_num = int(body.get("episode_number", 1))
            shot_num = int(body.get("shot_number", 1))
            shot_data = body.get("shot_data", {})
            action = shot_data.get("action_summary") or shot_data.get("action") or ""
            dialogue = shot_data.get("dialogue_malayalam") or shot_data.get("dialogue") or ""

            try:
                # Run propagation
                proposal = engine.propose_season_edit(
                    season_number=int(body.get("season_number", 3)),
                    episode_number=ep_num,
                    shot_number=shot_num,
                    new_action=action,
                    new_dialogue=dialogue,
                    user_notes="Browser portal single shot save"
                )
                report_markdown = engine.format_11_point_report(proposal)

                # Return reviewable proposal rather than silently writing to Sheet
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "status": "PROPOSED_STAGED",
                    "requires_approval": True,
                    "revision_id": proposal["revision_id"],
                    "proposal": proposal,
                    "butterfly_impact": proposal["butterfly_impact"],
                    "redevelopment": proposal["redevelopment"],
                    "stale_asset_audit": proposal["stale_asset_audit"],
                    "narrative_coherence": proposal.get("narrative_coherence", {}),
                    "report_markdown": report_markdown
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": f"Unknown endpoint: {parsed.path}"}).encode("utf-8"))


def create_server(host="127.0.0.1", port=8765, workspace_root=None):
    ws_root = Path(workspace_root) if workspace_root else REPO_ROOT

    def handler_factory(*args, **kwargs):
        return StudioPortalHandler(*args, workspace_root=ws_root, **kwargs)

    server = ThreadingHTTPServer((host, port), handler_factory)
    return server


def run_bridge_server(host="127.0.0.1", port=8765, workspace_root=None):
    server = create_server(host=host, port=port, workspace_root=workspace_root)
    print(f"🎬 Studio Portal Bridge Server running on http://{host}:{port}/")
    print(f"   Serving workspace: {workspace_root or REPO_ROOT}")
    print(f"   API Endpoints:")
    print(f"     • POST /api/propagate_edit")
    print(f"     • POST /api/approve_revision")
    print(f"     • POST /api/rollback_revision")
    print(f"     • POST /exec (Connected save route)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping bridge server...")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Studio Portal Backend Bridge")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8765, help="Port number")
    parser.add_argument("--workspace", type=str, default=None, help="Workspace directory")
    args = parser.parse_args()
    run_bridge_server(host=args.host, port=args.port, workspace_root=args.workspace)
