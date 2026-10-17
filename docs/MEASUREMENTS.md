# How the typeface was measured and drawn

The source is the ON TOP logo, `reference/on-top.png` (1756 × 177 px, white on transparent) and the
same smaller, `reference/on-top-header.png` (952 × 96). It holds five letters, four of them distinct:
**O, N, T, P**. Every other glyph is drawn from the rules read off these four and from the owner's
decisions on the drawn set (below). No outline is taken from any other font.

## Measured (2026-10-16, `on-top.png`, sub-pixel edges where the alpha crosses 0.5)

Cap height 163.57 px (baseline at y 170.69, top at 7.12). The font has a cap height of 700 units at
1000 units to the em, so 1 px of the image is 4.2795 units.

| What | Image (px) | Units |
|---|---|---|
| O width (first / second) | 312.7 / 310.3 | 1338 / 1328 → **1333** |
| O sides (left, right; both Os) | 60.6, 59.2 / 59.9, 59.7 | **256** |
| O top bar / bottom bar | 45.5 / 46.1 | **195 / 197** |
| O outer corner (Bezier fit, 8 corners, rms 0.1 px) | 54.8 wide, 41.4 tall, handles 0.605 | **234 × 177, k 0.605** |
| O counter corner (8 corners, rms 0.08 px) | 12.7 × 11.2, handles 0.55 | **54 × 48, k 0.55** |
| N width | 306.1 | **1310** |
| N stems (left, right) | 61.1, 62.8 | 262, 269 |
| N diagonal, upper edge | from x 404 on the top to the right stem at y 183 | as measured |
| N diagonal, lower edge | from the left stem at y 507 to x 876 on the base | as measured |
| N diagonal slope (dx/dy) | 1.232 / 1.213 | horizontal width 381 to 388 |
| T width, bar, stem | 298.2, 45.5, 62.2 | **1276, 195, 266** |
| P width, stem | 281.8, 60.8 | **1206, 260** |
| P bowl: top bar, counter, lower bar, foot of the bowl | 45.7, 37.2, 43.8, y 133.9 | 196, 159, 188, bowl foot at 157 |
| P bowl side | 58.3 | 250 |
| P outer bowl corner (fit, rms 0.1 px) | 49.5 × 40.3, handles 0.63 | **212 × 172, k 0.63** |
| P counter corner | 15.6 × 13.8, handles 0.66 | **67 × 59, k 0.66** |
| Gap O–N, T–O, O–P | 32.7, 21.7, 29.2 | 140, 93, 125 |
| Gap N–T (with the word space) | 150.0 | 642 |

The corner model: a cubic Bezier from the vertical side to the horizontal edge, reaching `rx` along
the horizontal edge and `ry` along the vertical one, its handles `k` of those reaches long (0.5523 is
an ellipse). The fits were made on the image's own edge points.

## What the measurements say

- **The letters are a monoline geometric face stretched 1.32 times in width.** Vertical strokes are
  1.32 × the horizontal ones (264 against 196), and every outer corner is 1.32 times wider than tall
  (234 × 177 is a corner of about 177, stretched). So the rules are written before the stretch and
  stretched after.
- **Round letters have rounded corners, straight ones square ones, and stroke ends are square.**
  O and the P's bowl are rounded outside; the N, the T and the P's stem have sharp corners. Counters
  are rounded rectangles on their round side and square where they meet a stem (the P).
- **Diagonals:** the N's diagonal is 214 thick before the stretch (a stem is 200, a bar 195): a
  diagonal weighs 200 upright, 195 flat and 214 at the N's angle, and in between (`diag_h` in
  `sources/glyphs.py`). Diagonals end square on the baseline and the cap height and meet a stem at
  the depth of a bar below the top (the N's crotch, 193 units).

## The rules for the rest of the set

| Rule | Value |
|---|---|
| Straight vertical stem | 264 |
| Side of a round | 254 to 256 |
| Top / bottom bar | 195 / 197 |
| Middle bar (A, F, H, the P's bowl) | 188 |
| Three-storey letters (B E S 2 3 5 6 8 9 ẞ $ &): three equal bars | 172; counters 92 |
| The ? | the same counter (92); its hook bar 150, so 90 stay clear above the period |
| Outer corner: every rounding of the letters, figures and the signs drawn from them, the O's own | 234 × 177, k 0.605 |
| Where a bar is thinner than the corner is tall (the S's round ends: bar 172, corner 177) | the O's corner, cut by the bar's end, never squashed |
| Outer corner of the P's and R's bowl (the logo's P, kept as measured) | 212 × 172, k 0.63 |
| Counter corner | 54 × 48 (the O's); 54 × 46 in the 92-unit counters of three-storey letters, so its two curves meet; 67 × 59 in the P's bowl and the round A and F that take it |
| Small signs approved as drawn: ( ) [ ] % ° and the a inside @ | their own smaller or larger corners, scaled to their size |
| Period | 264 × 196: a square before the stretch |
| Signs: horizontal strokes (= # _ and the hyphen's 188) | the three-storey bar, 172 |
| Signs: vertical strokes (# $) | 230, the 172 bar stretched 1.32 times |
| * and × | strokes 110 across, the Euro's bars ("nimm da die strichstärke von den € querstrichen"); the *'s upright 145, the 110 stretched 1.32 times |
| Arrows (< > « » ‹ ›) | the K's arm and leg: the N's angle at 0.75 of its weight |
| Euro | the C with two bars of 110 through its back, starting where its outer corners end (so no neck), 180 out to the left and 200 into the counter |
| ! and ? | 90 clear above the period |
| 7 and ẞ | the diagonal leaves the top bar's lower right corner, as the Z's does: no overhang |
| Widths | O 1333, N 1310, T 1276, P 1206 as measured; the others from their structure |

Three bars of 196 in a cap height of 700 leave two counters of 56, which close at the sizes the face
is used at (15 to 24 px on a screen at 1.25). At 172 the counters are 92 (the P's is 159).

## What the owner decided on the drawn set (2026-10-17)

The owner looked at the set and approved ( ) % @ and the letters H I J L M N O P Q R S T U V W X Y Z,
the round A, C and D. He ordered:

- **A:** the pointed A is the A ("spitzes A rein, kein rundes A als Standard"); the round A (the O's
  top on two legs, the P's crossbar and counter) is `ss01`.
- **C:** the ends turn in on the right, 90 past the counter's edge.
- **E:** round on the left like the C, with the square E's bars and counters ("rundes E, aber mit
  dem spacing zwischen den strichen wie beim eckigen"). The square E is `ss04`.
- **F:** the round A without its right side: its corner, its top bar, its crossbar at the P's height.
- **G:** the top ends square after its round corner without turning down; round lower corner; a
  short foot and a small spur pointing in. Without the spur the G read as a C at 16 to 24 px
  ("ERLEDICT"); he chose the spur after seeing that.
- **K:** arm and leg meet the stem itself at its middle, no bar ("Das erst K war gut, nur der
  quere balken in der mitte war schlecht"), stretched until the K is as wide as O, N and P
  ("gleiche breite durch das arme strecken, wie O, N, P"): 1250 wide, the arms at a slope of 1.84.
- **B:** his own proposal with both bowls the same size ("bauch sollte nicht glatt sein, sollte
  genau so gecurved sein, wie im beispiel ... beide gleich"): two bowls with the O's corners on
  the right, overlapping 120 around the middle so their corners curve into a waist; square at the
  stem; the counters on the three-storey grid.
- **&:** the first & he saw, chosen again ("Nimm das erste, aber ohne den dreieckigen überhang auf
  der rechten schräge"): the 8's storeys, the upper loop smaller and set in on a round shoulder,
  the lower bowl open on the right, a leg at 0.9 of the N's weight whose right edge runs straight
  on from the loop's side. The leg is one band of even width; the bowl's foot rounds with the O's
  corner and ends exactly on the leg's left edge, in a point where the counter's floor meets it
  ("der untere balken sollte von der krümmung her auf den queren balken mit der spitze enden");
  below that point a notch parts foot and leg.
- **Approved (2026-10-17):** A to Z, Ä Ö Ü ẞ, the figures and every sign: "NICHTS mehr ändern,
  alles abgenommen", after the & above and the * put back as it was ("dicker hat es verkackt").
  After that, on his word: the &'s foot ending on the leg, the * and then the × at the Euro's bar
  weight ("zu unkenntlich (dick)"; "das kleine sternchen (2 balken) ... auch"). The & and the *
  approved: "& Zeichen ist jetzt perfekt, sternchen auch".
- **8:** the B's waist on both sides.
- **One curve for every rounding** ("schau dir S und O an ... nicht einmal consistent von der
  curving der buchstabenrundung her"): every round corner of every glyph is the O's corner; the
  half-height bowls had a tighter one before.
- **Signs to match the letters:** the arrows are the K's arm and leg at the N's angle; the Euro's
  bars are light ("einfach kleinere striche") and run through the C's back; * and × take the
  Euro's bar weight; = # _ carry the three-storey bar; 7 and ẞ have no overhang.
- **S:** round ends; the square ends are `ss03`. **R:** the short leg; the long leg is `ss02`.

## Spacing and kerning (`sources/spacing.py`)

- **Sidebearings:** a straight side gets 72; a side that leaves white gets less, by 0.18 of its mean
  depth (capped at 362) over the cap height. With these three numbers the four letters space as in
  the image: stem 72, O 68, T 25 (O–N 140, T–O 93). The image's O–P is 15 tighter than its O–N: that
  pair is kerned −15 so "ON TOP" sets as the logo. The word space is 545 (N's 72 + 545 + T's 25 =
  the 642 measured).
- **Kerning:** a pair closes 55 % of the extra gap its nearest 40 % of rows leave. Pairs that stand
  at the normal gap over a long stretch (two bars at one height) are not closed; letters whose bars
  face each other over a fifth of the height or more (T T, F T) are opened to 95; letters whose
  corners meet at a point nearer than 50 (Y Y) are opened to 60.
  Punctuation tucks under an overhang only so far (period and comma −130, dashes −60, quotes −250,
  quotes at the J −120), and pairs of punctuation or figures whose ends face each other open to the
  normal gap (L. becomes 144). A kern never brings two outlines nearer than 70 units in two
  dimensions over the full glyph height (100 with punctuation); pairs that are not kerned keep the
  distance their sidebearings give (the nearest, K T and K 7, 50).

## How well "ON TOP" in the font falls on the image

`python tools/fit_report.py fonts/ttf/OnTop-Regular.ttf reference/on-top.png` sets "ON TOP" over the
image at the same cap height, left edge and baseline and compares every edge point (rows and
columns, sub-pixel). Version 1.000: mean deviation 0.52 px, 95 % of the edge points within 1.32 px,
at a cap height of 163.6 px. The −1 px run from the first O's right side through the second O's left
side is the logo's own: its two Os differ by 2.4 px in width, and the font has one O between them.
No letter differs in shape by more than about half a pixel.
