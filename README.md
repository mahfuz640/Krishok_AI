---
annotations_creators:
- expert-generated
language:
- en
license:
- cc-by-sa-4.0
task_categories:
- image-classification
tags:
- agriculture
- plant-disease
- biology
- medical
size_categories:
- 1K<n<10K
pretty_name: Bangladeshi Crops Disease Dataset (BCDD)
dataset_info:
  features:
  - name: image
    dtype: image
  - name: label
    dtype:
      class_label:
        names:
          '0': Corn_Cercospora_Leaf_Spot
          '1': Corn_Common_Rust
          '2': Corn_Healthy
          '3': Corn_Northern_Leaf_Blight
          '4': Potato_Early_Blight
          '5': Potato_Healthy
          '6': Potato_Late_Blight
          '7': Rice_Bacterial_Leaf_Blight
          '8': Rice_Brown_Spot
          '9': Rice_Healthy
          '10': Rice_Leaf_Blast
          '11': Rice_Leaf_Scald
          '12': Rice_Narrow_Brown_Spot
          '13': Tomato_Bacterial_Spot
          '14': Tomato_Healthy
          '15': Tomato_Late_Blight
          '16': Tomato_Leaf_Mold
          '17': Wheat_Brown_Rust
          '18': Wheat_Healthy
---

# 🇧🇩 Bangladeshi Crops Disease Dataset (BCDD)

![Images](https://img.shields.io/badge/Images-8%2C992-blue?style=for-the-badge&logo=google-photos&logoColor=white)
![Classes](https://img.shields.io/badge/Classes-19-green?style=for-the-badge&logo=google-lens&logoColor=white)
![Crops](https://img.shields.io/badge/Crops-5-orange?style=for-the-badge&logo=leaf&logoColor=white)
![License](https://img.shields.io/badge/License-CC--BY--SA--4.0-lightgrey?style=for-the-badge)

Official dataset for the **IEEE ECCE 2025** paper:
> **"Plant Disease Recognition from the Perspective of Bangladesh: A Comparative Study of Deep Learning Models and Ensemble Techniques"**

## 🚀 Associated Resources
| Resource | Link |
| :--- | :--- |
| **GitHub Code** | [![GitHub](https://img.shields.io/badge/GitHub-Repo-black?style=flat&logo=github)](https://github.com/MusfiqurTuhin/Plant-Disease-Recognition-from-the-Perspective-of-Bangladesh.git) |
| **Kaggle Source** | [![Kaggle](https://img.shields.io/badge/Kaggle-Dataset-blue?style=flat&logo=kaggle)](https://www.kaggle.com/datasets/musfiqurtuhin/bangladeshi-crops-disease-dataset-bcdd) |
| **Paper Abstract** | [![IEEE](https://img.shields.io/badge/IEEE-Xplore-blue?style=flat&logo=ieee)](https://ieeexplore.ieee.org/abstract/document/11013222) |

## 🔬 Collection Methodology
The dataset is a curated subset of three public repositories:
1.  **Wheat Leaf Disease Dataset** (6,134 images)
2.  **Rice Leaf Disease Dataset** (2,627 images)
3.  **Plant Village Dataset**

It focuses on **5 crops** (Corn, Potato, Rice, Tomato, Wheat) relevant to Bangladesh. Images were resized to **96x96 pixels** and augmented using rotation, flipping, and grayscale conversion to ensure robustness.

## 🐍 Quick Load
You can load this dataset directly in Python using the Hugging Face `datasets` library:

```python
from datasets import load_dataset

# Load the dataset
dataset = load_dataset("musfiqurtuhin/BCDD")

# View a training example
print(dataset['train'][0])
```
## 📝 Citation
If you use this dataset in your research, please cite our **ECCE 2025** paper:

```bibtex
@InProceedings{11013222,
  author={Rahman, Md. Musfiqur and Tusher, Md Mahbubur Rahman and Rinky, Susmita Roy and Mokit, Junaid Rahman and Biswas, Sudipa},
  booktitle={2025 International Conference on Electrical, Computer and Communication Engineering (ECCE)}, 
  title={Plant Disease Recognition from the Perspective of Bangladesh: A Comparative Study of Deep Learning Models and Ensemble Techniques}, 
  year={2025},
  pages={1-6},
  doi={10.1109/ECCE64574.2025.11013222}
}# Krishok_AI
