# SN Corporate Rating Model V2

This repository contains a **rule-based corporate credit rating engine** for non-financial corporates.

The model is built around:

- Multi-period financial statements  
- Altman Z-score  
- Peer benchmarking  
- Optional distress hardstops  
- Optional sovereign cap  

It is designed as a **transparent, documentation-heavy reference implementation**, rather than a black-box machine learning model.

---

## 📌 Start Here

- **High-level README**: [00_README.md](00_README.md)  
- **Methodology overview**: [1_Methodology_Overview.md](1_Methodology_Overview.md)  
- **Quantitative factors and ratios**: [2_Quantitative_Factors_and_Ratio_Definitions.md](2_Quantitative_Factors_and_Ratio_Definitions.md)  
- **Qualitative factors and scales**: [3_Qualitative_Factors_and_Scale_Definitions.md](3_Qualitative_Factors_and_Scale_Definitions.md)  
- **Hardstop workflow**: [4_Hardstop_Rating_Workflow.md](4_Hardstop_Rating_Workflow.md)  
- **Sovereign cap workflow**: [5_Sovereign_Cap_Workflow.md](5_Sovereign_Cap_Workflow.md)  
- **Outlook workflow**: [6_Corporate_Rating_Outlook_Workflow.md](6_Corporate_Rating_Outlook_Workflow.md)

---
### 🚀 Quickstart (5 Minutes)

### 1. Clone this repository:

   ```bash
   git clone https://github.com/snlabs-tech/SN-Corporate-Rating-Model-V2.git
   cd SN-Corporate-Rating-Model-V2
   ```

### 2. Open the main notebook

Open in **Jupyter Notebook** or **VS Code**:

```
7_corporate_rating_model_V2.ipynb
```

Then run:

- Menu: Kernel → Restart & Run All

Inspect the sample outputs:

- Intermediate scores  
- Hardstops  
- Sovereign cap  
- Final rating  
- Rating outlook  

### 3. Run the script demo (optional)

From the repository root (the main folder with this 'README.md'), run:

```
rating_model_V2_demo.py
```
This script uses sample financials and qualitative factors to compute a full issuer rating and prints the key outputs to the console.

---

## Code Walkthrough

For a detailed explanation of the implementation, see:

- Notebook: `7_corporate_rating_model_V2.ipynb`
- Code walkthrough document: `8_rating_model_V2_code_walkthrough.docx`
