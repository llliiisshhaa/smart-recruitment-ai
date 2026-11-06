import { useState, useEffect } from "react";
import { useAuth } from "../context/useAuth.js";
import { candidateApi } from "../api/candidate.js";
import StatusBadge from "../components/StatusBadge";
import { LoadingSpinner } from "../components/LoadingSpinner.jsx";
import { extractErrorMessage } from "../api/client.js";

export function CandidateProfile() {
  const { user } = useAuth();

  const [profile, setProfile] = useState(null);
  const [phone, setPhone] = useState("");
  const [headline, setHeadline] = useState("");
  const [location, setLocation] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [consenting, setConsenting] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [consentSuccess, setConsentSuccess] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchProfile() {
      setLoading(true);
      setError(null);
      try {
        const data = await candidateApi.getProfile();
        if (isMounted) {
          setProfile(data);
          setPhone(data.phone || "");
          setHeadline(data.headline || "");
          setLocation(data.location || "");
        }
      } catch (err) {
        if (isMounted) {
          setError(extractErrorMessage(err, "Failed to load profile."));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    fetchProfile();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSaveSuccess(false);

    try {
      const updated = await candidateApi.updateProfile({
        phone: phone.trim() || null,
        headline: headline.trim() || null,
        location: location.trim() || null,
      });
      setProfile(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to update profile."));
    } finally {
      setSaving(false);
    }
  };

  const handleGrantConsent = async () => {
    setConsenting(true);
    setError(null);
    setConsentSuccess(false);

    try {
      const updated = await candidateApi.giveConsent();
      setProfile(updated);
      setConsentSuccess(true);
      setTimeout(() => setConsentSuccess(false), 4000);
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to record consent."));
    } finally {
      setConsenting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading candidate profile..." />;
  }

  const hasConsent = Boolean(profile?.consent_given_at);

  return (
    <div className="max-w-4xl space-y-8 animate-in fade-in duration-200">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          Candidate Profile & Consent
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your personal details and privacy preferences.
        </p>
      </div>

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

      {saveSuccess && (
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
          <span>Profile changes saved successfully!</span>
        </div>
      )}

      {/* Profile Form Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl">
        <h2 className="text-lg font-bold text-white mb-1">
          Personal Information
        </h2>
        <p className="text-xs text-slate-400 mb-6">
          Information used by hiring recruiters when reviewing your job
          applications.
        </p>

        <form onSubmit={handleProfileSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Read-only Name */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Full Name
              </label>
              <input
                type="text"
                disabled
                value={user?.full_name || ""}
                className="w-full px-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-400 text-sm cursor-not-allowed"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Account full name
              </span>
            </div>

            {/* Read-only Email */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <input
                type="email"
                disabled
                value={user?.email || ""}
                className="w-full px-4 py-2.5 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-400 text-sm cursor-not-allowed"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Authentication email address
              </span>
            </div>
          </div>

          {/* Headline */}
          <div>
            <label
              htmlFor="headline"
              className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2"
            >
              Professional Headline
            </label>
            <input
              id="headline"
              type="text"
              maxLength={255}
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="e.g. Senior Python Developer | Distributed Systems"
              className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            />
            <span className="text-[11px] text-slate-400 mt-1 block">
              A brief summary of your role or specialization ({headline.length}
              /255).
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Phone */}
            <div>
              <label
                htmlFor="phone"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2"
              >
                Contact Phone
              </label>
              <input
                id="phone"
                type="tel"
                maxLength={30}
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+1 (555) 000-0000"
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Hidden from recruiters by default until explicit reveal.
              </span>
            </div>

            {/* Location */}
            <div>
              <label
                htmlFor="location"
                className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2"
              >
                Location
              </label>
              <input
                id="location"
                type="text"
                maxLength={255}
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. San Francisco, CA / Remote"
                className="w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Current city or preferred work location.
              </span>
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50 flex items-center gap-2 cursor-pointer"
            >
              {saving ? (
                <>
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Saving Changes...</span>
                </>
              ) : (
                <span>Save Profile Changes</span>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Consent Management Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 md:p-8 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Data Privacy & AI Evaluation Consent</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Required for resume uploading and automated job evaluation.
            </p>
          </div>

          <div>
            <StatusBadge status={hasConsent} type="consent" />
          </div>
        </div>

        {consentSuccess && (
          <div className="mt-4 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center gap-2">
            <svg
              className="w-4 h-4 shrink-0 text-emerald-400"
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
            <span>
              Your consent has been successfully recorded in the audit trail.
            </span>
          </div>
        )}

        <div className="mt-6 space-y-4 text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-5 rounded-xl border border-slate-800/80">
          <h3 className="text-sm font-semibold text-white">
            How We Handle Your Candidate Data
          </h3>
          <ul className="list-disc list-inside space-y-2 text-slate-300">
            <li>
              <strong>AI-Assisted Evaluation:</strong> Your uploaded resume and
              application data are parsed by our AI system strictly for
              extracting relevant skills and evaluating alignment with job
              requirements.
            </li>
            <li>
              <strong>Human-In-The-Loop Governance:</strong> AI matching assists
              screening but <em>never</em> automatically rejects applicants or
              makes final hiring decisions. All decisions (shortlist, hold,
              reject) are made by human recruiters.
            </li>
            <li>
              <strong>Contact Information Privacy:</strong> Your email and phone
              number are hidden by default from recruiter applicant lists and
              are only disclosed when authorized recruiters explicitly inspect
              your dossier.
            </li>
            <li>
              <strong>Candidate Control & Right to Deletion:</strong> You retain
              complete ownership over your uploaded documents and can
              permanently delete any of your resumes at any time through this
              portal.
            </li>
          </ul>
        </div>

        <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            {hasConsent ? (
              <p className="text-xs text-emerald-400 flex items-center gap-1.5">
                <span>✓</span>
                <span>
                  Consent active since{" "}
                  <strong>
                    {new Date(profile.consent_given_at).toLocaleString()}
                  </strong>
                </span>
              </p>
            ) : (
              <p className="text-xs text-amber-400 flex items-center gap-1.5">
                <span>!</span>
                <span>
                  Consent has not yet been recorded. Resume uploads remain
                  disabled.
                </span>
              </p>
            )}
          </div>

          <div>
            {!hasConsent && (
              <button
                type="button"
                onClick={handleGrantConsent}
                disabled={consenting}
                className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50 flex items-center gap-2 cursor-pointer"
              >
                {consenting ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Recording Consent...</span>
                  </>
                ) : (
                  <span>I Acknowledge & Grant Consent</span>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
