import os
import pandas as pd
import re

# Load dataset
base_dir = os.path.dirname(os.path.dirname(__file__))
csv_path = os.path.join(base_dir, "data", "data.csv")

df = pd.read_csv(csv_path)
df["drug"] = df["drug"].str.lower().str.strip()

def check_prescription(raw_text: str, age: int = 30):
    score = 100
    found_drugs = []

    # --- Find drugs mentioned in text ---
    for drug in df["drug"].unique():
        if re.search(rf"\b{drug}\b", raw_text.lower()):
            found_drugs.append(drug)

    warnings = []

    for drug in found_drugs:
        rows = df[df["drug"] == drug]
        for _, row in rows.iterrows():
            foods = row["foods_to_avoid"].split(",") if pd.notna(row["foods_to_avoid"]) else []
            interactions = row["drug_drug_interactions"].split(",") if pd.notna(row["drug_drug_interactions"]) else []
            alternatives = row["alternatives"].split(",") if pd.notna(row["alternatives"]) else []

            severity = str(row["severity"]).lower()
            if severity == "major":
                score -= 20
            elif severity == "moderate":
                score -= 10
            elif severity == "minor":
                score -= 5

            # --- Dosage check ---
            dosage_warning = "Not checked"
            status = "unknown"
            if pd.notna(row["max_safe_dose_adults"]):
                try:
                    max_adult = float(row["max_safe_dose_adults"])
                    numbers = [int(x) for x in re.findall(r"\d+", raw_text)]
                    if numbers:
                        prescribed = max(numbers)
                        if prescribed > max_adult:
                            dosage_warning = f"Prescribed dose {prescribed} exceeds safe adult limit {row['max_safe_dose_adults']} mg/day"
                            status = "unsafe"
                        else:
                            dosage_warning = f"✅ Dosage safe (within {row['max_safe_dose_adults']} mg/day)"
                            status = "safe"
                except:
                    pass

            warnings.append({
                "drug": drug,
                "severity": row["severity"],
                "interaction_description": row["interaction_description"],
                "mechanism": row["mechanism"],
                "recommendation": row["recommendation"],
                "foods_to_avoid": [f.strip() for f in foods if f.strip()],
                "drug_interactions": [i.strip().lower() for i in interactions if i.strip()],
                "dosage_check": {
                    "drug": drug,
                    "status": status,
                    "explanation": dosage_warning
                },
                "alternatives": [a.strip() for a in alternatives if a.strip()]
            })

    # --- Check drug–drug harmful combos ---
    harmful_combos = []
    for drug in found_drugs:
        rows = df[df["drug"] == drug]
        for _, row in rows.iterrows():
            interactions = row["drug_drug_interactions"].split(",") if pd.notna(row["drug_drug_interactions"]) else []
            for inter in interactions:
                if inter.lower().strip() in found_drugs:
                    harmful_combos.append(
                        (drug, inter, row["interaction_description"], row["severity"])
                    )

    return {
        "found_drugs": found_drugs,
        "harmful_combos": harmful_combos,
        "alternatives": {w["drug"]: w["alternatives"] for w in warnings if w["alternatives"]},
        "dosage_checks": [w["dosage_check"] for w in warnings],
        "food_advice": [(w["drug"], {"avoid": w["foods_to_avoid"], "take": []}) for w in warnings if w["foods_to_avoid"]],
        "mechanisms": [(w["drug"], w["mechanism"]) for w in warnings if w["mechanism"]],
        "safety_score": max(0, min(100, score))
    }

