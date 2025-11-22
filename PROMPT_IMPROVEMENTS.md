# Standards Enforcement Agent Prompt Improvements

## Summary
Refactored the standards enforcement agent prompt from 549 lines to 371 lines (32% reduction) while improving clarity and fixing critical issues.

## Key Improvements

### 1. Fixed Filename Length Target ✅
**Problem:** Prompt said "target ~25 character filename" but actual format produces 30-50 char filenames
- `doctype-vendor-subject-YYYYMMDD.ext` inherently requires 30-50 chars
- This caused the agent to over-abbreviate subjects

**Solution:** Changed guideline to "subject should be 1-3 words, typically 5-20 characters"
- Added rationale explaining that doctype, vendor, and date provide primary identification
- Subject adds final differentiation only

### 2. Clarified Vendor Determination Priority ✅
**Problem:** Ambiguous when to use specific vendors vs. generic descriptors

**Solution:** Added explicit 4-tier priority system:
1. Specific named vendor (chase, walmart, smith_john_md)
2. Generic with identifying details (store_1234, downtown_clinic)
3. Generic category (gas_station, medical_clinic, grocery_store)
4. Contextual fallback (personal, government_form)

### 3. Simplified Date Selection Logic ✅
**Problem:** 15+ lines of complex date selection rules caused decision paralysis

**Solution:** Reduced to simple lookup table:
- Receipt/invoice/bill → Transaction date
- Statement/report → Period end date
- Contract/policy/agreement → Effective/creation date
- Form → Filing/submission date
- Fallback: prefer explicitly labeled dates, then most recent

### 4. Specified When to Abbreviate ✅
**Problem:** No clear guidance on when to apply abbreviations

**Solution:** Added explicit threshold:
- "Apply abbreviations ONLY when subject alone exceeds 20 characters"
- Abbreviate longest words first
- Use standard abbreviations that other personnel will understand

### 5. Added Input Validation Rules ✅
**Problem:** No guidance on handling invalid input from Classification Agent

**Solution:** Added validation section:
- If vendor_raw is empty/null → infer from context or use generic descriptor
- If date_raw is empty → output empty string (dateless document allowed)
- If subject_raw is empty → derive from doctype or use generic term

### 6. Reduced Redundancy ✅
**Problem:** Multiple sections repeated the same concepts

**Solution:**
- Consolidated vendor examples from 20+ to 10 key edge cases
- Removed hyphenation guidance (trivial, adds noise)
- Reduced full examples from 11 to 6 (kept edge cases only)
- Consolidated formatting notes to single locations

### 7. Standardized XML Format ✅
**Problem:** Mixed use of attributes vs. nested elements

**Solution:** Consistently use nested `<input>` / `<output>` elements for better readability

## Metrics
- **Line count:** 549 → 371 (32% reduction)
- **Vendor examples:** 27 → 10 (kept edge cases)
- **Full examples:** 11 → 6 (kept edge cases)
- **Date rules:** 15 lines → 10 lines
- **Tests:** All 5 tests pass ✅

## Benefits
1. **Faster inference** - Shorter prompt = less tokens to process
2. **More consistent** - Clear priority rules reduce ambiguity
3. **Better filenames** - Corrected length target prevents over-abbreviation
4. **More maintainable** - Less redundancy = easier to update
5. **More robust** - Input validation handles edge cases

## Files Changed
- `prompts/standards-enforcement-agent-system.xml` - Main prompt file
- No code changes required
- All existing tests pass
