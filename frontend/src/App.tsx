import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { HomeScreen } from './features/home/HomeScreen';

/** Routes from Project.md §12 B6. Screens other than Home come in later steps (B-08, B-09, B-12...). */
export function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Routes>
        <Route path="/" element={<HomeScreen />} />
        <Route path="*" element={<HomeScreen />} />
      </Routes>
    </BrowserRouter>
  );
}
