import React, { useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import styles from './Chat.module.scss';
import PipelineProgess from '../../rag/PipelineProgess';
import { PipelineService } from '../../../services/PipelineService';
import type { PipelineProgressEvent } from '../../../services/PipelineService';
import ChatInterface from '../../chatcomponents/ChatInterface';

const CustomChat: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const params = new URLSearchParams(location.search);
  const url = params.get('url') || '';
  const rawMaxDepth = params.get('max_depth');
  const parsed = rawMaxDepth ? Number(rawMaxDepth) : NaN;
  const maxDepth = Number.isFinite(parsed) ? Math.max(50, Math.min(1000, Math.trunc(parsed))) : 250;

  const [pipelineDone, setPipelineDone] = useState(false);
  const [pipelineFailed, setPipelineFailed] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('initializing');
  const [status, setStatus] = useState<string>('start');
  const [value, setValue] = useState<number | undefined>(0);

  const handleStep = useCallback((_stepLabel: string, update: PipelineProgressEvent) => {

    if (update.status === 'start') {
      setCurrentStep(update.step);
      setStatus('start');
      setValue(0);
    }

    if ((update.status === 'in_progress') && (typeof update.value === 'number')) {
        setStatus('in_progress');
        setValue(update.value);
    }

    if (update.status === 'done') {
      setStatus('done');
      setValue(undefined);
    }

    if (update.status === 'failed') {
      setStatus('failed');
      setValue(undefined);
    }

    if (update.step === 'pipeline' && update.status === 'done') {
      setPipelineDone(true);
    } else if (update.step === 'pipeline' && update.status === 'failed') {
      setPipelineFailed(true);
      navigate('/');
    }
  }, [navigate]);

  const startedRef = React.useRef(false);

  React.useEffect(() => {
    if (!url || startedRef.current) return;
    startedRef.current = true;

    const svc = new PipelineService();
    let mounted = true;

    (async () => {
      try {
        setPipelineDone(false);
        setPipelineFailed(false);
        setStatus('start');
        setCurrentStep('initializing');

        await svc.runFullPipeline(
          (stepLabel: string, data: PipelineProgressEvent) => {
            handleStep(stepLabel, data);
          },
          url,
          maxDepth,
          undefined,
        );

        if (!mounted) return;

        setPipelineDone(true);
        setStatus('done');
        setCurrentStep('pipeline');
        setValue(undefined);
      } catch (err: any) {
        if (!mounted) return;
        setPipelineFailed(true);
        setStatus('failed');
        navigate('/');
      }
    })();

    return () => {
      mounted = false;
      svc.closeAll();
    };
  }, [url, handleStep, navigate]);

  return (
    <div className={`container-fluid min-vh-100 d-flex flex-column ${styles.chatContainer}`}>
      <h2 className="text-center mt-4">🌐 Chat sur les données de : {url}</h2>
      <p className="text-muted text-center mb-4">
        Les données de ce site ont été crawlées et analysées. Vous pouvez maintenant discuter avec notre modèle.
      </p>

      <div className={styles.chatBox}>
        {!pipelineDone && !pipelineFailed && (
          <PipelineProgess currentStep={currentStep} status={status} value={value} />
        )}

        {pipelineDone && !pipelineFailed && (
          <ChatInterface url={url} suggestions={[]}/>
        )}
      </div>
    </div>
  );
};

export default CustomChat;