"""
Integrates pharmacokinetics graphing tool with Grok and optionally the DrugBank API for retrieving pharmacokinetic parameters.
Author: tdiprima
"""
import numpy as np
import plotly.graph_objects as go
import json
import requests
import re
from openai import OpenAI
import os

# Configuration
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_API_BASE = "https://api.x.ai/v1"
DRUGBANK_API_KEY = "YOUR_DRUGBANK_API_KEY"
DRUGBANK_API_BASE = "https://api.drugbank.com/v1"


class PharmacokineticsGraph:
    def __init__(self):
        self.time_points = np.linspace(0, 24, 100)  # Time from 0 to 24 hours
        self.openai_client = OpenAI(api_key=XAI_API_KEY, base_url=XAI_API_BASE)

    def parse_input_with_grok(self, user_input):
        """Parse user input using Grok API."""
        try:
            response = self.openai_client.chat.completions.create(
                model="grok-beta",
                messages=[
                    {"role": "system", "content": "You are a highly precise assistant designed to parse drug and dosage commands. When given an input like 'show me [drug] at [dose] mg', extract the drug name and dosage, and return ONLY a JSON object with the fields 'drug', 'dosage', and 'unit'. Do not include any additional text, explanations, or formatting. Example output for 'show me metformin at 500 mg': {'drug': 'metformin', 'dosage': 500, 'unit': 'mg'}.  Do not return \"```\" or \"```json\"."},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                max_tokens=100
            )
            raw_response = response.choices[0].message.content
            print(f"Raw Grok response: {raw_response}")

            if not raw_response or raw_response.strip() == "":
                raise ValueError("Grok returned no content")

            try:
                result = json.loads(raw_response)
                return result
            except json.JSONDecodeError:
                print(f"Failed to parse as JSON. Raw response: {raw_response}")
                # json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)  # greedy match
                json_match = re.search(r'\{[^}]*\}', raw_response, re.DOTALL)  # safer and more specific
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError(f"Grok returned invalid format: {raw_response}")

        except Exception as e:
            print(f"Error parsing with Grok: {e}")
            return None

    def get_drug_params_from_drugbank(self, drug_name):
        """Fetch pharmacokinetic parameters from DrugBank API."""
        try:
            url = f"{DRUGBANK_API_BASE}/drugs"
            headers = {"Authorization": f"Bearer {DRUGBANK_API_KEY}"}
            params = {"name": drug_name.lower()}

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "Vd": data.get("volume_of_distribution", 50),
                "Ka": data.get("absorption_rate_constant", 0.3),
                "Ke": data.get("elimination_rate_constant", 0.08)
            }
        except Exception as e:
            print(f"Error fetching from DrugBank: {e}")
            return self.get_fallback_params(drug_name)

    def get_fallback_params(self, drug_name):
        """Fallback to hardcoded parameters."""
        fallback_params = {
            "metformin": {"Vd": 100, "Ka": 0.5, "Ke": 0.1},
            "wellbutrin xl": {"Vd": 47, "Ka": 0.4, "Ke": 0.1}
        }
        return fallback_params.get(drug_name.lower(), {"Vd": 50, "Ka": 0.3, "Ke": 0.08})

    def calculate_concentration(self, drug, dose):
        params = self.get_drug_params_from_drugbank(drug)
        Vd, Ka, Ke = params["Vd"], params["Ka"], params["Ke"]

        if Ka == Ke:
            Ka += 0.001
        concentration = (dose * Ka / (Vd * (Ka - Ke))) * (np.exp(-Ke * self.time_points) - np.exp(-Ka * self.time_points))
        return self.time_points, concentration

    def generate_plotly_json(self, drug, dose):
        time, conc = self.calculate_concentration(drug, dose)

        data = {
            "data": [{
                "type": "scatter",
                "mode": "lines",
                "name": f"{drug} {dose}mg",
                "x": time.tolist(),
                "y": conc.tolist(),
                "line": {"color": "blue", "width": 2}
            }],
            "layout": {
                "title": f"Pharmacokinetics of {drug} (Dose: {dose} mg)",
                "xaxis": {"title": "Time (hours)"},
                "yaxis": {"title": "Concentration (mg/L)"},
                "template": "plotly_white"
            }
        }

        return json.dumps(data)

    def plot_graph(self, drug, dose):
        time, conc = self.calculate_concentration(drug, dose)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=conc, mode='lines', name=f"{drug} {dose}mg", line=dict(color='blue', width=2)))
        fig.update_layout(
            title=f"Pharmacokinetics of {drug} (Dose: {dose} mg)",
            xaxis_title="Time (hours)",
            yaxis_title="Concentration (mg/L)",
            template="plotly_white"
        )
        fig.show()


def test_regex():
    test_string = '{"drug": "metformin", "dosage": 500, "unit": "mg"}'
    match = re.search(r'\{[^}]*\}', test_string, re.DOTALL)
    assert match is not None, "Regex should match JSON"
    assert json.loads(match.group()) == {"drug": "metformin", "dosage": 500, "unit": "mg"}, "Parsed JSON should be correct"


def main():
    pk_graph = PharmacokineticsGraph()

    while True:
        user_input = input("Enter command (e.g., 'show me wellbutrin xl at 300 mg') or 'quit' to exit: ")
        if user_input.lower() == 'quit':
            break

        try:
            # First, try Grok
            parsed_data = pk_graph.parse_input_with_grok(user_input)
            if not parsed_data:
                print("Falling back to manual parsing...")
                parts = user_input.lower().split()
                if "show" in parts and "me" in parts and "at" in parts:
                    drug_start = parts.index("me") + 1
                    dose_end = parts.index("at")
                    drug = " ".join(parts[drug_start:dose_end])
                    dose_str = parts[dose_end + 1].replace("mg", "").strip()
                    dose = int(dose_str) if dose_str.isdigit() else 0
                    parsed_data = {"drug": drug, "dosage": dose, "unit": "mg"}
                else:
                    raise ValueError("Could not parse input. Please use format 'show me [drug] at [dose] mg'.")

            drug = parsed_data["drug"]
            dose = parsed_data["dosage"]

            print(f"Parsed drug: '{drug}', Parsed dose: {dose}")

            # Generate and display the graph
            pk_graph.plot_graph(drug, dose)

            # Optionally generate JSON for Plotly
            # json_data = pk_graph.generate_plotly_json(drug, dose)
            # print("Plotly JSON data:", json_data)

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
    # test_regex()
