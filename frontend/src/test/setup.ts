import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Remove rendered components after every test (needed because vitest globals are off).
afterEach(() => cleanup());
