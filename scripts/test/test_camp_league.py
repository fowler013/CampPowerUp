"""Validation tests for the Camp League configuration."""

from camp_league import (
    BUILD_BATTLE_RUBRIC,
    BUILD_BATTLE_THEMES,
    JULY_GYMS,
    NOVEMBER_GYMS,
    POKEMON_SCAVENGER_HUNT,
    SURVIVAL_OBJECTIVES,
    build_battle_total_points,
    survival_challenge_total_points,
    total_points,
)


def test_build_battle_theme_count_and_total_score():
    assert len(BUILD_BATTLE_THEMES) == 10
    assert build_battle_total_points() == 40
    assert total_points(BUILD_BATTLE_RUBRIC) == 40


def test_survival_challenge_total_score():
    assert len(SURVIVAL_OBJECTIVES) == 7
    assert survival_challenge_total_points() == 70
    assert total_points(SURVIVAL_OBJECTIVES) == 70


def test_july_and_november_gym_sets():
    assert len(JULY_GYMS) == 4
    assert len(NOVEMBER_GYMS) == 8
    assert {gym.name for gym in JULY_GYMS} == {"Fire", "Water", "Grass", "Electric"}
    assert {gym.name for gym in NOVEMBER_GYMS} == {
        "Fire",
        "Water",
        "Grass",
        "Electric",
        "Fighting",
        "Psychic",
        "Ghost",
        "Dragon",
    }


def test_scavenger_hunt_size():
    assert len(POKEMON_SCAVENGER_HUNT) == 20
    assert all(challenge.description for challenge in POKEMON_SCAVENGER_HUNT)
