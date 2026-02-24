# Query Patterns — california_schools_template

## Top N Schools by SAT Score
**Trigger phrases**: "best SAT scores", "top schools by SAT", "highest SAT",
"schools with best test scores"
**Confidence**: verified (canonical BIRD-CRITIC pattern)

```sql
SELECT
	s."School",
	s."County",
	sat.AvgScrMath + sat.AvgScrRead + sat.AvgScrWrite AS sat_composite
FROM schools s
JOIN satscores sat ON s.CDSCode = sat.cds
WHERE sat.NumTstTakr IS NOT NULL
ORDER BY sat_composite DESC
LIMIT {{n}};
```

---

## FRPM Rate by County
**Trigger phrases**: "free meal rate by county", "poverty rate by county",
"FRPM eligibility by county", "which county has most eligible students"
**Confidence**: verified

```sql
SELECT
	f."County Name",
	SUM(f."FRPM Count (K-12)") AS total_frpm,
	SUM(f."Enrollment (K-12)") AS total_enrollment,
	SUM(f."FRPM Count (K-12)")::float / NULLIF(SUM(f."Enrollment (K-12)"), 0)
		AS county_frpm_rate
FROM frpm f
WHERE f."School Name" IS NOT NULL
GROUP BY f."County Name"
ORDER BY county_frpm_rate DESC;
```

---

## Schools with Both SAT Scores and FRPM Data
**Trigger phrases**: "compare SAT and poverty", "schools with high SAT and low FRPM",
"correlation between meals and scores"
**Confidence**: verified

```sql
SELECT
	s."School",
	s."County",
	sat.AvgScrMath + sat.AvgScrRead + sat.AvgScrWrite AS sat_composite,
	f."FRPM Count (K-12)"::float / NULLIF(f."Enrollment (K-12)", 0) AS frpm_rate
FROM schools s
JOIN satscores sat ON s.CDSCode = sat.cds
JOIN frpm f ON s.CDSCode = f.CDSCode
WHERE sat.NumTstTakr IS NOT NULL
  AND f."School Name" IS NOT NULL
ORDER BY sat_composite DESC;
```

---

## Charter vs Non-Charter School Comparison
**Trigger phrases**: "charter schools", "charter vs public", "do charter schools
perform better"
**Confidence**: verified

```sql
SELECT
	f."Charter School (Y/N)" AS is_charter,
	COUNT(*) AS school_count,
	AVG(sat.AvgScrMath + sat.AvgScrRead + sat.AvgScrWrite) AS avg_sat_composite,
	AVG(f."FRPM Count (K-12)"::float / NULLIF(f."Enrollment (K-12)", 0))
		AS avg_frpm_rate
FROM schools s
JOIN frpm f ON s.CDSCode = f.CDSCode
JOIN satscores sat ON s.CDSCode = sat.cds
WHERE sat.NumTstTakr IS NOT NULL
  AND f."School Name" IS NOT NULL
  AND f."Charter School (Y/N)" IS NOT NULL
GROUP BY f."Charter School (Y/N)"
ORDER BY is_charter;
```

---

## School Enrollment by County
**Trigger phrases**: "how many students", "enrollment by county", "largest counties"
**Confidence**: verified

```sql
SELECT
	f."County Name",
	SUM(f."Enrollment (K-12)") AS total_enrollment
FROM frpm f
WHERE f."School Name" IS NOT NULL
GROUP BY f."County Name"
ORDER BY total_enrollment DESC;
```
