# Roadmap (after v1.1)

Ideas and open items collected after release, mostly from user feedback. Nothing here is committed to. Each item gets its own entry in `findings.md` once work starts. `PLAN.md` still covers the shipped atmosphere work.

## Next: other USA versions

- **Support every USA release, not only Rev 1.** That means the original stock release (Rev 0) and any other USA revisions that exist. The Redump list is where to check which ones. Each version needs its own address map, the patches ported to it, and its own SHA1 accepted by the tools and the release.
- Starting point: a rebuilt xiso found locally (`default.xbe` sha1 1ceae5be…). It's probably Rev 0, which isn't confirmed (findings, "Whole-ISO xdelta patches").

## Investigate

- **Every Xbox difference vs PS2 and PC.** Build a full list of what the Xbox port does differently from the other versions: rendering, HUD, assets, gameplay bugs and the like. Rank each one by how visible it is and how hard it would be to patch. This list feeds the fixes below.

## Candidate fixes

- **Map/radar blips.** On the Xbox, compression damages the blip icons. Find out whether the cause is the texture data or the way the game draws them.
- **Parachute placement.** The parachute sits in the wrong place on CJ's back on the Xbox.

## Testing gaps

- **Xbox 360 (Aurora / backward compatibility).** Not tested. It's unknown whether a modified XBE boots there, and whether the blur and radiosity look right.
- **Real Redump Rev 1 image.** `redump-iso.xdelta` has only been tested on a synthetic image.
- **GUI xdelta tools.** Delta Patcher and xdelta UI haven't been tested on the release patch.
