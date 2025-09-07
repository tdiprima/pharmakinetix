"""
Dynamic graphing tool that can generate pharmacokinetic graphs (drug concentration over time)
Author: tdiprima
"""

import json
import re

import numpy as np
import plotly.graph_objects as go


class PharmacokineticsGraph:
    def __init__(self):
        # Default pharmacokinetic parameters for metformin
        self.drugs = {
            "metformin": {
                "Vd": 100,  # Volume of distribution (L)
                "Ka": 0.5,  # Absorption rate constant (h^-1)
                "Ke": 0.0693,  # Elimination rate constant (h^-1)
            },
            "wellbutrin xl": {"Vd": 1750, "Ka": 0.2, "Ke": 0.033},
        }
        self.time_points = np.linspace(0, 24, 100)  # Time from 0 to 24 hours

    def calculate_concentration(self, drug, dose):
        """Calculate drug concentration over time using a one-compartment model."""
        drug = (
            drug.lower().strip()
        )  # Normalize the drug name to lowercase and remove extra spaces

        if drug not in self.drugs:
            raise ValueError(
                f"Drug {drug} not found in database. Available drugs: {list(self.drugs.keys())}"
            )

        params = self.drugs[drug]
        Vd, Ka, Ke = params["Vd"], params["Ka"], params["Ke"]

        # Pharmacokinetic equation
        concentration = (dose * Ka / (Vd * (Ka - Ke))) * (
            np.exp(-Ke * self.time_points) - np.exp(-Ka * self.time_points)
        )
        return self.time_points, concentration

    def generate_plotly_json(self, drug, dose):
        """Generate JSON data for Plotly."""
        time, conc = self.calculate_concentration(drug, dose)

        data = {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": f"{drug} {dose}mg",
                    "x": time.tolist(),
                    "y": conc.tolist(),
                    "line": {"color": "blue", "width": 2},
                }
            ],
            "layout": {
                "title": f"Pharmacokinetics of {drug} (Dose: {dose} mg)",
                "xaxis": {"title": "Time (hours)"},
                "yaxis": {"title": "Concentration (mg/L)"},
                "template": "plotly_white",
            },
        }

        return json.dumps(data)

    def plot_graph(self, drug, dose):
        """Create and display the graph using Plotly."""
        time, conc = self.calculate_concentration(drug, dose)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=time,
                y=conc,
                mode="lines",
                name=f"{drug} {dose}mg",
                line=dict(color="blue", width=2),
            )
        )
        fig.update_layout(
            title=f"Pharmacokinetics of {drug} (Dose: {dose} mg)",
            xaxis_title="Time (hours)",
            yaxis_title="Concentration (mg/L)",
            template="plotly_white",
        )
        fig.show()


def parse_user_input(user_input):
    """
    Parse user input like 'show me metformin at 500 mg' or 'plot wellbutrin xl at 300 mg'.
    Returns (drug name, dose) if successful, else (None, None).
    """
    try:
        pattern = r"(?:show me|plot) ([a-z0-9 ]+) at (\d+)\s*mg"
        match = re.search(pattern, user_input.lower())

        if match:
            drug = match.group(1).strip()
            dose = int(match.group(2))
            print(f"Parsed drug name: '{drug}'")  # Debugging: Print the parsed drug
            print(f"Parsed dose: {dose}")  # Debugging: Print the parsed dose
            return drug, dose
        else:
            raise ValueError(
                "Invalid input format. Use 'show me [drug] at [dose] mg' or 'plot [drug] at [dose] mg'."
            )
    except Exception as e:
        print(f"Error parsing input: {e}")
        return None, None


# Example usage
if __name__ == "__main__":
    pk_graph = PharmacokineticsGraph()

    while True:
        user_input = input(
            "Enter command (e.g., 'show me wellbutrin xl at 300 mg') or 'quit' to exit: "
        )
        if user_input.lower() == "quit":
            break

        drug, dose = parse_user_input(user_input)
        if drug and dose:
            try:
                # Generate and display the graph
                pk_graph.plot_graph(drug, dose)

                # Optionally generate JSON for Plotly
                # json_data = pk_graph.generate_plotly_json(drug, dose)
                # print("Plotly JSON data:", json_data)

            except Exception as e:
                print(f"Error generating graph: {e}")
        else:
            print("Could not parse input. Please try again.")
