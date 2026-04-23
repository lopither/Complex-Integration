const form = document.querySelector("#analysis-form");
const plotElement = document.querySelector("#plot");
const statusText = document.querySelector("#status-text");
const submitButton = document.querySelector("#submit-button");

const symbolicResult = document.querySelector("#symbolic-result");
const numericResult = document.querySelector("#numeric-result");
const polarResult = document.querySelector("#polar-result");
const parsedFunction = document.querySelector("#parsed-function");
const parsedContour = document.querySelector("#parsed-contour");
const integrandDisplay = document.querySelector("#integrand-display");
const magnitudeDisplay = document.querySelector("#magnitude-display");

const examples = {
  residue: {
    function: "1 / z",
    contour: "exp(i*t)",
    t_min: "0",
    t_max: "2*pi",
    component: "abs",
    x_min: -3,
    x_max: 3,
    y_min: -3,
    y_max: 3,
    resolution: 81,
    integral_samples: 4000,
  },
  gaussian: {
    function: "exp(z)",
    contour: "2*cos(t) + i*sin(t)",
    t_min: "0",
    t_max: "2*pi",
    component: "real",
    x_min: -3,
    x_max: 3,
    y_min: -3,
    y_max: 3,
    resolution: 71,
    integral_samples: 3500,
  },
  pole: {
    function: "(z + 1) / (z^2 + 1)",
    contour: "1.5*exp(i*t)",
    t_min: "0",
    t_max: "2*pi",
    component: "imag",
    x_min: -3,
    x_max: 3,
    y_min: -3,
    y_max: 3,
    resolution: 81,
    integral_samples: 4200,
  },
};

document.querySelectorAll(".example-chip").forEach((button) => {
  button.addEventListener("click", () => {
    const example = examples[button.dataset.example];
    for (const [key, value] of Object.entries(example)) {
      const field = form.elements.namedItem(key);
      if (field) {
        field.value = value;
      }
    }
    form.requestSubmit();
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    function: form.function.value,
    contour: form.contour.value,
    t_min: form.t_min.value,
    t_max: form.t_max.value,
    component: form.component.value,
    x_min: Number(form.x_min.value),
    x_max: Number(form.x_max.value),
    y_min: Number(form.y_min.value),
    y_max: Number(form.y_max.value),
    resolution: Number(form.resolution.value),
    integral_samples: Number(form.integral_samples.value),
  };

  statusText.textContent = "Computing surface and contour integral...";
  submitButton.disabled = true;

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorPayload = await response.json();
      throw new Error(errorPayload.detail || "The server could not analyze that input.");
    }

    const result = await response.json();
    renderResult(result);
    statusText.textContent = `Rendered ${result.plot.surface_label} and evaluated the contour integral.`;
  } catch (error) {
    symbolicResult.textContent = "Error";
    numericResult.textContent = "Error";
    polarResult.textContent = "Error";
    parsedFunction.textContent = "-";
    parsedContour.textContent = "-";
    integrandDisplay.textContent = "-";
    magnitudeDisplay.textContent = "-";
    statusText.textContent = error.message;
    Plotly.purge(plotElement);
  } finally {
    submitButton.disabled = false;
  }
});

function renderResult(result) {
  symbolicResult.textContent = result.integral.symbolic_result || "No closed form found";
  numericResult.textContent = result.integral.numeric_rectangular;
  polarResult.textContent = result.integral.numeric_polar;
  parsedFunction.textContent = result.function_display;
  parsedContour.textContent = `${result.contour_display}, t in [${result.parameter_interval[0]}, ${result.parameter_interval[1]}]`;
  integrandDisplay.textContent = result.integral.integrand_display;
  magnitudeDisplay.textContent = result.integral.magnitude.toFixed(8);

  const surfaceTrace = {
    type: "surface",
    x: result.plot.surface.x,
    y: result.plot.surface.y,
    z: result.plot.surface.z,
    colorscale: [
      [0, "#11304c"],
      [0.45, "#4d7ea8"],
      [0.7, "#d8c99b"],
      [1, "#fff0b8"],
    ],
    opacity: 0.94,
    hovertemplate: "x=%{x:.3f}<br>y=%{y:.3f}<br>value=%{z:.3f}<extra></extra>",
    showscale: false,
  };

  const contourTrace = {
    type: "scatter3d",
    mode: "lines",
    x: result.plot.contour.x,
    y: result.plot.contour.y,
    z: result.plot.contour.z,
    line: {
      color: "#ff8c42",
      width: 8,
    },
    name: "Contour",
    hovertemplate: "x=%{x:.3f}<br>y=%{y:.3f}<br>surface=%{z:.3f}<extra>Contour</extra>",
  };

  const layout = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { l: 0, r: 0, b: 0, t: 16 },
    scene: {
      bgcolor: "rgba(0,0,0,0)",
      xaxis: {
        title: "Re(z)",
        gridcolor: "rgba(247, 228, 172, 0.18)",
        zerolinecolor: "rgba(247, 228, 172, 0.2)",
      },
      yaxis: {
        title: "Im(z)",
        gridcolor: "rgba(247, 228, 172, 0.18)",
        zerolinecolor: "rgba(247, 228, 172, 0.2)",
      },
      zaxis: {
        title: result.plot.surface_label,
        gridcolor: "rgba(247, 228, 172, 0.18)",
        zerolinecolor: "rgba(247, 228, 172, 0.2)",
      },
      camera: {
        eye: { x: 1.7, y: 1.35, z: 0.95 },
      },
      aspectratio: { x: 1, y: 1, z: 0.75 },
    },
    showlegend: false,
  };

  const config = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["select2d", "lasso2d"],
  };

  Plotly.react(plotElement, [surfaceTrace, contourTrace], layout, config);
}

form.requestSubmit();
