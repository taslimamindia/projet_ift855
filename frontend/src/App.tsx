import './App.css';
import { Routes, Route } from 'react-router-dom';
import Home from './components/pages/home/Home';
import NotFound from './components/pages/errors/NotFound';
import GovGnChat from './components/pages/chatpage/GovGnChat';
import CustomChat from './components/pages/chatpage/CustomChat';
import Header from './components/Header/Header';

function App() {
  return (
    <>
      <Header />
      <div className="container-fluid mt-3">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat/gov/gn" element={<GovGnChat />} />
          <Route path="/chat/custom" element={<CustomChat />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </div>
    </>
  )
};

export default App
