<!--
Vorlage für die AnkiWeb-Beschreibung (Feld "Description" beim Hochladen).
AnkiWeb erlaubt Markdown und einfaches HTML. Einfach den HTML-Block unten
(zwischen den Markern) in das AnkiWeb-Description-Feld kopieren.
Diese Datei wird NICHT mit ausgeliefert.
-->

# AnkiWeb description (paste-ready, copy the HTML below)

<!-- ===== BEGIN ANKIWEB DESCRIPTION ===== -->
<h1>Anki ID Copy &amp; Compare</h1>

<p><strong>TLDR:</strong> Copy selected Note IDs as a search string, send them to a friend, and <b>compare your collection with theirs</b> to instantly see exactly which cards you're missing — in a clear, colour-coded results panel. Built for students who share large decks (AnKing / Zanki / AMBOSS / Ankizin / Ankiphil).</p>

<h2>Why use this add-on?</h2>
<p>When you and your study partners use the same shared deck, it's hard to tell whether you're all studying the same cards. Comparing thousands of Note IDs by hand is slow and error-prone. This add-on does it in one click — and shows you not just <i>what</i> differs, but <i>where</i> (by subject) and <i>how</i> (e.g. cards you have but suspended).</p>

<h2>Key features</h2>

<p><b>1. Copy Note IDs as a search string</b></p>
<ul>
<li>Select notes in the Browser, right-click &rarr; <i>Copy Note IDs as Search String</i> (or press the shortcut, default <i>Ctrl+Alt+C</i>).</li>
<li>Copies a compact query (e.g. <i>nid:1,2,3</i>) to your clipboard — share it, or paste it into Anki's search bar.</li>
</ul>

<p><b>2. Compare with a friend — results scorecard</b></p>
<p>Paste your IDs and your friend's, click Compare, and get a scorecard with every region:</p>
<ul>
<li><b>Missing</b> (your friend has, you don't) — split into <i>present in your collection (e.g. suspended)</i> vs <i>not in your collection at all</i>.</li>
<li><b>Extra</b> (you have, your friend doesn't).</li>
<li><b>Shared</b> (both have).</li>
</ul>
<p>Each region opens straight in the Browser or copies to the clipboard.</p>

<p><b>3. Suspension-aware</b></p>
<p>For every region you own, see how many of those notes you have suspended and jump right to them — perfect for "activate the cards my study partner is learning that I've turned off".</p>

<p><b>4. Coverage breakdown by deck or tag</b></p>
<p>Break any region down by deck (subject) or by tag, sorted by count, to see <i>where</i> you differ — e.g. "Pharmacology: 42, Cardiology: 18" — and open each group in the Browser.</p>

<p><b>5. Find due siblings (Tools menu)</b></p>
<p>Via <i>Tools &rarr; Find due siblings &hellip;</i> (DE: <i>Werkzeuge &rarr; Fällige Geschwister finden &hellip;</i>) you find new (blue) cards whose sibling cards — other cards of the same note, e.g. other clozes — you have already learned to a stable state, so they don't drown in your pile of new cards. Options:</p>
<ul>
<li><b>Deck</b> — restrict the search to one deck, or leave empty for all decks.</li>
<li><b>Hide cards whose siblings are struggling</b> — exclude notes whose siblings are still in the learning phase, are leeches, or have too many lapses (default: on).</li>
<li><b>Advanced &rarr; Interval threshold</b> — minimum sibling interval (days) to count as learned (default: 21 days).</li>
<li><b>Advanced &rarr; Max. lapses</b> — maximum allowed lapses of the sibling (default: 1).</li>
</ul>
<p>A live count updates as you adjust the settings. Then choose <i>Show in browser</i> to inspect the cards, or <i>Start as study deck</i> to build a rescheduling filtered deck and review them immediately. Settings are remembered between sessions.</p>

<h2>Also</h2>
<ul>
<li>Modern interface that follows Anki's light and dark theme.</li>
<li>German and English (follows Anki's language setting).</li>
<li>Configurable shortcut and output format (compact <i>nid:1,2,3</i> or <i>nid:1 OR nid:2</i>) via Tools &rarr; Add-ons &rarr; Config.</li>
<li>Reachable from the Browser right-click menu or via <i>Tools &rarr; Anki ID Copy: Compare Note IDs</i>.</li>
</ul>

<h2>Compatibility</h2>
<p>Anki 2.1.50 and newer (both Qt5 and Qt6 builds).</p>

<h2>A note on Note IDs</h2>
<p>Comparison matches on Anki Note IDs. These stay identical for everyone who got a deck the same way (a shared AnkiCollab subscription, an AnkiHub deck, or the same downloaded .apkg), so the comparison is exact for study groups on the same source. If two people obtained "the same" deck through different channels, their IDs may not line up.</p>

<p>Open-source (MIT). Issues and contributions welcome: https://github.com/tamenmd/Anki_ID_Copy</p>
<!-- ===== END ANKIWEB DESCRIPTION ===== -->
