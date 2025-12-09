import React from 'react';
import { Outlet } from 'react-router-dom';
import AdminHeader from './header/AdminHeader';

const AdminLayout: React.FC = () => {
    return (
        <div>
            <AdminHeader />
            <div style={{ padding: '0 1rem' }}>
                <Outlet />
            </div>
        </div>
    );
};

export default AdminLayout;
