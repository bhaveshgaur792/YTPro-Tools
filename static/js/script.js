const API_ENDPOINT = "https://mindful-gentleness-production.up.railway.app/analyze";

document.getElementById("analyze-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const urlInput = e.target.querySelector("input");
    const url = urlInput.value.trim();
    const resultsDiv = document.getElementById("results");
    const errorDiv = document.getElementById("error");

    // Clear previous state
    resultsDiv.classList.add("d-none");
    errorDiv.classList.add("d-none");
    urlInput.blur();

    if (!url) {
        showError("Please enter a YouTube URL");
        return;
    }

    try {
        const response = await fetch(API_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `url=${encodeURIComponent(url)}`
        });

        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || "Analysis failed");
        }

        updateUI(data);
        resultsDiv.classList.remove("d-none");
    } catch (err) {
        showError(err.message);
        console.error("Analysis error:", err);
    }
});

function updateUI(data) {
    document.getElementById("title").textContent = data.title;
    document.getElementById("channel").textContent = data.channel;
    document.getElementById("views").textContent = data.views;
    document.getElementById("duration").textContent = data.duration;
    document.getElementById("tags").textContent = data.tags.join(", ") || "No tags available";
    document.getElementById("thumbnail").src = data.thumbnail || "./placeholder.jpg";
}

function showError(message) {
    const errorDiv = document.getElementById("error");
    errorDiv.textContent = `Error: ${message}`;
    errorDiv.classList.remove("d-none");
}
