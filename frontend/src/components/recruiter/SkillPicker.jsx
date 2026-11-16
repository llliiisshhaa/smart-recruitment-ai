import { useState, useEffect, useRef } from 'react';
import { skillsApi } from '../../api/skills.js';
import { extractErrorMessage } from '../../api/client.js';

/**
 * Reusable SkillPicker component.
 * Allows recruiters to search, select, toggle importance (required vs. preferred),
 * and remove taxonomy skills for job postings.
 *
 * @param {{
 *   selectedSkills: Array<{
 *     skill_id: number,
 *     name: string,
 *     category?: string,
 *     importance: 'required' | 'preferred'
 *   }>,
 *   onChange: (skills: Array<{ skill_id: number, name: string, category?: string, importance: 'required' | 'preferred' }>) => void,
 *   error?: string
 * }} props
 */
export function SkillPicker({ selectedSkills = [], onChange, error }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [availableSkills, setAvailableSkills] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const containerRef = useRef(null);

  // Debounced search to GET /skills
  useEffect(() => {
    let isMounted = true;
    const timer = setTimeout(async () => {
      setLoading(true);
      setFetchError(null);
      try {
        const data = await skillsApi.searchSkills(searchQuery);
        if (isMounted) {
          setAvailableSkills(data || []);
        }
      } catch (err) {
        if (isMounted) {
          setFetchError(extractErrorMessage(err, 'Could not load skills list.'));
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }, 250);

    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [searchQuery]);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter out already selected skills to prevent duplicates
  const selectedIds = new Set(selectedSkills.map((s) => s.skill_id));
  const filteredOptions = availableSkills.filter((s) => !selectedIds.has(s.id));

  // Add skill to selection
  const handleSelectSkill = (skill, defaultImportance = 'required') => {
    if (selectedIds.has(skill.id)) return;

    const newSkill = {
      skill_id: skill.id,
      name: skill.name,
      category: skill.category,
      importance: defaultImportance,
    };
    onChange([...selectedSkills, newSkill]);
    setSearchQuery('');
    setIsDropdownOpen(false);
  };

  // Toggle importance between 'required' and 'preferred'
  const handleToggleImportance = (skillId) => {
    const updated = selectedSkills.map((s) => {
      if (s.skill_id === skillId) {
        return {
          ...s,
          importance: s.importance === 'required' ? 'preferred' : 'required',
        };
      }
      return s;
    });
    onChange(updated);
  };

  // Remove skill
  const handleRemoveSkill = (skillId) => {
    const updated = selectedSkills.filter((s) => s.skill_id !== skillId);
    onChange(updated);
  };

  const requiredCount = selectedSkills.filter((s) => s.importance === 'required').length;
  const preferredCount = selectedSkills.filter((s) => s.importance === 'preferred').length;

  return (
    <div className="space-y-3" ref={containerRef}>
      <div className="flex items-center justify-between">
        <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Skills & Requirements <span className="text-rose-400">*</span>
        </label>
        <span className="text-[11px] text-slate-400">
          {requiredCount} Required &bull; {preferredCount} Preferred
        </span>
      </div>

      {/* Search Input & Dropdown */}
      <div className="relative">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setIsDropdownOpen(true);
            }}
            onFocus={() => setIsDropdownOpen(true)}
            placeholder="Type skill name to search (e.g. Python, Docker, React)..."
            className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
            {loading ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
          </div>
        </div>

        {/* Dropdown Results */}
        {isDropdownOpen && (
          <div className="absolute z-20 mt-1.5 w-full bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-h-60 overflow-y-auto divide-y divide-slate-800/60 animate-in fade-in">
            {fetchError ? (
              <div className="p-3 text-xs text-rose-400 text-center">
                {fetchError}
              </div>
            ) : filteredOptions.length === 0 ? (
              <div className="p-3.5 text-xs text-slate-400 text-center">
                {loading
                  ? 'Searching skills taxonomy...'
                  : searchQuery
                  ? `No matching skills found for "${searchQuery}".`
                  : 'All available matching skills already added.'}
              </div>
            ) : (
              filteredOptions.map((skill) => (
                <div
                  key={skill.id}
                  className="p-2.5 px-3 hover:bg-slate-800/80 cursor-pointer flex items-center justify-between transition-colors group"
                  onClick={() => handleSelectSkill(skill, 'required')}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white group-hover:text-indigo-300">
                      {skill.name}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {skill.category}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectSkill(skill, 'required');
                      }}
                      className="px-2 py-1 rounded bg-indigo-600/30 hover:bg-indigo-600 text-indigo-300 hover:text-white text-[11px] font-semibold transition-colors"
                      title="Add as Required"
                    >
                      + Required
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectSkill(skill, 'preferred');
                      }}
                      className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-semibold transition-colors"
                      title="Add as Preferred"
                    >
                      + Preferred
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Selected Skill Chips */}
      {selectedSkills.length === 0 ? (
        <div className="p-3 rounded-xl bg-slate-950/40 border border-dashed border-slate-800 text-center text-xs text-slate-500">
          No skills added yet. Search above to add required and preferred skills.
        </div>
      ) : (
        <div className="flex flex-wrap gap-2 pt-1">
          {selectedSkills.map((s) => {
            const isReq = s.importance === 'required';
            return (
              <div
                key={s.skill_id}
                className={`inline-flex items-center gap-2 pl-3 pr-2 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                  isReq
                    ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
                    : 'bg-slate-800/80 text-slate-300 border-slate-700'
                }`}
              >
                <span className="font-semibold text-white">{s.name}</span>

                {/* Importance Toggle Button */}
                <button
                  type="button"
                  onClick={() => handleToggleImportance(s.skill_id)}
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border transition-all ${
                    isReq
                      ? 'bg-indigo-600/40 text-indigo-200 border-indigo-400/40 hover:bg-indigo-600/60'
                      : 'bg-slate-700/60 text-slate-400 border-slate-600 hover:bg-slate-700'
                  }`}
                  title="Click to toggle between Required and Preferred"
                >
                  {isReq ? 'Required' : 'Preferred'}
                </button>

                {/* Remove Chip Button */}
                <button
                  type="button"
                  onClick={() => handleRemoveSkill(s.skill_id)}
                  className="text-slate-400 hover:text-rose-400 transition-colors p-0.5"
                  aria-label={`Remove ${s.name}`}
                >
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Validation Message */}
      {error ? (
        <p className="text-xs text-rose-400 mt-1">{error}</p>
      ) : selectedSkills.length > 0 && requiredCount === 0 ? (
        <p className="text-xs text-amber-400 mt-1">
          &bull; At least one skill must be marked as &quot;Required&quot;. Click a badge above to toggle.
        </p>
      ) : null}
    </div>
  );
}

