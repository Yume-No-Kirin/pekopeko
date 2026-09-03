import { useEffect, useState } from "react";
import StatCard from "../components/StatCard.jsx";
import ModuleCard from "../components/ModuleCard.jsx";
import { get } from "../api/client.js";
import { DOMAINS } from "../api/domains.js";

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;

function sumTotals(pages) {
  return pages.reduce((sum, page) => sum + page.total, 0);
}

// N+1 by design: ProposalSummary (the list-endpoint item shape) has no
// reviewed_at field, only ProposalDetail.frontmatter does. Same precedent as
// TASK-010's Validation screen - fetching the detail endpoint per item rather
// than extending TASK-007's ProposalSummary contract.
async function countRecentlyReviewed(domain, items) {
  const cutoff = Date.now() - THIRTY_DAYS_MS;
  const details = await Promise.all(
    items.map((item) => get(`/domains/${domain}/proposals/${item.id}`))
  );
  return details.filter((detail) => {
    const reviewedAt = detail.frontmatter && detail.frontmatter.reviewed_at;
    if (!reviewedAt) return false;
    const reviewedAtMs = new Date(reviewedAt).getTime();
    return !Number.isNaN(reviewedAtMs) && reviewedAtMs >= cutoff;
  }).length;
}

async function loadDashboardStats() {
  const [pendingByDomain, runningByDomain, proposedByDomain, editedByDomain, acceptedByDomain, rejectedByDomain] =
    await Promise.all([
      Promise.all(DOMAINS.map((d) => get(`/domains/${d}/ingestions?status=pending`))),
      Promise.all(DOMAINS.map((d) => get(`/domains/${d}/ingestions?status=running`))),
      Promise.all(DOMAINS.map((d) => get(`/domains/${d}/proposals?status=PROPOSED`))),
      Promise.all(DOMAINS.map((d) => get(`/domains/${d}/proposals?status=EDITED`))),
      // limit=500 (the API max) rather than the default 50: this fetch's `items` feed
      // countRecentlyReviewed below, so truncation can silently drop real 30-day decisions.
      Promise.all(DOMAINS.map((d) => get(`/domains/${d}/proposals?status=ACCEPTED&limit=500`))),
      Promise.all(DOMAINS.map((d) => get(`/domains/${d}/proposals?status=REJECTED&limit=500`))),
    ]);

  const ingestionsEnCours = sumTotals(pendingByDomain) + sumTotals(runningByDomain);
  // EDITED proposals are still undecided (src/app/review/pipeline.py only lets
  // PROPOSED/EDITED proposals be edited/accepted/rejected), so they count as pending too.
  const propositionsEnAttente = sumTotals(proposedByDomain) + sumTotals(editedByDomain);
  const connaissancesCanoniques = sumTotals(acceptedByDomain);

  const recentCounts = await Promise.all(
    DOMAINS.map(async (domain, i) => {
      const [acceptedRecent, rejectedRecent] = await Promise.all([
        countRecentlyReviewed(domain, acceptedByDomain[i].items),
        countRecentlyReviewed(domain, rejectedByDomain[i].items),
      ]);
      return { acceptedRecent, rejectedRecent };
    })
  );

  const totalAcceptedRecent = recentCounts.reduce((sum, c) => sum + c.acceptedRecent, 0);
  const totalRejectedRecent = recentCounts.reduce((sum, c) => sum + c.rejectedRecent, 0);
  const denominator = totalAcceptedRecent + totalRejectedRecent;
  const acceptanceRate = denominator === 0 ? null : totalAcceptedRecent / denominator;

  return { ingestionsEnCours, propositionsEnAttente, connaissancesCanoniques, acceptanceRate };
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadDashboardStats()
      .then((result) => {
        if (!cancelled) setStats(result);
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
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Vue d'ensemble du système d'ingestion et de validation</p>
      </header>

      <div className="content-wrapper">
        {error && (
          <div className="dashboard-error" role="alert">
            Impossible de charger les statistiques : {error.message}
          </div>
        )}

        {!error && !stats && <div className="dashboard-loading">Chargement des statistiques…</div>}

        {!error && stats && (
          <section className="stats-grid">
            <StatCard label="Ingestions en cours" value={stats.ingestionsEnCours} />
            <StatCard label="Propositions en attente" value={stats.propositionsEnAttente} />
            <StatCard
              label="Connaissances canoniques"
              value={stats.connaissancesCanoniques}
              detail="Tous domaines confondus"
            />
            <StatCard
              label="Taux d'acceptation"
              value={
                stats.acceptanceRate === null ? "—" : `${Math.round(stats.acceptanceRate * 100)}%`
              }
              detail="Sur les 30 derniers jours"
            />
          </section>
        )}

        <section className="modules-section">
          <h2 className="section-title">Modules disponibles</h2>
          <div className="modules-grid">
            <ModuleCard
              title="Validation"
              description="Vue unifiée de l'ingestion à la validation : toutes les notes proposées groupées par source, édition et validation directe dans la liste."
              status="available"
              to="/validation"
            />
            <ModuleCard
              title="Logs d'ingestion"
              description="Vue détaillée des tâches d'ingestion : logs complets, gestion des erreurs, ingestions rejetées ou échouées."
              status="available"
              to="/ingestion-logs"
            />
            <ModuleCard
              title="Settings"
              description="Configuration locale active : provider LLM, domaine par défaut, emplacements de l'index de retrieval et de l'état de tâche."
              status="available"
              to="/settings"
            />
            <ModuleCard
              title="Analytics"
              description="Tableaux de bord et métriques d'ingestion, visualisations des tendances et rapports d'activité."
              status="coming-soon"
            />
            <ModuleCard
              title="Export"
              description="Export de la base de connaissances canonique en différents formats (JSON, Markdown, GraphML)."
              status="coming-soon"
            />
            <ModuleCard
              title="Recherche"
              description="Recherche full-text et sémantique dans la base de connaissances, avec filtres par domaine et type."
              status="coming-soon"
            />
          </div>
        </section>
      </div>
    </>
  );
}
