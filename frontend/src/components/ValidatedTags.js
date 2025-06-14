import React, { useEffect, useState } from "react";
import api from "../services/api";

function scoreColor(score) {
  if (score >= 8) return "#4CAF50"; // verde
  if (score >= 6) return "#80cc33";
  if (score >= 4) return "#ffa64d";
  if (score >= 2) return "#ff4d4d";
  return "#ff1a1a";
}

function TagBadge({ tag }) {
  return <span className="tag-badge">{tag}</span>;
}

function ScoreBadge({ score }) {
  return (
    <span
      className="score-badge"
      style={{ backgroundColor: scoreColor(score), color: "#fff", padding: "0.3em 0.8em", borderRadius: "1em", fontWeight: 600 }}
    >
      {score.toFixed(1)}
    </span>
  );
}

function ValidatedTags() {
  const [validatedTags, setValidatedTags] = useState([]);
  const [answerTags, setAnswerTags] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTags();
  }, []);

  const fetchTags = async () => {
    setLoading(true);
    try {
      const [me, byAnswers] = await Promise.all([
        api.get("/api/validate/validated-tags/me"),
        api.get("/api/validate/validated-tags/by-answers"),
      ]);
      setValidatedTags(me.data.items);
      setAnswerTags(byAnswers.data.items);
    } catch (e) {
      // errore silenzioso
    }
    setLoading(false);
  };

  const renderTable = (items, role) => (
    <div className="validated-tags-table-wrapper">
      <h3 className="role-title">{role}</h3>
      {items.length === 0 ? (
        <p className="no-tags">Nessun dato disponibile.</p>
      ) : (
        <table className="validated-tags-table modern">
          <thead>
            <tr>
              <th>Tag</th>
              <th>Punteggio</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.question_id + "-" + item.user_id + "-" + item.created_at}>
                <td><TagBadge tag={item.tag} /></td>
                <td><ScoreBadge score={item.score} /></td>
                <td><span title={new Date(item.created_at).toLocaleString()}>{new Date(item.created_at).toLocaleDateString()}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );

  return (
    <div className="validated-tags-page">
      <h1 className="page-title">Punteggi delle Risposte</h1>
      <div className="tags-tables-container">
        {renderTable(validatedTags, "Come Validatore")}
        {renderTable(answerTags, "Come Rispondente")}
      </div>
      {loading && <div className="loading">Caricamento dati...</div>}
      <style>{`
        .validated-tags-page {
          max-width: 900px;
          margin: 2em auto;
          padding: 2em;
          background: #fff;
          border-radius: 1.5em;
          box-shadow: 0 2px 16px #0001;
        }
        .page-title {
          text-align: center;
          font-size: 2.2em;
          margin-bottom: 1.5em;
        }
        .tags-tables-container {
          display: flex;
          flex-wrap: wrap;
          gap: 2em;
          justify-content: space-between;
        }
        .validated-tags-table-wrapper {
          flex: 1 1 350px;
          min-width: 320px;
        }
        .role-title {
          font-size: 1.2em;
          margin-bottom: 0.7em;
          color: #222;
        }
        .validated-tags-table.modern {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
          background: #f9f9fb;
          border-radius: 1em;
          overflow: hidden;
          box-shadow: 0 1px 8px #0001;
        }
        .validated-tags-table.modern th, .validated-tags-table.modern td {
          padding: 0.8em 1.2em;
          text-align: center;
        }
        .validated-tags-table.modern th {
          background: #f1f1f7;
          color: #444;
          font-weight: 700;
          border-bottom: 2px solid #e0e0e0;
        }
        .validated-tags-table.modern tr:nth-child(even) {
          background: #f6f6fa;
        }
        .tag-badge {
          display: inline-block;
          background: #e0e7ff;
          color: #3730a3;
          font-weight: 600;
          border-radius: 1em;
          padding: 0.3em 1em;
          font-size: 1em;
        }
        .score-badge {
          font-size: 1.1em;
          letter-spacing: 0.03em;
        }
        .no-tags {
          color: #888;
          font-style: italic;
          margin: 1em 0;
        }
        @media (max-width: 800px) {
          .tags-tables-container {
            flex-direction: column;
            gap: 1.5em;
          }
        }
      `}</style>
    </div>
  );
}

export default ValidatedTags; 