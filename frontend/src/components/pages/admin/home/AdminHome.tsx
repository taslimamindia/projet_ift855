import React from 'react';
import { Link } from 'react-router-dom';
import styles from './AdminHome.module.scss';

const AdminHome: React.FC = () => {
    return (
        <div className={styles.container}>
            <h1>Admin Dashboard</h1>
            <p>Welcome to the administration area.</p>
            
            <div className={styles.cardContainer}>
                <Link to="/admin/memory" className={styles.card}>
                    <h3>Memory Monitor</h3>
                    <p>Monitor and manage system memory usage.</p>
                </Link>
                <Link to="/admin/crawler" className={styles.card}>
                    <h3>Crawler</h3>
                    <p>Lancer un crawl personnalisé (Admin).</p>
                </Link>
                {/* Add more admin links here as needed */}
            </div>
        </div>
    );
};

export default AdminHome;
