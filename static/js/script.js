document.getElementById("analyze-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = e.target.querySelector("input").value;
    const resultsDiv = document.getElementById("results");
    const errorDiv = document.getElementById("error");

    // Reset UI state
    resultsDiv.classList.add("d-none");
    errorDiv.classList.add("d-none");

    try {
        const response = await fetch("https://mindful-gentleness-production.up.railway.app/analyze", {
            method: "POST",
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded" 
            },
            body: `url=${encodeURIComponent(url)}`
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // Update UI with results
        document.getElementById("title").textContent = data.title;
        document.getElementById("channel").textContent = data.channel;
        document.getElementById("views").textContent = data.views;
        document.getElementById("duration").textContent = data.duration;
        document.getElementById("tags").textContent = data.tags.join(", ") || "No tags found";
        document.getElementById("thumbnail").src = data.thumbnail || "https://via.placeholder.com/300";
        resultsDiv.classList.remove("d-none");
    } catch (err) {
        errorDiv.textContent = `Error: ${err.message}`;
        errorDiv.classList.remove("d-none");
        console.error("Analysis error:", err);
    }
});
