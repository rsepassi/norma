#!/bin/bash
cd "$(dirname $(dirname "$0"))"
source .env
python3 src/norma_bot.py
