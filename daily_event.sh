#!/bin/bash

git pull
pip3 install -r requirements.txt

python3 src/main.py --output --canon --headless --rng-mode random
python3 send_first_output_to_discord.py

git add .
git commit -m "Ran event for $DATE" || echo "No changes to commit"
git push || echo "No changes to push"