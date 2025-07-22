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
    Character(id='ENT0000', name='POLICE EXCITEMENT', costumes=['default']),
    Character(id='ENT0001', name='FINANCE INSTINCT', costumes=['default']),
    Character(id='ENT0002', name='CITY STEAK', costumes=['default']),
    Character(id='ENT0003', name='CIGARETTE', costumes=['default']),
    Character(id='ENT0004', name='SOUP REPUTATION', costumes=['default']),
    Character(id='ENT0005', name='TENNIS', costumes=['default']),
    Character(id='ENT0006', name='DEATH REVOLUTION', costumes=['default']),
    Character(id='ENT0007', name='BROADCAST JOURNALISM', costumes=['default']),
]

def get_character_by_id(char_id: str) -> Character:
    for c in CHARACTERS:
        if c.id == char_id:
            return c
    raise ValueError(f'Character with id {char_id} not found')
