# Complex Integration Studio

Complex Integration Studio is a FastAPI-based web application for visualizing complex functions and evaluating contour integrals.

The user can enter a complex-valued function `f(z)`, define a parameterized contour `z(t)`, and explore the function as a 3D surface while the app computes the integral along that path.

## Features

- Enter a complex function in terms of `z`
- Define a contour in terms of `t`
- Plot one of these 3D surfaces over the complex plane:
  - `|f(z)|`
  - `Re(f(z))`
  - `Im(f(z))`
- Overlay the contour directly on the rendered surface
- Compute the contour integral `integral f(z) dz`
- Attempt symbolic integration first, then provide a numeric result

## Tech Stack

- Backend: FastAPI
- Math engine: SymPy + NumPy
- Frontend: HTML, CSS, vanilla JavaScript
- Visualization: Plotly.js

## How It Works

1. The user enters a function such as `1 / z` or `exp(z)`.
2. The user defines a contour such as `exp(i*t)`.
3. The backend parses both expressions safely with SymPy.
4. The app samples the selected surface across the complex plane.
5. The contour integral is evaluated from
   `f(z(t)) * z'(t)`.
6. The frontend renders the 3D surface and draws the contour on top of it.

## Run Locally

```powershell
py -m pip install -r requirements.txt
py -m uvicorn app:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Example Inputs

### 1. Classic residue example

- `f(z) = 1 / z`
- `z(t) = exp(i*t)`
- `t in [0, 2*pi]`

Expected result: approximately `2*pi*i`

### 2. Exponential on an ellipse

- `f(z) = exp(z)`
- `z(t) = 2*cos(t) + i*sin(t)`
- `t in [0, 2*pi]`

### 3. Rational function with poles

- `f(z) = (z + 1) / (z^2 + 1)`
- `z(t) = 1.5*exp(i*t)`
- `t in [0, 2*pi]`

## Project Structure

```text
ComplexIntegrationWebsite/
|-- app.py
|-- complex_math.py
|-- requirements.txt
|-- README.md
`-- static/
    |-- app.js
    |-- index.html
    `-- styles.css
```

## Notes

- Use `i` for the imaginary unit.
- Use `^` for powers.
- Symbolic integration is attempted when possible, but some inputs will return only a numeric result.
- Functions with singularities may produce clipped surfaces in the visualizer to keep the plot readable.

## Future Improvements

- Add more contour presets
- Add export options for plots and results
- Add support for domain coloring
- Add a step-by-step derivation panel for symbolic results

## License

Add your preferred license before publishing to GitHub.
