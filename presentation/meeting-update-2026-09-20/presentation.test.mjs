import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const deckPath = join(here, 'index.html');

function readDeck() {
  assert.equal(existsSync(deckPath), true, 'index.html must exist');
  return readFileSync(deckPath, 'utf8');
}

test('the discussion deck has eight focused slides', () => {
  const html = readDeck();
  const slides = html.match(/<section\b[^>]*class="slide(?:\s[^"]*)?"/g) ?? [];
  assert.equal(slides.length, 8);
});

test('the deck carries the corrected evidence and current scenario', () => {
  const html = readDeck();
  for (const fact of [
    '295.0',
    '292.0',
    '36',
    '0.206%',
    '797.6',
    '12%',
    '130',
    '42',
    '884',
    '−0.4',
  ]) {
    assert.match(html, new RegExp(fact.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  }
});

test('the deck does not present void or disallowed claims', () => {
  const html = readDeck();
  for (const retired of ['175.5', '+11.7', '13.4-point', '829.2', '548.6', '437.6']) {
    assert.equal(html.includes(retired), false, `retired figure found: ${retired}`);
  }
  for (const disallowed of ['دربنا النموذج', 'قمنا بتدريب', 'trained agent']) {
    assert.equal(html.includes(disallowed), false, `disallowed claim found: ${disallowed}`);
  }
});

test('the deck supports navigation, fullscreen, and expandable viva notes', () => {
  const html = readDeck();
  assert.match(html, /data-action="prev"/);
  assert.match(html, /data-action="next"/);
  assert.match(html, /requestFullscreen/);
  assert.match(html, /keydown/);
  assert.match(html, /class="viva-note/);
  assert.match(html, /aria-expanded=/);
});

test('the document is Arabic-first and opens without network dependencies', () => {
  const html = readDeck();
  assert.match(html, /<html[^>]*lang="ar"[^>]*dir="rtl"/);
  assert.equal(/https?:\/\//.test(html), false, 'deck must be fully offline');
});
