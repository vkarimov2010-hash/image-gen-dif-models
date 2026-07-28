import { NavLink, Route, HashRouter, Routes } from "react-router-dom";
import { CreditBadge } from "./components/CreditBadge";
import { GeneratePage } from "./pages/GeneratePage";
import { HistoryPage } from "./pages/HistoryPage";
import "./App.css";

function App() {
  return (
    <HashRouter>
      <div className="app-shell">
        <header className="app-header">
          <h1>Сравнение моделей генерации изображений</h1>
          <nav>
            <NavLink to="/" end>
              Генерация
            </NavLink>
            <NavLink to="/history">История</NavLink>
          </nav>
          <CreditBadge />
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<GeneratePage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
}

export default App;
