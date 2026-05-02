import React, { useState } from "react";

import { EmptyState, StatusPill } from "./Shared/ScreenComponents.jsx";
import { findById, formatDateTime } from "./Shared/ScreenUtils.jsx";

export function DocsScreen({ data, navigate }) {
  const [type, setType] = useState("all");
  const [search, setSearch] = useState("");
  const docs = (data.docs || []).filter((doc) => {
    const typeMatch = type === "all" || String(doc.document_type) === type;
    const term = `${doc.title} ${doc.document_type} ${doc.visibility}`.toLowerCase();
    return typeMatch && (!search || term.includes(search.toLowerCase()));
  });
  const types = ["all", ...new Set((data.docs || []).map((doc) => doc.document_type).filter(Boolean))];

  return (
    <section className="docs-layout">
      <aside className="docs-side">{types.map((item) => <button key={item} className={item === type ? "active" : ""} onClick={() => setType(item)}>{item === "all" ? "All Documents" : item}</button>)}</aside>
      <main><nav className="docs-nav"><strong>Across The Globe</strong><span><button onClick={() => navigate("/home/")}>Home</button><button>New Doc</button><button>My Docs</button><button>History</button><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search For Docs..." /></span></nav><h1>{type === "all" ? "Documents" : type}</h1><table className="docs-list"><tbody>{docs.map((doc) => <tr key={doc.id} onClick={() => navigate(`/docs/post-detail/${doc.id}`)}><td>{doc.title}</td><td><StatusPill tone={doc.visibility === "Private" ? "red" : "green"}>{doc.visibility || "Authenticated User"}</StatusPill></td></tr>)}</tbody></table>{!docs.length && <EmptyState label="No Documents Returned From Backend." />}</main>
    </section>
  );
}

export function DocsDetailScreen({ data, route, navigate }) {
  const id = route.split("/").filter(Boolean).pop();
  const doc = findById(data.docs, id) || {};
  return (
    <section className="docs-detail"><nav className="docs-nav dark"><strong>Across The Globe</strong><span><button onClick={() => navigate("/docs/")}>Home</button><button>New Doc</button><button>My Docs</button><button>History</button></span></nav><article><h1>{doc.title || "Document"}</h1><p>Created By {doc.owner_name || ""}</p><p>Last Updated By: {formatDateTime(doc.updated_at)}</p><button className="primary-button">Edit Doc</button><hr /><div className="doc-body" dangerouslySetInnerHTML={{ __html: doc.body || doc.metadata?.body || "" }} />{!doc.body && !doc.metadata?.body && <p className="doc-body">{doc.description || "Document Content Has Not Been Populated Yet."}</p>}</article></section>
  );
}