import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { candidateApi } from "../api/candidate.js";
import { resumesApi } from "../api/resumes.js";
import StatusBadge from "../components/StatusBadge";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import { LoadingSpinner } from "../components/LoadingSpinner.jsx";
import { extractErrorMessage } from "../api/client.js";

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const MAX_RESUMES = 5;

export function CandidateResumes() {
  const fileInputRef = useRef(null);

  const [resumes, setResumes] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Selected file state for upload preview
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // Feedback notifications
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Deletion modal state
  const [resumeToDelete, setResumeToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Download state tracker
  const [downloadingId, setDownloadingId] = useState(null);

  // Refresh helper for after upload or delete operations
  const refreshData = async () => {
    try {
      const [resumesData, profileData] = await Promise.all([
        resumesApi.listResumes(),
        candidateApi.getProfile(),
      ]);
      setResumes(resumesData);
      setProfile(profileData);
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to refresh resume documents."));
    }
  };

  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const [resumesData, profileData] = await Promise.all([
          resumesApi.listResumes(),
          candidateApi.getProfile(),
        ]);
        if (isMounted) {
          setResumes(resumesData);
          setProfile(profileData);
        }
      } catch (err) {
        if (isMounted) {
          setError(
            extractErrorMessage(err, "Failed to load resume documents."),
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    init();

    return () => {
      isMounted = false;
    };
  }, []);

  const hasConsent = Boolean(profile?.consent_given_at);

  // File validation helper
  const validateFile = (file) => {
    if (!file) return "No file chosen.";

    const validExtensions = [".pdf", ".docx"];
    const fileName = file.name.toLowerCase();
    const isValidExtension = validExtensions.some((ext) =>
      fileName.endsWith(ext),
    );

    if (!isValidExtension) {
      return "Only PDF (.pdf) and Microsoft Word (.docx) documents are allowed.";
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File exceeds the 5 MB limit (size: ${(file.size / (1024 * 1024)).toFixed(2)} MB).`;
    }

    if (file.size === 0) {
      return "The chosen file is empty.";
    }

    return null;
  };

  const handleFileSelection = (file) => {
    setError(null);
    setSuccessMessage(null);

    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setSelectedFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  // Upload handler
  const handleUpload = async () => {
    if (!selectedFile) return;

    if (!hasConsent) {
      setError(
        "You must provide data processing consent before uploading resumes.",
      );
      return;
    }

    if (resumes.length >= MAX_RESUMES) {
      setError(`You have reached the maximum limit of ${MAX_RESUMES} resumes.`);
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccessMessage(null);

    try {
      await resumesApi.uploadResume(selectedFile, (progressEvent) => {
        if (progressEvent.total) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          setUploadProgress(percent);
        }
      });

      setSuccessMessage(`"${selectedFile.name}" was uploaded successfully.`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await refreshData();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not upload resume document."));
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  // Authenticated file download
  const handleDownload = async (resume) => {
    setDownloadingId(resume.id);
    setError(null);

    try {
      const response = await resumesApi.downloadResume(resume.id);
      const blob = new Blob([response.data], {
        type: response.headers["content-type"] || "application/octet-stream",
      });

      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = resume.original_filename || `resume_${resume.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to download resume file."));
    } finally {
      setDownloadingId(null);
    }
  };

  // Delete resume confirmation
  const handleDeleteConfirm = async () => {
    if (!resumeToDelete) return;

    setDeleting(true);
    setError(null);

    try {
      await resumesApi.deleteResume(resumeToDelete.id);
      setSuccessMessage(
        `"${resumeToDelete.original_filename}" has been deleted.`,
      );
      setResumeToDelete(null);
      await refreshData();
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to delete resume."));
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading resume documents..." />;
  }

  return (
    <div className="max-w-4xl space-y-8 animate-in fade-in duration-200">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Resume Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Upload, inspect, and manage your CV documents (up to {MAX_RESUMES}{" "}
            files).
          </p>
        </div>

        <div className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300">
          Capacity:{" "}
          <span className="text-white font-bold">{resumes.length}</span> /{" "}
          {MAX_RESUMES}
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-sm text-rose-300 flex items-center gap-2">
          <svg
            className="w-5 h-5 shrink-0 text-rose-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-300 flex items-center gap-2">
          <svg
            className="w-5 h-5 shrink-0 text-emerald-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          <span>{successMessage}</span>
        </div>
      )}

      {/* Consent Warning Banner */}
      {!hasConsent && (
        <div className="p-5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 shrink-0 text-amber-400 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div>
              <p className="font-semibold text-white">
                Data Processing Consent Required
              </p>
              <p className="text-amber-200/80 mt-0.5">
                Under system privacy requirements, you must record consent
                before uploading resumes.
              </p>
            </div>
          </div>
          <Link
            to="/candidate/profile"
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shrink-0 transition-colors"
          >
            Review & Grant Consent &rarr;
          </Link>
        </div>
      )}

      {/* Upload Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl">
        <h2 className="text-lg font-bold text-white mb-1">Upload New Resume</h2>
        <p className="text-xs text-slate-400 mb-5">
          Supported formats: PDF or DOCX (maximum 5 MB per document).
        </p>

        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
            dragActive
              ? "border-indigo-500 bg-indigo-500/5"
              : "border-slate-800 hover:border-slate-700 bg-slate-950/40"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileSelection(e.target.files[0]);
              }
            }}
          />

          <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 text-indigo-400 mx-auto flex items-center justify-center mb-3">
            <svg
              className="w-6 h-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.75}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
              />
            </svg>
          </div>

          <p className="text-sm font-semibold text-white mb-1">
            {selectedFile ? (
              <span className="text-indigo-400">{selectedFile.name}</span>
            ) : (
              "Drag and drop your resume file here, or browse"
            )}
          </p>

          <p className="text-xs text-slate-400 mb-4">
            {selectedFile
              ? `Selected file size: ${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB`
              : "PDF or DOCX documents up to 5 MB"}
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={
                uploading || !hasConsent || resumes.length >= MAX_RESUMES
              }
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors disabled:opacity-50 cursor-pointer"
            >
              Choose File
            </button>

            {selectedFile && (
              <button
                type="button"
                onClick={handleUpload}
                disabled={
                  uploading || !hasConsent || resumes.length >= MAX_RESUMES
                }
                className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50 flex items-center gap-2 cursor-pointer"
              >
                {uploading ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Uploading ({uploadProgress}%)...</span>
                  </>
                ) : (
                  <span>Upload Document</span>
                )}
              </button>
            )}
          </div>

          {uploading && uploadProgress > 0 && (
            <div className="w-full max-w-xs mx-auto mt-4">
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-indigo-500 h-1.5 rounded-full transition-all duration-200"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Resume Document Table / List */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl">
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white">Stored Resumes</h2>
            <p className="text-xs text-slate-400">
              Active CV versions available for attaching to job applications
            </p>
          </div>
          <span className="text-xs text-slate-400">
            {resumes.length} document{resumes.length !== 1 ? "s" : ""}
          </span>
        </div>

        {resumes.length === 0 ? (
          <div className="text-center py-12 px-4">
            <div className="h-12 w-12 rounded-2xl bg-slate-800 text-slate-400 mx-auto flex items-center justify-center mb-3">
              <svg
                className="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-white">
              No resumes stored yet
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
              Select or drop a PDF/DOCX resume file above to store it in your
              candidate profile.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {resumes.map((resume) => (
              <div
                key={resume.id}
                className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3.5 min-w-0">
                  <div className="h-10 w-10 rounded-xl bg-slate-800 border border-slate-700/80 flex items-center justify-center text-indigo-400 shrink-0">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.75}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate">
                      {resume.original_filename}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
                      <span>
                        Uploaded{" "}
                        {new Date(resume.created_at).toLocaleDateString()}
                      </span>
                      <span>&bull;</span>
                      <StatusBadge
                        status={resume.parse_status}
                        type="parse_status"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                  {/* Download Button */}
                  <button
                    type="button"
                    onClick={() => handleDownload(resume)}
                    disabled={downloadingId === resume.id}
                    className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 transition-colors disabled:opacity-50 cursor-pointer"
                    title="Download Resume"
                    aria-label={`Download ${resume.original_filename}`}
                  >
                    {downloadingId === resume.id ? (
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent inline-block" />
                    ) : (
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                    )}
                  </button>

                  {/* Delete Button */}
                  <button
                    type="button"
                    onClick={() => setResumeToDelete(resume)}
                    className="p-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 border border-rose-500/20 transition-colors cursor-pointer"
                    title="Delete Resume"
                    aria-label={`Delete ${resume.original_filename}`}
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirmation Modal for Resume Deletion */}
      <ConfirmModal
        isOpen={Boolean(resumeToDelete)}
        title="Delete Resume Document?"
        message={`Are you sure you want to permanently delete "${resumeToDelete?.original_filename}"? This action removes the document from disk and candidate records immediately.`}
        confirmText="Delete Resume"
        confirmVariant="danger"
        isLoading={deleting}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setResumeToDelete(null)}
      />
    </div>
  );
}
