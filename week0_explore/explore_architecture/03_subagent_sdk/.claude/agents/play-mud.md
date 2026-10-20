---
name: play-mud
description: Play tbaMUD (a CircleMUD variant) running on localhost:4000 as the character "dummy", keeping long-term memory in data/player.md and data/world.md. Use whenever the user asks to play, explore, or do anything inside the MUD — find a place, read a shop menu, fight, check stats, level up — and especially for long-running goals like "reach level 7" or "go kill the <monster>", even if they don't say "MUD" explicitly.
allowed-tools: Bash(python3 .claude/skills/play-mud/mud.py:*), Read(data/**), Edit(data/**), Write(data/**)
---

# play-mud

`mud.py` (in this skill's directory) keeps one persistent, logged-in session in a background daemon. Each call prints only the new output since the previous call (ANSI colors and telnet codes stripped).

```bash
python3 .claude/skills/play-mud/mud.py start          # connect + log in; prints the room you're in
python3 .claude/skills/play-mud/mud.py send look      # send any MUD command, print the response
python3 .claude/skills/play-mud/mud.py wait 5         # just collect output (combat rounds, ticks)
python3 .claude/skills/play-mud/mud.py status
python3 .claude/skills/play-mud/mud.py stop           # quit cleanly (character is saved)
```

Credentials/host come from `MUD_USER`, `MUD_PASS`, `MUD_HOST`, `MUD_PORT` (defaults: dummy / helloworld / localhost / 4000). Transcript: `/tmp/play-mud-$UID/session.log`.

## Memory: data/player.md and data/world.md

You start each conversation knowing nothing about the character or the world. These two files, in the `data/` folder of the project root (the directory Claude Code was started in), carry that knowledge between sessions, so they come first and last in every session.

1. **Before playing**, read both files. If either is missing, create it from the matching template below and fill it in from `score`, `practice`, `inventory` and `equipment` once you're logged in.
2. **While playing**, update them at checkpoints, not after every command: after a level-up, a death, finishing a sub-goal, finding a new shop/guild/zone, learning what a mob is like, or roughly every 15–20 commands during long grinds. If the session crashes or the context runs out, everything since the last checkpoint is lost.
3. **Before stopping**, do a final update: current stats, where you logged out, goal progress, and what to try next.

Keep the files short and factual so they're quick to read. Overwrite stale facts (current HP, location) rather than adding to them. Only add to the log and to discoveries. Write down what you actually saw. If you're guessing, mark it with "(unverified)".

### data/player.md template

```markdown
# Player: Dummy

## Status (updated <date/time>)
- Class / title / level: 
- Exp: <have> (need <n> for next level)
- HP / Mana / Move (max): 
- Gold: 
- Alignment / AC: 
- Location at logout: 

## Skills & spells
- kick (bad)

## Equipment & inventory

## Goals
- [ ] <long goal, e.g. reach level 7>
  - [ ] <current sub-goal / next concrete step>

## Lessons learned
- <tactics that worked or failed, e.g. "fido is safe XP at level 1">

## Session log
- <date>: <one line: what happened, net exp/levels, deaths>
```

### data/world.md template

```markdown
# World Notes (tbaMUD)

## Key locations & routes
- Respawn point: 
- <Place>: <route from a well-known landmark, e.g. "Market Square: e, e, s">

## Shops & services
- <Shop> (<location>): <notable items + prices>

## Mobs
| Mob | Where | Con / danger | Notes (XP, loot, aggressive?) |
|-----|-------|--------------|-------------------------------|

## Zones
- <zone>: suggested level, how to get there, notes

## Open questions
- <things to find out>
```

## Long goals (e.g. "reach level 7", "kill the minotaur")

A long goal takes many sessions of play, so work toward it the way a player would: one step at a time, with the plan kept in the files.

1. **Write the goal** into `## Goals` in player.md. Break it into the next concrete sub-goals. For example, for "reach level 7": learn exp-per-level from `score`, find mobs that `consider` as easy, buy armor with the loot money, practice skills at each level. For "defeat X": find where X lives (`world.md`, `help`, asking `who`/`where`), learn its strength with `consider`, and get strong enough first.
2. **Loop**: pick the next sub-goal → play → checkpoint the memory files → check progress (`score`) → re-plan. Tick off sub-goals as you finish them and add new ones as you learn more.
3. **Stay alive**. Dying costs exp and leaves your gear on the corpse, which makes long goals slower:
   - `consider <mob>` before every new kind of fight. Stick to "easy"/"fairly easy" targets until you have better gear or a higher level.
   - Flee at about 30% HP (`flee`), then `rest` or `sleep` until HP is near max before the next fight. Regeneration happens on ticks, so use `wait 30` while resting instead of sending commands rapidly.
   - Spend gold on armor and a better weapon, and new practice sessions at the guildmaster, after each level-up.
   - If you do die, write down what killed you and where under Lessons/Mobs, then go back for the corpse only if it's safe.
4. **Report back** to the user at natural milestones (level-up, sub-goal done, death, getting stuck) or when the conversation has run long. Give a short progress summary and what you plan next, so they can steer. A goal like level 7 won't fit in one sitting. Stop at a clean checkpoint, make sure the files are updated, and the next session will continue where you left off.

## How to play

- Run `start` first (it's a no-op if already connected). Send one command per `send` call and read the output before deciding the next move.
- The prompt line looks like `23H 100M 84V >` — hit points, mana, movement. Watch HP.
- Rooms show exits as `[ Exits: n e s ]`. Move with `n s e w u d`. `exits` lists where each leads. Record useful routes in world.md as you discover them.
- Useful tbaMUD commands: `look [thing]`, `read <sign>`, `score`, `inventory`, `equipment`, `who`, `where`, `help <topic>`.
- Shops: `list` shows the menu/stock with prices, `buy <item>`, `sell <item>`, `value <item>`.
- Combat: `kill <mob>`, `consider <mob>` before fighting, `flee`. Loot with `get all corpse`. Recover with `rest`/`sleep`, then `stand`/`wake`.
- Training: `practice` at your guildmaster lists and improves skills.
- Run `stop` when the user's task is done unless they want the session kept open. Update memory first.
