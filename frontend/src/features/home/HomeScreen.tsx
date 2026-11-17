import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { LanguageSwitch } from '../../components/LanguageSwitch';

const QUICK = [
  { key: 'map', to: '/map', color: 'text-blue' },
  { key: 'voice', to: '/settings', color: 'text-purple' },
  { key: 'accessible', to: '/settings', color: 'text-green' },
  { key: 'directory', to: '/map', color: 'text-orange' },
] as const;

/**
 * Home screen (prototype HomeScreen, without the fake parts:
 * no "Hi, Furkan", no fixed recent searches, no fake listening).
 */
export function HomeScreen() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [q, setQ] = useState('');

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const text = q.trim();
    if (text) navigate(`/search?q=${encodeURIComponent(text)}`);
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 bg-bg px-4 pb-10 pt-6 text-text">
      <header className="flex items-center justify-between">
        <div>
          {/* lang="en": the brand name must not get Turkish capitalisation ("GUİDE") */}
          <p lang="en" className="font-mono text-xs uppercase tracking-widest text-red">
            {t('app.name')}
          </p>
          <p className="text-sm text-text3">{t('app.tagline')}</p>
        </div>
        <LanguageSwitch />
      </header>

      <h1 className="text-3xl font-bold leading-tight">{t('home.title')}</h1>

      <form role="search" onSubmit={onSubmit} className="flex gap-2">
        <label htmlFor="home-search" className="sr-only">
          {t('home.searchLabel')}
        </label>
        <input
          id="home-search"
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t('home.searchPlaceholder')}
          className="min-h-touch min-w-0 flex-1 rounded-2xl bg-card px-4 text-text placeholder:text-text3
                     focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue"
        />
        <button
          type="submit"
          className="min-h-touch rounded-2xl bg-redStrong px-4 font-semibold text-white
                     focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue"
        >
          {t('home.searchButton')}
        </button>
      </form>

      <nav aria-label={t('home.quickNav')}>
        <ul className="grid grid-cols-2 gap-3">
          {QUICK.map(({ key, to, color }) => (
            <li key={key}>
              <button
                type="button"
                onClick={() => navigate(to)}
                className="min-h-touch w-full rounded-2xl bg-card p-4 text-left hover:bg-cardHi
                           focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue"
              >
                <span className={`block text-sm font-semibold ${color}`}>{t(`home.quick.${key}`)}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </main>
  );
}
