# Drive retrieval provenance and limitations

Retrieved 2026-11-04 through the Google Drive connector. Private Drive URLs, file IDs, folder IDs and personal paths are omitted or explicitly redacted for public publication. No sharing permissions or source documents were changed.

| Requested document | Retrieval result | Provider last-modified UTC | Local artifact |
|---|---|---|---|
| WORKFLOW_GOVERNANCE.md | Exact Drive filename not found. The chat “Develop Workflow Governance” contains an assistant-authored writing artifact with this name; “Assess Project Status” later links a replacement download and explicitly says the project attachment itself was not replaced. These establish chat artifacts, not a fetched Drive file. | Unknown; not inferred from a chat date | No fabricated Drive copy |
| STANDARDS_REGISTER.md | Exact Drive filename not found. “Develop Workflow Governance” reports a generated downloadable Markdown file. A separately titled native Google Doc was found; identity with the requested Markdown file is not established. | Unknown for exact Markdown file | Related project-only extract below |
| gpt_RollingAuditHandoff.md | Exact title located and readable text fetched | 2026-10-01T03:13:54.418Z | gpt_RollingAuditHandoff.md |
| NUMBER_PROJECT_CURRENT_WORK_ORDER.md | Exact title located and readable text fetched | 2026-09-28T20:21:52.475Z | NUMBER_PROJECT_CURRENT_WORK_ORDER.md |

For each readable exact-title source, discovery search returned title, MIME type, size, created_at and updated_at. A subsequent get_file_metadata request for id/name/mimeType/modifiedTime/createdTime/size returned the same modification instant in modified_time. The text fetch independently returned the same modified_time. These are current provider metadata at retrieval, not historical session timestamps or proof that a particular chat consumed that revision.

- Handoff: text/markdown; provider size 47,338 bytes; created 2026-09-09T01:39:13.888Z.
- Work order: text/markdown; provider size 27,072 bytes; created 2026-09-15T14:29:59.022Z.
- Related native document: exact displayed title “00 — Standards Register & Adoption Map”; application/vnd.google-apps.document; created 2026-09-12T23:14:50.204Z; last modified 2026-09-12T23:16:04.157Z. This date belongs only to that related Google Doc.

The work-order folder listing independently corroborated its title and modification time. Discovery included exact-name queries, title-keyword queries, a related-title search, and the known Workflow Management folder listing/search. Failure to find a title does not prove it never existed, was never attached to a project, or is unavailable through every account/surface.

The two .md files here are scrubbed readable-text snapshots, not certified binary-preserving raw downloads. Their scientific/project prose was retained; privacy markers are the only intended content edits. SHA256SUMS.txt records local delivery bytes, not the private originals. Any embedded historical digest describes its original named object and should not be applied to a scrubbed file.

The handoff is a rolling, layered document: it contains later updates and preserved historical sections. It is not a contemporaneous September-2 transcript and cannot establish who first proposed a ritual, the owner's exact messages, or why work stopped. In particular, its October-1 modification and later Phase B entries limit any claim of a late-September stop.

The current work order is NP-POWER-THRESHOLD-01 revision 1, specification prepared / not frozen / execution not started. It is not the consumed historical PySR work order, even though the rolling filename is the same.
