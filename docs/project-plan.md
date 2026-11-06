# Project plan

Source: team Project Plan document (Nov 3 meeting). Deadlines: presentation **Wed Nov 18, 11:59 PM**
(recorded on Zoom, ≤ 15 min, ≤ 10 slides: Introduction, Methodology, Results, Conclusion);
final report **Mon Dec 7, 11:59 PM**.

## Who owns what

|             | **Avneesh: analyst**                               | **Sami: Layer 2, documentation, code review**                                      | **Elliot: research, slides, logistics**                                  |
|-------------|----------------------------------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Owns**    | Shared node set, Layer 1, all modeling and figures | Layer 2, repository and README, report drafting, reproducibility, contribution log | Literature review, drug-class table, slides, logistics, discussion board |
| **Reviews** | Sami’s code                                        | Avneesh’s code                                                                     | —                                                                        |
| **Load**    | Heaviest                                           | Heavy                                                                              | Light                                                                    |

## Week 1 (Nov 3–9): build the two-layer network

| **Owner**        | **Task**                                                                                                                                                  | **Due**                          |
|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| Avneesh          | Set up the repository; choose the ~300 drugs and map all names to single ingredients via RxNorm codes. This shared node set is what both layers build on. | Wed Nov 4                        |
| Avneesh          | **Layer 1:** pull labels, mine the interactions text with negation handling, tag edges that come from class-level mentions                                | Sat Nov 7                        |
| Sami             | **Layer 2:** pull co-report counts, compute observed/expected weights, apply the signal filter (at least 5 reports, lower confidence bound above 0)       | Sat Nov 7                        |
| Avneesh and Sami | **Cross-review:** each reviews the other’s layer code within 24 hours of it being pushed. Merge both layers and **freeze the data snapshot**.             | Sun Nov 8                        |
| Sami             | Repository structure, README, and a data dictionary for both layers; start the contribution log                                                           | Tue Nov 3, then ongoing          |
| Sami             | Start the report draft, including the “Network data” section                                                                                              | Sun Nov 8                        |
| Elliot           | Literature check: confirm no published work already builds a label-vs-report two-layer network                                                            | Fri Nov 6                        |
| Elliot           | Build a drug-class reference table for the 300 drugs, for checking the block-model groups                                                                 | Mon Nov 9                        |
| Elliot           | Confirm the presentation format (in class or recorded)                                                                                                    | Once the sign-up sheet is posted |

## Weeks 2–5 (to be planned)

Week 2 (Nov 10–16): notebooks 04–05 on the frozen network; slides drafted.
Week 3 (Nov 17–18): record and submit the presentation.
Weeks 3–5 (Nov 19 – Dec 7): report, sensitivity checks, final clean-up.
