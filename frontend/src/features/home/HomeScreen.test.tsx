/** UT-UI-001: Home screen renders with the design tokens and a working EN/TR switch. */
import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it } from 'vitest';
import i18n from '../../i18n';
import { HomeScreen } from './HomeScreen';

function renderHome() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <HomeScreen />
    </MemoryRouter>,
  );
}

describe('HomeScreen', () => {
  beforeEach(async () => {
    await act(() => i18n.changeLanguage('en'));
  });

  it('renders the title, search box and quick actions', () => {
    renderHome();
    expect(screen.getByRole('heading', { level: 1, name: 'Where do you want to go?' })).toBeInTheDocument();
    expect(screen.getByRole('searchbox', { name: 'Search for a room, person or place' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Step-free routes' })).toBeInTheDocument();
  });

  it('uses the design tokens', () => {
    renderHome();
    expect(screen.getByRole('main')).toHaveClass('bg-bg', 'text-text');
    expect(screen.getByRole('button', { name: 'Search' })).toHaveClass('bg-redStrong');
  });

  it('switches to Turkish and back', async () => {
    renderHome();
    await act(async () => fireEvent.click(screen.getByRole('button', { name: /Change language/ })));
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Nereye gitmek istiyorsunuz?');
    expect(document.documentElement.lang).toBe('tr');
    await act(async () => fireEvent.click(screen.getByRole('button', { name: /Dili değiştir/ })));
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Where do you want to go?');
  });

  it('keeps the brand name English in Turkish (no "GUİDE")', async () => {
    await act(() => i18n.changeLanguage('tr'));
    renderHome();
    expect(screen.getByText('TEDU Guide')).toHaveAttribute('lang', 'en');
  });
});
