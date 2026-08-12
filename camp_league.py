"""Reusable data model for the Camp Power-Up Minecraft & Pokémon League.

This module captures the baseline peer-to-peer rules, challenge sets, and league
structure used across the July pilot, November league, March refinement camp,
and June flagship event.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ScoringItem:
    """A single scoring category or challenge objective."""

    name: str
    points: int


@dataclass(frozen=True)
class GymDefinition:
    """A single gym challenge within the Pokémon league."""

    name: str
    badge_name: str
    specialty: str


@dataclass(frozen=True)
class Challenge:
    """A single scavenger hunt or tournament prompt."""

    description: str


@dataclass(frozen=True)
class Award:
    """An award or recognition recognized at camp."""

    name: str
    description: str


BUILD_BATTLE_THEMES = [
    "Pokémon Gym",
    "Dream House",
    "Castle",
    "Treehouse",
    "Zoo",
    "Theme Park",
    "Secret Base",
    "Volcano Base",
    "Underwater City",
    "Space Station",
]

BUILD_BATTLE_RUBRIC = [
    ScoringItem("Creativity", 10),
    ScoringItem("Detail", 10),
    ScoringItem("Theme", 10),
    ScoringItem("Presentation", 10),
]

SURVIVAL_OBJECTIVES = [
    ScoringItem("Build Shelter", 5),
    ScoringItem("Build Farm", 5),
    ScoringItem("Find Iron", 5),
    ScoringItem("Full Iron Armor", 10),
    ScoringItem("Find Diamonds", 10),
    ScoringItem("Build Nether Portal", 15),
    ScoringItem("Find Fortress", 20),
]

JULY_GYMS = [
    GymDefinition("Fire", "Flame Badge", "Blazing challenge"),
    GymDefinition("Water", "Cascade Badge", "Water-based challenge"),
    GymDefinition("Grass", "Nature Badge", "Nature and growth challenge"),
    GymDefinition("Electric", "Volt Badge", "Speed and energy challenge"),
]

NOVEMBER_GYMS = [
    GymDefinition("Fire", "Flame Badge", "Blazing challenge"),
    GymDefinition("Water", "Cascade Badge", "Water-based challenge"),
    GymDefinition("Grass", "Nature Badge", "Nature and growth challenge"),
    GymDefinition("Electric", "Volt Badge", "Speed and energy challenge"),
    GymDefinition("Fighting", "Battle Badge", "Power and resilience challenge"),
    GymDefinition("Psychic", "Mind Badge", "Focus and strategy challenge"),
    GymDefinition("Ghost", "Specter Badge", "Mystery and calm challenge"),
    GymDefinition("Dragon", "Dragon Badge", "Legendary strength challenge"),
]

POKEMON_SCAVENGER_HUNT = [
    Challenge("Catch a Water Type"),
    Challenge("Catch a Flying Type"),
    Challenge("Catch a Pokémon that evolves"),
    Challenge("Catch a Pokémon with two types"),
    Challenge("Catch a Pokémon beginning with 'P'"),
    Challenge("Catch a Fire Type"),
    Challenge("Catch a Grass Type"),
    Challenge("Catch an Electric Type"),
    Challenge("Catch a Pokémon found in the wild"),
    Challenge("Catch a Pokémon with a trainer card"),
    Challenge("Catch a Pokémon with a shiny appearance"),
    Challenge("Catch a Pokémon from the first generation"),
    Challenge("Catch a Pokémon with a name that starts with 'B'"),
    Challenge("Catch a Pokémon that uses sound-based moves"),
    Challenge("Catch a Pokémon with a special evolution line"),
    Challenge("Catch a Pokémon with a dual-typed first evolution"),
    Challenge("Catch a Pokémon that lives in the sky"),
    Challenge("Catch a Pokémon that is known for speed"),
    Challenge("Catch a Pokémon with the word 'leaf' in its name"),
    Challenge("Catch a Pokémon that shares a type with a gym leader"),
]

CAMP_AWARDS = [
    Award("Master Builder", "Top combined score in Minecraft league events."),
    Award("Pokémon Champion", "Winner of the Pokémon Championship finals."),
    Award("Best Teammate", "Positive collaboration and support across camp teams."),
    Award("Sportsmanship", "Respectful, encouraging, and gracious play throughout camp."),
    Award("Camp MVP", "Most outstanding overall impact across all camp activities."),
]

PROJECT_PHASES = [
    {
        "name": "Phase 0",
        "window": "This Week",
        "goal": "Define the minimum viable camp product and success criteria.",
        "deliverables": [
            "Finalize Minecraft Build Battle rules",
            "Finalize Survival Challenge scoring",
            "Create Pokémon scavenger hunt",
            "Create 4-gym Pokémon League",
            "Design July awards",
        ],
    },
    {
        "name": "Phase 1",
        "window": "July 20-21 Pilot Camp",
        "goal": "Test activities, timing, age range, and interest before broader league expansion.",
        "deliverables": [
            "Run July Build Battle rubric",
            "Run July Survival objectives",
            "Run 4-gym challenge set",
            "Capture staff observations for iteration",
        ],
    },
    {
        "name": "Phase 2",
        "window": "November Camp",
        "goal": "Expand the league to a full multi-event competitive model.",
        "deliverables": [
            "8-gym Pokémon League",
            "Badge collection and Championship entry path",
            "Minecraft Build Battle, Survival Challenge, and Championship Build events",
            "Master Builder scoring framework",
        ],
    },
    {
        "name": "Phase 3",
        "window": "March Camp",
        "goal": "Refine camp structure with team operations and older-camper leadership.",
        "deliverables": [
            "Team Captains for grades 7-8",
            "Minecraft city build challenge",
            "Pokémon team gym battles",
            "Staff guide for team and judge processes",
        ],
    },
    {
        "name": "Phase 4",
        "window": "June Flagship Camp",
        "goal": "Deliver the polished flagship camp experience with full daily structure.",
        "deliverables": [
            "Monday: Build Battle Qualifier",
            "Tuesday: Survival League",
            "Wednesday: Team Build Challenge",
            "Thursday: League Qualifiers",
            "Friday: Grand Finals",
        ],
    },
]

TRACKS = {
    "minecraft": [
        "Build Battle Pack",
        "Survival Challenge Pack",
    ],
    "pokemon": [
        "Gym Leader Pack",
        "Tournament Pack",
        "Scavenger Hunt Pack",
    ],
    "camp_operations": [
        "Awards",
        "Registration",
        "Staff",
    ],
}

FLAGSHIP_SCHEDULE = {
    "Monday": "Build Battle Qualifier",
    "Tuesday": "Survival League",
    "Wednesday": "Team Build Challenge",
    "Thursday": "League Qualifiers",
    "Friday": "Grand Finals",
}


def total_points(items: Sequence[ScoringItem]) -> int:
    """Return the sum of all points in a scoring list."""

    return sum(item.points for item in items)


def build_battle_total_points() -> int:
    """Return the Build Battle rubric total."""

    return total_points(BUILD_BATTLE_RUBRIC)


def survival_challenge_total_points() -> int:
    """Return the total Survival Challenge points."""

    return total_points(SURVIVAL_OBJECTIVES)


def get_phase_names() -> list[str]:
    """Return each phase in order."""

    return [phase["name"] for phase in PROJECT_PHASES]
