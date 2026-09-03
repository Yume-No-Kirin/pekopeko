import { useEffect, useState } from "react";
import { get } from "../api/client.js";

export default function Settings() {
  const [config, setConfig] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    get("/config")
      .then((data) => {
        if (!cancelled) setConfig(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <header className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Configuration locale (lecture seule)</p>
      </header>

      <div className="content-wrapper">
        {error && (
          <div className="settings-error" role="alert">
            Impossible de charger la configuration : {error.message}
          </div>
        )}

        {!error && !config && <div className="settings-loading">Chargement de la configuration…</div>}

        {!error && config && (
          <dl className="settings-fields">
            <dt>Provider LLM actif</dt>
            <dd>{config.llm_provider.active}</dd>

            <dt>Domaine par défaut</dt>
            <dd>{config.default.domain}</dd>

            <dt>Emplacement de l'index de retrieval</dt>
            <dd>{config.retrieval.index_dir}</dd>

            <dt>Emplacement de l'état de tâche</dt>
            <dd>{config.task_state.dir}</dd>
          </dl>
        )}

        <p className="settings-help">
          Cette configuration est lue depuis le fichier local <code>~/.pekopeko/config.yaml</code>{" "}
          (et le fichier compagnon optionnel <code>~/.pekopeko/.env</code> pour les secrets).
          L'édition se fait manuellement dans ces fichiers — il n'y a pas d'interface
          d'édition pour le moment.
        </p>
      </div>
    </>
  );
}
