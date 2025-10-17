import React from "react";

type PipelineProgessProps = {
  currentStep: string;
  status: string;
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

export const PipelineProgess: React.FC<PipelineProgessProps> = ({ currentStep, status }) => {
  // Only use currentStep and status as requested.

  if (status === "failed") {
    return <div className="alert alert-danger">Le pipeline a échoué.</div>;
  }

  // When status === 'start' we display the current step animation/label.
  if (currentStep in ICONS) {
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
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default PipelineProgess;