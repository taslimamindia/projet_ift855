import React, { useEffect, useState } from 'react';
import styles from './AdminFolders.module.scss';
import { AdminService } from '../../../../services/AdminService';

type FetchState = 'idle' | 'loading' | 'error' | 'success';

const AdminFolders: React.FC = () => {
    const [folders, setFolders] = useState<string[]>([]);
    const [selected, setSelected] = useState<Record<string, boolean>>({});
    const [fetchState, setFetchState] = useState<FetchState>('idle');
    const [deleteState, setDeleteState] = useState<FetchState>('idle');
    const [message, setMessage] = useState<string>('');

    const loadFolders = async () => {
        setFetchState('loading');
        setMessage('');
        try {
            const data = await AdminService.listFolders();
            setFolders(data);
            const nextSel: Record<string, boolean> = {};
            data.forEach((f) => (nextSel[f] = false));
            setSelected(nextSel);
            setFetchState('success');
        } catch (e: any) {
            setFetchState('error');
            setMessage(e?.message || 'Error loading folders');
        }
    };

    useEffect(() => {
        loadFolders();
    }, []);

    const toggle = (folder: string) => {
        setSelected((prev) => ({ ...prev, [folder]: !prev[folder] }));
    };

    const deleteSelected = async () => {
        const toDelete = Object.entries(selected)
            .filter(([, v]) => v)
            .map(([k]) => k);

        if (toDelete.length === 0) {
            setMessage('Please select at least one folder.');
            return;
        }
        setDeleteState('loading');
        setMessage('');
        try {
            console.log('Deleting folders:', toDelete);
            const txt = await AdminService.deleteFolders(toDelete);
            setDeleteState('success');
            setMessage(txt || 'Deletion successful');
            await loadFolders();
        } catch (e: any) {
            setDeleteState('error');
            setMessage(e?.message || 'Error deleting folders');
        }
    };

    const allChecked = folders.length > 0 && folders.every((f) => selected[f]);
    const toggleAll = () => {
        const next: Record<string, boolean> = {};
        folders.forEach((f) => (next[f] = !allChecked));
        setSelected(next);
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.header}>Folder Management (Admin)</h1>

            {fetchState === 'loading' && <p>Loading folders…</p>}
            {message && (
                <p className={deleteState === 'error' || fetchState === 'error' ? styles.error : styles.success}>{message}</p>
            )}

            <div className={styles.actions}>
                <button onClick={loadFolders} disabled={fetchState === 'loading'}>Refresh</button>
                <button onClick={toggleAll} disabled={folders.length === 0}>
                    {allChecked ? 'Uncheck all' : 'Check all'}
                </button>
                <button onClick={deleteSelected} disabled={deleteState === 'loading'}>Delete selected</button>
            </div>
            
            <div className={styles.list}>
                {folders.length === 0 && fetchState === 'success' && <p>No folders found.</p>}
                {folders.map((folder) => (
                    <label key={folder} className={styles.item}>
                        <input type="checkbox" checked={!!selected[folder]} onChange={() => toggle(folder)} />
                        <span>{folder}</span>
                    </label>
                ))}
            </div>
        </div>
    );
};

export default AdminFolders;
