"""
Integrates pharmacokinetics graphing tool with Grok for retrieving pharmacokinetic parameters.
Author: tdiprima
"""
import numpy as np
import plotly.graph_objects as go
import json
import re
from openai import OpenAI
import os

# Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_BASE = "https://api.x.ai/v1"

ALLOWED_UNITS = {"mg", "ug", "µg"}


class PharmacokineticsGraph:
    def __init__(self):
        self.time_points = np.linspace(0, 24, 100)  # Time from 0 to 24 hours
        self.openai_client = OpenAI(api_key=XAI_API_KEY, base_url=XAI_API_BASE)

    def parse_input_with_grok(self, user_input):
        """Use Grok to extract dosage/unit and infer Vd, Ka, ke."""
        try:
            response = self.openai_client.chat.completions.create(
                model="grok-beta",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a pharmacokinetics assistant. When given a prompt like "
                            "'show me the graph for 500 mg metformin' or 'simulate 5 mg lorazepam', "
                            "you must: 1) Identify the drug name and dosage, 2) Get the "
                            "pharmacokinetic parameters: Vd (in L), Ka (in h^-1), and ke (in h^-1) using "
                            "common knowledge or trained data. Then return ONLY a JSON object with "
                            "fields: Vd, Ka, ke, dosage, unit, and drug. Do not include any explanations or formatting. "
                            "Example: {\"drug\": \"metformin\", \"Vd\": 60, \"Ka\": 1.2, \"ke\": 0.1, \"dosage\": 500, \"unit\": \"mg\"}"
                        )
                    },
                    {"role": "user", "content": user_input}
                ],
                temperature=0.2,
                max_tokens=150
            )
            raw_response = response.choices[0].message.content
            print(f"Raw Grok response: {raw_response}")

            if not raw_response or raw_response.strip() == "":
                raise ValueError("Grok returned no content")

            try:
                result = json.loads(raw_response)
                return self.validate_and_convert_input(result)
            except json.JSONDecodeError:
                json_match = re.search(r'\{[^}]*\}', raw_response, re.DOTALL)
                if json_match:
                    return self.validate_and_convert_input(json.loads(json_match.group()))
                else:
                    raise ValueError(f"Grok returned invalid format: {raw_response}")

        except Exception as e:
            print(f"Error parsing with Grok: {e}")
            return None

    def validate_and_convert_input(self, data):
        """Validate extracted fields and normalize units."""
        try:
            Vd = float(data["Vd"])
            Ka = float(data["Ka"])
            ke = float(data["ke"])
            dosage = float(data["dosage"])
            unit = data["unit"].lower()
            drug = data.get("drug", "the drug").capitalize()

            if unit not in ALLOWED_UNITS:
                raise ValueError(f"Unsupported unit: {unit}")

            if unit in {"ug", "µg"}:
                dosage = dosage / 1000  # convert to mg
                unit = "mg"

            if Vd <= 0 or Ka <= 0 or ke <= 0 or dosage <= 0:
                raise ValueError("All values must be positive numbers.")

            return {"Vd": Vd, "Ka": Ka, "ke": ke, "dosage": dosage, "unit": unit, "drug": drug}
        except Exception as e:
            print(f"Validation error: {e}")
            return None

    def simulate_concentration(self, dosage, Vd, Ka, ke):
        """Simulate drug concentration over time using a one-compartment model."""
        t = self.time_points
        concentration = (dosage * Ka) / (Vd * (Ka - ke)) * (np.exp(-ke * t) - np.exp(-Ka * t))
        return concentration

    def plot_graph(self, concentration, drug_name):
        """Generate a plotly graph of drug concentration over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.time_points, y=concentration, mode='lines', name='Concentration'))
        fig.update_layout(title=f'{drug_name} Concentration vs. Time',
                          xaxis_title='Time (hours)',
                          yaxis_title='Concentration (mg/L)')
        fig.show()


if __name__ == "__main__":
    pk = PharmacokineticsGraph()

    while True:
        user_input = input("Enter your drug request (e.g., '500 mg metformin') or 'quit' to exit: ")
        if user_input.lower() == 'quit':
            break

        parsed = pk.parse_input_with_grok(user_input)
        if parsed:
            concentration = pk.simulate_concentration(
                dosage=parsed["dosage"],
                Vd=parsed["Vd"],
                Ka=parsed["Ka"],
                ke=parsed["ke"]
            )
            pk.plot_graph(concentration, drug_name=parsed["drug"])
        else:
            print("Failed to parse or validate input.")
