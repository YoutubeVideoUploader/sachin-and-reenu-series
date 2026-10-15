#!/usr/bin/env python3
"""
=============================================================================
SEASON STORY MODEL (SSM)
Sachin & Reenu AI Animation Studio
=============================================================================
Authoritative, versioned narrative model covering all 10 episodes of a season.
Tracks premise, central conflict, plotlines, character arcs, relationship
development, timeline, decisions, mysteries/clues, prop continuity,
episode objectives, and the setup/climax/resolution of the Grand Finale.
=============================================================================
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class StoryFact:
    """Represents a canonical story fact with provenance tracking."""
    def __init__(
        self,
        fact_id: str,
        name: str,
        category: str,  # 'premise', 'clue', 'revelation', 'prop', 'relationship', 'decision', 'hazard'
        description: str,
        introduced_in: str,  # e.g., 'S3_E4_S10'
        established_in_version: str = "v1.0",
        entities: Optional[List[str]] = None,
        depends_on: Optional[List[str]] = None,
        status: str = "ACTIVE"  # 'ACTIVE', 'MODIFIED', 'REVOKED'
    ):
        self.fact_id = fact_id
        self.name = name
        self.category = category
        self.description = description
        self.introduced_in = introduced_in
        self.established_in_version = established_in_version
        self.entities = entities or []
        self.depends_on = depends_on or []
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "introduced_in": self.introduced_in,
            "established_in_version": self.established_in_version,
            "entities": self.entities,
            "depends_on": self.depends_on,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'StoryFact':
        return cls(
            fact_id=d["fact_id"],
            name=d.get("name", d["fact_id"]),
            category=d.get("category", "event"),
            description=d.get("description", ""),
            introduced_in=d.get("introduced_in", ""),
            established_in_version=d.get("established_in_version", "v1.0"),
            entities=d.get("entities", []),
            depends_on=d.get("depends_on", []),
            status=d.get("status", "ACTIVE")
        )


class CharacterState:
    """Tracks a character's current state within a specific episode."""
    def __init__(
        self,
        character_name: str,
        emotion: str,
        knowledge: List[str],
        relationship_notes: str,
        props_in_possession: List[str],
        physical_condition: str = "Healthy",
        location: str = "Munnar"
    ):
        self.character_name = character_name
        self.emotion = emotion
        self.knowledge = knowledge
        self.relationship_notes = relationship_notes
        self.props_in_possession = props_in_possession
        self.physical_condition = physical_condition
        self.location = location

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_name": self.character_name,
            "emotion": self.emotion,
            "knowledge": self.knowledge,
            "relationship_notes": self.relationship_notes,
            "props_in_possession": self.props_in_possession,
            "physical_condition": self.physical_condition,
            "location": self.location
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CharacterState':
        return cls(
            character_name=d.get("character_name", ""),
            emotion=d.get("emotion", "Neutral"),
            knowledge=d.get("knowledge", []),
            relationship_notes=d.get("relationship_notes", ""),
            props_in_possession=d.get("props_in_possession", []),
            physical_condition=d.get("physical_condition", "Healthy"),
            location=d.get("location", "")
        )


class EpisodeNarrative:
    """Detailed narrative model for an individual episode (10 shots)."""
    def __init__(
        self,
        episode_number: int,
        title_english: str,
        title_malayalam: str,
        synopsis: str,
        cliffhanger: str,
        central_objective: str,
        active_plotlines: List[str],
        clues_introduced: List[str],
        clues_resolved: List[str],
        character_states: Dict[str, CharacterState],
        shots: List[Dict[str, Any]]
    ):
        self.episode_number = episode_number
        self.title_english = title_english
        self.title_malayalam = title_malayalam
        self.synopsis = synopsis
        self.cliffhanger = cliffhanger
        self.central_objective = central_objective
        self.active_plotlines = active_plotlines
        self.clues_introduced = clues_introduced
        self.clues_resolved = clues_resolved
        self.character_states = character_states
        self.shots = shots

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_number": self.episode_number,
            "title_english": self.title_english,
            "title_malayalam": self.title_malayalam,
            "synopsis": self.synopsis,
            "cliffhanger": self.cliffhanger,
            "central_objective": self.central_objective,
            "active_plotlines": self.active_plotlines,
            "clues_introduced": self.clues_introduced,
            "clues_resolved": self.clues_resolved,
            "character_states": {k: v.to_dict() for k, v in self.character_states.items()},
            "shots": self.shots
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'EpisodeNarrative':
        char_states = {}
        for k, cs_dict in d.get("character_states", {}).items():
            char_states[k] = CharacterState.from_dict(cs_dict)
        return cls(
            episode_number=d["episode_number"],
            title_english=d.get("title_english", ""),
            title_malayalam=d.get("title_malayalam", ""),
            synopsis=d.get("synopsis", ""),
            cliffhanger=d.get("cliffhanger", ""),
            central_objective=d.get("central_objective", ""),
            active_plotlines=d.get("active_plotlines", []),
            clues_introduced=d.get("clues_introduced", []),
            clues_resolved=d.get("clues_resolved", []),
            character_states=char_states,
            shots=d.get("shots", [])
        )


class SeasonStoryModel:
    """Authoritative, season-wide narrative model covering all 10 episodes."""
    def __init__(
        self,
        season_number: int,
        season_title: str,
        premise: str,
        central_conflict: str,
        theme: str,
        version: str = "v1.0",
        episodes: Optional[Dict[int, EpisodeNarrative]] = None,
        facts: Optional[Dict[str, StoryFact]] = None,
        plotlines: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        self.season_number = season_number
        self.season_title = season_title
        self.premise = premise
        self.central_conflict = central_conflict
        self.theme = theme
        self.version = version
        self.episodes = episodes or {}
        self.facts = facts or {}
        self.plotlines = plotlines or {}

    def get_shot(self, episode_number: int, shot_number: int) -> Optional[Dict[str, Any]]:
        ep = self.episodes.get(episode_number)
        if not ep:
            return None
        for s in ep.shots:
            if s.get("shot_number") == shot_number:
                return s
        return None

    def get_shot_key(self, episode_number: int, shot_number: int) -> str:
        return f"S{self.season_number}_E{episode_number}_S{shot_number:02d}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "season_number": self.season_number,
            "season_title": self.season_title,
            "premise": self.premise,
            "central_conflict": self.central_conflict,
            "theme": self.theme,
            "version": self.version,
            "plotlines": self.plotlines,
            "facts": {k: v.to_dict() for k, v in self.facts.items()},
            "episodes": [self.episodes[ep_num].to_dict() for ep_num in sorted(self.episodes.keys())]
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'SeasonStoryModel':
        episodes = {}
        for ep_data in d.get("episodes", []):
            ep_obj = EpisodeNarrative.from_dict(ep_data)
            episodes[ep_obj.episode_number] = ep_obj

        facts = {}
        for f_id, f_data in d.get("facts", {}).items():
            facts[f_id] = StoryFact.from_dict(f_data)

        return cls(
            season_number=d.get("season_number", 3),
            season_title=d.get("season_title", "Season 3: The Munnar Trip"),
            premise=d.get("premise", ""),
            central_conflict=d.get("central_conflict", ""),
            theme=d.get("theme", ""),
            version=d.get("version", "v1.0"),
            episodes=episodes,
            facts=facts,
            plotlines=d.get("plotlines", {})
        )

    def export_flat_outline(self) -> Dict[str, Any]:
        """Exports in the exact format compatible with season_3_shot_outline.json."""
        episodes_list = []
        flattened_shots = []

        for ep_num in sorted(self.episodes.keys()):
            ep = self.episodes[ep_num]
            ep_dict = {
                "episode_number": ep.episode_number,
                "title_english": ep.title_english,
                "title_malayalam": ep.title_malayalam,
                "synopsis": ep.synopsis,
                "cliffhanger": ep.cliffhanger,
                "shots": ep.shots
            }
            episodes_list.append(ep_dict)
            for s in ep.shots:
                s_copy = dict(s)
                s_copy["episode_number"] = ep.episode_number
                flattened_shots.append(s_copy)

        return {
            "season_number": self.season_number,
            "season_title": self.season_title,
            "total_episodes": len(episodes_list),
            "total_shots": len(flattened_shots),
            "episodes": episodes_list,
            "flattened_shots": flattened_shots
        }


def build_canonical_season_3_model(workspace_root: Optional[Path] = None) -> SeasonStoryModel:
    """
    Constructs the canonical Season 3 model by ingesting season_3_shot_outline.json
    and augmenting it with explicit plotlines, character states, and story facts.
    """
    root = workspace_root or Path(".")
    outline_path = root / "season_3_shot_outline.json"
    if not outline_path.exists():
        fallback = Path(__file__).resolve().parent.parent / "season_3_shot_outline.json"
        if fallback.exists():
            root = fallback.parent
            outline_path = fallback
        else:
            raise FileNotFoundError(f"Outline file not found: {outline_path}")

    with open(outline_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    season_num = data.get("season_number", 3)
    season_title = data.get("season_title", "Season 3: The Munnar Trip (മൂന്നാർ യാത്ര)")
    premise = "Sachin, Reenu, and Amal embark on an adventurous college vacation trip to the misty hills of Munnar, where an eerie urban legend about a woman in the mist entangles them in a thirty-year-old high-range secret."
    central_conflict = "Unraveling the tragic secret of Bhadra (the woman in the mist) and the suspicious motives of homestay caretaker Sreedharan before the spirit traps them forever."
    theme = "Love, courage, and standing up for the forgotten truth in the face of fear."

    # Define Canonical Plotlines
    plotlines = {
        "PLOT_WOMAN_IN_MIST": {
            "name": "The Mystery of Bhadra (Woman in the Mist)",
            "description": "Apparitions, clues, and revelations regarding Bhadra's tragic past and trapped spirit.",
            "arc": "Introduction (Ep 1-2) -> Investigation (Ep 4-6) -> Discovery of Betrayal (Ep 7-8) -> Resolution (Ep 10)"
        },
        "PLOT_CARETAKER_SECRET": {
            "name": "Caretaker Sreedharan's Guilt",
            "description": "The homestay caretaker's warnings, locked room secrets, and eventual confession of guilt.",
            "arc": "Eerie Welcome (Ep 3) -> Room 13 Warning (Ep 3-4) -> Confrontation (Ep 9) -> Redemption (Ep 10)"
        },
        "PLOT_SACHIN_REENU_ROMANCE": {
            "name": "Sachin & Reenu Emotional Bond",
            "description": "Growing trust, mutual protection, and deepening romance through shared peril.",
            "arc": "Carefree romance (Ep 1) -> Protective anxiety (Ep 2-5) -> Bravery together (Ep 7-9) -> Deepened bond (Ep 10)"
        },
        "PLOT_AMAL_COMIC_SKEPTIC": {
            "name": "Amal's Skepticism to Panic",
            "description": "Amal's journey from witty skeptic and food lover to terrified believer and loyal savior.",
            "arc": "Jokes & driving (Ep 1-2) -> Reluctant follower (Ep 3-5) -> Panic & ghost detector (Ep 6-7) -> Heroic rescue (Ep 10)"
        }
    }

    # Canonical Facts with Provenance
    facts = {
        "FACT_MIST_ROAD_DEPARTURE": StoryFact(
            "FACT_MIST_ROAD_DEPARTURE",
            "Departure to Munnar",
            "premise",
            "Sachin, Reenu, and Amal travel by car through the winding high ranges of Munnar.",
            "S3_E1_S01",
            entities=["Sachin", "Reenu", "Amal", "Car"]
        ),
        "FACT_WOMAN_IN_MIST_SIGHTING": StoryFact(
            "FACT_WOMAN_IN_MIST_SIGHTING",
            "First Sighting of the Woman in the Mist",
            "mystery",
            "Reenu spots an ethereal woman standing in the mountain fog who vanishes without a trace.",
            "S3_E1_S10",
            entities=["Reenu", "Sachin", "Bhadra"]
        ),
        "FACT_CAR_STALLED_GAP_ROAD": StoryFact(
            "FACT_CAR_STALLED_GAP_ROAD",
            "Car Stalls on Gap Road",
            "hazard",
            "Amal's car engine abruptly sputters and dies on a desolate, foggy high-range road.",
            "S3_E2_S08",
            entities=["Amal", "Car"]
        ),
        "FACT_FREEZING_HANDPRINT": StoryFact(
            "FACT_FREEZING_HANDPRINT",
            "Icy Handprint on Car Window",
            "clue",
            "A freezing paranormal handprint slowly presses against the misted passenger window from outside.",
            "S3_E2_S10",
            entities=["Reenu", "Sachin", "Bhadra"],
            depends_on=["FACT_CAR_STALLED_GAP_ROAD"]
        ),
        "FACT_CARETAKER_MEETING": StoryFact(
            "FACT_CARETAKER_MEETING",
            "Meeting Caretaker Sreedharan",
            "character",
            "Elderly caretaker Sreedharan welcomes the shivering trio into the secluded colonial homestay.",
            "S3_E3_S02",
            entities=["Sreedharan (The Caretaker)", "Sachin", "Reenu", "Amal"]
        ),
        "FACT_LOCKED_ROOM_WARNING": StoryFact(
            "FACT_LOCKED_ROOM_WARNING",
            "Warning About Room 13",
            "decision",
            "Sreedharan strictly warns them never to open or enter Room 13 at the end of the hallway.",
            "S3_E3_S07",
            entities=["Sreedharan (The Caretaker)", "Room 13"]
        ),
        "FACT_VINTAGE_PHOTO_CLUE": StoryFact(
            "FACT_VINTAGE_PHOTO_CLUE",
            "Discovery of the Three-Person Photograph",
            "clue",
            "Inside Room 13, Amal discovers an eerie vintage photograph depicting three people instead of two.",
            "S3_E4_S10",
            entities=["Amal", "Sachin", "Reenu", "Vintage Photo", "Room 13"],
            depends_on=["FACT_LOCKED_ROOM_WARNING"]
        ),
        "FACT_ABANDONED_FACTORY_TREK": StoryFact(
            "FACT_ABANDONED_FACTORY_TREK",
            "Trek into the Tea Plantation and Old Factory",
            "location",
            "During a morning walk in the tea plantation, they enter an abandoned British-era tea factory.",
            "S3_E5_S05",
            entities=["Sachin", "Reenu", "Amal", "Abandoned Factory"]
        ),
        "FACT_NOTEBOOK_DRAWING_FOUND": StoryFact(
            "FACT_NOTEBOOK_DRAWING_FOUND",
            "Bhadra's Notebook and Sketch",
            "clue",
            "Reenu and Sachin discover an old notebook in the factory containing a sketch matching the woman on the road.",
            "S3_E5_S06",
            entities=["Reenu", "Sachin", "Bhadra"],
            depends_on=["FACT_ABANDONED_FACTORY_TREK", "FACT_WOMAN_IN_MIST_SIGHTING"]
        ),
        "FACT_WARNING_NOTE_DISCOVERED": StoryFact(
            "FACT_WARNING_NOTE_DISCOVERED",
            "Warning Note to Avoid the Bridge",
            "clue",
            "Reenu discovers an anonymous note slipped inside the homestay warning: 'Do not go to the old bridge'.",
            "S3_E6_S10",
            entities=["Reenu", "Warning Note"]
        ),
        "FACT_BHADRA_LOCKET_FOUND": StoryFact(
            "FACT_BHADRA_LOCKET_FOUND",
            "Discovery of the Antique Locket",
            "prop",
            "At the forbidden dilapidated bridge, Reenu recovers an antique silver locket belonging to Bhadra.",
            "S3_E7_S04",
            entities=["Reenu", "Bhadra's Locket"],
            depends_on=["FACT_WARNING_NOTE_DISCOVERED"]
        ),
        "FACT_BRIDGE_COLLAPSE": StoryFact(
            "FACT_BRIDGE_COLLAPSE",
            "Old Bridge Collapses",
            "hazard",
            "A structural crash in the dense forest destroys the old bridge walkway, cutting off that route.",
            "S3_E7_S10",
            entities=["Bridge", "Amal", "Sachin"]
        ),
        "FACT_TORN_BETRAYAL_LETTER": StoryFact(
            "FACT_TORN_BETRAYAL_LETTER",
            "Uncovering the Betrayal Letter",
            "revelation",
            "In an estate shed, Sachin and Reenu find newspaper clippings and a letter proving Bhadra was deliberately betrayed.",
            "S3_E8_S10",
            entities=["Sachin", "Reenu", "Betrayal Letter"],
            depends_on=["FACT_BRIDGE_COLLAPSE"]
        ),
        "FACT_CARETAKER_CONFESSION": StoryFact(
            "FACT_CARETAKER_CONFESSION",
            "Caretaker Sreedharan's Confession",
            "revelation",
            "Confronted with the letter, Sreedharan confesses he kept the truth hidden and warns Bhadra's spirit returns tonight.",
            "S3_E9_S02",
            entities=["Sreedharan (The Caretaker)", "Sachin", "Reenu"],
            depends_on=["FACT_TORN_BETRAYAL_LETTER", "FACT_VINTAGE_PHOTO_CLUE"]
        ),
        "FACT_FINALE_EVIDENCE_RECOVERY": StoryFact(
            "FACT_FINALE_EVIDENCE_RECOVERY",
            "Final Clue Recovered from Collapsing Factory",
            "climax",
            "Sachin recovers the hidden compartment in the factory bringing justice to Bhadra before the building collapses.",
            "S3_E10_S04",
            entities=["Sachin", "Reenu", "Amal", "Bhadra"],
            depends_on=["FACT_CARETAKER_CONFESSION", "FACT_BHADRA_LOCKET_FOUND"]
        ),
        "FACT_FINALE_PHOTO_PEACE_REVEAL": StoryFact(
            "FACT_FINALE_PHOTO_PEACE_REVEAL",
            "The Ghost in the Photo Smiles in Peace",
            "payoff",
            "In the departing car, Sachin and Amal look at the vintage photo and see Bhadra's spirit smiling in peaceful release.",
            "S3_E10_S10",
            entities=["Sachin", "Amal", "Vintage Photo", "Bhadra"],
            depends_on=["FACT_VINTAGE_PHOTO_CLUE", "FACT_FINALE_EVIDENCE_RECOVERY"]
        )
    }

    # Episode Objectives & Character States
    objectives = {
        1: "Reach Munnar before dark while enjoying the romantic mountain drive.",
        2: "Survive the engine breakdown and mysterious presence on foggy Gap Road.",
        3: "Settle into the eerie colonial homestay and heed the caretaker's rules.",
        4: "Investigate Room 13 to identify the source of midnight whispers.",
        5: "Explore the tea plantation and uncover the truth of the abandoned factory.",
        6: "Detect the stalker and decipher the mysterious warning note.",
        7: "Investigate the forbidden bridge and recover the ghost's lost locket.",
        8: "Seek shelter from the storm and piece together the tragic betrayal.",
        9: "Confront Caretaker Sreedharan and prepare for the midnight reckoning.",
        10: "Grand Finale: Recover the final evidence, escape the collapsing factory, and grant peace to Bhadra's spirit."
    }

    episodes = {}
    for ep_dict in data.get("episodes", []):
        ep_n = ep_dict.get("episode_number")
        shots = ep_dict.get("shots", [])

        # Build Character States per Episode
        c_sachin = CharacterState(
            "Sachin",
            emotion="Romantic & Excited" if ep_n == 1 else ("Protective & Anxious" if ep_n < 7 else "Determined & Brave"),
            knowledge=["Munnar route", "Gap road fog"] + (["Photo clue"] if ep_n >= 4 else []) + (["Letter clue"] if ep_n >= 8 else []),
            relationship_notes="Cherishing vacation with Reenu" if ep_n < 5 else "Deeply bonded with Reenu through shared peril",
            props_in_possession=["Travel cross-bag", "Phone"] + (["Car keys"] if ep_n == 2 else []),
            location="Gap Road" if ep_n <= 2 else ("Homestay" if ep_n in (3, 4, 6, 9) else "Factory/Plantation")
        )

        c_reenu = CharacterState(
            "Reenu",
            emotion="Cheerful & Romantic" if ep_n == 1 else ("Intrigued & Sensitive to spirit" if ep_n < 7 else "Empathetic to Bhadra"),
            knowledge=["Woman sighting"] + (["Locket clue"] if ep_n >= 7 else []),
            relationship_notes="Trusting Sachin completely",
            props_in_possession=["Silver wristwatch", "Handbag"] + (["Antique locket"] if ep_n >= 7 else []),
            location="Gap Road" if ep_n <= 2 else ("Homestay" if ep_n in (3, 4, 6, 9) else "Factory/Plantation")
        )

        c_amal = CharacterState(
            "Amal",
            emotion="Jovial & Carefree" if ep_n == 1 else ("Panicked & Skeptical" if ep_n < 8 else "Loyal Defender"),
            knowledge=["Driving car"] + (["Ghost detector"] if ep_n == 6 else []),
            relationship_notes="Best friend and third wheel",
            props_in_possession=["Car steering wheel", "Smartphone GPS"],
            location="Gap Road" if ep_n <= 2 else ("Homestay" if ep_n in (3, 4, 6, 9) else "Factory/Plantation")
        )

        char_states = {"Sachin": c_sachin, "Reenu": c_reenu, "Amal": c_amal}

        clues_in = []
        if ep_n == 2: clues_in.append("FACT_FREEZING_HANDPRINT")
        elif ep_n == 4: clues_in.append("FACT_VINTAGE_PHOTO_CLUE")
        elif ep_n == 5: clues_in.append("FACT_NOTEBOOK_DRAWING_FOUND")
        elif ep_n == 6: clues_in.append("FACT_WARNING_NOTE_DISCOVERED")
        elif ep_n == 7: clues_in.append("FACT_BHADRA_LOCKET_FOUND")
        elif ep_n == 8: clues_in.append("FACT_TORN_BETRAYAL_LETTER")

        clues_res = []
        if ep_n == 9: clues_res.extend(["FACT_TORN_BETRAYAL_LETTER", "FACT_CARETAKER_CONFESSION"])
        elif ep_n == 10: clues_res.extend(["FACT_VINTAGE_PHOTO_CLUE", "FACT_BHADRA_LOCKET_FOUND", "FACT_FINALE_EVIDENCE_RECOVERY"])

        ep_narrative = EpisodeNarrative(
            episode_number=ep_n,
            title_english=ep_dict.get("title_english", f"Episode {ep_n}"),
            title_malayalam=ep_dict.get("title_malayalam", ""),
            synopsis=ep_dict.get("synopsis", ""),
            cliffhanger=ep_dict.get("cliffhanger", ""),
            central_objective=objectives.get(ep_n, f"Complete Episode {ep_n} beat"),
            active_plotlines=["PLOT_WOMAN_IN_MIST", "PLOT_CARETAKER_SECRET", "PLOT_SACHIN_REENU_ROMANCE", "PLOT_AMAL_COMIC_SKEPTIC"],
            clues_introduced=clues_in,
            clues_resolved=clues_res,
            character_states=char_states,
            shots=shots
        )
        episodes[ep_n] = ep_narrative

    model = SeasonStoryModel(
        season_number=season_num,
        season_title=season_title,
        premise=premise,
        central_conflict=central_conflict,
        theme=theme,
        version="v1.0",
        episodes=episodes,
        facts=facts,
        plotlines=plotlines
    )
    return model


if __name__ == "__main__":
    model = build_canonical_season_3_model()
    print(f"✓ Canonical Season {model.season_number} Model Built Successfully!")
    print(f"  Episodes: {len(model.episodes)}")
    print(f"  Facts: {len(model.facts)}")
    print(f"  Plotlines: {len(model.plotlines)}")
