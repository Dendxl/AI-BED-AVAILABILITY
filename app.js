async function fetchHospitals() {
  let res = await fetch("/api/hospitals");
  return await res.json();
}

async function fillHospitalOptions() {
  const hospitals = await fetchHospitals();
  const sel = document.getElementById("hospital_id");
  sel.innerHTML = hospitals.map(h => `<option value="${h.id}">${h.name}</option>`).join("");
}

function updateTable(rows) {
  const body = document.getElementById("datatable");
  body.innerHTML = rows.map(r => `
    <tr>
      <td data-label="Hospital">${r.name}</td>
      <td data-label="Total">${r.total_beds ?? '-'}</td>
      <td data-label="Occupied">${r.occupied_beds ?? '-'}</td>
      <td data-label="Available">${r.available_beds ?? '-'}</td>
      <td data-label="%">${r.percentage ?? '-'}</td>
      <td data-label="Status"><span class="badge ${r.color}">${r.status}</span></td>
      <td data-label="Likely Full">${r.likely_full}</td>
      <td data-label="Updated At">${r.updated_at || '-'}</td>
    </tr>`).join("");
}

async function refreshDashboard() {
  const data = await fetchHospitals();
  updateTable(data);
}

document.getElementById("bedForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const hospital_id = document.getElementById("hospital_id").value;
  const total_beds = document.getElementById("total_beds").value;
  const occupied_beds = document.getElementById("occupied_beds").value;
  const icu_beds = document.getElementById("icu_beds").value;
  const note = document.getElementById("note").value;
  const msg = document.getElementById("message");

  if (Number(occupied_beds) > Number(total_beds)) {
    msg.textContent = "Error: occupied beds cannot exceed total beds.";
    msg.style.color = "red";
    return;
  }

  const resp = await fetch("/api/update", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({hospital_id, total_beds, occupied_beds, icu_beds, note})
  });

  if (resp.ok) {
    msg.textContent = "Data submitted successfully.";
    msg.style.color = "green";
    document.getElementById("bedForm").reset();
    refreshDashboard();
  } else {
    const body = await resp.json();
    msg.textContent = `Failed: ${body.error || "unknown error"}`;
    msg.style.color = "red";
  }
});

window.addEventListener("load", async () => {
  await fillHospitalOptions();
  await refreshDashboard();
  setInterval(refreshDashboard, 5500);
});
