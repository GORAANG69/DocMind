import { NavLink, Outlet } from 'react-router-dom';
import { FileText, Search, LayoutDashboard } from 'lucide-react';

const AppLayout = () => {
  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">
            <FileText size={20} color="white" />
          </div>
          <div className="logo-text">DocMind</div>
        </div>

        <nav className="nav-menu">
          <NavLink 
            to="/" 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            end
          >
            <LayoutDashboard size={20} />
            Dashboard
          </NavLink>
          <NavLink 
            to="/documents" 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <FileText size={20} />
            Documents
          </NavLink>
          <NavLink 
            to="/search" 
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <Search size={20} />
            Search
          </NavLink>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
