import React from "react";
import "./PipelineProgess.scss";

type PipelineProgessProps = {
  currentStep: string;
  status: string;
  value?: number;
};

const ICONS: Record<string, string> = {
  initializing: "initializing",
  crawling: "crawling",
  embedding: "embedding",
  indexing: "indexing",
};
const LABELS: Record<string, string> = {
  initializing: "Initialisation du RAG",
  crawling: "Exploration du site",
  embedding: "Calcul des embeddings",
  indexing: "Vectorisation et indexation des données",
};

export const PipelineProgess: React.FC<PipelineProgessProps> = ({ currentStep, status, value }) => {
  // Only use currentStep and status as requested.
  // Debug: verify props received from backend

  if (status === "failed") {
    return <div className="alert alert-danger">Le pipeline a échoué.</div>;
  }

  // When status === 'start' we display the current step animation/label.
  if (currentStep in ICONS && status !== "failed") {
    const gifPath = `/icons/${currentStep}.gif`;
    const label = LABELS[currentStep] || currentStep;

    return (
      <div className="d-flex align-items-center my-auto justify-content-center">
        <div className="d-flex align-items-center my-auto mt-5">
          <div className="m-0 p-0">
            <img
              src={gifPath}
              alt={label}
              onError={(e) => {
                const img = e.currentTarget;
                img.style.display = "none";
                const span = document.createElement("i");
                img.parentElement?.insertBefore(span, img);
              }}
              className="me-4"
              style={{ width: 64, height: 64, objectFit: "contain" }}
            />
          </div>
          <div className="m-2">
            {label} {"en cours..."}
            {(currentStep === "crawling" || currentStep === "embedding") && typeof value === "number" ? (
              <div
                className="ms-3 pipeline-progress"
                aria-label="Progression"
                style={{
                  // expose progress value to CSS via variable for conic-gradient
                  // clamp between 0 and 100
                  // CSS expects percentage value
                  ["--progress" as any]: `${Math.max(0, Math.min(100, value))}%`,
                }}
              >
                <div className="pipeline-progress__circle">
                  <div className="pipeline-progress__inner">{Math.round(value)}%</div>
                </div>
                <span className="pipeline-progress__sr-only">Progression {value}%</span>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default PipelineProgess;