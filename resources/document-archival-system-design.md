# Document Archival System Design

This archival system synthesizes industry standards from ARMA International's recordkeeping principles, NARA file naming standards, and ISO 15489 records management specifications to create a broad-categorical structure for personal document management.

## Directory Taxonomy Structure

The four-level hierarchy follows the pattern: **Domain → Category → Vendor → Document**, using broad classifications that accommodate diverse document types without granular subdivisions.

### Level 1: Domain (6 primary domains)

**Financial**
Core financial instruments and accounts including banking, investments, credit, and retirement accounts. Encompasses all monetary transactions, statements, and account-related documentation.

**Property**
Real and personal property ownership documentation, including real estate, vehicles, and major assets. Contains purchase records, titles, deeds, and maintenance documentation.

**Insurance**
All insurance policies and related documentation across health, property, casualty, life, and disability coverage. Organized by insurance type rather than asset protected.

**Tax**
Federal and state tax returns with supporting documentation. Maintains chronological organization by tax year.

**Legal**
Identity documents, estate planning, and legal agreements. Contains permanent records including birth certificates, wills, trusts, and powers of attorney.

**Medical**
Healthcare records, medical expenses, and health insurance documentation.

### Level 2: Category (by domain)

**Financial categories:**
- Banking (checking, savings, money market accounts)
- Credit (credit cards, lines of credit)
- Investment (brokerage, mutual funds, stocks, bonds)
- Retirement (401k, IRA, pension, Social Security)
- Loans (mortgages, auto loans, student loans, personal loans)

**Property categories:**
- Real_Estate (primary residence, investment properties, land)
- Vehicles (automobiles, boats, RVs, motorcycles)
- Major_Assets (expensive purchases: appliances, jewelry, collections)

**Insurance categories:**
- Health (medical, dental, vision insurance policies)
- Property_Casualty (homeowners, auto, umbrella liability)
- Life_Disability (life insurance, disability insurance, long-term care)

**Tax categories:**
- Federal (IRS returns, federal tax documentation)
- State (state tax returns and documentation)
- Supporting_Docs (receipts, 1099s, W-2s, deduction records)

**Legal categories:**
- Identity (birth certificates, passports, Social Security cards)
- Estate (wills, trusts, beneficiary designations)
- Agreements (contracts, legal settlements, powers of attorney)

**Medical categories:**
- Records (medical history, test results, immunizations)
- Expenses (bills, receipts, EOBs)
- Providers (doctor contacts, prescription records)

### Level 3: Vendor

This level identifies the specific institution, company, or entity associated with the document. **Vendor names are frozen at the time of archival**—corporate name changes, mergers, or rebranding are not reflected in historical documents.

**Naming conventions for vendors:**
- Use commonly recognized names, not legal corporate entities
- Remove punctuation and special characters
- Use underscores for multi-word names: "Bank_of_America" not "BankofAmerica"
- Abbreviate when standard abbreviation exists: "BCBS" for Blue Cross Blue Shield
- For individuals (doctors, lawyers): lastname_firstname format

**Examples by category:**

*Banking:* Chase, Wells_Fargo, Bank_of_America, Ally_Bank, Local_Credit_Union

*Investment:* Vanguard, Fidelity, Charles_Schwab, TD_Ameritrade, Robinhood

*Insurance:* State_Farm, Geico, Aetna, BCBS, United_Healthcare

*Real Estate:* Property address as identifier (123_Main_St, 456_Oak_Ave)

*Retailers:* Amazon, Best_Buy, Home_Depot, Target, Walmart

*Utilities:* Duke_Energy, Comcast, Verizon, City_Water, Waste_Management

*Healthcare:* Smith_John_MD, City_Hospital, CVS_Pharmacy, Quest_Diagnostics

### Level 4: Document (files)

Individual documents stored with standardized naming convention. This level contains the actual document files with embedded metadata in the filename.

### Complete Taxonomy Examples

```
Financial/
├── Banking/
│   ├── Chase/
│   │   ├── statement-chase-checking-20250131.pdf
│   │   ├── statement-chase-checking-20250228.pdf
│   │   └── receipt-chase-wiretransfer-20250315.pdf
│   └── Ally_Bank/
│       ├── statement-allybank-savings-20250131.pdf
│       └── statement-allybank-savings-20250228.pdf
├── Investment/
│   └── Vanguard/
│       ├── statement-vanguard-ira-20250331-q1.pdf
│       └── confirmation-vanguard-purchase-20250215.pdf
└── Credit/
    └── Amex/
        ├── statement-amex-bluecash-20250131.pdf
        └── receipt-amex-annual_fee-20250101.pdf

Property/
├── Real_Estate/
│   └── 123_Main_St/
│       ├── deed-123main-purchase-19950815.pdf
│       ├── invoice-acme_roofing-replacement-20231020.pdf
│       └── receipt-lowes-kitchen_reno-20240305.pdf
└── Vehicles/
    └── 2022_Honda_Accord/
        ├── title-honda-purchase-20220612.pdf
        ├── receipt-honda_dealer-maintenance-20250201.pdf
        └── invoice-jiffy_lube-oil_change-20250415.pdf

Insurance/
├── Health/
│   └── BCBS/
│       ├── policy-bcbs-family_plan-20250101.pdf
│       ├── eob-bcbs-hospital_visit-20250320.pdf
│       └── receipt-bcbs-premium-20250401.pdf
└── Property_Casualty/
    └── State_Farm/
        ├── policy-statefarm-homeowners-20250101.pdf
        └── policy-statefarm-auto-20250601.pdf

Tax/
├── Federal/
│   ├── 2024/
│   │   ├── return-irs-form1040-20250415.pdf
│   │   └── notice-irs-refund_issued-20250520.pdf
│   └── 2023/
│       └── return-irs-form1040-20240415.pdf
└── Supporting_Docs/
    └── 2024/
        ├── receipt-goodwill-donation-20240815.pdf
        └── form-employer-w2-20250131.pdf

Legal/
├── Identity/
│   ├── certificate-vitals-birth_smith_john-19800101.pdf
│   └── passport-state_dept-smith_john-20200301.pdf
└── Estate/
    ├── will-attorney_jones-smith_family-20230915.pdf
    └── trust-attorney_jones-revocable_living-20230915.pdf

Medical/
├── Expenses/
│   ├── City_Hospital/
│   │   ├── invoice-city_hosp-surgery-20250110.pdf
│   │   └── receipt-city_hosp-payment-20250201.pdf
│   └── CVS_Pharmacy/
│       └── receipt-cvs-prescription-20250305.pdf
└── Records/
    └── Smith_John_MD/
        └── report-smith_md-annual_physical-20250220.pdf
```

## File Naming Convention

Standardized naming pattern: **doctype-vendor-subject-YYYYMMDD.ext**

### Component Specifications

**1. Document Type (doctype)**
Primary document classification based on functional purpose.

**Core document types:**
- **statement:** Regular periodic summaries (bank statements, investment statements, credit card statements)
- **receipt:** Proof of payment for goods or services
- **invoice:** Bill requesting payment (not yet paid)
- **policy:** Insurance coverage documents, terms and conditions
- **contract:** Legal agreements, service agreements
- **deed:** Property ownership transfer documents
- **title:** Vehicle or property ownership documents
- **return:** Tax returns filed with government
- **notice:** Official communications from institutions
- **report:** Medical test results, inspection reports, appraisals
- **certificate:** Official certifications (birth, death, marriage, diplomas)
- **form:** Standardized forms (W-2, 1099, tax forms)
- **letter:** Correspondence
- **agreement:** Legal binding documents, settlements
- **confirmation:** Transaction confirmations (purchases, trades)
- **eob:** Explanation of Benefits (insurance)
- **record:** Historical documentation, medical records

**2. Vendor (vendor)**
Institution, company, or entity name using Level 3 vendor naming conventions.

**Formatting rules:**
- Lowercase only
- Replace spaces with underscores
- Remove all punctuation except underscores
- Use standard abbreviations when widely recognized
- For individuals: lastname_firstname
- Keep concise: 2-4 words maximum

**3. Subject (subject)**
Brief descriptor providing context. Optional but recommended for non-routine documents.

**Guidelines:**
- 1-3 words maximum
- Lowercase with underscores between words
- Specific enough to differentiate similar documents
- Descriptive of content or purpose

**Common subject patterns:**
- Account types: checking, savings, credit, ira, 401k
- Transaction types: purchase, sale, transfer, payment, refund
- Document purposes: annual_physical, oil_change, quarterly, closing
- Specific identifiers: form1040, w2, kitchen_reno, roof_replacement

**4. Date (YYYYMMDD)**
ISO 8601 format providing universal sortability.

**Date selection rules:**
- Use statement/document date (not received date)
- Use transaction date for receipts and invoices
- Use effective date for policies and contracts
- Use filing date for tax returns
- Use event date for reports and certificates
- Format: Year (4 digits) + Month (2 digits) + Day (2 digits)
- No separators: 20250415 not 2025-04-15

**Quarterly statements:**
- Primary date: End of quarter (20250331 for Q1 ending March 31)
- Optional suffix: -q1, -q2, -q3, -q4 for clarity (statement-vanguard-ira-20250331-q1.pdf)

**Annual documents:**
- Use December 31 of the year: 20241231
- Or specific date if document has one

**5. File Extension (.ext)**
Standard file extensions based on document format.

### Complete Naming Examples

**Banking documents:**
- statement-chase-checking-20250131.pdf
- statement-chase-savings-20250228.pdf
- receipt-chase-wire_transfer-20250315.pdf
- notice-chase-fee_waiver-20250410.pdf

**Investment documents:**
- statement-vanguard-ira-20250331-q1.pdf
- confirmation-vanguard-stock_purchase-20250215.pdf
- statement-fidelity-401k-20250630-q2.pdf
- notice-schwab-dividend_payment-20250520.pdf

**Credit card documents:**
- statement-amex-bluecash-20250131.pdf
- receipt-amex-annual_fee-20250101.pdf
- letter-discover-interest_rate_change-20250201.pdf

**Real estate documents:**
- deed-123main-purchase-19950815.pdf
- invoice-acme_roofing-replacement-20231020.pdf
- receipt-lowes-kitchen_reno-20240305.pdf
- contract-hvac_company-annual_service-20250101.pdf
- report-home_inspector-annual_inspection-20250320.pdf

**Vehicle documents:**
- title-honda-purchase-20220612.pdf
- receipt-honda_dealer-maintenance-20250201.pdf
- invoice-jiffy_lube-oil_change-20250415.pdf
- contract-extended_warranty-purchase-20220612.pdf

**Insurance documents:**
- policy-bcbs-family_plan-20250101.pdf
- eob-bcbs-hospital_visit-20250320.pdf
- receipt-bcbs-premium_payment-20250401.pdf
- policy-statefarm-homeowners-20250101.pdf
- policy-statefarm-auto-20250601.pdf
- letter-geico-coverage_change-20250415.pdf

**Tax documents:**
- return-irs-form1040-20250415.pdf
- form-employer-w2-20250131.pdf
- form-vanguard-1099div-20250131.pdf
- receipt-goodwill-donation-20240815.pdf
- notice-irs-refund_issued-20250520.pdf

**Legal documents:**
- certificate-vitals-birth_smith_john-19800101.pdf
- passport-state_dept-smith_john-20200301.pdf
- will-attorney_jones-smith_family-20230915.pdf
- trust-attorney_jones-revocable_living-20230915.pdf
- agreement-divorce-settlement-20220630.pdf
- contract-real_estate-home_purchase-19950815.pdf

**Medical documents:**
- invoice-city_hosp-surgery-20250110.pdf
- receipt-city_hosp-payment-20250201.pdf
- eob-bcbs-surgery_coverage-20250110.pdf
- receipt-cvs-prescription-20250305.pdf
- report-smith_md-annual_physical-20250220.pdf
- report-quest_labs-blood_test-20250221.pdf
- record-vaccination-covid_booster-20250115.pdf

### Special Naming Scenarios

**Multi-page documents:**
- Single PDF preferred: statement-chase-checking-20250131.pdf
- If separate pages required: statement-chase-checking-20250131-p1.pdf, statement-chase-checking-20250131-p2.pdf

**Amended documents:**
- Add suffix: return-irs-form1040-20250415-amended.pdf
- Or: return-irs-form1040x-20250830.pdf (using form number for amended return)

**Multiple versions:**
- Use revision suffix: contract-lease-apartment-20250101-v1.pdf, contract-lease-apartment-20250101-v2.pdf
- Or date of revision: contract-lease-apartment-20250101-revised_20250215.pdf

**Multiple transactions same day:**
- Add time: receipt-target-groceries-20250415-1430.pdf
- Or transaction detail: receipt-target-groceries-20250415.pdf, receipt-target-electronics-20250415.pdf

**Unknown dates:**
- Use approximate date: document-vendor-subject-202500.pdf (if only year known)
- Use discovery date: document-vendor-subject-20250415.pdf (date you received/found it)

## System Documentation

```
DIRECTORY STRUCTURE:
4 levels: Domain > Category > Vendor > Document
- Level 1: 6 domains (Financial, Property, Insurance, Tax, Legal, Medical)
- Level 2: Functional categories within each domain
- Level 3: Specific vendors/institutions
- Level 4: Individual document files

FILE NAMING CONVENTION:
Pattern: doctype-vendor-subject-YYYYMMDD.ext

Components:
- doctype: Type of document (receipt, invoice, statement, policy, etc.)
- vendor: Institution or company name (lowercase, underscores for spaces)
- subject: Brief descriptor (optional, 1-3 words)
- date: ISO 8601 format YYYYMMDD (effective date, not creation date)
- ext: File extension

Examples:
- statement-chase-checking-20250131.pdf
- receipt-homedepot-lumber-20240720.pdf
- policy-statefarm-homeowners-20250101.pdf
```