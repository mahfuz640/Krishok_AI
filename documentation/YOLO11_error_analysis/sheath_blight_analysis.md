# Sheath blight error analysis

## Test-set finding

Of **257** true Sheath blight test examples, the model correctly predicts **46** (recall **17.90%**) and misclassifies **211**. The largest destination is Rice Tungro (**103**, 40.08% of true Sheath blight cases), followed by Healthy (**53**, 20.62%), Brown spot (**44**, 17.12%), Leaf smut (**6**, 2.33%), and Blast (**5**, 1.95%). Sheath blight precision is **100%** (46/46 predicted Sheath blight examples), so the dominant failure is under-prediction/low recall.

Gallery contact sheets: `sheath_blight_vs_rice_tungro.png` (**103** images) and `sheath_blight_vs_healthy.png` (**53** images). Review against source labels before changing any labels. Dataset audit records 8 unresolved cross-class exact-duplicate groups excluded from the benchmark, including four Rice Tungro/Sheath blight pairs; none enters the benchmark according to manifests. Exact duplicates within test remain (4 groups / 8 manifest entries), but none crosses splits. Near-duplicate image leakage was not assessed.

## Interpretation and next steps

This is a pronounced class-specific recall problem. Conduct blinded agronomist review of the confusion galleries and inspect class-specific coverage, capture conditions, symptoms, and label quality. Any corrected labels must be made only after source review in a separately versioned dataset; preserve the approved test labels for this evaluation. Address the Colab inventory mismatch before future training.
