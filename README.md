# PylaAI Showdown Fork

A fork of [PylaAI](https://github.com/PylaAI/PylaAI) (v0.6.5) that adds **two Showdown gamemodes** and a **live debug window** for visualizing AI detections in real time.

## Showdown Modes

The base PylaAI ships Showdown as a disabled, unimplemented button. This fork adds two fully playable Showdown strategies — pick the one that fits your playstyle.

### Showdown (Defensive)
A team-oriented survival strategy. The bot sticks with allies and only fights when it has to.

- **Follow allies** — moves toward and stays near the closest teammate at all times.
- **Attack enemies in range** — if an enemy walks into attack range, the bot fights back with normal attack, super, gadget, and hypercharge.
- **Kiting** — when close to an ally and an enemy is also inside safe range, the bot backs away from the enemy instead of standing still.
- Best for: longer survival, passive trophy pushing, brawlers with short range.
- Only attacks in brawlers range so for brawlers like piper it will attack farther than el primo

### Aggressive Showdown
A kill-focused rush strategy. The bot stays with allies until it spots an enemy, then charges straight at them.

- **Stay with teammates** — while no enemies are visible, the bot follows the closest ally just like regular Showdown.
- **Rush enemies on sight** — as soon as an enemy appears anywhere in the AI's vision, the bot pushes directly toward them trying to secure the kill. It never backs away.
- **Full ability usage** — super, gadget, and hypercharge all fire as soon as the enemy is in range while charging in.
- Best for: aggressive brawlers (tanks, assassins), power cube farming, fast-paced games.

### Side-by-Side Comparison

| | Showdown | Aggressive SD |
|---|---|---|
| No enemies visible | Follow closest ally | Follow closest ally |
| Enemy appears | Stay with ally, attack only if enemy is in range | Rush toward enemy immediately |
| Enemy inside safe range | Kite away from enemy | Keep pushing forward |
| Wall detection | Enabled | Enabled |

Both modes are available as buttons in the Hub under **Vertical > Select Gamemode**.

## Live Debug Window

A real-time OpenCV overlay showing exactly what the AI vision model is detecting each frame:
- **Player** (orange), **Allies** (green), **Enemies** (red), **Walls** (gray)
- Range circles around the player: safe range (cyan), attack range (red), super range (magenta)
- HUD showing current brawler, gamemode, movement keys, and super/gadget/hypercharge status

Enable it in the Hub under **Additional Settings > Show Debug Window**, or set `show_debug_window = "yes"` in `cfg/general_config.toml`.

## Setup

Requires Python 3.10+ and an Android emulator (LDPlayer, BlueStacks, or MEmu) running Brawl Stars.

```bash
git clone https://github.com/YOUR_USERNAME/github-showdown.git
cd github-showdown
python setup.py install
python main.py
```

Or if using Conda:
```bash
conda run python main.py
```

A `run.bat` is included for double-click launching on Windows.

## Notes

- This is the localhost/offline version. API features (login, online stats, auto-updating) are not enabled.
- You can get the .pt version of the AI vision model at https://github.com/AngelFireLA/BrawlStarsBotMaking
- Run `python -m unittest discover` to check for regressions.

## Credits

This project is a fork of **[PylaAI](https://github.com/PylaAI/PylaAI)** — the original bot and all underlying AI, detection, lobby automation, and game logic were created by the PylaAI team:

- **Iyordanov** — original developer
- **AngelFire** — original developer

Join the PylaAI Discord: https://discord.gg/xUusk3fw4A

Showdown gamemodes and debug window added by this fork. All original work remains under the upstream license.

## License

This project inherits the [CC BY-NC 4.0](LICENSE) license from the original PylaAI repository. Non-commercial use only. See [LICENSE](LICENSE) for full terms.
