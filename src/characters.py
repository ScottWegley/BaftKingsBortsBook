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
    Character(id='ENT0000', name='ENT0000', costumes=['default']),
    Character(id='ENT0001', name='ENT0001', costumes=['default']),
    Character(id='ENT0002', name='ENT0002', costumes=['default']),
    Character(id='ENT0003', name='ENT0003', costumes=['default']),
    Character(id='ENT0004', name='ENT0004', costumes=['default']),
    Character(id='ENT0005', name='ENT0005', costumes=['default']),
    Character(id='ENT0006', name='ENT0006', costumes=['default']),
    Character(id='ENT0007', name='ENT0007', costumes=['default']),
]

def get_character_by_id(char_id: str) -> Character:
    for c in CHARACTERS:
        if c.id == char_id:
            return c
    raise ValueError(f'Character with id {char_id} not found')
