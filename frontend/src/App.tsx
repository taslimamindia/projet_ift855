import './App.css';
import { Routes, Route } from 'react-router-dom';
import Home from './components/pages/home/Home';
import NotFound from './components/pages/errors/NotFound';
import GovGnChat from './components/pages/chatpage/GovGnChat';
import CustomChat from './components/pages/chatpage/CustomChat';

function App() {
  return (
    <>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat/gov/gn" element={<GovGnChat />} />
        <Route path="/chat/custom" element={<CustomChat />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  )
};

export default App
