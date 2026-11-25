# Dataset License Report

Audit date: 2026-11-19. This records documented license claims, not legal advice or an independent chain-of-title review. Do not infer a license from the fact that a ZIP is locally available.

| Dataset | License evidence found | Assessment |
|---|---|---|
| RiceLeafDiseaseBD | Nested dataset README states Creative Commons Attribution 4.0 International (CC BY 4.0). | License is documented in the supplied dataset README. |
| Agri-Vision4 | README inside the supplied outer ZIP states CC BY 4.0. | License is documented in the supplied dataset README. |
| BCDD | Supplied root README/front matter states CC BY-SA 4.0; the publisher's Hugging Face dataset card also lists `cc-by-sa-4.0`: [BCDD dataset card](https://huggingface.co/datasets/musfiqurtuhin/BCDD). | Confirmed as the publisher-hosted dataset license metadata. The BCDD ZIP itself has no license file. |
| VegHealth14 | Root `metadata.json` has no license field; the VegHealth14 ZIP contains metadata and the nested image archive but no supplied README/license document was found. Root `README.md` is BCDD documentation and does not establish VegHealth14 licensing. | **Unknown from supplied project materials. Do not assume a license.** |

For BCDD, the live publisher card lists CC BY-SA 4.0 as of this audit. The license badge/front matter in the local root README agrees. The archive contains no separate `LICENSE` member.

For RiceLeafDiseaseBD and Agri-Vision4, the statements above are the README claims included with the datasets. Preserve their attribution/citation details when using them. VegHealth14 should not be used for redistribution or commercial release until its license is obtained from the dataset publisher.
