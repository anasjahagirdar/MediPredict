import AnalyzePage from './AnalyzePage';


function PredictPage() {
  return (
    <>
      <section className="analyze-page__container">
        <div className="analyze-card">
          <header className="analyze-card__header">
            <p className="analyze-card__eyebrow">Prediction Workspace</p>
            <h1>New prediction</h1>
          </header>
        </div>
      </section>
      <AnalyzePage />
    </>
  );
}


export default PredictPage;
