/** UT-UI-002: every text key exists in both English and Turkish, and no text is empty. */
import { describe, expect, it } from 'vitest';
import en from './en.json';
import tr from './tr.json';

type Tree = { [key: string]: string | Tree };

function keys(tree: Tree, prefix = ''): string[] {
  return Object.entries(tree).flatMap(([k, v]) =>
    typeof v === 'string' ? [`${prefix}${k}`] : keys(v, `${prefix}${k}.`),
  );
}

function values(tree: Tree): string[] {
  return Object.values(tree).flatMap((v) => (typeof v === 'string' ? [v] : values(v)));
}

describe('i18n files', () => {
  it('have exactly the same keys', () => {
    expect(keys(tr as Tree).sort()).toEqual(keys(en as Tree).sort());
  });

  it('have no empty texts', () => {
    for (const v of [...values(en as Tree), ...values(tr as Tree)]) {
      expect(v.trim().length > 0).toBe(true);
    }
  });
});
