# Cloud Coach overview

This app is a local study, quiz, flashcard, and readiness tracker for three tools that show up together constantly in real cloud/platform engineering roles: **AWS**, **Terraform**, and **Kubernetes**. It is not affiliated with Amazon, HashiCorp, or the Cloud Native Computing Foundation, and it does not contain real exam questions from any certification body.

## Why these three together

They form a natural stack in most modern infrastructure jobs:

- **AWS** is the cloud provider — the actual compute, storage, network, and managed services you're provisioning.
- **Terraform** is how you provision it declaratively and repeatably, instead of clicking through a console.
- **Kubernetes** is how you run and orchestrate the workloads once compute exists — often on top of AWS via EKS.

A job posting for "Platform Engineer," "DevOps Engineer," "Site Reliability Engineer," or "Cloud Engineer" very often expects working knowledge of all three, even if day-to-day work leans harder on one.

## The certifications this app loosely tracks

None of these are required to use this app, and none of this app's practice percentages are official predictors of a real score. But if you're using this app to prepare for a certification, here's the honest picture as commonly published:

| Certification | Format | Commonly published passing bar |
|---|---|---|
| AWS Certified Solutions Architect – Associate (SAA-C03) | 65 scored multiple-choice/multiple-response, scaled 100–1000 | Scaled score of 720 (roughly 72%, but it is NOT literally 72% of raw questions — AWS scales per-question difficulty) |
| HashiCorp Certified: Terraform Associate | ~57 multiple-choice/true-false | Scaled score, commonly cited around 70% |
| Certified Kubernetes Administrator (CKA) | Hands-on performance tasks in a live cluster, no multiple choice | 66/100 |

Confirm current format, question counts, and passing bars directly with the certifying body before you register — these change between exam versions.

## What this app does NOT do

- It does not simulate the real exam UI or timing exactly (CKA in particular is a hands-on lab exam this app cannot replicate — you need a real cluster for that).
- It does not track your progress toward AWS's tiered certifications (Associate → Professional → Specialty) — it only covers Associate-level breadth.
- It does not give legal or compliance advice about cloud architecture (HIPAA, FedRAMP, etc.) — those require a specialist, not a study app.

## How to actually use this app

1. Pick a track on the dashboard — it just changes which topics get prioritized in "What to do next," it doesn't lock you out of anything.
2. Take a baseline mixed quiz in Practice to see where you actually stand.
3. Use Learn for the full write-up on a topic, or ask Coach a specific question.
4. Drill vocabulary and syntax with Flashcards in spare minutes.
5. Come back to My Progress regularly — not just when you feel ready.
