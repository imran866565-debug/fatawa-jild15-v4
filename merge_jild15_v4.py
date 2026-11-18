#!/usr/bin/env python3
"""Merge Fatawa Razviya Jild 15 easy-Urdu tashreeh v4 chunks into jild-15.json.

Reads the 15 leaf chunk files listed in chunks-manifest-v4-jild15.json,
concatenates them in order 01 -> 02 -> 03a -> 03b -> 04a -> 04b -> 05a
-> 05b -> 05c -> 06 -> 07 -> 08 -> 09 -> 10 -> 11, JOINS the three
masala-72 parts (leaves 05a+05b+05c) and the two masala-74 parts
(leaves 06+07) into single items, derives start_page = min(pages)
where the field is absent, normalises page markers, validates, and
writes {"masail": [...]} to jild-15.json.

ORDER -- chunk order is the order:
  The v3 merged file ~/workspace/fatawa-app/content/tashreeh/jild-15.json
  has ID order == concatenation order of the v4 leaf chunks (verified
  locally by the coordinator: all 222 ids match the v3 sequence exactly
  after the two joins). Do NOT sort or reorder. Within each chunk,
  items keep file order. CHUNK_ORDER is an explicit 15-leaf list
  because 03a/03b, 04a/04b and 05a/05b/05c break the numeric range
  pattern.

GENERIC CONSECUTIVE-DUPLICATE JOIN (the joins in this merge): two
  masail were written in multiple leaves because they are too big for
  one worker, so concatenation gives the same id 2-3 times
  consecutively. Each group is joined into ONE item: pages = sorted
  union, sawal = the single non-empty one (assert exactly one
  non-empty, and that it is in the FIRST part), jawab = parts
  concatenated with a single space, notes = concatenated in order,
  title / volume_id / start_page from the FIRST part.
  masala-72 (3 parts): leaves 05a (pp.312-358, FULL sawal 1,680ch) +
    05b (pp.359-405, sawal EMPTY) + 05c (pp.406-451, sawal EMPTY) ->
    1 item, 140 pages, notes 6+36+28 = 70. All three parts carry the
    SAME title (verified by the coordinator). Verified seams: part 1
    ends "…جن کی حقیقت مقصود نہیں،" (p.358); part 2 starts "درجہ
    چہارم یہ ہے کہ" and ends "…اسی شرح مقاصد میں ہے کہ" (p.405);
    part 3 starts with the restored Arabic "«الکذب وھو محال باجماع
    العلماء لان الکذب نقص باتفاق العقلاء»" (original p.406 head) — the
    exact completion of part 2's hanging "کہ".
  masala-74 (2 parts): leaf 06 (pp.466-500, FULL sawal) + leaf 07
    (pp.501-513, sawal EMPTY) -> 1 item, 48 pages. The two parts'
    TITLES DIFFER by design (v3 chunk titles, kept exactly): part 1
    "مسئلہ ۷۴: سیالکوٹی کی عبارت اور امکانِ کذب — القمع المبین (حصہ
    اول)", part 2 "مسئلہ ۷۴ — القمع المبین لاٰمال المکذبین (جواب کا
    بقیہ حصہ)" — the joined title is part 1's, which is the merged-v3
    title (asserted in the merge). Verified seam: part 1 ends "…جبکہ
    یہ بعینہ جبریہ کا" (original p.500's own hanging words, after the
    coordinator's fix-up removing the duplicated "مذہب ہے" + the
    continues-marker sentence); part 2 starts "مذہب ہے، لہٰذا حال کا
    سہارا لینا بیکار ہوا" (the Urdu rendering of p.501's "فلا فائدۃ
    لتمسک بالحال").
  After the joins there are 222 items and 222 unique ids — the
  duplicate-id assertion runs AFTER the joins, not before.
  NO rename quirk in Jild 15's merge: the v3 merged file has 222
  UNIQUE ids. The 9 page-ids (jild15-p240, p258, p260, p264, p267,
  p277, p284, p305, p309) are v3's own disambiguations of the
  twice-numbered masail 30/31/33/34/39/47/50/62/70 — kept exactly,
  NOT merge renames.

BOUNDARY DEDUP / FOLD (3 masail — the Jild 10/11/12/13/14 pattern):
  the v3 chunk files overlap by one item at 3 boundaries; the merged
  v3 has each ONCE with combined pages + combined notes. Each boundary
  masala is written ONCE, in the EARLIER leaf, combining both halves'
  tashreeh into one flowing passage with ALL notes from both halves:
  masala-29-kufr-28-29 (leaf 03a, [201-212] — folds in chunk-03b's
  masala-28), masala-46 (leaf 04a, [275, 276, 277] — folds in
  chunk-04b's half), jild15-jibrail-salam (leaf 09, [664, 665] — folds
  in chunk-10's p664 half). The LATER leaf EXCLUDES the folded item
  (03b excludes masala-28; 04b excludes masala-46; 10 excludes p664).
  Leaf page ranges share 4 pages at boundaries (212, 277, 665, 711 —
  consecutive items sharing a page), so per-leaf present pages sum to
  666 while the merged file has 662 UNIQUE pages. Those are v3 ids,
  kept exactly — they are NOT merge renames.

START_PAGE: every one of the 15 v4 leaf chunks carries start_page ==
  min(pages) for all its items (verified by the coordinator). The
  derivation code below stays as a safety net; it is expected to
  derive 0 items.

MARKER NORMALISATION (the only text transformation): page markers, if
  present, are normalised to the single form [safha N] written with the
  Urdu word for page:
  - lenticular-bracket form (U+3010/U+3011 around the Urdu word for
    page + number) -> [safha N]
  - [short form] -> [safha N]
  - [safha N] stays as-is
  Applied to every string field of every item (jawab, sawal, title,
  notes). The 15 v4 chunks contain ZERO markers of any form (verified
  locally), so normalisation is expected to be a no-op here; the code
  stays so the merge is robust and the "none remain" assertions still
  run. No other text is touched and no markers are invented.
  NOTE: the literal lenticular-bracket characters are written here only
  as U+3010/U+3011 escapes, never as literal characters in this file.

VALIDATION (fails loudly on any violation):
  222 items (after the two joins); ID sequence EXACTLY == the v3
  merged file's ID sequence (embedded below as V3_IDS, copied verbatim
  from ~/workspace/fatawa-app/content/tashreeh/jild-15.json); pages per
  item identical to v3 (embedded as V3_PAGES, same source, verified
  against the v3 file before pushing); 662 unique pages (min 4, max
  742); volume_ids == {51}; start_page == min(pages) for every item
  (after derivation); zero empty tashreeh_jawab; no lenticular / short
  markers remain; first id jild15-pesh-lafz, last id jild15-p740-taqriz.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = "chunks-manifest-v4-jild15.json"

# Concatenation order: chunk files 01 -> 18, in order.
CHUNK_ORDER = ["jild-15-chunk-01.json", "jild-15-chunk-02.json", "jild-15-chunk-03a.json", "jild-15-chunk-03b.json", "jild-15-chunk-04a.json", "jild-15-chunk-04b.json", "jild-15-chunk-05a.json", "jild-15-chunk-05b.json", "jild-15-chunk-05c.json", "jild-15-chunk-06.json", "jild-15-chunk-07.json", "jild-15-chunk-08.json", "jild-15-chunk-09.json", "jild-15-chunk-10.json", "jild-15-chunk-11.json"]

EXPECTED_ITEMS = 222
EXPECTED_PAGES = 662
EXPECTED_MIN_PAGE = 4
EXPECTED_MAX_PAGE = 742
EXPECTED_VOLUME_IDS = {51}
EXPECTED_FIRST_ID = "jild15-pesh-lafz"
EXPECTED_LAST_ID = "jild15-p740-taqriz"

# v3 ID sequence, verbatim from content/tashreeh/jild-15.json.
V3_IDS = ['jild15-pesh-lafz', 'jild15-masala-1', 'jild15-masala-2', 'jild15-masala-3', 'jild15-masala-8', 'jild15-masala-9', 'jild15-masala-10', 'jild15-abhaas-akheerah', 'jild15-khat-tarikhi', 'jild15-masala-11', 'jild15-masala-12', 'jild15-masala-13', 'jild15-masala-14', 'jild15-masala-15', 'jild15-masala-16', 'jild15-masala-17', 'jild15-masala-18', 'jild15-masala-19', 'jild15-masala-20', 'jild15-masala-21', 'jild15-masala-22', 'jild15-masala-23', 'jild15-masala-24', 'jild15-masala-25-26', 'jild15-masala-27', 'jild15-masala-28', 'jild15-masala-29', 'jild15-masala-29-hukm', 'jild15-masala-29-kufr-1', 'jild15-masala-29-kufr-2', 'jild15-masala-29-kufr-3', 'jild15-masala-29-kufr-4', 'jild15-masala-29-kufr-5', 'jild15-masala-29-kufr-6', 'jild15-masala-29-kufr-7', 'jild15-masala-29-kufr-8', 'jild15-masala-29-kufr-9', 'jild15-masala-29-kufr-10', 'jild15-masala-29-kufr-11-19', 'jild15-masala-29-kufr-20-21', 'jild15-masala-29-kufr-22', 'jild15-masala-29-kufr-23', 'jild15-masala-29-kufr-24', 'jild15-masala-29-kufr-25', 'jild15-masala-29-kufr-26', 'jild15-masala-29-kufr-27', 'jild15-masala-29-kufr-28-29', 'jild15-masala-30', 'jild15-masala-31', 'jild15-masala-33', 'jild15-masala-34', 'jild15-masala-39', 'jild15-masala-41', 'jild15-masala-47', 'jild15-masala-50', 'jild15-masala-53', 'jild15-masala-56', 'jild15-masala-57', 'jild15-masala-62', 'jild15-masala-69', 'jild15-masala-70', 'jild15-tazyeel-jaleel', 'jild15-p240', 'jild15-p258', 'jild15-masala-32', 'jild15-p260', 'jild15-p264', 'jild15-masala-35', 'jild15-masala-36-37', 'jild15-masala-38', 'jild15-p267', 'jild15-masala-40', 'jild15-masala-41-42', 'jild15-masala-43', 'jild15-masala-44', 'jild15-masala-45', 'jild15-masala-46', 'jild15-p277', 'jild15-masala-48', 'jild15-masala-49', 'jild15-p284', 'jild15-masala-51', 'jild15-masala-52-58', 'jild15-masala-59', 'jild15-masala-60', 'jild15-masala-61', 'jild15-p305', 'jild15-masala-63-65', 'jild15-masala-66', 'jild15-masala-67', 'jild15-masala-68-69', 'jild15-p309', 'jild15-masala-71', 'jild15-masala-72', 'jild15-masala-73', 'jild15-masala-74', 'jild15-masala-75', 'jild15-p520', 'jild15-masala-76', 'jild15-masala-77', 'jild15-masala-78', 'jild15-qahr-al-diyan', 'jild15-masala-79-80', 'jild15-masala-81', 'jild15-irshad-adam-tauba', 'jild15-irshad-musa', 'jild15-irshad-adam-noor', 'jild15-irshad-khatam-shanain', 'jild15-irshad-darwaza-jannat', 'jild15-irshad-bisharat-ibrahim', 'jild15-irshad-yaqub', 'jild15-irshad-ashiya', 'jild15-irshad-asma-kutub', 'jild15-irshad-salman', 'jild15-irshad-akhir-nabiyyin', 'jild15-irshad-rahmat', 'jild15-irshad-shafaat', 'jild15-irshad-iltija-shafaat', 'jild15-irshad-adam-azan', 'jild15-irshad-inshirah', 'jild15-irshad-bisharat-milad', 'jild15-irshad-rahib', 'jild15-irshad-zaid', 'jild15-irshad-inkar-wujuhat', 'jild15-irshad-muqawqis', 'jild15-irshad-tara-milad', 'jild15-irshad-yahud-milad', 'jild15-irshad-ahbar-naat', 'jild15-irshad-yathrib', 'jild15-irshad-yusha', 'jild15-irshad-tazyeel-yahudi', 'jild15-asma-nabi', 'jild15-ana-muhammad-ahmad', 'jild15-nabi-tauba-qubool', 'jild15-malik-liwa-ahmad', 'jild15-dus-asma', 'jild15-hashir-aqib', 'jild15-rasul-jihad', 'jild15-nau-aakhar', 'jild15-akhir-zaman', 'jild15-darya-rahmat', 'jild15-aakhireen-biasat', 'jild15-tazyeel-baqir', 'jild15-farooq-nida', 'jild15-jibrail-salam', 'jild15-khatam-665', 'jild15-lauh-666', 'jild15-imarat-668', 'jild15-sosmar-668', 'jild15-tazyeel-670', 'jild15-la-nabi-670', 'jild15-umar-672', 'jild15-faida-673', 'jild15-dajjal-675', 'jild15-ali-harun-676', 'jild15-iyadat-678', 'jild15-ghaus-679', 'jild15-siddiq-akbar-681', 'jild15-tazyeel-682', 'jild15-ali-rai-683', 'jild15-shaikhain-jannati-685', 'jild15-khairunnas-685', 'jild15-sabqat-687', 'jild15-madh-687', 'jild15-afdal-iman-688', 'jild15-shaikhain-afdal-689', 'jild15-nusus-690', 'jild15-zarib-692', 'jild15-nasara-sham-694', 'jild15-herqal-darbar-694', 'jild15-tasarruf-696', 'jild15-tasaveer-696', 'jild15-muqawqis-699', 'jild15-ibn-salam-700', 'jild15-hijrat-abbas-701', 'jild15-wasiyyat-702', 'jild15-madina-702', 'jild15-yafoor-704', 'jild15-mubashshirat-706', 'jild15-tis-kazzab-707', 'jild15-ali-harun-708', 'jild15-ibn-zumal-710', 'jild15-tasjeel-jameel', 'jild15-p713', 'jild15-p714', 'jild15-p715', 'jild15-p718-mumasilat', 'jild15-p718-turpushti', 'jild15-p719-ibn-hajar', 'jild15-p720-hindiyya', 'jild15-p720-alam-8', 'jild15-p720-alam-9', 'jild15-p721-nusus-11', 'jild15-p721-qasimiyya', 'jild15-p722-tatar', 'jild15-p722-shifa', 'jild15-p723-tareeqay', 'jild15-p724-majma', 'jild15-p724-ardabili', 'jild15-p725-ghazali', 'jild15-p725-ghunya', 'jild15-p726-tuhfa', 'jild15-p727-faraid', 'jild15-p727-mawahib', 'jild15-p728-nasafi', 'jild15-p728-tamheed', 'jild15-p729-abdul-ali', 'jild15-p729-qastalani', 'jild15-p731-sayyid', 'jild15-p731-munafiq', 'jild15-p732-jahannami', 'jild15-p733-azab', 'jild15-p733-tasmiya', 'jild15-p733-aag', 'jild15-p734-zarqani', 'jild15-p735-hadithiyya', 'jild15-p737-shaykh-akbar', 'jild15-p738-bad-aqeeda', 'jild15-p738-rafzi', 'jild15-p739-dalail', 'jild15-p740-katabahu', 'jild15-p740-taqriz']

# v3 pages per item id, verbatim from content/tashreeh/jild-15.json.
V3_PAGES = {
"jild15-pesh-lafz": [4, 5, 6, 7],
"jild15-masala-1": [74],
"jild15-masala-2": [74],
"jild15-masala-3": [74, 75, 76],
"jild15-masala-8": [76],
"jild15-masala-9": [76],
"jild15-masala-10": [78, 79, 80, 81, 82, 83, 84, 85, 86],
"jild15-abhaas-akheerah": [88, 89, 90, 91, 92, 93, 94, 95, 96, 97],
"jild15-khat-tarikhi": [98, 99, 100],
"jild15-masala-11": [100],
"jild15-masala-12": [100, 101],
"jild15-masala-13": [101, 102],
"jild15-masala-14": [104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140],
"jild15-masala-15": [142, 143, 144, 145, 146, 147, 148, 149],
"jild15-masala-16": [149],
"jild15-masala-17": [150, 151],
"jild15-masala-18": [151, 152, 153],
"jild15-masala-19": [153, 154],
"jild15-masala-20": [154, 155],
"jild15-masala-21": [155],
"jild15-masala-22": [156, 157, 158, 159, 160],
"jild15-masala-23": [160, 161],
"jild15-masala-24": [161, 162, 163],
"jild15-masala-25-26": [163, 164],
"jild15-masala-27": [164, 165, 166],
"jild15-masala-28": [166],
"jild15-masala-29": [168, 169, 170, 171, 172, 173, 174, 175, 176, 177],
"jild15-masala-29-hukm": [177, 178],
"jild15-masala-29-kufr-1": [178, 179],
"jild15-masala-29-kufr-2": [179],
"jild15-masala-29-kufr-3": [179, 180],
"jild15-masala-29-kufr-4": [180],
"jild15-masala-29-kufr-5": [180, 181],
"jild15-masala-29-kufr-6": [181, 182],
"jild15-masala-29-kufr-7": [182, 183],
"jild15-masala-29-kufr-8": [183],
"jild15-masala-29-kufr-9": [183, 184],
"jild15-masala-29-kufr-10": [184],
"jild15-masala-29-kufr-11-19": [184, 185],
"jild15-masala-29-kufr-20-21": [185, 186, 187],
"jild15-masala-29-kufr-22": [187, 188],
"jild15-masala-29-kufr-23": [188, 189, 190],
"jild15-masala-29-kufr-24": [190, 191, 192, 193, 194, 195, 196, 197],
"jild15-masala-29-kufr-25": [197, 198, 199, 200],
"jild15-masala-29-kufr-26": [200, 201],
"jild15-masala-29-kufr-27": [201],
"jild15-masala-29-kufr-28-29": [201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212],
"jild15-masala-30": [212, 213],
"jild15-masala-31": [213, 214],
"jild15-masala-33": [214],
"jild15-masala-34": [214, 215],
"jild15-masala-39": [215, 216],
"jild15-masala-41": [216, 217],
"jild15-masala-47": [217, 218],
"jild15-masala-50": [218, 219],
"jild15-masala-53": [219, 220],
"jild15-masala-56": [220, 221, 222, 223, 224, 225],
"jild15-masala-57": [225, 226, 227],
"jild15-masala-62": [227, 228, 229, 230],
"jild15-masala-69": [230, 231],
"jild15-masala-70": [231, 232, 233, 234],
"jild15-tazyeel-jaleel": [234, 235, 236, 237, 238],
"jild15-p240": [240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258],
"jild15-p258": [258, 259],
"jild15-masala-32": [259],
"jild15-p260": [260, 261, 262, 263],
"jild15-p264": [264],
"jild15-masala-35": [264, 265],
"jild15-masala-36-37": [265, 266],
"jild15-masala-38": [266, 267],
"jild15-p267": [267],
"jild15-masala-40": [267, 268],
"jild15-masala-41-42": [268],
"jild15-masala-43": [268, 269, 270, 271],
"jild15-masala-44": [272, 273],
"jild15-masala-45": [273, 274, 275],
"jild15-masala-46": [275, 276, 277],
"jild15-p277": [277, 278, 279, 280],
"jild15-masala-48": [280, 281],
"jild15-masala-49": [281, 282, 283, 284],
"jild15-p284": [284, 285, 286, 287, 288, 289, 290, 291, 292],
"jild15-masala-51": [292, 293, 294, 295, 296, 297, 298],
"jild15-masala-52-58": [299, 300, 301, 302],
"jild15-masala-59": [302, 303],
"jild15-masala-60": [303, 304],
"jild15-masala-61": [304, 305],
"jild15-p305": [305],
"jild15-masala-63-65": [305, 306],
"jild15-masala-66": [306, 307],
"jild15-masala-67": [307, 308],
"jild15-masala-68-69": [308],
"jild15-p309": [309],
"jild15-masala-71": [309, 310],
"jild15-masala-72": [312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451],
"jild15-masala-73": [452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464],
"jild15-masala-74": [466, 467, 468, 469, 470, 471, 472, 473, 474, 475, 476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513],
"jild15-masala-75": [514, 515, 516, 517, 518, 519, 520],
"jild15-p520": [520, 521, 522, 523, 524, 525, 526, 527, 528],
"jild15-masala-76": [530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554],
"jild15-masala-77": [556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570],
"jild15-masala-78": [572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595],
"jild15-qahr-al-diyan": [596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611],
"jild15-masala-79-80": [612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629],
"jild15-masala-81": [630, 631, 632, 633, 634],
"jild15-irshad-adam-tauba": [634],
"jild15-irshad-musa": [634, 635],
"jild15-irshad-adam-noor": [635],
"jild15-irshad-khatam-shanain": [635],
"jild15-irshad-darwaza-jannat": [635, 636],
"jild15-irshad-bisharat-ibrahim": [636],
"jild15-irshad-yaqub": [636],
"jild15-irshad-ashiya": [636, 637],
"jild15-irshad-asma-kutub": [637],
"jild15-irshad-salman": [637, 638],
"jild15-irshad-akhir-nabiyyin": [638],
"jild15-irshad-rahmat": [638, 639],
"jild15-irshad-shafaat": [640],
"jild15-irshad-iltija-shafaat": [640, 641],
"jild15-irshad-adam-azan": [641],
"jild15-irshad-inshirah": [641, 642],
"jild15-irshad-bisharat-milad": [642],
"jild15-irshad-rahib": [642, 643],
"jild15-irshad-zaid": [643, 644],
"jild15-irshad-inkar-wujuhat": [644, 645],
"jild15-irshad-muqawqis": [645],
"jild15-irshad-tara-milad": [645, 646],
"jild15-irshad-yahud-milad": [646],
"jild15-irshad-ahbar-naat": [646, 647],
"jild15-irshad-yathrib": [647],
"jild15-irshad-yusha": [647],
"jild15-irshad-tazyeel-yahudi": [647, 648],
"jild15-asma-nabi": [648],
"jild15-ana-muhammad-ahmad": [648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658],
"jild15-nabi-tauba-qubool": [658],
"jild15-malik-liwa-ahmad": [658, 659],
"jild15-dus-asma": [659, 660],
"jild15-hashir-aqib": [660],
"jild15-rasul-jihad": [660],
"jild15-nau-aakhar": [661, 662],
"jild15-akhir-zaman": [662],
"jild15-darya-rahmat": [662],
"jild15-aakhireen-biasat": [662, 663],
"jild15-tazyeel-baqir": [663],
"jild15-farooq-nida": [663, 664],
"jild15-jibrail-salam": [664, 665],
"jild15-khatam-665": [665, 666],
"jild15-lauh-666": [666, 667],
"jild15-imarat-668": [668],
"jild15-sosmar-668": [668, 669, 670],
"jild15-tazyeel-670": [670],
"jild15-la-nabi-670": [670, 671],
"jild15-umar-672": [672],
"jild15-faida-673": [673, 674],
"jild15-dajjal-675": [675, 676],
"jild15-ali-harun-676": [676, 677, 678],
"jild15-iyadat-678": [678, 679],
"jild15-ghaus-679": [679, 680],
"jild15-siddiq-akbar-681": [681, 682],
"jild15-tazyeel-682": [682, 683],
"jild15-ali-rai-683": [683, 684, 685],
"jild15-shaikhain-jannati-685": [685],
"jild15-khairunnas-685": [685, 686],
"jild15-sabqat-687": [687],
"jild15-madh-687": [687, 688],
"jild15-afdal-iman-688": [688, 689],
"jild15-shaikhain-afdal-689": [689, 690],
"jild15-nusus-690": [690, 691],
"jild15-zarib-692": [691, 692, 693],
"jild15-nasara-sham-694": [694],
"jild15-herqal-darbar-694": [694, 695],
"jild15-tasarruf-696": [696],
"jild15-tasaveer-696": [696, 697, 698, 699],
"jild15-muqawqis-699": [699, 700],
"jild15-ibn-salam-700": [700, 701],
"jild15-hijrat-abbas-701": [701],
"jild15-wasiyyat-702": [702],
"jild15-madina-702": [702, 703, 704],
"jild15-yafoor-704": [704, 705, 706],
"jild15-mubashshirat-706": [706, 707],
"jild15-tis-kazzab-707": [707, 708],
"jild15-ali-harun-708": [708, 709, 710],
"jild15-ibn-zumal-710": [710, 711],
"jild15-tasjeel-jameel": [711, 712, 713],
"jild15-p713": [713],
"jild15-p714": [714],
"jild15-p715": [715, 716, 717, 718],
"jild15-p718-mumasilat": [718],
"jild15-p718-turpushti": [718, 719],
"jild15-p719-ibn-hajar": [719],
"jild15-p720-hindiyya": [720],
"jild15-p720-alam-8": [720],
"jild15-p720-alam-9": [720, 721],
"jild15-p721-nusus-11": [721],
"jild15-p721-qasimiyya": [721, 722],
"jild15-p722-tatar": [722],
"jild15-p722-shifa": [722, 723],
"jild15-p723-tareeqay": [723, 724],
"jild15-p724-majma": [724],
"jild15-p724-ardabili": [724, 725],
"jild15-p725-ghazali": [725],
"jild15-p725-ghunya": [725, 726],
"jild15-p726-tuhfa": [726],
"jild15-p727-faraid": [727],
"jild15-p727-mawahib": [727, 728],
"jild15-p728-nasafi": [728],
"jild15-p728-tamheed": [728, 729],
"jild15-p729-abdul-ali": [729],
"jild15-p729-qastalani": [729, 730, 731],
"jild15-p731-sayyid": [731],
"jild15-p731-munafiq": [731, 732],
"jild15-p732-jahannami": [732],
"jild15-p733-azab": [733],
"jild15-p733-tasmiya": [733],
"jild15-p733-aag": [733, 734],
"jild15-p734-zarqani": [734, 735],
"jild15-p735-hadithiyya": [735, 736],
"jild15-p737-shaykh-akbar": [737],
"jild15-p738-bad-aqeeda": [738],
"jild15-p738-rafzi": [738, 739],
"jild15-p739-dalail": [739, 740],
"jild15-p740-katabahu": [740],
"jild15-p740-taqriz": [740, 741, 742],
}

# The Urdu word for "page" is safha; the canonical marker is [safha N].
# Lenticular brackets are U+3010 (open) and U+3011 (close); the short
# form is "[safha-initial N]" with the single-letter abbreviation.
# All three patterns are built from escapes so this file never contains
# a literal lenticular-bracket pair.
SAFHA = "\u0635\u0641\u062d\u06c1"  # the Urdu word for page
RE_LENTICULAR = re.compile("\u3010" + SAFHA + " (\\d+)\u3011")
RE_SHORT = re.compile("\\[\u0635 (\\d+)\\]")
RE_FULL = re.compile("\\[" + SAFHA + " \\d+\\]")
LENTICULAR_PREFIX = "\u3010" + SAFHA  # for the "none remain" check
SHORT_PREFIX_RE = re.compile("\\[\u0635 \\d+\\]")

# Canonical output key order for every item (the JSON contract).
ITEM_KEYS = ["id", "title", "volume_id", "pages", "start_page",
             "tashreeh_sawal", "tashreeh_jawab", "notes"]


def normalise_markers(text):
    """Normalise page markers in one string. Returns (new_text, counts)."""
    counts = {"lenticular": 0, "short": 0, "full_before": 0}
    counts["full_before"] = len(RE_FULL.findall(text))
    text, n1 = RE_LENTICULAR.subn("[" + SAFHA + " \\1]", text)
    counts["lenticular"] = n1
    text, n2 = RE_SHORT.subn("[" + SAFHA + " \\1]", text)
    counts["short"] = n2
    return text, counts


def normalise_item(item):
    """Normalise markers in every string field of one item (recursively
    through lists/dicts). Returns per-form counts for this item."""
    totals = {"lenticular": 0, "short": 0, "full_before": 0}

    def walk(value):
        if isinstance(value, str):
            new, c = normalise_markers(value)
            for k in totals:
                totals[k] += c[k]
            return new
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        return value

    for key in list(item.keys()):
        item[key] = walk(item[key])
    return totals


def main():
    assert len(V3_IDS) == EXPECTED_ITEMS, "embedded V3_IDS length mismatch"
    assert set(V3_PAGES) == set(V3_IDS), "embedded V3_PAGES keys != V3_IDS"
    assert sum(len(v) for v in V3_PAGES.values()) >= EXPECTED_PAGES

    manifest = json.load(open(os.path.join(BASE, MANIFEST), encoding="utf-8"))
    entries = manifest["chunks"]
    assert len(entries) == 15, f"expected 15 manifest entries, got {len(entries)}"
    assert all(e.get("status") == "done" for e in entries), "not all chunks done"
    by_file = {e["file"]: e for e in entries}
    assert set(by_file) == set(CHUNK_ORDER), (
        f"manifest files != CHUNK_ORDER: "
        f"missing={set(CHUNK_ORDER) - set(by_file)} "
        f"extra={set(by_file) - set(CHUNK_ORDER)}"
    )

    all_items = []
    derived = []
    for fname in CHUNK_ORDER:
        path = os.path.join(BASE, fname)
        d = json.load(open(path, encoding="utf-8"))
        items = d["masail"]
        entry = by_file[fname]
        assert len(items) == entry["items"], (
            f"{fname}: {len(items)} items, manifest says {entry['items']}"
        )
        # Marker normalisation, with before/after counts per chunk.
        before = {"lenticular": 0, "short": 0, "full_before": 0}
        for it in items:
            c = normalise_item(it)
            for k in before:
                before[k] += c[k]
        after_full = sum(
            len(RE_FULL.findall(json.dumps(it, ensure_ascii=False)))
            for it in items
        )
        print(
            f"{fname}: {len(items)} items | markers before: "
            f"lenticular={before['lenticular']} short={before['short']} "
            f"full={before['full_before']} | after: full={after_full}"
        )
        assert after_full == (
            before["lenticular"] + before["short"] + before["full_before"]
        ), f"{fname}: marker count changed by normalisation!"
        # Derive start_page = min(pages) where absent (none expected: all chunks carry start_page).
        for it in items:
            if "start_page" not in it:
                it["start_page"] = min(it["pages"])
                derived.append(it["id"])
        all_items.extend(items)

    # GENERIC CONSECUTIVE-DUPLICATE JOIN (new for Jild 15): two
    # masail were written in multiple leaves because they are too big
    # for one worker, so concatenation gives the same id 2-3 times
    # consecutively. Each group is joined into ONE item: pages =
    # sorted union, sawal = the single non-empty one (assert exactly
    # one non-empty, and that it is in the FIRST part), jawab = parts
    # concatenated with a single space, notes = concatenated in order,
    # title / volume_id / start_page from the FIRST part.
    #   masala-72 (3 parts): leaves 05a (pp.312-358, FULL sawal
    #     1,680ch) + 05b (pp.359-405, sawal EMPTY) + 05c (pp.406-451,
    #     sawal EMPTY) -> 1 item, 140 pages, notes 6+36+28 = 70. All
    #     three parts carry the SAME title (verified by the
    #     coordinator). Verified seams: part 1 ends "…جن کی حقیقت
    #     مقصود نہیں،" (p.358); part 2 starts "درجہ چہارم یہ ہے کہ"
    #     and ends "…اسی شرح مقاصد میں ہے کہ" (p.405); part 3 starts
    #     with the restored Arabic "«الکذب وھو محال باجماع العلماء
    #     لان الکذب نقص باتفاق العقلاء»" (original p.406 head) — the
    #     exact completion of part 2's hanging "کہ".
    #   masala-74 (2 parts): leaf 06 (pp.466-500, FULL sawal) + leaf
    #     07 (pp.501-513, sawal EMPTY) -> 1 item, 48 pages. The two
    #     parts' TITLES DIFFER by design (v3 chunk titles, kept
    #     exactly): part 1 "مسئلہ ۷۴: سیالکوٹی کی عبارت اور امکانِ
    #     کذب — القمع المبین (حصہ اول)", part 2 "مسئلہ ۷۴ — القمع
    #     المبین لاٰمال المکذبین (جواب کا بقیہ حصہ)" — the joined title
    #     is part 1's, which is the merged-v3 title (asserted below).
    #     Verified seam: part 1 ends "…جبکہ یہ بعینہ جبریہ کا"
    #     (original p.500's own hanging words, after the coordinator's
    #     fix-up removing the duplicated "مذہب ہے" + the
    #     continues-marker sentence); part 2 starts "مذہب ہے، لہٰذا
    #     حال کا سہارا لینا بیکار ہوا" (the Urdu rendering of p.501's
    #     "فلا فائدۃ لتمسک بالحال").
    # After the joins there are 222 items and 222 unique ids — the
    # duplicate-id assertion runs AFTER the joins, not before.
    # NO rename quirk in Jild 15's merge: the v3 merged file has 222
    # UNIQUE ids. The 9 page-ids (jild15-p240, p258, p260, p264, p267,
    # p277, p284, p305, p309) are v3's own disambiguations of the
    # twice-numbered masail 30/31/33/34/39/47/50/62/70 — kept exactly,
    # NOT merge renames.
    def join_consecutive(item_id, expected_parts, seam_checks, title_must_match=True):
        idxs = [i for i, it in enumerate(all_items) if it["id"] == item_id]
        assert len(idxs) == expected_parts, (
            f"expected exactly {expected_parts} {item_id} parts, got {len(idxs)}"
        )
        assert all(idxs[k + 1] == idxs[k] + 1 for k in range(len(idxs) - 1)), (
            f"{item_id} parts are not consecutive"
        )
        parts = [all_items[i] for i in idxs]
        vols = {p.get("volume_id") for p in parts}
        assert vols == {51}, f"{item_id} volume mismatch: {vols}"
        non_empty_sawal = [p for p in parts if p.get("tashreeh_sawal")]
        assert len(non_empty_sawal) == 1, (
            f"{item_id}: expected exactly 1 non-empty sawal, got {len(non_empty_sawal)}"
        )
        assert non_empty_sawal[0] is parts[0], (
            f"{item_id}: the non-empty sawal must be in the FIRST part"
        )
        if title_must_match:
            assert all(p["title"] == parts[0]["title"] for p in parts), (
                f"{item_id} part titles differ"
            )
        for (part_no, which, needle) in seam_checks:
            txt = parts[part_no]["tashreeh_jawab"]
            if which == "end":
                assert txt.rstrip().endswith(needle), (
                    f"{item_id} part {part_no + 1} jawab does not end at the verified seam: {needle!r}"
                )
            else:
                assert txt.lstrip().startswith(needle), (
                    f"{item_id} part {part_no + 1} jawab does not start at the verified seam: {needle!r}"
                )
        joined = {
            "id": item_id,
            "title": parts[0]["title"],
            "volume_id": parts[0]["volume_id"],
            "pages": sorted(set().union(*[set(p["pages"]) for p in parts])),
            "start_page": min(min(p["pages"]) for p in parts),
            "tashreeh_sawal": parts[0]["tashreeh_sawal"],
            "tashreeh_jawab": " ".join(
                p["tashreeh_jawab"].strip() for p in parts
            ),
            "notes": sum((p.get("notes") or [] for p in parts), []),
        }
        all_items[idxs[0]:idxs[-1] + 1] = [joined]
        print(
            f"{item_id} joined: "
            + " + ".join(
                f"part {k + 1} ({len(p['pages'])}pp, "
                f"sawal {'EMPTY' if not p.get('tashreeh_sawal') else str(len(p['tashreeh_sawal'])) + 'ch'}, "
                f"jawab {len(p['tashreeh_jawab'])}ch, notes {len(p.get('notes') or [])})"
                for k, p in enumerate(parts)
            )
            + f" -> 1 item, {len(joined['pages'])} pages, "
              f"jawab {len(joined['tashreeh_jawab'])}ch, notes {len(joined['notes'])}"
        )
        return joined

    join_consecutive(
        "jild15-masala-72", 3,
        [(0, "end", "جن کی حقیقت مقصود نہیں،"),
         (1, "start", "درجہ چہارم یہ ہے کہ"),
         (1, "end", "اسی شرح مقاصد میں ہے کہ"),
         (2, "start", "«الکذب وھو محال باجماع العلماء لان الکذب نقص باتفاق العقلاء»")],
        title_must_match=True,
    )
    join_consecutive(
        "jild15-masala-74", 2,
        [(0, "end", "جبکہ یہ بعینہ جبریہ کا"),
         (1, "start", "مذہب ہے، لہٰذا حال کا سہارا لینا بیکار ہوا")],
        title_must_match=False,
    )
    # masala-74 title check: the joined title (part 1's) must equal the
    # merged-v3 title — the two part titles differ by design (see above).
    m74 = next(it for it in all_items if it["id"] == "jild15-masala-74")
    assert m74["title"] == "مسئلہ ۷۴: سیالکوٹی کی عبارت اور امکانِ کذب — القمع المبین (حصہ اول)", (
        f"masala-74 joined title != merged-v3 title: {m74['title']!r}"
    )
    assert len(all_items) == len({it["id"] for it in all_items}), (
        f"DUPLICATE IDS after joins: "
        f"{[i for i in [it['id'] for it in all_items] if [it['id'] for it in all_items].count(i) > 1]}"
    )
    print("renames applied: [] (no duplicate masala numbers in Jild 15's merge; masala-72 and masala-74 are joins, not renames)")

    print(f"after joins: {len(all_items)} items (225 concatenated)")
    print(f"start_page derived for {len(derived)} items (expected 0: all chunks carry start_page)")
    assert len(all_items) == EXPECTED_ITEMS, (
        f"expected {EXPECTED_ITEMS} items, got {len(all_items)}"
    )

    # Rebuild each item in the canonical key order (the JSON contract).
    canonical = []
    for it in all_items:
        assert set(it.keys()) == set(ITEM_KEYS), (
            f"{it.get('id')}: keys {sorted(it.keys())} != {sorted(ITEM_KEYS)}"
        )
        canonical.append({k: it[k] for k in ITEM_KEYS})
    all_items = canonical

    # Validation.
    ids = [it["id"] for it in all_items]
    assert ids == V3_IDS, (
        f"ID sequence != v3: first diff at "
        f"{next((i for i, (a, b) in enumerate(zip(ids, V3_IDS)) if a != b), min(len(ids), len(V3_IDS)))}"
    )
    assert len(ids) == len(set(ids)), (
        f"DUPLICATE IDS: {[i for i in ids if ids.count(i) > 1]}"
    )
    empty = [it["id"] for it in all_items if not it.get("tashreeh_jawab")]
    assert not empty, f"EMPTY JAWAB: {empty}"
    vols = set(it.get("volume_id") for it in all_items)
    assert vols == EXPECTED_VOLUME_IDS, f"volume_ids {vols} != {EXPECTED_VOLUME_IDS}"
    pages = set()
    for it in all_items:
        assert it["pages"] == V3_PAGES[it["id"]], (
            f"{it['id']}: pages {it['pages']} != v3 {V3_PAGES[it['id']]}"
        )
        pages.update(it["pages"])
    assert len(pages) == EXPECTED_PAGES, (
        f"expected {EXPECTED_PAGES} unique pages, got {len(pages)}"
    )
    assert min(pages) == EXPECTED_MIN_PAGE, f"min page {min(pages)}"
    assert max(pages) == EXPECTED_MAX_PAGE, f"max page {max(pages)}"
    exceptions = {
        it["id"] for it in all_items if it["start_page"] != min(it["pages"])
    }
    assert not exceptions, f"start_page != min(pages): {sorted(exceptions)}"
    assert ids[0] == EXPECTED_FIRST_ID, f"first id {ids[0]}"
    assert ids[-1] == EXPECTED_LAST_ID, f"last id {ids[-1]}"

    out = {"masail": all_items}
    out_text = json.dumps(out, ensure_ascii=False, indent=1)
    assert LENTICULAR_PREFIX not in out_text, "lenticular markers remain in output!"
    assert not SHORT_PREFIX_RE.search(out_text), "short markers remain in output!"
    total_markers = len(RE_FULL.findall(out_text))
    print(
        f"VALIDATION PASSED: {len(all_items)} items, {len(pages)} unique pages "
        f"(min {min(pages)}, max {max(pages)}), volume_ids {sorted(vols)}, "
        f"first {ids[0]}, last {ids[-1]}, start_page == min(pages) for all, "
        f"derived start_page for {len(derived)} items, markers {total_markers}"
    )

    with open(os.path.join(BASE, "jild-15.json"), "w", encoding="utf-8") as f:
        f.write(out_text)
    print(f"WROTE jild-15.json: {len(out_text.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
