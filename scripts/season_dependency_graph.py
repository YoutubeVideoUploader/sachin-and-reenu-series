#!/usr/bin/env python3
"""
=============================================================================
SEASON DEPENDENCY GRAPH (SDG)
Sachin & Reenu AI Animation Studio
=============================================================================
Multi-relational directed causal graph connecting:
- Shots (100 shots: S3_E1_S01 through S3_E10_S10)
- Episodes (E1 through E10)
- Story Facts (Premise, Clues, Decisions, Revelations, Props, Hazards)
- Plotlines (Mystery, Romance, Caretaker Secret, Comic Arc)
- Character States (Knowledge, Emotion, Props, Relationships)
- Grand Finale Components (Setup, Climax, Payoff)

Edge Relationships:
- CAUSED_BY, DEPENDS_ON, REVEALS, FORESHADOWS, RESOLVES,
  CHANGES_KNOWLEDGE, CHANGES_RELATIONSHIP, TRANSFERS_PROP,
  ESTABLISHES_LOCATION, PAYS_OFF
=============================================================================
"""

import sys
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict, deque
from season_story_model import SeasonStoryModel, StoryFact, build_canonical_season_3_model

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class GraphEdge:
    """Directed edge in the season narrative graph."""
    def __init__(self, source: str, target: str, relationship: str, description: str = ""):
        self.source = source
        self.target = target
        self.relationship = relationship  # e.g., 'DEPENDS_ON', 'REVEALS', 'PAYS_OFF'
        self.description = description

    def to_dict(self) -> Dict[str, str]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "description": self.description
        }


class SeasonDependencyGraph:
    """
    Season-wide causal dependency graph covering all 10 episodes and the Grand Finale.
    """
    def __init__(self, story_model: SeasonStoryModel):
        self.story_model = story_model
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.forward_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self.reverse_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self.shot_to_facts: Dict[str, List[str]] = defaultdict(list)
        self.fact_to_shots: Dict[str, List[str]] = defaultdict(list)
        self._build_graph()

    def _add_edge(self, source: str, target: str, rel: str, desc: str = ""):
        edge = GraphEdge(source, target, rel, desc)
        self.forward_edges[source].append(edge)
        self.reverse_edges[target].append(edge)

    def _build_graph(self):
        """Constructs all nodes and semantic causal relationships."""
        # 1. Register Episode and Shot Nodes
        for ep_num in sorted(self.story_model.episodes.keys()):
            ep = self.story_model.episodes[ep_num]
            ep_node_id = f"EPISODE_{ep_num}"
            self.nodes[ep_node_id] = {
                "id": ep_node_id,
                "type": "EPISODE",
                "episode_number": ep_num,
                "title": ep.title_english,
                "central_objective": ep.central_objective
            }

            for s in ep.shots:
                s_num = s.get("shot_number")
                shot_key = self.story_model.get_shot_key(ep_num, s_num)
                self.nodes[shot_key] = {
                    "id": shot_key,
                    "type": "SHOT",
                    "episode_number": ep_num,
                    "shot_number": s_num,
                    "speaker": s.get("speaker") or s.get("character"),
                    "action": s.get("action") or s.get("action_summary"),
                    "dialogue": s.get("dialogue_malayalam") or s.get("dialogue"),
                    "location": s.get("location")
                }
                # Shot belongs to episode
                self._add_edge(shot_key, ep_node_id, "PART_OF_EPISODE")

        # 2. Register Facts and Map to Introducing Shots
        for f_id, fact in self.story_model.facts.items():
            self.nodes[f_id] = {
                "id": f_id,
                "type": "FACT",
                "name": fact.name,
                "category": fact.category,
                "description": fact.description,
                "introduced_in": fact.introduced_in,
                "entities": fact.entities
            }
            if fact.introduced_in and fact.introduced_in in self.nodes:
                self.shot_to_facts[fact.introduced_in].append(f_id)
                self.fact_to_shots[f_id].append(fact.introduced_in)
                self._add_edge(fact.introduced_in, f_id, "INTRODUCES_FACT", f"Introduces {fact.name}")

            # Inter-fact dependencies
            for dep_fact_id in fact.depends_on:
                if dep_fact_id in self.story_model.facts:
                    self._add_edge(dep_fact_id, f_id, "DEPENDS_ON", f"{f_id} requires {dep_fact_id}")

        # 3. Canonical Season 3 Narrative Causal Handshakes (Butterfly Links)
        # Episode 1 -> Episode 2
        self._add_edge("S3_E1_S10", "S3_E2_S01", "FORESHADOWS", "E1 woman in mist sighting builds dread for E2 Gap Road transit")
        self._add_edge("FACT_WOMAN_IN_MIST_SIGHTING", "FACT_FREEZING_HANDPRINT", "FORESHADOWS", "First sighting escalates into physical handprint contact")

        # Episode 2 -> Episode 3
        self._add_edge("FACT_CAR_STALLED_GAP_ROAD", "FACT_CARETAKER_MEETING", "CAUSED_BY", "Breakdown on road forces stranded arrival at homestay")
        self._add_edge("FACT_FREEZING_HANDPRINT", "FACT_LOCKED_ROOM_WARNING", "CHANGES_KNOWLEDGE", "Terror from handprint primes curiosity about supernatural warning")

        # Episode 3 -> Episode 4
        self._add_edge("FACT_LOCKED_ROOM_WARNING", "FACT_VINTAGE_PHOTO_CLUE", "DEPENDS_ON", "Warning creates irresistible motive to inspect Room 13")
        self._add_edge("S3_E3_S10", "S3_E4_S01", "CAUSED_BY", "Cliffhanger door creak directly triggers entering Room 13")

        # Episode 4 -> Episode 8, Episode 9, Episode 10 (CRITICAL LONG-RANGE MULTI-HOP)
        self._add_edge("FACT_VINTAGE_PHOTO_CLUE", "FACT_TORN_BETRAYAL_LETTER", "FORESHADOWS", "The 3rd person in photo foreshadows identity in betrayal letter")
        self._add_edge("FACT_VINTAGE_PHOTO_CLUE", "FACT_CARETAKER_CONFESSION", "DEPENDS_ON", "Confronting Sreedharan requires knowing about the 3-person photograph")
        self._add_edge("FACT_VINTAGE_PHOTO_CLUE", "FACT_FINALE_PHOTO_PEACE_REVEAL", "PAYS_OFF", "Grand finale ending photo reveal is the direct payoff of E4 photo discovery")
        self._add_edge("S3_E4_S10", "S3_E10_S10", "PAYS_OFF", "The photo discovered in E4 S10 reveals the smiling spirit in E10 S10")

        # Episode 5 -> Episode 6
        self._add_edge("FACT_ABANDONED_FACTORY_TREK", "FACT_NOTEBOOK_DRAWING_FOUND", "ESTABLISHES_LOCATION", "Trek into tea bushes leads to notebook discovery in old factory")
        self._add_edge("FACT_NOTEBOOK_DRAWING_FOUND", "S3_E6_S03", "REVEALS", "Notebook drawing connects to eerie factory wall markings in E6")

        # Episode 6 -> Episode 7
        self._add_edge("FACT_WARNING_NOTE_DISCOVERED", "FACT_BHADRA_LOCKET_FOUND", "CAUSED_BY", "Warning note triggers Reenu's determination to investigate the old bridge")
        self._add_edge("S3_E6_S10", "S3_E7_S01", "DEPENDS_ON", "Reenu showing the bridge note is the opening action of E7")

        # Episode 7 -> Episode 8
        self._add_edge("FACT_BHADRA_LOCKET_FOUND", "FACT_FINALE_EVIDENCE_RECOVERY", "TRANSFERS_PROP", "Bhadra's locket serves as supernatural talisman in finale")
        self._add_edge("FACT_BRIDGE_COLLAPSE", "FACT_TORN_BETRAYAL_LETTER", "CAUSED_BY", "Bridge crash cuts off escape, forcing them into estate shed where letter is found")
        self._add_edge("S3_E7_S10", "S3_E8_S01", "CAUSED_BY", "Escape from crashing bridge leads directly to taking shelter in estate shed")

        # Episode 8 -> Episode 9
        self._add_edge("FACT_TORN_BETRAYAL_LETTER", "FACT_CARETAKER_CONFESSION", "REVEALS", "The letter directly enables Sachin to break Sreedharan's silence")
        self._add_edge("S3_E8_S10", "S3_E9_S01", "DEPENDS_ON", "Reading the letter text leads immediately to morning confrontation with Sreedharan")

        # Episode 9 -> Episode 10 (GRAND FINALE DEPENDENCIES)
        self._add_edge("FACT_CARETAKER_CONFESSION", "FACT_FINALE_EVIDENCE_RECOVERY", "CAUSED_BY", "Sreedharan's revelation directs them to final hidden compartment in factory")
        self._add_edge("S3_E9_S10", "S3_E10_S01", "DEPENDS_ON", "Caretaker's door opening warning triggers midnight sprint to the factory")

        # Finale Internal Causal Sequence
        self._add_edge("FACT_FINALE_EVIDENCE_RECOVERY", "FACT_FINALE_PHOTO_PEACE_REVEAL", "RESOLVES", "Recovering evidence frees Bhadra's spirit, enabling peaceful photo payoff")

    def get_forward_dependencies(self, start_node_id: str) -> Dict[str, Any]:
        """
        Transitive downstream reachability via BFS.
        Discovers all directly and indirectly affected nodes across the season.
        """
        direct_nodes: Set[str] = set()
        indirect_nodes: Set[str] = set()
        visited: Set[str] = set()
        causal_paths: Dict[str, List[GraphEdge]] = {}

        # Direct successors
        for edge in self.forward_edges.get(start_node_id, []):
            direct_nodes.add(edge.target)
            causal_paths[edge.target] = [edge]

        queue = deque(list(direct_nodes))
        visited.add(start_node_id)
        visited.update(direct_nodes)

        while queue:
            curr = queue.popleft()
            curr_path = causal_paths.get(curr, [])
            for edge in self.forward_edges.get(curr, []):
                tgt = edge.target
                if tgt not in visited:
                    visited.add(tgt)
                    indirect_nodes.add(tgt)
                    causal_paths[tgt] = curr_path + [edge]
                    queue.append(tgt)

        return {
            "start_node": start_node_id,
            "direct_affected_nodes": sorted(list(direct_nodes)),
            "indirect_affected_nodes": sorted(list(indirect_nodes)),
            "all_affected_nodes": sorted(list(direct_nodes.union(indirect_nodes))),
            "causal_paths": causal_paths
        }

    def trace_butterfly_impact(
        self,
        pivot_ep: int,
        pivot_shot: int,
        new_action: str,
        new_dialogue: str,
        removed_fact_ids: Optional[List[str]] = None,
        added_fact_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Season-Wide Butterfly-Effect Propagation Engine.
        Identifies:
        - Directly affected scenes and episodes
        - Indirectly affected scenes and episodes
        - Unaffected episodes with explicit rationale
        - Specific impact on Episode 10 Grand Finale
        """
        pivot_key = self.story_model.get_shot_key(pivot_ep, pivot_shot)
        if pivot_key not in self.nodes:
            raise ValueError(f"Shot {pivot_key} does not exist in season {self.story_model.season_number}.")

        # 1. Identify Seed Nodes for Propagation
        seed_nodes = {pivot_key}
        for f_id in self.shot_to_facts.get(pivot_key, []):
            seed_nodes.add(f_id)
        if removed_fact_ids:
            seed_nodes.update(removed_fact_ids)
        if added_fact_ids:
            seed_nodes.update(added_fact_ids)

        all_direct: Set[str] = set()
        all_indirect: Set[str] = set()
        causal_explanations: Dict[str, str] = {}

        # 2. Trace Forward Dependencies from each Seed Node
        for s_node in seed_nodes:
            deps = self.get_forward_dependencies(s_node)
            for d in deps["direct_affected_nodes"]:
                all_direct.add(d)
                path = deps["causal_paths"].get(d, [])
                if path:
                    causal_explanations[d] = f"Directly affected via [{path[0].relationship}]: {path[0].description or path[0].source + ' -> ' + path[0].target}"
            for ind in deps["indirect_affected_nodes"]:
                all_indirect.add(ind)
                path = deps["causal_paths"].get(ind, [])
                if path:
                    chain = " -> ".join([e.source for e in path] + [path[-1].target])
                    causal_explanations[ind] = f"Indirectly affected via chain: ({chain}) - {path[-1].description or path[-1].relationship}"

        # Ensure seed nodes themselves are considered directly affected
        all_direct.add(pivot_key)
        causal_explanations[pivot_key] = f"Pivot edit shot: modified action/dialogue at {pivot_key}"

        # 3. Categorize Episodes
        all_affected_nodes = all_direct.union(all_indirect)
        affected_episodes: Set[int] = set()
        affected_shots_map: Dict[int, List[str]] = defaultdict(list)

        for node_id in all_affected_nodes:
            node_data = self.nodes.get(node_id, {})
            if node_data.get("type") == "EPISODE":
                affected_episodes.add(node_data["episode_number"])
            elif node_data.get("type") == "SHOT":
                ep_n = node_data["episode_number"]
                affected_episodes.add(ep_n)
                affected_shots_map[ep_n].append(node_id)
            elif node_data.get("type") == "FACT":
                intro = node_data.get("introduced_in", "")
                if intro in self.nodes:
                    ep_n = self.nodes[intro]["episode_number"]
                    affected_episodes.add(ep_n)
                    affected_shots_map[ep_n].append(intro)

        # Chronological boundary check: if Shot N is modified, Shot N+1 in same or next ep is checked
        # Check boundary with immediate next shot
        all_shots_flat = []
        for ep_n in sorted(self.story_model.episodes.keys()):
            for s in self.story_model.episodes[ep_n].shots:
                all_shots_flat.append(self.story_model.get_shot_key(ep_n, s["shot_number"]))

        if pivot_key in all_shots_flat:
            p_idx = all_shots_flat.index(pivot_key)
            if p_idx + 1 < len(all_shots_flat):
                next_shot_key = all_shots_flat[p_idx + 1]
                all_direct.add(next_shot_key)
                next_ep = self.nodes[next_shot_key]["episode_number"]
                affected_episodes.add(next_ep)
                affected_shots_map[next_ep].append(next_shot_key)
                if next_shot_key not in causal_explanations:
                    causal_explanations[next_shot_key] = f"Immediate chronological boundary handshake following {pivot_key}"

        # 4. Determine Unaffected Episodes & Compute Rationale
        all_episode_nums = set(self.story_model.episodes.keys())
        unaffected_episodes = sorted(list(all_episode_nums - affected_episodes))
        unaffected_rationale: Dict[int, str] = {}

        for u_ep in unaffected_episodes:
            if u_ep < pivot_ep:
                unaffected_rationale[u_ep] = f"Episode {u_ep} occurs chronologically prior to the pivot edit in Episode {pivot_ep} and has zero forward causal dependencies on the change."
            else:
                unaffected_rationale[u_ep] = f"Episode {u_ep} has independent local story beats with zero graph edges connecting from the changed facts or downstream butterfly paths."

        # 5. Grand Finale (Episode 10) Specific Evaluation
        finale_affected = 10 in affected_episodes
        finale_rationale = ""
        finale_affected_elements = []

        if finale_affected:
            for node_id in all_affected_nodes:
                if "E10" in node_id or "FINALE" in node_id:
                    finale_affected_elements.append(node_id)
            finale_rationale = (
                f"Episode 10 (Grand Finale) IS affected because the edit ripples into "
                f"{len(finale_affected_elements)} finale component(s): {', '.join(finale_affected_elements[:4])}. "
                f"The climax resolution, clues payoff, and ending scene require re-evaluation."
            )
        else:
            finale_rationale = (
                "Episode 10 (Grand Finale) is UNAFFECTED. The pivot edit does not alter the essential clues "
                "(photo, notebook, locket, letter), the factory confrontation, or the resolution of Bhadra's spirit. "
                "The grand finale remains completely valid and causally supported."
            )

        return {
            "pivot_shot": pivot_key,
            "pivot_episode": pivot_ep,
            "seed_nodes": sorted(list(seed_nodes)),
            "directly_affected_nodes": sorted(list(all_direct)),
            "indirectly_affected_nodes": sorted(list(all_indirect)),
            "affected_episodes": sorted(list(affected_episodes)),
            "unaffected_episodes": unaffected_episodes,
            "unaffected_rationale": unaffected_rationale,
            "affected_shots_by_episode": {k: sorted(list(set(v))) for k, v in affected_shots_map.items()},
            "causal_explanations": causal_explanations,
            "grand_finale_evaluation": {
                "is_affected": finale_affected,
                "rationale": finale_rationale,
                "affected_elements": finale_affected_elements
            }
        }


if __name__ == "__main__":
    model = build_canonical_season_3_model()
    graph = SeasonDependencyGraph(model)
    print(f"✓ Season Dependency Graph Built Successfully!")
    print(f"  Nodes: {len(graph.nodes)}")
    print(f"  Forward Edge Out-Degrees: {sum(len(edges) for edges in graph.forward_edges.values())}")

    # Test Butterfly Impact: Edit Episode 4 Photo Clue
    impact = graph.trace_butterfly_impact(4, 10, "Sachin drops and breaks the photo", "അയ്യോ!")
    print("\n[Butterfly Test: Edit Ep 4 Shot 10]")
    print(f"  Affected Episodes: {impact['affected_episodes']}")
    print(f"  Unaffected Episodes: {impact['unaffected_episodes']}")
    print(f"  Grand Finale Affected: {impact['grand_finale_evaluation']['is_affected']}")
    print(f"  Finale Rationale: {impact['grand_finale_evaluation']['rationale']}")
