<h1 align="center">Brawler Data Contribution</h1>

<p align="center">
  <a href="#How-To">How-To</a>
  •
  <a href="#guidelines-and-reference">Guidelines and Reference</a>
  •
  <a href="#Resources">Resources</a>
  •
  <a href="#TODO">TODO</a>
</p>

Please follow the steps and guidelines on this page when contributing to the Brawler data. All contribution is welcome and greatly appreciated!

## How-To

Firstly, open/download a text editor with `json` support. [Visual Studio Code](https://code.visualstudio.com), [Atom](https://atom.io) and [Sublime Text](https://www.sublimetext.com) are popular choices.

Once you have the text editor opened, make a new file named `brawler_name.json` (replacing `brawler_name` with the actual name). Enter all the data as outlined in [Guidelines and Reference](#guidelines-and-reference) section.

Save the file and send it to me on Discord via a direct message. My Discord username is `Snowsy#0529`.

And that is all! I'll add the file to the bot data and credit you in the bot's credit command and on the webpage. You can choose any name and optionally share a website (link to your profile, server, etc.) for the credit.

Please do note that I may not be able to credit you if someone shares a Brawler's file before. The list of Brawlers left to complete is [here](#todo).

## Guidelines and Reference

**Note:** All the stats are **level 1** stats. You can see all the Brawler data [here](brawlcord/data/brawlers.json).

### Non-Spawners

```json
{
    "Shelly": {
        "desc": "Shelly’s spread-fire shotgun blasts the other team with buckshot. Her Super destroys cover and keeps her opponents at a distance!",
        "health": 3600,
        "attack": {
            "name": "Buckshot",
            "damage": 300,
            "desc": "Shelly's boomstick fires a wide spread of pellets to a medium range. The more pellets hit, the greater the damage.",
            "range": 7.67,
            "reload": 1.5,
            "projectiles": 5
        },
        "speed": 720,
        "rarity": "Trophy Road",
        "unlockTrp": 0,
        "ult": {
            "name": "Super Shell",
            "damage": 320,
            "desc": "Shelly's Super Shell obliterates both cover and enemies. Any survivors get knocked back.",
            "range": 7.33,
            "projectiles": 9
        },
        "sp1": {
            "name": "Shell Shock",
            "desc": "Shelly's Super shells slow down enemies for **3.0** seconds!"
        },
        "sp2": {
            "name": "Band-Aid",
            "desc": "When Shelly falls below **40%** health, she instantly heals for **1800** health. Band-Aid recharges in **20.0** seconds."
        },
        "skins": {
            "Bandita": [30, -1],
            "Star": [-1, -1],
            "Witch": [-1, -1]
        }
    }
}
```

#### Main key (`"Shelly"`)

Name of the Brawler. Must be capitalized.

#### General

- `"desc"`: Brawler's description.
- `"health"`: Brawler's health points.
- `"speed"`: Brawler's speed
- `"rarity"`: Brawler's rarity
- `"unlockTrp"`: Trophies the Brawler is available at on the Trophy Road. If the Brawler is not a Trophy Road Brawler, put `-1`.

#### Attack - `"attack"`

- `"name"`: Name of the attack
- `"desc"`: Description of the attack
- `"damage"`: Damage the attack deals. If the attack has multiple projectiles, only enter damage per **one** projectile.
- `"range"`: Range of the attack
- `"reload"`: Reload time of the attack
- `"projectiles"`: Number of projectiles of the attack

#### Super - `"ult"`

- `"name"`: Name of the super
- `"desc"`: Description of the super
- `"damage"`: Damage the super deals. If the super has multiple projectiles, only enter damage per **one** projectile. If the Brawler heals instead, like Poco, change `"damage"` to `"heal"`. Similarly, `"boost"` for speed boost (Max). If a Brawler's super does multiple things, enter each of them separately. Pam is considered to be a spawner.
- `"range"`: Range of the super
- `"projectiles"`: Number of projectiles of the super

#### Star Powers

- `"sp1"`: First Star Power's data
- `"sp2"`: Second Star Power's data
- `"name"`: Star Power's name
- `"desc"`: Star Power's description

#### Skins - `"skins"`

- `"Skin Name"`: [`Price in gems`, `Price in Star Points`]

If a skin is `Gem` skin, enter the SP cost as `-1`. Similarly, if a skin is `Star Points` skin, enter Gem cost as `-1`. Enter `-1` for both in case the skins is a **limited skin** (like Red Nose Nita, Corsair Colt, etc).

### Spawners

```json
{
    "Nita": {
        "desc": "Nita strikes her enemies with a thunderous shockwave. Her Super summons a massive bear to fight by her side!",
        "health": 4000,
        "attack": {
            "name": "Rupture",
            "damage": 800,
            "desc": "Nita sends forth a shockwave, damaging enemies caught in the tremor.",
            "range": 5.5,
            "reload": 1.25,
            "projectiles": 1
        },
        "speed": 720,
        "rarity": "Trophy Road",
        "unlockTrp": 10,
        "ult": {
            "name": "Overbearing",
            "desc": "Nita summons the spirit of Big Baby Bear to hunt down her enemies.",
            "bear": {
                "health": 4000,
                "damage": 400,
                "range": 1.33,
                "speed": 620
            }
        },
        "sp1": {
            "name": "Bear with Me",
            "desc": "Nita recovers **500** health whenever her bear hits an enemy. When Nita deals damage, her bear regains **500** health."
        },
        "sp2": {
            "name": "Happy Bear",
            "desc": "Nita's bear attacks faster. Time between swipes is reduced by **60%**."
        },
        "skins": {
            "Panda": [30, -1],
            "Red Nose": [-1, -1],
            "Shiba": [150, -1]
        }
    }
}
```

All data except `Super` should be added the same way as [Non-Spawners](#non-spawners).

#### Spawner Super - `"ult"`

These examples will explain that better:

**Jessie:**

```json
{
    "ult": {
        "name": "Scrappy!",
        "desc": "Jessie deploys a gun turret that automatically shoots at enemies. It's made of 100% recycled materials!",
        "scrappy": {
            "health": 2800,
            "damage": 260,
            "range": 4.67,
            "speed": 0
        }
    }
}
```

**Penny:**

```json
{
    "ult": {
        "name": "Old Lobber",
        "desc": "Penny sets up her cannon! It can shoot at enemies at a long range, even if they are behind cover.",
        "cannon": {
            "health": 2800,
            "damage": 1200,
            "range": 14.33,
            "reload": 2.5
        }
    }
}

```

**Pam:**

```json
{
    "ult": {
        "name": "Mama's Kiss'",
        "desc": "Pam's healing turret will fix up her and teammates who stay in its area of effect.",
        "turret": {
            "health": 2800,
            "heal": 320,
            "range": 5
        }
    }
}
```

If you have any questions, feel free to ask me on [Discord](https://discord.gg/7zJ3PbJ). My username is `Snowsy#0529`.

## Resources

The best place to find all the data is the [Brawl Stars Wiki](https://brawlstars.fandom.com/wiki/Category:Brawlers).

[Star List](https://www.starlist.pro/brawlers/) is also a good source, but it doesn't have all the data.

## TODO

- [ ] Tick
- [ ] 8-Bit
- [ ] Emz
- [ ] Rosa
- [X] Frank
- [ ] Bibi
- [ ] Bea
- [X] Mortis
- [X] Tara
- [ ] Gene
- [ ] Max
- [ ] Mr. P
- [X] Crow
- [X] Spike
- [X] Leon
- [ ] Sandy
