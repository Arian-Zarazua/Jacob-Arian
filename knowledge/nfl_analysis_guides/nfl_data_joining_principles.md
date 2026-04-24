# NFL Data Joining Principles

## Step 1: choose primary key
boxscore link > nano ID > date+team.

## Step 2: normalize identifiers
team aliases and dates.

## Step 3: avoid duplicates
ensure 1 row per game/team.

## Step 4: validate joins
check mismatches and missing games.

## Step 5: propagate keys
carry unified IDs across tables.
