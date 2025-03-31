# pharmakinetix
Pharmacokinetics app

## PK Formula

### [pk\_graph_generator.py](pk_graph_generator.py)


#### Pharmacokinetic Model
For simplicity, we'll use a one-compartment model with first-order absorption and elimination, which is common for drugs like metformin. The key parameters include:

- **Dose**: User-provided (e.g., 500 mg).
- **Volume of Distribution (Vd)**: How the drug distributes in the body (assumed value for metformin, e.g., 100 L).
- **Clearance (Cl)**: How quickly the drug is removed (assumed value, e.g., 10 L/h).
- **Absorption Rate Constant (Ka)**: How quickly the drug is absorbed (e.g., 0.5 h^-1).
- **Elimination Rate Constant (Ke)**: How quickly the drug is eliminated (e.g., 0.1 h^-1).

The concentration over time can be modeled using the equation:

\[
C(t) = \frac{Dose \cdot Ka}{V_d (Ka - Ke)} \cdot (e^{-Ke \cdot t} - e^{-Ka \cdot t})
\]

Where:

- \(C(t)\): Concentration at time \(t\).
- \(Dose\): Administered dose.
- \(Ka\): Absorption rate constant.
- \(Ke\): Elimination rate constant.
- \(Vd\): Volume of distribution.
- \(t\): Time.

The pharmacokinetic parameters (Vd, Ka, Ke) are simplified. In a real application, you'd need a database of drug-specific parameters or an API like DrugBank.

### [pk-visualizer.html](pk-visualizer.html)

```js
k = Math.log(2) / halfLife
C(t) = (Dose × Bioavailability / Vd) × e^(-kt)
```
