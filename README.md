# pharmakinetix
Pharmacokinetics app

## PK Formula

#### Pharmacokinetic Model

- **Dose**: User-provided (e.g., 500 mg).
- **Volume of Distribution (Vd)**: How the drug distributes in the body (assumed value for metformin, e.g., 100 L).
- **Clearance (Cl)**: How quickly the drug is removed (assumed value, e.g., 10 L/h).
- **Absorption Rate Constant (Ka)**: How quickly the drug is absorbed (e.g., 0.5 h^-1).
- **Elimination Rate Constant (Ke)**: How quickly the drug is eliminated (e.g., 0.1 h^-1).

The concentration over time can be modeled using the equation:

![concentration over time](formula.png)

Where:

- \(C(t)\): Concentration at time \(t\).
- \(Dose\): Administered dose.
- \(Ka\): Absorption rate constant.
- \(Ke\): Elimination rate constant.
- \(Vd\): Volume of distribution.
- \(t\): Time.

<br>
