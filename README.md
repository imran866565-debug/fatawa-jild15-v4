# Fatawa Razviya — Jild 15 tashreeh v4 merge

Merge workspace: 15 leaf chunk files of the easy-Urdu tashreeh v4 for Fatawa Razviya Jild 15 (volume_id 51; 222 items, 662 pages) are merged into `jild-15.json` by GitHub Actions (`merge_jild15_v4.py`), then published as a v1.0 release asset.

Item order reproduces the v3 merged file exactly (first jild15-pesh-lafz, last jild15-p740-taqriz). All 15 leaf chunks carry start_page == min(pages). The v3 merged file disambiguates the twice-numbered masala 30/31/33/34/39/47/50/62/70 as page-ids (jild15-p240 etc.), kept exactly; the merge joins masala-72 (leaves 05a+05b+05c) and masala-74 (leaves 06+07) into single items, matching the v3 merged file. No page markers are present in the chunks.
