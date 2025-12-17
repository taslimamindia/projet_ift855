import React, { useState, useCallback, useEffect } from 'react';
import styles from './AdminCrawler.module.scss';
import { PipelineService } from '../../../../services/PipelineService';
import type { PipelineProgressEvent } from '../../../../services/PipelineService';
import PipelineProgess from '../../../rag/PipelineProgess';
import { AdminService } from '../../../../services/AdminService';

const AdminCrawler: React.FC = () => {
    const [url, setUrl] = useState('');
    const [maxDepth, setMaxDepth] = useState<number>(250);
    const [dataFolder, setDataFolder] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [pipelineDone, setPipelineDone] = useState(false);
    const [pipelineFailed, setPipelineFailed] = useState(false);
    const [currentStep, setCurrentStep] = useState<string>('initializing');
    const [status, setStatus] = useState<string>('start');
    const [error, setError] = useState<string | null>(null);
    const [value, setValue] = useState<number | undefined>(0);

    useEffect(() => {
        const fetchConfig = async () => {
            try {
                const data = await AdminService.getConfig();
                if (data.default_folder) {
                    setDataFolder(data.default_folder);
                }
            } catch (error) {
                console.error('Failed to fetch config:', error);
            }
        };
        fetchConfig();
    }, []);

    const handleStep = useCallback((_stepLabel: string, update: PipelineProgressEvent) => {
        if (update.status === 'start') {
            setCurrentStep(update.step);
        }

        if (update.status === 'in_progress' && typeof update.value === 'number') {
            setValue(update.value);
        }

        if (update.status === 'done') {
            setValue(0);
        }
    
        if (update.status === 'failed') {
            setValue(undefined);
        }

        setStatus(update.status);

        if (update.step === 'pipeline' && update.status === 'done') {
            setPipelineDone(true);
            setIsProcessing(false);
        } else if (update.step === 'pipeline' && update.status === 'failed') {
            setPipelineFailed(true);
            setIsProcessing(false);
            setError(update.error || 'Pipeline failed');
        }
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url.trim() || !dataFolder.trim()) return;

        setIsProcessing(true);
        setPipelineDone(false);
        setPipelineFailed(false);
        setError(null);
        setStatus('start');
        setCurrentStep('initializing');

        const svc = new PipelineService();
        const max_depth = Math.max(50, Math.min(1000, Number(maxDepth) || 250));

        try {
            await svc.runAdminPipeline(
                (stepLabel: string, data: PipelineProgressEvent) => {
                    handleStep(stepLabel, data);
                },
                url,
                dataFolder,
                max_depth,                
                undefined,
            );
        } catch (err: any) {
            console.error('Pipeline failed:', err);
            setPipelineFailed(true);
            setIsProcessing(false);
            setError(err.message || 'An error occurred');
        }
    };

    return (
        <div className={styles.crawlerContainer}>
            <div className={styles.card}>
                <h2 className={styles.cardTitle}>Admin Crawler</h2>
                <p className={styles.cardText}>
                    Configure and run the crawling pipeline with admin parameters.
                </p>

                {!isProcessing && !pipelineDone && (
                    <form onSubmit={handleSubmit}>
                        <div className={styles.formGroup}>
                            <label htmlFor="url" className={styles.label}>Website URL</label>
                            <input
                                id="url"
                                type="url"
                                placeholder="https://"
                                className={styles.input}
                                value={url}
                                onChange={(e) => {
                                    let value = e.target.value;
                                    if (value && !value.startsWith("https://")) {
                                        value = "https://" + value;
                                    }
                                    setUrl(value);
                                }}
                                required
                            />
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="dataFolder" className={styles.label}>Data folder</label>
                            <input
                                id="dataFolder"
                                type="text"
                                placeholder="Folder name to store crawled data"
                                className={styles.input}
                                value={dataFolder}
                                onChange={(e) => setDataFolder(e.target.value)}
                                required
                            />
                            <span className={styles.helperText}>The folder name where crawled data will be saved.</span>
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="maxDepth" className={styles.label}>Max depth</label>
                            <input
                                id="maxDepth"
                                type="number"
                                className={styles.input}
                                value={maxDepth}
                                min={50}
                                max={2000}
                                onChange={(e) => {
                                    let v = Number(e.target.value);
                                    if (Number.isNaN(v)) v = 250;
                                    setMaxDepth(v);
                                }}
                            />
                            <span className={styles.helperText}>Between 50 and 1000 pages (default: 250)</span>
                        </div>

                        <button type="submit" className={styles.submitButton} disabled={isProcessing}>
                            Run Pipeline
                        </button>
                    </form>
                )}

                {(isProcessing || pipelineDone || pipelineFailed) && (
                    <div className="mt-4">
                        
                        {(!pipelineDone && !pipelineFailed && isProcessing) && (
                            <PipelineProgess currentStep={currentStep} status={status} value={value} />
                        )}

                        {pipelineDone && (
                            <div className={`${styles.status} ${styles.success}`}>
                                Pipeline completed successfully!
                                <button 
                                    className={`btn btn-primary mt-3 d-block mx-auto`}
                                    onClick={() => {
                                        setIsProcessing(false);
                                        setPipelineDone(false);
                                        setCurrentStep('initializing');
                                        setStatus('start');
                                    }}
                                >
                                    New Crawl
                                </button>
                            </div>
                        )}

                        {pipelineFailed && (
                            <div className={`${styles.status} ${styles.error}`}>
                                Error: {error}
                                <button 
                                    className={`btn btn-secondary mt-3 d-block mx-auto`}
                                    onClick={() => {
                                        setIsProcessing(false);
                                        setPipelineFailed(false);
                                        setError(null);
                                    }}
                                >
                                    Retry
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminCrawler;
