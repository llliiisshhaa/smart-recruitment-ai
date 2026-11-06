import React from "react";
import StatusBadge from "./StatusBadge.jsx";
import { LoadingSpinner } from "./LoadingSpinner.jsx";

export function ParsedResumeModal({
  isOpen,
  onClose,
  resume,
  parsedData,
  isLoading,
  error,
  onRetry,
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-white truncate">
                {resume?.original_filename || "Parsed Resume Dossier"}
              </h2>
              {resume?.parse_status && (
                <StatusBadge status={resume.parse_status} />
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Deterministic offline AI resume analysis & evidence extraction
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors cursor-pointer"
            aria-label="Close modal"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {isLoading ? (
            <div className="py-12">
              <LoadingSpinner text="Extracting and verifying resume data..." />
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 space-y-3">
              <p className="font-semibold text-white">Parsing Unsuccessful</p>
              <p className="text-xs">{error}</p>
              {onRetry && (
                <button
                  type="button"
                  onClick={onRetry}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition-colors cursor-pointer"
                >
                  Retry Parsing
                </button>
              )}
            </div>
          ) : parsedData ? (
            <>
              {/* Contact Information */}
              {parsedData.parsed_json?.contact && (
                <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-3">
                    Candidate Profile & Contacts
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-slate-500 block">Name:</span>
                      <span className="font-semibold text-white">
                        {parsedData.parsed_json.contact.name || "Not detected"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Email:</span>
                      <span className="font-semibold text-white">
                        {parsedData.parsed_json.contact.email || "Not detected"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Phone:</span>
                      <span className="font-semibold text-white">
                        {parsedData.parsed_json.contact.phone || "Not detected"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">LinkedIn:</span>
                      {parsedData.parsed_json.contact.linkedin ? (
                        <a
                          href={parsedData.parsed_json.contact.linkedin}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-400 hover:underline"
                        >
                          {parsedData.parsed_json.contact.linkedin}
                        </a>
                      ) : (
                        <span className="text-slate-500">Not detected</span>
                      )}
                    </div>
                    <div>
                      <span className="text-slate-500 block">GitHub:</span>
                      {parsedData.parsed_json.contact.github ? (
                        <a
                          href={parsedData.parsed_json.contact.github}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-400 hover:underline"
                        >
                          {parsedData.parsed_json.contact.github}
                        </a>
                      ) : (
                        <span className="text-slate-500">Not detected</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Extracted Skills & Supporting Evidence */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
                    Extracted Technical Skills & Evidence (
                    {parsedData.skills?.length || 0})
                  </h3>
                </div>

                {(!parsedData.skills || parsedData.skills.length === 0) ? (
                  <p className="text-xs text-slate-500 italic">
                    No skills matched from standard taxonomy.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {parsedData.skills.map((skill, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 text-xs space-y-1.5"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-bold text-white text-sm capitalize">
                            {skill.name}
                          </span>
                          <div className="flex items-center gap-2">
                            {skill.category && (
                              <span className="px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 text-[10px]">
                                {skill.category}
                              </span>
                            )}
                            <span
                              className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold ${
                                skill.supported_by_context
                                  ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                  : "bg-amber-500/10 text-amber-300 border border-amber-500/20"
                              }`}
                            >
                              {skill.supported_by_context
                                ? "Contextually Supported"
                                : "Skills List Mention"}
                            </span>
                          </div>
                        </div>

                        {skill.evidence_text ? (
                          <div className="text-slate-300 bg-slate-900/60 p-2 rounded-lg border border-slate-800/80 italic text-[11px]">
                            &ldquo;{skill.evidence_text}&rdquo;
                          </div>
                        ) : (
                          <p className="text-[11px] text-slate-500 italic">
                            No direct evidence excerpt recorded.
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Education */}
              {parsedData.parsed_json?.education?.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-3">
                    Education
                  </h3>
                  <div className="space-y-2">
                    {parsedData.parsed_json.education.map((edu, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-xs"
                      >
                        <p className="font-semibold text-white">
                          {edu.degree || "Degree"}
                          {edu.field_of_study ? ` in ${edu.field_of_study}` : ""}
                        </p>
                        {edu.institution && (
                          <p className="text-slate-400 mt-0.5">
                            {edu.institution}
                          </p>
                        )}
                        <div className="flex items-center gap-3 text-slate-500 text-[11px] mt-1">
                          {(edu.start_year || edu.end_year) && (
                            <span>
                              {edu.start_year ? `${edu.start_year} - ` : ""}
                              {edu.end_year || ""}
                            </span>
                          )}
                          {edu.grade && <span>Grade / CGPA: {edu.grade}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience */}
              {parsedData.parsed_json?.experience?.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-3">
                    Experience
                  </h3>
                  <div className="space-y-2">
                    {parsedData.parsed_json.experience.map((exp, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-xs"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-semibold text-white">
                            {exp.title || "Position"}
                          </p>
                          {(exp.start_date || exp.end_date) && (
                            <span className="text-[11px] text-slate-500">
                              {exp.start_date ? `${exp.start_date} - ` : ""}
                              {exp.end_date || ""}
                            </span>
                          )}
                        </div>
                        {exp.organization && (
                          <p className="text-slate-400 mt-0.5">
                            {exp.organization}
                          </p>
                        )}
                        {exp.description && (
                          <p className="text-slate-300 mt-1 whitespace-pre-line text-[11px]">
                            {exp.description}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Projects */}
              {parsedData.parsed_json?.projects?.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-3">
                    Projects
                  </h3>
                  <div className="space-y-2">
                    {parsedData.parsed_json.projects.map((proj, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/40 border border-slate-800 text-xs"
                      >
                        <p className="font-semibold text-white">
                          {proj.title || "Project"}
                        </p>
                        {proj.description && (
                          <p className="text-slate-300 mt-1 whitespace-pre-line text-[11px]">
                            {proj.description}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Certifications & Languages */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {parsedData.parsed_json?.certifications?.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-2">
                      Certifications
                    </h3>
                    <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                      {parsedData.parsed_json.certifications.map((c, i) => (
                        <li key={i}>
                          {c.name} {c.issuer ? `(${c.issuer})` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {parsedData.parsed_json?.languages?.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-2">
                      Languages
                    </h3>
                    <div className="flex flex-wrap gap-1.5">
                      {parsedData.parsed_json.languages.map((lang, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded-lg bg-slate-800 text-slate-300 text-xs"
                        >
                          {lang}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors cursor-pointer"
          >
            Close Dossier
          </button>
        </div>
      </div>
    </div>
  );
}

