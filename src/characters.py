"""
Character system for marble race simulation.
Each character has an id, name, and a list of costumes (must include 'default').
Assets are stored in assets/characters/{id}/{costume}.png
"""

from typing import List

class Character:
    def __init__(self, id: str, name: str, costumes: List[str]):
        self.id = id
        self.name = name
        self.costumes = costumes
        if 'default' not in costumes:
            raise ValueError('Every character must have a "default" costume')


CHARACTERS = [
    Character(id='ENT0000', name='PIANO BOOM', costumes=['default']),
    Character(id='ENT0001', name='MICHAEL', costumes=['default']),
    Character(id='ENT0002', name='INSTINCT', costumes=['default']),
    Character(id='ENT0003', name='CIGARETTE', costumes=['default']),
    Character(id='ENT0004', name='BROADCAST', costumes=['default']),
    Character(id='ENT0005', name='BUBBLE COLLECTION', costumes=['default']),
    Character(id='ENT0006', name='VIRGIN WHIP', costumes=['default']),
    Character(id='ENT0007', name='FINANCE', costumes=['default']),
]

def get_character_by_id(char_id: str) -> Character:
    for c in CHARACTERS:
        if c.id == char_id:
            return c
    raise ValueError(f'Character with id {char_id} not found')
