async function loadTickets() {
  const res = await fetch("/tickets/");
  const data = await res.json();
  const container = document.getElementById("ticketList");
  container.innerHTML = "";

  data.results.forEach(ticket => {
    const statusClass = ticket.status.replace(" ", "-");
    const div = document.createElement("div");
    div.className = "ticket";
    div.innerHTML = `
      <strong>#${ticket.id} — ${ticket.title}</strong>
      <span class="status ${statusClass}">${ticket.status}</span>
      <p>${ticket.description}</p>
      <small>By: ${ticket.requester} | Priority: ${ticket.priority} | Agent: ${ticket.assigned_agent || "Unassigned"}</small>
      <br><br>
      <select onchange="updateStatus(${ticket.id}, this.value)">
        <option value="">Change Status...</option>
        <option value="Open">Open</option>
        <option value="In Progress">In Progress</option>
        <option value="Resolved">Resolved</option>
        <option value="Closed">Closed</option>
      </select>
    `;
    container.appendChild(div);
  });
}

async function updateStatus(ticketId, newStatus) {
  if (!newStatus) return;

  const body = { status: newStatus };
  if (newStatus === "Closed" || newStatus === "Resolved") {
    const note = prompt("Enter resolution note:");
    if (note) body.resolution_note = note;
  }

  const res = await fetch(`/tickets/${ticketId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const err = await res.json();
    alert("Error: " + err.detail);
  }
  loadTickets();
}

function setupCreateForm() {
  document.getElementById("createForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const ticket = {
      title: document.getElementById("title").value,
      description: document.getElementById("description").value,
      requester: document.getElementById("requester").value,
      category: document.getElementById("category").value,
      priority: document.getElementById("priority").value
    };

    const res = await fetch("/tickets/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(ticket)
    });

    if (res.ok) {
      e.target.reset();
      loadTickets();
    } else {
      alert("Error creating ticket");
    }
  });
}

setupCreateForm();
loadTickets();