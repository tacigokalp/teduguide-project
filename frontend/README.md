# TEDU Guide — frontend (Area B)

```bash
pnpm install     # or: npm install
pnpm dev         # http://localhost:5173
pnpm test        # UT-UI-001 (Home), UT-UI-002 (i18n keys)
pnpm build
```

- Design tokens: `tailwind.config.ts` (contrast-checked for WCAG AA; see the comment there).
- Texts: `src/i18n/en.json` and `src/i18n/tr.json`. Never hard-code text in a component; add the key to **both** files (UT-UI-002 fails otherwise).
