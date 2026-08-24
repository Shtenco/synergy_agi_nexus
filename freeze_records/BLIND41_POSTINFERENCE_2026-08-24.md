# Blind-41 POST-INFERENCE RESULT

Pre-inference commitment commit: `31b67fb047450f97f23b823d26477d701f97a094`
R7.27 freeze SHA-256: `6f726b95bc9f8ec54edb0e9794aefeae4897aa905ee0747496cf44fc7377ee52`
Blind-41 no-gold SHA-256: `3ba3e990a30f9f4d667fad52671ea413c815231911b2c2475d6992372ee0a616`

Frozen R7.27 result:
- total: 160/200 = 80.0%
- resolved: 165/200 = 82.5%
- conditional accuracy: 160/165 = 96.9697%
- false VERIFIED: 5
- standard/composable: 160/160 = 100%, false VERIFIED 0
- near-OOD: 0/40 correct; 5 resolved wrong + 35 safe abstentions

Frozen R7.26 on same Blind-41:
- total: 0/200 correct
- resolved: 25/200
- false VERIFIED: 25

Paired R7.26→R7.27: 160 corrections / 0 regressions on correctness.

All five R7.27 false VERIFIED are B41_046..B41_050 (natural-logarithm + add). Diagnosis: LOG is unrecognized, while a recognized downstream ADD is incorrectly treated as a complete scalar program. This shows that RecognizedOperators=100% is insufficient; a future version needs a semantic-span completeness proof that no unknown operator span remains. R7.27 is NOT patched after this observation.