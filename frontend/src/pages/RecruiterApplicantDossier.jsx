import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { recruiterApi } from '../api/recruiter.js';
import { jobsApi } from '../api/jobs.js';
import { extractErrorMessage } from '../api/client.js';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { ConfirmModal } from '../components/ConfirmModal.jsx';
import { LoadingSpinner } from '../components/LoadingSpinner.jsx';

export function RecruiterApplicantDossier() {
  const { applicationId } = useParams();

  const [dossier, setDossier] = useState(null);
  const [job, setJob] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [applicationStatus, setApplicationStatus] = useState('applied');

  // Contact reveal state (in-memory only, never persisted to localStorage or URL)
  const [revealedContact, setRevealedContact] = useState(null);
  const [revealModalOpen, setRevealModalOpen] = useState(false);
  const [revealingContact, setRevealingContact] = useState(false);

  // Resume download state
  const [downloadingResume, setDownloadingResume] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  // Review submission form state
  const [reviewDecision, setReviewDecision] = useState('shortlist'); // 'shortlist' | 'hold' | 'reject'
  const [reviewNotes, setReviewNotes] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState(null);
  const [reviewSuccessBanner, setReviewSuccessBanner] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notFound, setNotFound] = useState(false);

  const loadDossier = useCallback(async (appId) => {
    try {
      const appData = await recruiterApi.getApplicationDetail(Number(appId), false);
      setDossier(appData);
      setReviews(appData.reviews || []);
      setApplicationStatus(appData.status);
      setError(null);
      setNotFound(false);

      if (appData.job_id) {
        try {
          const jobData = await jobsApi.getJobById(appData.job_id);
          setJob(jobData);
        } catch {
          setJob({ title: `Job #${appData.job_id}` });
        }
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setNotFound(true);
      } else {
        setError(extractErrorMessage(err, 'Failed to load applicant dossier.'));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    async function init() {
      try {
        const appData = await recruiterApi.getApplicationDetail(Number(applicationId), false);
        if (!isMounted) return;

        setDossier(appData);
        setReviews(appData.reviews || []);
        setApplicationStatus(appData.status);
        setError(null);
        setNotFound(false);

        if (appData.job_id) {
          try {
            const jobData = await jobsApi.getJobById(appData.job_id);
            if (isMounted) setJob(jobData);
          } catch {
            if (isMounted) setJob({ title: `Job #${appData.job_id}` });
          }
        }
      } catch (err) {
        if (!isMounted) return;
        if (err.response?.status === 404) {
          setNotFound(true);
        } else {
          setError(extractErrorMessage(err, 'Failed to load applicant dossier.'));
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
  }, [applicationId]);

  const handleRetry = () => {
    setLoading(true);
    setNotFound(false);
    setError(null);
    loadDossier(applicationId);
  };

  // Contact reveal action
  const handleConfirmRevealContact = async () => {
    setRevealingContact(true);
    try {
      const updatedData = await recruiterApi.getApplicationDetail(Number(applicationId), true);
      setRevealedContact({
        email: updatedData.email || 'No email on record',
        phone: updatedData.phone || 'No phone on record',
      });
      setRevealModalOpen(false);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to reveal candidate contact details.'));
      setRevealModalOpen(false);
    } finally {
      setRevealingContact(false);
    }
  };

  // Resume download action
  const handleDownloadResume = async () => {
    if (!dossier?.id) return;

    setDownloadingResume(true);
    setDownloadError(null);

    try {
      const response = await recruiterApi.downloadApplicationResume(dossier.id);
      const blob = new Blob([response.data], {
        type: response.headers['content-type'] || 'application/octet-stream',
      });

      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download =
        dossier.resume?.original_filename || `resume_application_${dossier.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      if (err.response?.status === 404) {
        setDownloadError('Resume file missing: The document could not be found on storage.');
      } else {
        setDownloadError(extractErrorMessage(err, 'Failed to download applicant resume.'));
      }
    } finally {
      setDownloadingResume(false);
    }
  };

  // Review submission
  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!reviewDecision || submittingReview) return;

    setSubmittingReview(true);
    setReviewError(null);
    setReviewSuccessBanner(null);

    try {
      const newReview = await recruiterApi.submitReview(Number(applicationId), {
        decision: reviewDecision,
        notes: reviewNotes.trim() || undefined,
      });

      // Update state without refetching entire dossier (avoids audit log duplicate and preserves revealed contact)
      setReviews((prev) => [...prev, newReview]);
      setApplicationStatus('reviewed');
      setReviewNotes('');
      setReviewSuccessBanner(
        `Evaluation recorded: Application marked as reviewed (${newReview.decision.toUpperCase()}).`
      );
    } catch (err) {
      setReviewError(extractErrorMessage(err, 'Failed to submit review decision.'));
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading applicant dossier and evaluation history..." />;
  }

  // 404 Not Found state
  if (notFound) {
    return (
      <div className="max-w-xl mx-auto py-16 px-4 text-center">
        <div className="h-16 w-16 rounded-2xl bg-slate-800 text-slate-400 mx-auto flex items-center justify-center mb-4 border border-slate-700">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Application Not Found</h2>
        <p className="text-sm text-slate-400 mb-6 max-w-md mx-auto">
          The requested application dossier does not exist or belongs to a job posting you do not own.
        </p>
        <Link
          to="/recruiter/jobs"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-md shadow-indigo-600/20 transition-all"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Job Postings
        </Link>
      </div>
    );
  }

  // General error banner
  if (error && !dossier) {
    return (
      <div className="max-w-3xl mx-auto p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4 text-center">
        <div className="text-rose-400 text-sm font-medium">{error}</div>
        <div className="flex items-center justify-center gap-3">
          <Link
            to="/recruiter/jobs"
            className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white text-xs font-semibold"
          >
            &larr; Back to Job Postings
          </Link>
          <button
            type="button"
            onClick={handleRetry}
            className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500 cursor-pointer"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const isContactRevealed = Boolean(revealedContact);
  const contactEmail = revealedContact ? revealedContact.email : null;
  const contactPhone = revealedContact ? revealedContact.phone : null;

  // Process parsed skills with sections
  const resumeSkills = dossier?.resume?.skills || [];
  const parsedJsonSkills = dossier?.resume?.parsed_json?.skills || [];
  const sectionMap = {};
  if (Array.isArray(parsedJsonSkills)) {
    parsedJsonSkills.forEach((ps) => {
      if (ps && ps.name) {
        sectionMap[ps.name.toLowerCase()] = ps.section || 'resume';
      }
    });
  }

  const isResumeParsed = dossier?.resume?.parse_status === 'parsed';

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-200">
      {/* Top back navigation */}
      <div>
        <Link
          to={dossier?.job_id ? `/recruiter/jobs/${dossier.job_id}/applications` : '/recruiter/jobs'}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-indigo-400 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Applicants
        </Link>
      </div>

      {/* Header Banner: Candidate Profile Summary */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-slate-800">
          <div className="flex items-start gap-4">
            <div className="h-14 w-14 rounded-2xl bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white text-xl shadow-lg shadow-indigo-500/20 shrink-0">
              {dossier.candidate_name?.charAt(0)?.toUpperCase() || 'C'}
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                  {dossier.candidate_name}
                </h1>
                <StatusBadge status={applicationStatus} audience="recruiter" />
              </div>
              <p className="text-sm text-slate-300 font-medium">
                {dossier.headline || 'Candidate'}
              </p>
              <div className="flex items-center gap-2 text-xs text-slate-400 flex-wrap">
                <span>Location: {dossier.location || 'Not specified'}</span>
                <span>&bull;</span>
                <span>Applied {new Date(dossier.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          <div className="text-right self-start md:self-center bg-slate-950/40 p-3 rounded-xl border border-slate-800/80">
            <p className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Applying For</p>
            <p className="text-sm font-bold text-white mt-0.5">
              {job?.title || `Job #${dossier.job_id}`}
            </p>
            {job?.status && (
              <span className="text-[11px] text-slate-400 capitalize">
                Role Status: {job.status}
              </span>
            )}
          </div>
        </div>

        {/* Contact Details Card with Privacy Protection */}
        <div className="mt-6 p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Candidate Contact Details
              </h3>
            </div>
            {isContactRevealed ? (
              <div className="flex flex-wrap items-center gap-6 pt-1 text-xs text-slate-300">
                <div>
                  <span className="text-slate-400 font-medium">Email: </span>
                  <a href={`mailto:${contactEmail}`} className="text-indigo-400 hover:underline font-semibold">
                    {contactEmail}
                  </a>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Phone: </span>
                  <span className="text-white font-semibold">{contactPhone}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                Protected under anti-bias privacy protocols to support fair candidate evaluation.
              </p>
            )}
          </div>

          {!isContactRevealed && (
            <button
              type="button"
              onClick={() => setRevealModalOpen(true)}
              disabled={revealingContact}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-300 hover:text-white border border-slate-700 text-xs font-semibold shadow-sm transition-all flex items-center gap-2 shrink-0 cursor-pointer disabled:opacity-50"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <span>{revealingContact ? 'Revealing...' : 'Reveal Contact Details'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Two Columns Grid: Left (Resume & Skills), Right (Review Timeline & Form) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 spans): Resume & Skills Dossier */}
        <div className="lg:col-span-2 space-y-6">
          {/* Resume File Section */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h2 className="text-base font-bold text-white">Attached Resume Document</h2>
              {dossier.resume && <StatusBadge status={dossier.resume.parse_status} />}
            </div>

            {dossier.resume ? (
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/40 border border-slate-800/80">
                <div className="flex items-center gap-3.5 min-w-0">
                  <div className="h-10 w-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400 shrink-0">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate">
                      {dossier.resume.original_filename}
                    </p>
                    <p className="text-[11px] text-slate-400">
                      Uploaded {new Date(dossier.resume.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleDownloadResume}
                  disabled={downloadingResume}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all flex items-center gap-2 shrink-0 cursor-pointer disabled:opacity-50"
                >
                  {downloadingResume ? (
                    <>
                      <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent inline-block" />
                      <span>Downloading...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      <span>Download Resume</span>
                    </>
                  )}
                </button>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No resume attached to this application.</p>
            )}

            {downloadError && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                <svg className="w-4 h-4 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{downloadError}</span>
              </div>
            )}
          </div>

          {/* Parsed Skills Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h2 className="text-base font-bold text-white">Extracted Skill Evidence</h2>
                <p className="text-xs text-slate-400">
                  Deterministic NLP extraction with verbatim evidence sentences
                </p>
              </div>
              <span className="text-xs text-slate-400">
                {resumeSkills.length} skill{resumeSkills.length !== 1 ? 's' : ''} found
              </span>
            </div>

            {/* Match score neutral note */}
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
              <svg className="w-4 h-4 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Match score: not computed yet</span>
            </div>

            {!isResumeParsed ? (
              <div className="text-center py-10 px-4 bg-slate-950/20 rounded-xl border border-slate-800/80">
                <p className="text-sm font-semibold text-slate-300">Resume not parsed yet</p>
                <p className="text-xs text-slate-400 mt-1">
                  The candidate's resume has not yet been processed by the parsing pipeline.
                </p>
              </div>
            ) : resumeSkills.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-400">
                No taxonomy skills were identified in this document.
              </div>
            ) : (
              <div className="space-y-3">
                {resumeSkills.map((sk, idx) => {
                  const section = sectionMap[sk.name.toLowerCase()] || 'skills';
                  return (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 hover:border-slate-700 transition-colors space-y-2"
                    >
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-sm">{sk.name}</span>
                          {sk.category && (
                            <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[11px] font-medium">
                              {sk.category}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 text-xs">
                          <span className="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-[11px] font-medium capitalize">
                            Section: {section}
                          </span>
                          {sk.supported_by_context && (
                            <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[11px] font-medium">
                              Context Verified
                            </span>
                          )}
                        </div>
                      </div>

                      {sk.evidence_text ? (
                        <p className="text-xs text-slate-300 italic bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 leading-relaxed">
                          "{sk.evidence_text}"
                        </p>
                      ) : (
                        <p className="text-[11px] text-slate-400 italic">
                          Found in resume (no contextual sentence).
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column (1 span): Review Form & Timeline */}
        <div className="space-y-6">
          {/* Review Submission Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div className="pb-3 border-b border-slate-800">
              <h2 className="text-base font-bold text-white">Record Human Review</h2>
              <p className="text-xs text-slate-400">
                Record your hiring evaluation decision on this applicant
              </p>
            </div>

            {reviewSuccessBanner && (
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>{reviewSuccessBanner}</span>
              </div>
            )}

            {reviewError && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300 flex items-center gap-2">
                <svg className="w-4 h-4 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{reviewError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitReview} className="space-y-4">
              {/* Decision Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Review Decision
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'shortlist', label: 'Shortlist', color: 'hover:border-emerald-500 focus:ring-emerald-500' },
                    { value: 'hold', label: 'Hold', color: 'hover:border-amber-500 focus:ring-amber-500' },
                    { value: 'reject', label: 'Reject', color: 'hover:border-rose-500 focus:ring-rose-500' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setReviewDecision(opt.value)}
                      disabled={submittingReview}
                      className={`py-2 px-3 rounded-xl text-xs font-bold transition-all border cursor-pointer ${
                        reviewDecision === opt.value
                          ? opt.value === 'shortlist'
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500 shadow-sm shadow-emerald-500/20'
                            : opt.value === 'hold'
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500 shadow-sm shadow-amber-500/20'
                            : 'bg-rose-500/20 text-rose-300 border-rose-500 shadow-sm shadow-rose-500/20'
                          : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Review Notes */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="review-notes" className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                    Evaluation Notes
                  </label>
                  <span className={`text-[11px] font-mono ${reviewNotes.length > 900 ? 'text-amber-400' : 'text-slate-400'}`}>
                    {reviewNotes.length} / 1000
                  </span>
                </div>
                <textarea
                  id="review-notes"
                  rows={4}
                  maxLength={1000}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  disabled={submittingReview}
                  placeholder="Record your feedback and assessment reasoning..."
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={submittingReview || !reviewDecision}
                className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-600/25 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submittingReview ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent inline-block" />
                    <span>Submitting Review...</span>
                  </>
                ) : (
                  <span>Submit Evaluation</span>
                )}
              </button>
            </form>

            {/* Persistent AI Decision Disclaimer */}
            <div className="pt-3 border-t border-slate-800/80">
              <p className="text-[11px] text-slate-400 leading-relaxed italic text-center">
                AI-assisted insights support, but do not replace, recruiter judgement.
              </p>
            </div>
          </div>

          {/* Review History Timeline */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="pb-3 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-base font-bold text-white">Review History</h2>
              <span className="text-xs text-slate-400">{reviews.length} entries</span>
            </div>

            {reviews.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-4 text-center">
                No reviews recorded yet. Submit your evaluation above.
              </p>
            ) : (
              <div className="space-y-4">
                {reviews.map((r) => (
                  <div
                    key={r.id}
                    className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <StatusBadge status={r.decision} />
                      <span className="text-[11px] text-slate-400">
                        {new Date(r.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {r.notes ? (
                      <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                        {r.notes}
                      </p>
                    ) : (
                      <p className="text-[11px] text-slate-400 italic">
                        No additional notes provided.
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Confirm Modal for Contact Reveal */}
      <ConfirmModal
        isOpen={revealModalOpen}
        title="Reveal Candidate Contact Details?"
        message="Revealing the candidate's email address and phone number will be recorded permanently in the security audit log to maintain hiring transparency and privacy compliance. Do you wish to proceed?"
        confirmText="Reveal Contact Info"
        confirmVariant="primary"
        isLoading={revealingContact}
        onConfirm={handleConfirmRevealContact}
        onCancel={() => setRevealModalOpen(false)}
      />
    </div>
  );
}
