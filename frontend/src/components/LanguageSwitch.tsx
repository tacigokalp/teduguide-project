import { useTranslation } from 'react-i18next';

/** EN / TR toggle. One button that switches to the other language. */
export function LanguageSwitch() {
  const { t, i18n } = useTranslation();
  const current = i18n.language.startsWith('tr') ? 'tr' : 'en';
  const other = current === 'tr' ? 'en' : 'tr';

  return (
    <button
      type="button"
      onClick={() => void i18n.changeLanguage(other)}
      aria-label={`${t('language.switchLabel')}: ${t(`language.${other}`)}`}
      className="min-h-touch min-w-touch rounded-full bg-card px-4 font-mono text-sm text-text2
                 hover:bg-cardHi focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue"
    >
      {other.toUpperCase()}
    </button>
  );
}
