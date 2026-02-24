# Metrics — california_schools_template

## FRPM Rate (Free or Reduced Price Meal Eligibility Rate)
**Definition**: Percentage of K-12 students eligible for free or reduced-price
meals. A proxy for school-level poverty rate.
**Confidence**: verified

```sql
SELECT
	s."School",
	s."County",
	f."FRPM Count (K-12)"::float / NULLIF(f."Enrollment (K-12)", 0) AS frpm_rate
FROM schools s
JOIN frpm f ON s.CDSCode = f.CDSCode
WHERE f."School Name" IS NOT NULL
ORDER BY frpm_rate DESC;
```

---

## Free Meal Rate (Strict — excludes reduced-price)
**Definition**: Percentage eligible for FREE meals only (not reduced-price).
**Confidence**: verified

```sql
SELECT
	s."School",
	f."Free Meal Count (K-12)"::float / NULLIF(f."Enrollment (K-12)", 0) AS free_meal_rate
FROM schools s
JOIN frpm f ON s.CDSCode = f.CDSCode
WHERE f."School Name" IS NOT NULL;
```

---

## SAT Composite Score (Total)
**Definition**: Sum of average math + reading + writing scores for a school.
Used when user asks for "SAT score" without specifying subject.
**Confidence**: verified

```sql
SELECT
	s."School",
	sat.AvgScrMath + sat.AvgScrRead + sat.AvgScrWrite AS sat_composite
FROM schools s
JOIN satscores sat ON s.CDSCode = sat.cds
WHERE sat.NumTstTakr IS NOT NULL
ORDER BY sat_composite DESC;
```

---

## SAT Math Average
**Definition**: Average SAT math section score for a school.
**Confidence**: verified

```sql
SELECT s."School", sat.AvgScrMath
FROM schools s
JOIN satscores sat ON s.CDSCode = sat.cds
WHERE sat.NumTstTakr IS NOT NULL;
```
