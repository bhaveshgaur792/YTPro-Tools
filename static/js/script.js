document.getElementById("analyze-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const url = e.target.querySelector("input").value;
    const resultsDiv = document.getElementById("results");
    const errorDiv = document.getElementById("error");

    resultsDiv.classList.add("d-none");
    errorDiv.classList.add("d-none");

    try {
        const response = await fetch("https://your-backend.up.railway.app/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: `url=${encodeURIComponent(url)}`
        });
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        document.getElementById("title").textContent = data.title;
        document.getElementById("channel").textContent = data.channel;
        document.getElementById("views").textContent = data.views;
        document.getElementById("duration").textContent = data.duration;
        document.getElementById("tags").textContent = data.tags.join(", ");
        document.getElementById("thumbnail").src = data.thumbnail;
        resultsDiv.classList.remove("d-none");
    } catch (err) {
        errorDiv.textContent = `Error: ${err.message}`;
        errorDiv.classList.remove("d-none");
    }
});
