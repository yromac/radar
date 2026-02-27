import { Routes, Route } from 'react-router-dom'
import { Nav } from './components/Nav'
import { Home } from './pages/Home'
import { Events } from './pages/Events'
import { Subscribe } from './pages/Subscribe'
import { Partners } from './pages/Partners'

export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/"          element={<Home />}      />
        <Route path="/events"    element={<Events />}    />
        <Route path="/subscribe" element={<Subscribe />} />
        <Route path="/partners"  element={<Partners />}  />
      </Routes>
    </>
  )
}
