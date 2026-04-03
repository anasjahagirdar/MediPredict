import './DisclaimerTicker.css';


function DisclaimerTicker() {
  return (
    <div className="disclaimer-ticker" role="note" aria-label="Medical disclaimer">
      <div className="disclaimer-ticker__track">
        <span className="disclaimer-ticker__text">
          This platform provides AI-generated health insights for informational purposes only and should not be considered a medical diagnosis. Please consult a qualified healthcare professional for medical advice.
        </span>
        <span className="disclaimer-ticker__text" aria-hidden="true">
          This platform provides AI-generated health insights for informational purposes only and should not be considered a medical diagnosis. Please consult a qualified healthcare professional for medical advice.
        </span>
      </div>
    </div>
  );
}


export default DisclaimerTicker;
