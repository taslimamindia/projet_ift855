import React from 'react';
import { NavLink } from 'react-router-dom';
import styles from './AdminHeader.module.scss';

const AdminHeader: React.FC = () => {
    return (
        <div className={styles.adminHeader}>
            <nav>
                <ul className={styles.nav}>
                    <li>
                        <NavLink 
                            to="/admin" 
                            end
                            className={({ isActive }) => 
                                `${styles.navLink} ${isActive ? styles.active : ''}`
                            }
                        >
                            Dashboard
                        </NavLink>
                    </li>
                    <li>
                        <NavLink 
                            to="/admin/memory" 
                            className={({ isActive }) => 
                                `${styles.navLink} ${isActive ? styles.active : ''}`
                            }
                        >
                            Memory Monitor
                        </NavLink>
                    </li>
                    <li>
                        <NavLink 
                            to="/admin/crawler" 
                            className={({ isActive }) => 
                                `${styles.navLink} ${isActive ? styles.active : ''}`
                            }
                        >
                            Crawler
                        </NavLink>
                    </li>
                </ul>
            </nav>
        </div>
    );
};

export default AdminHeader;
